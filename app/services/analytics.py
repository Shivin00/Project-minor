from collections import Counter

from sqlalchemy.orm import Session

from app.models import AnalysisResult, Post


def build_summary(db: Session) -> dict:
    posts = db.query(Post).all()
    results = db.query(AnalysisResult).all()

    location_counter = Counter(post.location for post in posts)
    sentiment_counter = Counter(result.sentiment_label for result in results)
    topic_counter = Counter()
    for result in results:
        for topic in (result.dominant_topics or "").split(","):
            if topic.strip():
                topic_counter[topic.strip()] += 1

    average_code_mix_score = round(sum(post.code_mix_score for post in posts) / len(posts), 3) if posts else 0.0
    return {
        "total_posts": len(posts),
        "total_results": len(results),
        "top_locations": [{"location": name, "count": count} for name, count in location_counter.most_common(10)],
        "sentiment_distribution": [{"label": name, "count": count} for name, count in sentiment_counter.most_common()],
        "top_topics": [{"topic": name, "count": count} for name, count in topic_counter.most_common(10)],
        "average_code_mix_score": average_code_mix_score,
    }
