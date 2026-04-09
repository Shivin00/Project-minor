import os

import pandas as pd
import plotly.express as px
import requests
import streamlit as st


API_BASE = os.getenv("API_BASE_URL", "http://127.0.0.1:8000")

st.set_page_config(page_title="Code-Mixed Sentiment Dashboard", layout="wide")
st.title("Code-Mixed Hyper-Local Sentiment Dashboard")

summary_resp = requests.get(f"{API_BASE}/api/v1/analytics/summary", timeout=15)
posts_resp = requests.get(f"{API_BASE}/api/v1/posts?limit=200", timeout=15)
results_resp = requests.get(f"{API_BASE}/api/v1/results?limit=200", timeout=15)

if summary_resp.status_code != 200:
    st.error("Backend is not ready yet. Start FastAPI and ingest/analyze data first.")
    st.stop()

summary = summary_resp.json()
posts = posts_resp.json() if posts_resp.status_code == 200 else []
results = results_resp.json() if results_resp.status_code == 200 else []

metric_columns = st.columns(4)
metric_columns[0].metric("Posts", summary["total_posts"])
metric_columns[1].metric("Results", summary["total_results"])
metric_columns[2].metric("Avg Code-Mix Score", summary["average_code_mix_score"])
metric_columns[3].metric("Top Topic Count", summary["top_topics"][0]["count"] if summary["top_topics"] else 0)

sentiment_df = pd.DataFrame(summary["sentiment_distribution"])
location_df = pd.DataFrame(summary["top_locations"])
topic_df = pd.DataFrame(summary["top_topics"])
posts_df = pd.DataFrame(posts)
results_df = pd.DataFrame(results)

chart_columns = st.columns(2)

if not sentiment_df.empty:
    chart_columns[0].plotly_chart(
        px.bar(sentiment_df, x="label", y="count", title="Sentiment Distribution", color="label"),
        use_container_width=True,
    )

if not location_df.empty:
    chart_columns[1].plotly_chart(
        px.bar(location_df, x="location", y="count", title="Top Locations"),
        use_container_width=True,
    )

if not topic_df.empty:
    st.plotly_chart(px.bar(topic_df, x="topic", y="count", title="Top Topics"), use_container_width=True)

if not posts_df.empty:
    st.subheader("Latest Posts")
    st.dataframe(posts_df[["id", "location", "probable_languages", "code_mix_score", "text"]], use_container_width=True)

if not results_df.empty:
    st.subheader("Latest Analysis Results")
    st.dataframe(
        results_df[["id", "provider", "sentiment_label", "sentiment_score", "dominant_topics", "emotion", "latency_ms"]],
        use_container_width=True,
    )
