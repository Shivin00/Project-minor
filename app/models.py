from datetime import datetime

from sqlalchemy import DateTime, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Post(Base):
    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    source: Mapped[str] = mapped_column(String(100), default="unknown")
    author: Mapped[str] = mapped_column(String(100), default="anonymous")
    location: Mapped[str] = mapped_column(String(120), default="unknown")
    text: Mapped[str] = mapped_column(Text)
    normalized_text: Mapped[str] = mapped_column(Text)
    hashtags: Mapped[str] = mapped_column(Text, default="")
    mentions: Mapped[str] = mapped_column(Text, default="")
    probable_languages: Mapped[str] = mapped_column(String(200), default="unknown")
    code_mix_score: Mapped[float] = mapped_column(Float, default=0.0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class AnalysisResult(Base):
    __tablename__ = "analysis_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    post_id: Mapped[int] = mapped_column(Integer, index=True)
    provider: Mapped[str] = mapped_column(String(50))
    sentiment_label: Mapped[str] = mapped_column(String(30))
    sentiment_score: Mapped[float] = mapped_column(Float, default=0.0)
    dominant_topics: Mapped[str] = mapped_column(Text, default="")
    emotion: Mapped[str] = mapped_column(String(50), default="neutral")
    reasoning: Mapped[str] = mapped_column(Text, default="")
    latency_ms: Mapped[float] = mapped_column(Float, default=0.0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class BenchmarkRun(Base):
    __tablename__ = "benchmark_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    provider_a: Mapped[str] = mapped_column(String(50))
    provider_b: Mapped[str] = mapped_column(String(50))
    compared_posts: Mapped[int] = mapped_column(Integer, default=0)
    disagreement_count: Mapped[int] = mapped_column(Integer, default=0)
    provider_a_avg_confidence: Mapped[float] = mapped_column(Float, default=0.0)
    provider_b_avg_confidence: Mapped[float] = mapped_column(Float, default=0.0)
    provider_a_avg_latency_ms: Mapped[float] = mapped_column(Float, default=0.0)
    provider_b_avg_latency_ms: Mapped[float] = mapped_column(Float, default=0.0)
    summary: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
