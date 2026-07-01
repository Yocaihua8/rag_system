from __future__ import annotations

from collections import Counter
from collections.abc import Mapping
from dataclasses import replace
import math
import re
import sys

from backend.config.reranker import get_default_reranker
from backend.config.vector_store import get_default_vector_store
from backend.providers.base import BaseReranker, BaseVectorStore
from backend.domain.embeddings import EmbeddingClient, embed_with_fallback, get_default_embedding_client
from backend.domain.models import DocumentChunk, SearchHit
from backend.storage import KnowledgeStore
from backend.domain.vector_index import cosine_similarity


_DEFAULT_RERANKER = object()
_DEFAULT_VECTOR_STORE = object()


def search_documents(
    store: KnowledgeStore,
    project_id: str,
    query: str,
    limit: int = 5,
    embedding_client: EmbeddingClient | None = None,
    use_keyword: bool = True,
    use_vector: bool = True,
    vector_store: BaseVectorStore | None | object = _DEFAULT_VECTOR_STORE,
    reranker: BaseReranker | None | object = _DEFAULT_RERANKER,
) -> list[SearchHit]:
    tokens = _tokenize(query)
    chunks = store.list_chunks(project_id)
    keyword_scores = _bm25_keyword_scores(chunks, tokens) if use_keyword else {}
    query_vector = {}
    if use_vector:
        query_vectors, _, _ = embed_with_fallback(
            embedding_client or get_default_embedding_client(),
            [query],
        )
        query_vector = query_vectors[0] if query_vectors else {}
    candidate_limit = max(limit * 3, limit)
    active_vector_store = get_default_vector_store() if vector_store is _DEFAULT_VECTOR_STORE else vector_store
    vector_records = _vector_records(
        store=store,
        project_id=project_id,
        query_vector=query_vector,
        limit=candidate_limit,
        use_vector=use_vector,
        vector_store=active_vector_store,
    )
    candidate_chunks = _candidate_chunks(
        chunks,
        keyword_scores=keyword_scores,
        vector_records=vector_records,
        use_keyword=use_keyword,
        use_vector_store=use_vector and active_vector_store is not None and bool(query_vector),
        limit=candidate_limit,
    )
    graph_seed_chunks = _graph_seed_chunks(
        candidate_chunks,
        keyword_scores=keyword_scores,
        vector_records=vector_records,
        use_keyword=use_keyword,
        use_vector_store=use_vector and active_vector_store is not None and bool(query_vector),
    )
    graph_related = store.list_graph_related_chunks(project_id, graph_seed_chunks, limit=candidate_limit)
    graph_records = {item.chunk.id: item for item in graph_related}
    candidate_chunks = _with_graph_candidate_chunks(candidate_chunks, graph_related)
    retrieval = _retrieval_label(use_keyword, use_vector)
    hits: list[SearchHit] = []
    for chunk in candidate_chunks:
        keyword_score = keyword_scores.get(chunk.id, 0.0)
        vector_record = vector_records.get(chunk.id, {})
        graph_record = graph_records.get(chunk.id)
        graph_score = graph_record.score if graph_record is not None else 0.0
        vector_score = (
            _vector_score(query_vector, vector_record)
            if use_vector
            else 0.0
        )
        score = keyword_score + vector_score + graph_score
        hits.append(
            SearchHit(
                document=chunk.document,
                score=score,
                snippet=_snippet(chunk.content, tokens),
                chunk=chunk,
                keyword_score=keyword_score,
                vector_score=vector_score,
                retrieval=_retrieval_with_graph(retrieval, keyword_score, vector_score, graph_score),
                vector_provider=str(vector_record.get("provider", "local")),
                vector_model=str(vector_record.get("model", "hashing-96")),
                graph_score=graph_score,
                graph_depth=graph_record.depth if graph_record is not None else None,
            )
        )
    hits.sort(
        key=lambda hit: (hit.score, hit.document.updated_at, -_chunk_index(hit)),
        reverse=True,
    )
    candidate_hits = hits[:candidate_limit]
    active_reranker = get_default_reranker() if reranker is _DEFAULT_RERANKER else reranker
    if active_reranker is not None:
        ranked_hits = [
            hit for hit in active_reranker.rerank(query, candidate_hits, top_n=limit)
            if isinstance(hit, SearchHit)
        ]
        return _with_rerank_scores(ranked_hits, active_reranker)
    return candidate_hits[:limit]


def _vector_records(
    *,
    store: KnowledgeStore,
    project_id: str,
    query_vector: Mapping[str, float],
    limit: int,
    use_vector: bool,
    vector_store: BaseVectorStore | None,
) -> dict[str, dict[str, object]]:
    if not use_vector:
        return {}
    if vector_store is not None and query_vector:
        try:
            return _provider_vector_records(vector_store.search(project_id, query_vector, limit))
        except Exception as exc:  # pragma: no cover - defensive fallback for optional providers.
            print(
                f"WARNING: vector store search failed; falling back to SQLite vectors: {exc}",
                file=sys.stderr,
            )
    return {
        str(record["chunk_id"]): dict(record)
        for record in store.list_chunk_vector_records(project_id)
    }


def _provider_vector_records(raw_hits: list[object]) -> dict[str, dict[str, object]]:
    records: dict[str, dict[str, object]] = {}
    for hit in raw_hits:
        chunk_id = _hit_value(hit, "chunk_id")
        if chunk_id is None:
            continue
        records[str(chunk_id)] = {
            "chunk_id": str(chunk_id),
            "score": float(_hit_value(hit, "score") or 0.0),
            "provider": str(_hit_value(hit, "provider") or "local"),
            "model": str(_hit_value(hit, "model") or "hashing-96"),
        }
    return records


def _hit_value(hit: object, name: str) -> object:
    if isinstance(hit, Mapping):
        return hit.get(name)
    return getattr(hit, name, None)


def _candidate_chunks(
    chunks: list[DocumentChunk],
    *,
    keyword_scores: dict[str, float],
    vector_records: dict[str, dict[str, object]],
    use_keyword: bool,
    use_vector_store: bool,
    limit: int,
) -> list[DocumentChunk]:
    if not use_vector_store:
        return chunks

    candidate_ids = set(vector_records)
    if use_keyword:
        candidate_ids.update(_top_keyword_chunk_ids(keyword_scores, limit))
    return [chunk for chunk in chunks if chunk.id in candidate_ids]


def _top_keyword_chunk_ids(keyword_scores: dict[str, float], limit: int) -> list[str]:
    ranked = sorted(keyword_scores.items(), key=lambda item: item[1], reverse=True)
    return [chunk_id for chunk_id, _ in ranked[:limit]]


def _with_graph_candidate_chunks(
    candidate_chunks: list[DocumentChunk],
    graph_related: list[object],
) -> list[DocumentChunk]:
    chunks = list(candidate_chunks)
    seen = {chunk.id for chunk in chunks}
    for item in graph_related:
        chunk = getattr(item, "chunk", None)
        if not isinstance(chunk, DocumentChunk) or chunk.id in seen:
            continue
        seen.add(chunk.id)
        chunks.append(chunk)
    return chunks


def _graph_seed_chunks(
    candidate_chunks: list[DocumentChunk],
    *,
    keyword_scores: dict[str, float],
    vector_records: dict[str, dict[str, object]],
    use_keyword: bool,
    use_vector_store: bool,
) -> list[DocumentChunk]:
    seeds: list[DocumentChunk] = []
    for chunk in candidate_chunks:
        keyword_hit = use_keyword and keyword_scores.get(chunk.id, 0.0) > 0
        vector_hit = use_vector_store and chunk.id in vector_records
        if keyword_hit or vector_hit:
            seeds.append(chunk)
    return seeds


def _vector_score(query_vector: Mapping[str, float], vector_record: dict[str, object]) -> float:
    if "score" in vector_record:
        return float(vector_record.get("score") or 0.0)
    return cosine_similarity(query_vector, dict(vector_record.get("vector", {})))


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


def _retrieval_with_graph(
    base_retrieval: str,
    keyword_score: float,
    vector_score: float,
    graph_score: float,
) -> str:
    if graph_score <= 0:
        return base_retrieval
    if keyword_score <= 0 and vector_score <= 0:
        return "graph"
    return f"{base_retrieval}+graph"


def _chunk_index(hit: SearchHit) -> int:
    return hit.chunk.chunk_index if hit.chunk is not None else 0


def _with_rerank_scores(hits: list[SearchHit], reranker: BaseReranker) -> list[SearchHit]:
    model_scores = getattr(reranker, "last_scores", {})
    ranked_total = len(hits)
    result: list[SearchHit] = []
    for index, hit in enumerate(hits):
        score = model_scores.get(id(hit)) if isinstance(model_scores, dict) else None
        if score is None:
            score = float(ranked_total - index)
        result.append(replace(hit, rerank_score=float(score)))
    return result
