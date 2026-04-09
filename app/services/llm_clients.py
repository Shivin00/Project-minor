import json
import time
from typing import Any

import requests

from app.config import settings


SYSTEM_PROMPT = """
You analyze code-mixed regional social media text.
Return valid JSON only with keys:
sentiment_label, sentiment_score, dominant_topics, emotion, reasoning.
sentiment_label must be one of: positive, negative, neutral, mixed.
sentiment_score must be between 0 and 1.
dominant_topics must be a JSON array of short topic strings.
""".strip()


def _safe_parse_json(raw_text: str) -> dict[str, Any]:
    raw_text = raw_text.strip()
    if raw_text.startswith("```"):
        raw_text = raw_text.strip("`")
        raw_text = raw_text.replace("json", "", 1).strip()
    try:
        return json.loads(raw_text)
    except json.JSONDecodeError:
        start = raw_text.find("{")
        end = raw_text.rfind("}")
        if start != -1 and end != -1:
            return json.loads(raw_text[start : end + 1])
        raise


def call_openai(text: str) -> tuple[dict[str, Any], float]:
    if not settings.openai_api_key:
        raise ValueError("OPENAI_API_KEY is not configured.")

    url = f"{settings.openai_base_url.rstrip('/')}/chat/completions"
    payload = {
        "model": settings.openai_model,
        "temperature": 0.1,
        "response_format": {"type": "json_object"},
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Text: {text}"},
        ],
    }
    headers = {
        "Authorization": f"Bearer {settings.openai_api_key}",
        "Content-Type": "application/json",
    }

    started = time.perf_counter()
    response = requests.post(url, json=payload, headers=headers, timeout=60)
    response.raise_for_status()
    latency_ms = (time.perf_counter() - started) * 1000
    content = response.json()["choices"][0]["message"]["content"]
    return _safe_parse_json(content), round(latency_ms, 2)


def call_ollama(text: str) -> tuple[dict[str, Any], float]:
    url = f"{settings.ollama_base_url.rstrip('/')}/api/chat"
    payload = {
        "model": settings.ollama_model,
        "stream": False,
        "format": "json",
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Text: {text}"},
        ],
    }

    started = time.perf_counter()
    response = requests.post(url, json=payload, timeout=120)
    response.raise_for_status()
    latency_ms = (time.perf_counter() - started) * 1000
    content = response.json()["message"]["content"]
    return _safe_parse_json(content), round(latency_ms, 2)
