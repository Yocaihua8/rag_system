from __future__ import annotations

from collections import Counter
import math
import re

from backend.knowledge_island.embeddings import EmbeddingClient, embed_with_fallback, get_default_embedding_client
from backend.knowledge_island.models import DocumentChunk, SearchHit
from backend.knowledge_island.storage import KnowledgeStore


def search_documents(
    store: KnowledgeStore,
    project_id: str,
    query: str,
    limit: int = 5,
    embedding_client: EmbeddingClient | None = None,
    use_keyword: bool = True,
    use_vector: bool = True,
    vector_backend=None,
) -> list[SearchHit]:
    from backend.knowledge_island.vector_backend import get_vector_backend

    tokens = _tokenize(query)
    chunks = store.list_chunks(project_id)
    chunks_by_id = {chunk.id: chunk for chunk in chunks}
    keyword_scores = _bm25_keyword_scores(chunks, tokens) if use_keyword else {}
    query_vector = {}
    if use_vector:
        query_vectors, _, _ = embed_with_fallback(
            embedding_client or get_default_embedding_client(),
            [query],
        )
        query_vector = query_vectors[0] if query_vectors else {}
    ann_hits: dict[str, float] = {}
    backend = vector_backend or get_vector_backend(store)
    if vector_backend is None and use_vector and query_vector and not _is_bucket_vector(query_vector):
        from backend.knowledge_island.vector_backend import SqliteVectorBackend

        backend = SqliteVectorBackend(store)
    if use_vector and query_vector:
        ann_hits = {
            chunk_id: score
            for chunk_id, score in backend.search(project_id, query_vector, top_k=limit * 4)
        }
    candidate_ids = set(keyword_scores) | set(ann_hits)
    if not candidate_ids:
        candidate_ids = set(chunks_by_id)
    retrieval = _retrieval_label(use_keyword, use_vector)
    hits: list[SearchHit] = []
    for chunk_id in candidate_ids:
        chunk = chunks_by_id.get(chunk_id)
        if chunk is None:
            continue
        keyword_score = keyword_scores.get(chunk.id, 0.0)
        vector_score = ann_hits.get(chunk.id, 0.0) if use_vector else 0.0
        vector_metadata = (
            backend.metadata_for(chunk.id)
            if hasattr(backend, "metadata_for")
            else {}
        )
        score = keyword_score + vector_score
        hits.append(
            SearchHit(
                document=chunk.document,
                score=score,
                snippet=_snippet(chunk.content, tokens),
                chunk=chunk,
                keyword_score=keyword_score,
                vector_score=vector_score,
                retrieval=retrieval,
                vector_provider=str(vector_metadata.get("provider", "qdrant")),
                vector_model=str(vector_metadata.get("model", "hashing-96")),
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


def _bm25_keyword_scores(chunks: list[DocumentChunk], query_tokens: list[str]) -> dict[str, float]:
    if not chunks or not query_tokens:
        return {}

    query_terms = list(dict.fromkeys(query_tokens))
    corpus_tokens = [_tokenize(chunk.content) for chunk in chunks]
    scores = _local_bm25_scores(corpus_tokens, query_terms)
    return {chunk.id: score for chunk, score in zip(chunks, scores)}


def _local_bm25_scores(
    corpus_tokens: list[list[str]],
    query_terms: list[str],
    k1: float = 1.5,
    b: float = 0.75,
) -> list[float]:
    document_count = len(corpus_tokens)
    if document_count == 0:
        return []

    average_doc_length = sum(len(tokens) for tokens in corpus_tokens) / document_count or 1.0
    document_term_sets = [set(tokens) for tokens in corpus_tokens]
    document_frequencies = {
        term: sum(1 for term_set in document_term_sets if term in term_set)
        for term in query_terms
    }

    scores: list[float] = []
    for tokens in corpus_tokens:
        term_counts = Counter(tokens)
        doc_length = len(tokens) or 1
        length_normalizer = k1 * (1 - b + b * (doc_length / average_doc_length))
        score = 0.0
        for term in query_terms:
            term_frequency = term_counts.get(term, 0)
            if term_frequency == 0:
                continue
            document_frequency = document_frequencies[term]
            idf = math.log(
                1 + (document_count - document_frequency + 0.5) / (document_frequency + 0.5)
            )
            term_weight = 2.0 if _is_cjk(term) else 1.0
            score += (
                term_weight
                * idf
                * (term_frequency * (k1 + 1))
                / (term_frequency + length_normalizer)
            )
        scores.append(score)
    return scores


def _snippet(content: str, tokens: list[str], radius: int = 80) -> str:
    lowered = content.lower()
    positions = [lowered.find(token) for token in tokens if token and lowered.find(token) >= 0]
    start = max(min(positions) - radius, 0) if positions else 0
    end = min(start + radius * 2, len(content))
    return content[start:end].replace("\n", " ").strip()


def _is_cjk(text: str) -> bool:
    return any("\u4e00" <= char <= "\u9fff" for char in text)


def _retrieval_label(use_keyword: bool, use_vector: bool) -> str:
    if use_keyword and use_vector:
        return "hybrid"
    if use_vector:
        return "vector"
    if use_keyword:
        return "keyword"
    return "disabled"


def _is_bucket_vector(vector: dict[str, float]) -> bool:
    return any(str(index) in vector for index in range(96))


def _chunk_index(hit: SearchHit) -> int:
    return hit.chunk.chunk_index if hit.chunk is not None else 0
