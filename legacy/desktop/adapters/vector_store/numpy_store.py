from __future__ import annotations

from math import sqrt
from typing import Dict, List, Tuple

from legacy.desktop.ports.vector_store import IVectorStore, VectorSearchResult


class NumpyVectorStore(IVectorStore):
    """Small in-memory vector store used by legacy tests and keyword fallback."""

    def __init__(self) -> None:
        self._items: dict[str, tuple[list[float], dict[str, str]]] = {}

    def upsert(
        self,
        chunk_id: str,
        vector: List[float],
        metadata: Dict[str, str],
    ) -> None:
        self._items[chunk_id] = (list(vector), dict(metadata))

    def upsert_batch(
        self,
        items: List[Tuple[str, List[float], Dict[str, str]]],
    ) -> None:
        for chunk_id, vector, metadata in items:
            self.upsert(chunk_id, vector, metadata)

    def search(
        self,
        query_vector: List[float],
        top_k: int,
        workspace_id: str,
        domain: str = "",
    ) -> List[VectorSearchResult]:
        results: list[VectorSearchResult] = []
        for chunk_id, (vector, metadata) in self._items.items():
            if metadata.get("workspace_id") != workspace_id:
                continue
            if domain and metadata.get("domain") != domain:
                continue
            results.append(
                VectorSearchResult(
                    chunk_id=chunk_id,
                    score=_cosine_similarity(query_vector, vector),
                )
            )
        results.sort(key=lambda result: result.score, reverse=True)
        return results[:top_k]

    def delete_by_workspace(self, workspace_id: str) -> None:
        self._items = {
            chunk_id: item
            for chunk_id, item in self._items.items()
            if item[1].get("workspace_id") != workspace_id
        }

    def delete_by_document(self, document_id: str) -> None:
        self._items = {
            chunk_id: item
            for chunk_id, item in self._items.items()
            if item[1].get("document_id") != document_id
        }

    def count(self, workspace_id: str) -> int:
        return sum(
            1
            for _, metadata in self._items.values()
            if metadata.get("workspace_id") == workspace_id
        )


def _cosine_similarity(left: list[float], right: list[float]) -> float:
    if not left or not right:
        return 0.0
    size = min(len(left), len(right))
    dot = sum(left[i] * right[i] for i in range(size))
    left_norm = sqrt(sum(value * value for value in left))
    right_norm = sqrt(sum(value * value for value in right))
    if left_norm == 0 or right_norm == 0:
        return 0.0
    return dot / (left_norm * right_norm)

