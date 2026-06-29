"""
VectorRetriever — 基于向量相似度的语义检索。

依赖链：IEmbedder → embed query → IVectorStore → search → IChunkStore → load full Chunk
"""
from __future__ import annotations

from typing import List

from src.domain.models.chunk import Chunk
from src.ports.chunk_store import IChunkStore
from src.ports.embedder import IEmbedder
from src.ports.retriever import IRetriever, RetrievalQuery, RetrievalResult
from src.ports.vector_store import IVectorStore


class VectorRetriever(IRetriever):

    def __init__(
        self,
        embedder: IEmbedder,
        vector_store: IVectorStore,
        chunk_store: IChunkStore,
    ) -> None:
        self._embedder = embedder
        self._vector_store = vector_store
        self._chunk_store = chunk_store

    # ------------------------------------------------------------------ #
    # IRetriever 实现
    # ------------------------------------------------------------------ #

    def search(self, query: RetrievalQuery) -> RetrievalResult:
        # ① 嵌入查询
        q_vector = self._embedder.embed(query.question).vector

        # ② 向量相似度搜索（多取一倍供后续过滤）
        domain_filter = query.domains[0] if len(query.domains) == 1 else ""
        raw = self._vector_store.search(
            query_vector=q_vector,
            top_k=query.top_k * 2,
            workspace_id=query.workspace_id,
            domain=domain_filter,
        )

        if not raw:
            return RetrievalResult(chunks=[], scores=[])

        # ③ 批量加载所有 Chunk（一次 SQL 替代 N 次）
        chunk_ids = [r.chunk_id for r in raw]
        chunk_map: dict[str, Chunk] = {
            c.id: c for c in self._chunk_store.list_by_ids(chunk_ids)
        }

        # ④ 过滤 + 截取 top_k
        chunks: List[Chunk] = []
        scores: List[float] = []
        domains = set(query.domains) if query.domains else None

        for result in raw:
            if len(chunks) >= query.top_k:
                break
            chunk = chunk_map.get(result.chunk_id)
            if chunk is None:
                continue
            # 多域过滤
            if domains and chunk.domain not in domains:
                continue
            # 标签过滤
            if query.tags:
                if not set(query.tags).intersection(chunk.tags):
                    continue
            chunks.append(chunk)
            scores.append(result.score)

        return RetrievalResult(chunks=chunks, scores=scores)

    def index(self, chunks: List[Chunk]) -> None:
        """批量嵌入并写入向量库。由 IngestWorkspaceUseCase 调用。"""
        if not chunks:
            return
        texts = [c.content for c in chunks]
        embeddings = self._embedder.embed_batch(texts)

        items = [
            (
                chunk.id,
                emb.vector,
                {
                    "workspace_id": chunk.workspace_id,
                    "domain": chunk.domain,
                    "document_id": chunk.document_id,
                },
            )
            for chunk, emb in zip(chunks, embeddings)
        ]
        self._vector_store.upsert_batch(items)

    def clear(self, workspace_id: str) -> None:
        self._vector_store.delete_by_workspace(workspace_id)

    def remove_by_document(self, document_id: str) -> None:
        self._vector_store.delete_by_document(document_id)
