from __future__ import annotations

import hashlib
import json
import math
import re

VECTOR_DIMENSIONS = 96


def text_vector(text: str, dimensions: int = VECTOR_DIMENSIONS) -> dict[str, float]:
    buckets: dict[str, float] = {}
    for token in _tokens(text):
        bucket = str(_bucket(token, dimensions))
        buckets[bucket] = buckets.get(bucket, 0.0) + 1.0
    norm = math.sqrt(sum(value * value for value in buckets.values()))
    if norm == 0:
        return {}
    return {key: value / norm for key, value in buckets.items()}


def cosine_similarity(left: dict[str, float], right: dict[str, float]) -> float:
    if not left or not right:
        return 0.0
    small, large = (left, right) if len(left) <= len(right) else (right, left)
    return sum(value * large.get(key, 0.0) for key, value in small.items())


def serialize_vector(vector: dict[str, float]) -> str:
    return json.dumps(vector, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def deserialize_vector(payload: str) -> dict[str, float]:
    try:
        raw = json.loads(payload)
    except json.JSONDecodeError:
        return {}
    if not isinstance(raw, dict):
        return {}
    return {str(key): float(value) for key, value in raw.items() if isinstance(value, int | float)}


def _tokens(text: str) -> list[str]:
    tokens: list[str] = []
    for part in re.findall(r"[a-zA-Z0-9_]+|[\u4e00-\u9fff]+", text.lower()):
        tokens.append(part)
        if _is_cjk(part) and len(part) > 1:
            tokens.extend(part[i : i + 2] for i in range(len(part) - 1))
    return [token for token in tokens if len(token) >= 2]


def _bucket(token: str, dimensions: int) -> int:
    digest = hashlib.sha256(token.encode("utf-8")).digest()
    return int.from_bytes(digest[:4], "big") % dimensions


def _is_cjk(text: str) -> bool:
    return any("\u4e00" <= char <= "\u9fff" for char in text)
