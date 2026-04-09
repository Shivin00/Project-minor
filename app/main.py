import json
from pathlib import Path

from fastapi import Depends, FastAPI, File, HTTPException, Query, UploadFile
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from app.config import settings
from app.database import Base, engine, get_db
from app.models import AnalysisResult, BenchmarkRun, Post
from app.schemas import BenchmarkResponse, IngestRecord, IngestResponse, SummaryResponse
from app.services.analytics import build_summary
from app.services.benchmark import run_benchmark
from app.services.preprocessing import preprocess_record
from app.services.sentiment import analyze_text


Base.metadata.create_all(bind=engine)

app = FastAPI(title=settings.app_name, version="1.0.0")
PROJECT_ROOT = Path(__file__).resolve().parent.parent
SAMPLE_DATA_PATH = PROJECT_ROOT / "sample_data" / "code_mixed_posts.jsonl"


DEPLOY_DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Code-Mixed Sentiment Analytics</title>
  <style>
    :root {
      --bg: #f3efe7;
      --card: rgba(255, 251, 245, 0.95);
      --ink: #1f2933;
      --accent: #0f766e;
      --accent-2: #b45309;
      --line: rgba(31, 41, 51, 0.12);
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: Georgia, "Times New Roman", serif;
      color: var(--ink);
      background:
        radial-gradient(circle at top left, rgba(180, 83, 9, 0.12), transparent 30%),
        radial-gradient(circle at top right, rgba(15, 118, 110, 0.15), transparent 28%),
        linear-gradient(180deg, #faf7f2 0%, var(--bg) 100%);
    }
    .wrap {
      max-width: 1100px;
      margin: 0 auto;
      padding: 32px 20px 56px;
    }
    .hero, .card {
      background: var(--card);
      border: 1px solid var(--line);
      border-radius: 20px;
      box-shadow: 0 14px 36px rgba(31, 41, 51, 0.08);
    }
    .hero {
      padding: 28px;
      margin-bottom: 22px;
    }
    h1, h2, h3 { margin-top: 0; }
    h1 { font-size: clamp(2rem, 5vw, 3.4rem); line-height: 1; margin-bottom: 10px; }
    p { line-height: 1.6; }
    .actions {
      display: flex;
      flex-wrap: wrap;
      gap: 12px;
      margin-top: 18px;
    }
    button, a.button {
      border: none;
      text-decoration: none;
      cursor: pointer;
      padding: 12px 16px;
      border-radius: 999px;
      color: white;
      background: var(--accent);
      font-size: 0.95rem;
    }
    .secondary {
      background: var(--accent-2);
    }
    .grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
      gap: 16px;
      margin-bottom: 18px;
    }
    .card { padding: 20px; }
    .metric {
      font-size: 2rem;
      font-weight: 700;
      margin: 6px 0 0;
    }
    .subtle {
      color: rgba(31, 41, 51, 0.72);
      font-size: 0.95rem;
    }
    .row {
      display: grid;
      grid-template-columns: 1.1fr 0.9fr;
      gap: 18px;
      margin-top: 18px;
    }
    table {
      width: 100%;
      border-collapse: collapse;
      font-size: 0.94rem;
    }
    th, td {
      text-align: left;
      padding: 10px 8px;
      border-bottom: 1px solid var(--line);
      vertical-align: top;
    }
    code {
      background: rgba(15, 118, 110, 0.08);
      padding: 2px 6px;
      border-radius: 8px;
    }
    .status {
      min-height: 24px;
      margin-top: 12px;
      font-size: 0.95rem;
    }
    @media (max-width: 800px) {
      .row { grid-template-columns: 1fr; }
    }
  </style>
</head>
<body>
  <div class="wrap">
    <section class="hero">
      <h1>Code-Mixed Hyper-Local Sentiment Analytics</h1>
      <p>
        This deploy-friendly dashboard runs directly from the FastAPI app, which makes it a better fit for Vercel.
        For local development, you can still use the Streamlit dashboard.
      </p>
      <div class="actions">
        <button id="loadSample">Load Sample Data</button>
        <button id="runAnalysis" class="secondary">Run Rule-Based Analysis</button>
        <a class="button" href="/docs">Open API Docs</a>
      </div>
      <div class="status" id="status"></div>
    </section>

    <section class="grid">
      <div class="card"><div class="subtle">Posts</div><div class="metric" id="totalPosts">0</div></div>
      <div class="card"><div class="subtle">Results</div><div class="metric" id="totalResults">0</div></div>
      <div class="card"><div class="subtle">Avg Code-Mix Score</div><div class="metric" id="avgMix">0</div></div>
      <div class="card"><div class="subtle">Top Topic</div><div class="metric" id="topTopic">-</div></div>
    </section>

    <section class="row">
      <div class="card">
        <h2>Recent Posts</h2>
        <table>
          <thead>
            <tr><th>Location</th><th>Languages</th><th>Code-Mix</th><th>Text</th></tr>
          </thead>
          <tbody id="postsBody">
            <tr><td colspan="4" class="subtle">No posts yet.</td></tr>
          </tbody>
        </table>
      </div>
      <div class="card">
        <h2>Top Topics</h2>
        <table>
          <thead>
            <tr><th>Topic</th><th>Count</th></tr>
          </thead>
          <tbody id="topicsBody">
            <tr><td colspan="2" class="subtle">No topics yet.</td></tr>
          </tbody>
        </table>
        <h3 style="margin-top: 24px;">Sentiment Distribution</h3>
        <table>
          <thead>
            <tr><th>Label</th><th>Count</th></tr>
          </thead>
          <tbody id="sentimentBody">
            <tr><td colspan="2" class="subtle">No results yet.</td></tr>
          </tbody>
        </table>
      </div>
    </section>
  </div>

  <script>
    const statusNode = document.getElementById("status");

    function setStatus(message, isError = false) {
      statusNode.textContent = message;
      statusNode.style.color = isError ? "#b91c1c" : "#0f766e";
    }

    function renderRows(targetId, rows, emptyCols, mapRow) {
      const body = document.getElementById(targetId);
      if (!rows.length) {
        body.innerHTML = `<tr><td colspan="${emptyCols}" class="subtle">No data yet.</td></tr>`;
        return;
      }
      body.innerHTML = rows.map(mapRow).join("");
    }

    async function refreshDashboard() {
      const [summaryRes, postsRes] = await Promise.all([
        fetch("/api/v1/analytics/summary"),
        fetch("/api/v1/posts?limit=10")
      ]);

      if (!summaryRes.ok) {
        throw new Error("Could not load analytics summary.");
      }

      const summary = await summaryRes.json();
      const posts = postsRes.ok ? await postsRes.json() : [];

      document.getElementById("totalPosts").textContent = summary.total_posts;
      document.getElementById("totalResults").textContent = summary.total_results;
      document.getElementById("avgMix").textContent = summary.average_code_mix_score;
      document.getElementById("topTopic").textContent = summary.top_topics.length ? summary.top_topics[0].topic : "-";

      renderRows("postsBody", posts, 4, (post) => `
        <tr>
          <td>${post.location}</td>
          <td>${post.probable_languages}</td>
          <td>${post.code_mix_score}</td>
          <td>${post.text}</td>
        </tr>
      `);

      renderRows("topicsBody", summary.top_topics, 2, (topic) => `
        <tr><td>${topic.topic}</td><td>${topic.count}</td></tr>
      `);

      renderRows("sentimentBody", summary.sentiment_distribution, 2, (item) => `
        <tr><td>${item.label}</td><td>${item.count}</td></tr>
      `);
    }

    async function postAndRefresh(url, message) {
      setStatus(message);
      const response = await fetch(url, { method: "POST" });
      if (!response.ok) {
        const error = await response.text();
        throw new Error(error);
      }
      await refreshDashboard();
      setStatus("Success.");
    }

    document.getElementById("loadSample").addEventListener("click", async () => {
      try {
        await postAndRefresh("/api/v1/ingest/sample", "Loading sample dataset...");
      } catch (error) {
        setStatus(error.message, true);
      }
    });

    document.getElementById("runAnalysis").addEventListener("click", async () => {
      try {
        await postAndRefresh("/api/v1/analyze/run?provider=rule_based", "Running rule-based analysis...");
      } catch (error) {
        setStatus(error.message, true);
      }
    });

    refreshDashboard().catch(() => {
      setStatus("Deploy is live. Load sample data to populate the dashboard.");
    });
  </script>
</body>
</html>
""".strip()


@app.get("/", response_class=HTMLResponse)
def root_dashboard():
    return HTMLResponse(content=DEPLOY_DASHBOARD_HTML)


@app.get("/health")
def health_check():
    return {"status": "ok", "app": settings.app_name, "environment": settings.app_env}


@app.post("/api/v1/ingest/sample", response_model=IngestResponse)
def ingest_sample(db: Session = Depends(get_db)):
    if not SAMPLE_DATA_PATH.exists():
        raise HTTPException(status_code=404, detail="Sample data file not found.")

    inserted = 0
    with SAMPLE_DATA_PATH.open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            payload = preprocess_record(json.loads(line))
            db.add(Post(**payload))
            inserted += 1

    db.commit()
    return IngestResponse(inserted=inserted, total_posts=db.query(Post).count())


@app.post("/api/v1/ingest/json", response_model=IngestResponse)
async def ingest_json(file: UploadFile = File(...), db: Session = Depends(get_db)):
    content = (await file.read()).decode("utf-8")
    inserted = 0

    try:
        if content.lstrip().startswith("["):
            records = json.loads(content)
            for record in records:
                payload = preprocess_record(IngestRecord(**record).model_dump())
                db.add(Post(**payload))
                inserted += 1
        else:
            for line in content.splitlines():
                if not line.strip():
                    continue
                record = json.loads(line)
                payload = preprocess_record(IngestRecord(**record).model_dump())
                db.add(Post(**payload))
                inserted += 1
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Invalid JSON input: {exc}") from exc

    db.commit()
    return IngestResponse(inserted=inserted, total_posts=db.query(Post).count())


@app.post("/api/v1/analyze/run")
def analyze_posts(
    provider: str = Query("rule_based", pattern="^(rule_based|ollama|openai)$"),
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
):
    posts = db.query(Post).order_by(Post.id.desc()).limit(limit).all()
    if not posts:
        raise HTTPException(status_code=404, detail="No posts found. Ingest data first.")

    inserted = 0
    for post in posts:
        output = analyze_text(post.normalized_text, provider)
        db.add(
            AnalysisResult(
                post_id=post.id,
                provider=provider,
                sentiment_label=output.sentiment_label,
                sentiment_score=output.sentiment_score,
                dominant_topics=",".join(output.dominant_topics),
                emotion=output.emotion,
                reasoning=output.reasoning,
                latency_ms=output.latency_ms,
            )
        )
        inserted += 1

    db.commit()
    return {"provider": provider, "processed_posts": inserted}


@app.get("/api/v1/analytics/summary", response_model=SummaryResponse)
def analytics_summary(db: Session = Depends(get_db)):
    return SummaryResponse(**build_summary(db))


@app.get("/api/v1/posts")
def list_posts(limit: int = Query(100, ge=1, le=500), db: Session = Depends(get_db)):
    posts = db.query(Post).order_by(Post.id.desc()).limit(limit).all()
    return [
        {
            "id": post.id,
            "source": post.source,
            "author": post.author,
            "location": post.location,
            "text": post.text,
            "probable_languages": post.probable_languages,
            "code_mix_score": post.code_mix_score,
            "created_at": post.created_at,
        }
        for post in posts
    ]


@app.get("/api/v1/results")
def list_results(
    provider: str | None = Query(default=None, pattern="^(rule_based|ollama|openai)$"),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    query = db.query(AnalysisResult).order_by(AnalysisResult.id.desc())
    if provider:
        query = query.filter(AnalysisResult.provider == provider)
    results = query.limit(limit).all()
    return [
        {
            "id": result.id,
            "post_id": result.post_id,
            "provider": result.provider,
            "sentiment_label": result.sentiment_label,
            "sentiment_score": result.sentiment_score,
            "dominant_topics": result.dominant_topics.split(",") if result.dominant_topics else [],
            "emotion": result.emotion,
            "reasoning": result.reasoning,
            "latency_ms": result.latency_ms,
            "created_at": result.created_at,
        }
        for result in results
    ]


@app.post("/api/v1/benchmark/run", response_model=BenchmarkResponse)
def benchmark(
    provider_a: str = Query(..., pattern="^(rule_based|ollama|openai)$"),
    provider_b: str = Query(..., pattern="^(rule_based|ollama|openai)$"),
    limit: int = Query(25, ge=1, le=200),
    db: Session = Depends(get_db),
):
    if provider_a == provider_b:
        raise HTTPException(status_code=400, detail="Choose two different providers for benchmarking.")

    try:
        benchmark_run = run_benchmark(db, provider_a, provider_b, limit=limit)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return BenchmarkResponse(
        benchmark_id=benchmark_run.id,
        provider_a=benchmark_run.provider_a,
        provider_b=benchmark_run.provider_b,
        compared_posts=benchmark_run.compared_posts,
        disagreement_count=benchmark_run.disagreement_count,
        provider_a_avg_confidence=benchmark_run.provider_a_avg_confidence,
        provider_b_avg_confidence=benchmark_run.provider_b_avg_confidence,
        provider_a_avg_latency_ms=benchmark_run.provider_a_avg_latency_ms,
        provider_b_avg_latency_ms=benchmark_run.provider_b_avg_latency_ms,
        summary=benchmark_run.summary,
    )


@app.get("/api/v1/benchmark/history")
def benchmark_history(limit: int = Query(25, ge=1, le=200), db: Session = Depends(get_db)):
    history = db.query(BenchmarkRun).order_by(BenchmarkRun.id.desc()).limit(limit).all()
    return [
        {
            "id": item.id,
            "provider_a": item.provider_a,
            "provider_b": item.provider_b,
            "compared_posts": item.compared_posts,
            "disagreement_count": item.disagreement_count,
            "provider_a_avg_confidence": item.provider_a_avg_confidence,
            "provider_b_avg_confidence": item.provider_b_avg_confidence,
            "provider_a_avg_latency_ms": item.provider_a_avg_latency_ms,
            "provider_b_avg_latency_ms": item.provider_b_avg_latency_ms,
            "summary": item.summary,
            "created_at": item.created_at,
        }
        for item in history
    ]
