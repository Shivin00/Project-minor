from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class IngestRecord(BaseModel):
    source: str = "unknown"
    author: str = "anonymous"
    location: str = "unknown"
    text: str


class IngestResponse(BaseModel):
    inserted: int
    total_posts: int


class AnalysisOutput(BaseModel):
    sentiment_label: str
    sentiment_score: float
    dominant_topics: list[str] = Field(default_factory=list)
    emotion: str
    reasoning: str
    latency_ms: float = 0.0


class SummaryResponse(BaseModel):
    total_posts: int
    total_results: int
    top_locations: list[dict[str, Any]]
    sentiment_distribution: list[dict[str, Any]]
    top_topics: list[dict[str, Any]]
    average_code_mix_score: float


class BenchmarkResponse(BaseModel):
    benchmark_id: int
    provider_a: str
    provider_b: str
    compared_posts: int
    disagreement_count: int
    provider_a_avg_confidence: float
    provider_b_avg_confidence: float
    provider_a_avg_latency_ms: float
    provider_b_avg_latency_ms: float
    summary: str
