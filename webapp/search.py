from __future__ import annotations

import re

from webapp.models import SearchHit
from webapp.storage import KnowledgeStore
from webapp.vector_index import cosine_similarity, text_vector


def search_documents(
    store: KnowledgeStore,
    project_id: str,
    query: str,
    limit: int = 5,
) -> list[SearchHit]:
    tokens = _tokenize(query)
    query_vector = text_vector(query)
    chunk_vectors = store.list_chunk_vectors(project_id)
    hits: list[SearchHit] = []
    for chunk in store.list_chunks(project_id):
        keyword_score = _score(chunk.content, tokens, query)
        vector_score = cosine_similarity(query_vector, chunk_vectors.get(chunk.id, {}))
        score = keyword_score + vector_score
        hits.append(
            SearchHit(
                document=chunk.document,
                score=score,
                snippet=_snippet(chunk.content, tokens),
                chunk=chunk,
                keyword_score=keyword_score,
                vector_score=vector_score,
                retrieval="hybrid",
            )
        )
    hits.sort(
        key=lambda hit: (hit.score, hit.document.updated_at, -_chunk_index(hit)),
        reverse=True,
    )
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


def _chunk_index(hit: SearchHit) -> int:
    return hit.chunk.chunk_index if hit.chunk is not None else 0
