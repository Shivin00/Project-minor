import re
from collections import Counter

from app.config import settings


ROMANIZED_INDIC_HINTS = {
    "punjabi": {"yaar", "bohot", "bahut", "sahi", "kudi", "pind", "veere", "acha", "achha", "nahi", "haan"},
    "hindi": {"yaar", "bohot", "bahut", "nahi", "acha", "achha", "mast", "bekaar", "jaldi", "thoda"},
    "hinglish": {"scene", "vibes", "issue", "yaar", "nahi", "bro", "market", "road"},
}


def normalize_text(text: str) -> str:
    text = (text or "").strip()
    text = re.sub(r"\s+", " ", text)
    return text[: settings.max_text_length]


def extract_hashtags(text: str) -> list[str]:
    return re.findall(r"#(\w+)", text)


def extract_mentions(text: str) -> list[str]:
    return re.findall(r"@(\w+)", text)


def detect_probable_languages(text: str) -> tuple[list[str], float]:
    tokens = [token.lower() for token in re.findall(r"[a-zA-Z']+", text)]
    if not tokens:
        return ["unknown"], 0.0

    token_counts = Counter(tokens)
    matched = {}
    for language, hints in ROMANIZED_INDIC_HINTS.items():
        overlap = sum(token_counts[token] for token in hints if token in token_counts)
        if overlap:
            matched[language] = overlap

    english_like = sum(1 for token in tokens if len(token) > 3 and token.isascii())
    mix_score = min(1.0, (len(matched) * 0.25) + (english_like / max(len(tokens), 1)) * 0.5)

    if not matched:
        return ["english"], round(min(1.0, english_like / max(len(tokens), 1)), 3)

    languages = sorted(matched, key=matched.get, reverse=True)
    return languages, round(mix_score, 3)


def preprocess_record(record: dict) -> dict:
    text = normalize_text(record.get("text", ""))
    probable_languages, code_mix_score = detect_probable_languages(text)
    return {
        "source": record.get("source", "unknown"),
        "author": record.get("author", "anonymous"),
        "location": record.get("location", "unknown"),
        "text": record.get("text", ""),
        "normalized_text": text.lower(),
        "hashtags": ",".join(extract_hashtags(text)),
        "mentions": ",".join(extract_mentions(text)),
        "probable_languages": ",".join(probable_languages),
        "code_mix_score": code_mix_score,
    }
