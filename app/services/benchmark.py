from statistics import mean

from sqlalchemy.orm import Session

from app.models import BenchmarkRun, Post
from app.services.sentiment import analyze_text


def run_benchmark(db: Session, provider_a: str, provider_b: str, limit: int = 25) -> BenchmarkRun:
    posts = db.query(Post).order_by(Post.id.desc()).limit(limit).all()
    if not posts:
        raise ValueError("No posts found. Ingest data before benchmarking.")

    results_a = [analyze_text(post.normalized_text, provider_a) for post in posts]
    results_b = [analyze_text(post.normalized_text, provider_b) for post in posts]
    disagreement_count = sum(1 for left, right in zip(results_a, results_b) if left.sentiment_label != right.sentiment_label)

    benchmark = BenchmarkRun(
        provider_a=provider_a,
        provider_b=provider_b,
        compared_posts=len(posts),
        disagreement_count=disagreement_count,
        provider_a_avg_confidence=round(mean(result.sentiment_score for result in results_a), 3),
        provider_b_avg_confidence=round(mean(result.sentiment_score for result in results_b), 3),
        provider_a_avg_latency_ms=round(mean(result.latency_ms for result in results_a), 2),
        provider_b_avg_latency_ms=round(mean(result.latency_ms for result in results_b), 2),
        summary=(
            f"Compared {len(posts)} posts. Disagreements: {disagreement_count}. "
            f"{provider_a} avg confidence {round(mean(result.sentiment_score for result in results_a), 3)} vs "
            f"{provider_b} avg confidence {round(mean(result.sentiment_score for result in results_b), 3)}."
        ),
    )
    db.add(benchmark)
    db.commit()
    db.refresh(benchmark)
    return benchmark
