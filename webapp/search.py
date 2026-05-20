from __future__ import annotations

import re

from webapp.models import SearchHit
from webapp.storage import KnowledgeStore


def search_documents(
    store: KnowledgeStore,
    project_id: str,
    query: str,
    limit: int = 5,
) -> list[SearchHit]:
    tokens = _tokenize(query)
    hits: list[SearchHit] = []
    for document in store.list_documents(project_id):
        score = _score(document.content, tokens, query)
        hits.append(SearchHit(document=document, score=score, snippet=_snippet(document.content, tokens)))
    hits.sort(key=lambda hit: (hit.score, hit.document.updated_at), reverse=True)
    return hits[:limit]


def _tokenize(text: str) -> list[str]:
    tokens: list[str] = []
    for part in re.findall(r"[a-zA-Z0-9_]+|[\u4e00-\u9fff]+", text.lower()):
        tokens.append(part)
        if _is_cjk(part) and len(part) > 1:
            tokens.extend(part[i : i + 2] for i in range(len(part) - 1))
    return [token for token in tokens if len(token) >= 2]


def _score(content: str, tokens: list[str], query: str) -> float:
    lowered = content.lower()
    score = 0.0
    for token in tokens:
        score += lowered.count(token) * (2.0 if _is_cjk(token) else 1.0)
    compact_query = re.sub(r"\W+", "", query.lower())
    compact_content = re.sub(r"\W+", "", lowered)
    if compact_query and compact_query in compact_content:
        score += 5.0
    return score


def _snippet(content: str, tokens: list[str], radius: int = 80) -> str:
    lowered = content.lower()
    positions = [lowered.find(token) for token in tokens if token and lowered.find(token) >= 0]
    start = max(min(positions) - radius, 0) if positions else 0
    end = min(start + radius * 2, len(content))
    return content[start:end].replace("\n", " ").strip()


def _is_cjk(text: str) -> bool:
    return any("\u4e00" <= char <= "\u9fff" for char in text)
