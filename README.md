# Code-Mixed Language Processing for Hyper-Local Sentiment Analytics

An end-to-end project for ingesting code-mixed social media or forum text, classifying sentiment, extracting hyper-local themes, and benchmarking local quantized LLMs against cloud APIs.

## What this project does

- Ingests JSON/JSONL social posts containing code-mixed text such as Punjabi-English or Hindi-English.
- Detects code-mixing signals with lightweight heuristics.
- Runs sentiment and topic extraction through one of three providers:
  - `rule_based`: offline baseline that works without any external API.
  - `ollama`: local quantized LLM inference through the Ollama HTTP API.
  - `openai`: cloud inference using OpenAI-compatible chat completions.
- Stores results in SQLite.
- Exposes analytics and benchmarking through a FastAPI backend.
- Includes a Streamlit dashboard for interactive exploration.

## Why this is publishable

This project targets a real NLP blind spot: models trained on standard English often fail on regional, conversational, romanized, and code-mixed text. The benchmark API helps compare local quantized models for privacy, cost, and latency against cloud APIs for structured extraction quality.

## Architecture

```text
sample_data / external data
        |
        v
FastAPI ingestion endpoints
        |
        v
preprocessing + code-mix heuristics
        |
        v
provider layer
  - rule_based
  - ollama
  - openai
        |
        v
SQLite storage
        |
        +--> analytics endpoints
        +--> benchmark endpoints
        +--> Streamlit dashboard
```

## Project structure

```text
app/
  main.py
  config.py
  database.py
  models.py
  schemas.py
  services/
    analytics.py
    benchmark.py
    llm_clients.py
    preprocessing.py
    sentiment.py
dashboard.py
sample_data/
  code_mixed_posts.jsonl
requirements.txt
.env.example
```

## Data format

Input records can be JSON arrays or JSONL. Each item should look like:

```json
{
  "source": "local_forum",
  "author": "user_001",
  "location": "Ludhiana",
  "text": "Yaar road condition bohot kharab hai, but market vibes were still nice."
}
```

## Implementation details

### 1. Ingestion

- Use `POST /api/v1/ingest/sample` to load the included sample dataset.
- Use `POST /api/v1/ingest/json` to upload custom JSON or JSONL content.
- Every post is normalized before storage.

### 2. Preprocessing

The pipeline performs:

- lowercasing and whitespace cleanup
- text length limiting
- hashtag and mention extraction
- heuristic code-mix scoring
- probable language tagging

The heuristic is intentionally simple so you can later replace it with FastText language ID, transliteration normalization, token-level language identification, or transformer-based tagging.

### 3. Sentiment extraction

Each provider returns structured output in a common schema:

```json
{
  "sentiment_label": "positive",
  "sentiment_score": 0.84,
  "dominant_topics": ["roads", "market"],
  "emotion": "frustrated",
  "reasoning": "speaker complains about roads but appreciates market vibe"
}
```

### 4. Benchmarking

The benchmark runner compares two providers on the same dataset and records:

- prediction disagreement count
- label distribution
- average confidence
- average latency in milliseconds

For publication-quality evaluation, extend it with gold labels, F1 score, Cohen's kappa, and human judgment rubrics.

## Setup

### 1. Create a virtual environment

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

### 2. Install dependencies

```powershell
pip install -r requirements.txt
```

### 3. Configure environment

```powershell
Copy-Item .env.example .env
```

Edit `.env` depending on your provider.

## Provider setup

### Option A: Offline baseline

No API key required. Use provider value `rule_based`.

### Option B: Ollama local quantized model

1. Install Ollama.
2. Start the Ollama server.
3. Pull a quantized model:

```powershell
ollama pull llama3.1:8b-instruct-q4_K_M
```

4. Keep these values in `.env`:

```text
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.1:8b-instruct-q4_K_M
```

Use provider value `ollama`.

### Option C: OpenAI cloud API

Put your key in `.env`:

```text
OPENAI_API_KEY=your_key_here
OPENAI_MODEL=gpt-4o-mini
OPENAI_BASE_URL=https://api.openai.com/v1
```

Use provider value `openai`.

## Run the backend

```powershell
uvicorn app.main:app --reload
```

Backend docs:

- Swagger UI: `http://127.0.0.1:8000/docs`
- Health check: `http://127.0.0.1:8000/health`

## Run the dashboard

```powershell
streamlit run dashboard.py
```

Set a custom backend URL for Streamlit if the API is hosted elsewhere:

```powershell
$env:API_BASE_URL="https://your-project.vercel.app"
streamlit run dashboard.py
```

## Typical workflow

```powershell
curl -X POST http://127.0.0.1:8000/api/v1/ingest/sample
curl -X POST "http://127.0.0.1:8000/api/v1/analyze/run?provider=rule_based"
curl -X POST "http://127.0.0.1:8000/api/v1/benchmark/run?provider_a=ollama&provider_b=openai"
curl http://127.0.0.1:8000/api/v1/analytics/summary
```

## Deploy on Vercel

Vercel is a good fit for the FastAPI app. For deployment, use the built-in browser dashboard at `/` instead of the local Streamlit UI.

### Important production note

Do not use SQLite on Vercel for persistent data. Vercel Functions are stateless, so local files like `data/app.db` are not reliable for production storage. Use a hosted Postgres database and set `DATABASE_URL` in Vercel.

Example `DATABASE_URL`:

```text
postgresql+psycopg://USER:PASSWORD@HOST:5432/DATABASE
```

### What was added for Vercel

- [app/index.py](/c:/Users/SHIVIN/Desktop/Project%20-%20Minor/app/index.py) as the Vercel Python entrypoint
- [vercel.json](/c:/Users/SHIVIN/Desktop/Project%20-%20Minor/vercel.json) with function config
- a built-in dashboard on `/` served directly by FastAPI in [app/main.py](/c:/Users/SHIVIN/Desktop/Project%20-%20Minor/app/main.py)

### Deploy steps

1. Push this project to GitHub.
2. In Vercel, click `Add New Project`.
3. Import the GitHub repository.
4. In Project Settings, add these environment variables:

```text
APP_NAME=Code-Mixed Hyper-Local Sentiment Analytics
APP_ENV=production
DATABASE_URL=postgresql+psycopg://USER:PASSWORD@HOST:5432/DATABASE
OPENAI_API_KEY=
OPENAI_MODEL=gpt-4o-mini
OPENAI_BASE_URL=https://api.openai.com/v1
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.1:8b-instruct-q4_K_M
MAX_TEXT_LENGTH=1200
```

5. Deploy.
6. Open the deployed URL and use `/` for the dashboard or `/docs` for the API.

### Recommended provider choice on Vercel

- `rule_based`: best default for a reliable demo
- `openai`: good for cloud inference if `OPENAI_API_KEY` is set
- `ollama`: not suitable for Vercel unless you host Ollama separately and expose an accessible URL

## Suggested thesis/report sections

1. Problem statement: failure of standard NLP on code-mixed regional text.
2. Dataset design: local forum/social posts, annotation schema, class balance.
3. Methods: preprocessing, prompt design, provider abstraction, benchmarking.
4. Experiments: rule-based vs quantized local LLM vs cloud model.
5. Metrics: accuracy, latency, cost, privacy, topic quality.
6. Results: where quantized local models succeed or fail.
7. Future work: token-level language tagging and gold-label evaluation.

## Important notes

- The included code-mix detector is heuristic and intended as a strong starter, not a final research model.
- The benchmark endpoint is comparative; for a paper, add gold annotations and test-set metrics.
- If you want a fully local demo, `rule_based` and `ollama` are enough.
