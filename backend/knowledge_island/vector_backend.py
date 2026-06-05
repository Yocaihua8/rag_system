from __future__ import annotations

import os
import warnings
from typing import Protocol, runtime_checkable

from backend.knowledge_island.vector_index import VECTOR_DIMENSIONS, cosine_similarity

VECTOR_DIM = VECTOR_DIMENSIONS


def sparse_to_dense(sparse: dict[str, float], dim: int = VECTOR_DIM) -> list[float]:
    """Convert {bucket_id: weight} sparse vector to a fixed-length dense vector."""
    return [sparse.get(str(index), 0.0) for index in range(dim)]


def dense_to_sparse(dense: list[float]) -> dict[str, float]:
    return {str(index): value for index, value in enumerate(dense) if value != 0.0}


@runtime_checkable
class VectorBackend(Protocol):
    def upsert(
        self,
        chunk_id: str,
        project_id: str,
        vector: dict[str, float],
        payload: dict,
    ) -> None:
        ...

    def search(
        self,
        project_id: str,
        vector: dict[str, float],
        top_k: int,
    ) -> list[tuple[str, float]]:
        ...

    def delete(self, chunk_ids: list[str], project_id: str) -> None:
        ...

    def count(self, project_id: str) -> int:
        ...


class SqliteVectorBackend:
    """Wrapper for the existing SQLite full-scan vector behavior."""

    def __init__(self, store):
        self._store = store
        self._last_metadata: dict[str, dict[str, str]] = {}

    def upsert(
        self,
        chunk_id: str,
        project_id: str,
        vector: dict[str, float],
        payload: dict,
    ) -> None:
        return None

    def search(
        self,
        project_id: str,
        vector: dict[str, float],
        top_k: int,
    ) -> list[tuple[str, float]]:
        records = self._store.list_chunk_vector_records(project_id)
        self._last_metadata = {
            str(record["chunk_id"]): {
                "provider": str(record.get("provider", "local")),
                "model": str(record.get("model", "hashing-96")),
            }
            for record in records
        }
        results = []
        for record in records:
            score = cosine_similarity(vector, dict(record.get("vector", {})))
            results.append((str(record["chunk_id"]), score))
        results.sort(key=lambda item: item[1], reverse=True)
        return results[:top_k]

    def delete(self, chunk_ids: list[str], project_id: str) -> None:
        return None

    def count(self, project_id: str) -> int:
        return self._store.count_chunk_vectors(project_id)

    def metadata_for(self, chunk_id: str) -> dict[str, str]:
        return self._last_metadata.get(chunk_id, {})


class QdrantVectorBackend:
    """Qdrant local-mode vector backend stored under runtime/qdrant by default."""

    def __init__(self, path: str = "runtime/qdrant"):
        try:
            from qdrant_client import QdrantClient
            from qdrant_client import models
        except ImportError as exc:
            raise ImportError("qdrant-client 未安装，请运行: pip install qdrant-client") from exc
        self._client = QdrantClient(path=path)
        self._models = models
        self._last_metadata: dict[str, dict[str, str]] = {}

    def upsert(
        self,
        chunk_id: str,
        project_id: str,
        vector: dict[str, float],
        payload: dict,
    ) -> None:
        collection = self._ensure_collection(project_id)
        point_payload = dict(payload)
        point_payload.setdefault("project_id", project_id)
        self._client.upsert(
            collection_name=collection,
            points=[
                self._models.PointStruct(
                    id=chunk_id,
                    vector=sparse_to_dense(vector),
                    payload=point_payload,
                )
            ],
        )

    def search(
        self,
        project_id: str,
        vector: dict[str, float],
        top_k: int,
    ) -> list[tuple[str, float]]:
        collection = self._collection_name(project_id)
        if collection not in self._collection_names():
            self._last_metadata = {}
            return []
        result = self._client.query_points(
            collection_name=collection,
            query=sparse_to_dense(vector),
            limit=top_k,
            with_payload=True,
        )
        self._last_metadata = {
            str(point.id): {
                "provider": str((point.payload or {}).get("provider", "qdrant")),
                "model": str((point.payload or {}).get("model", "hashing-96")),
            }
            for point in result.points
        }
        return [(str(point.id), float(point.score)) for point in result.points]

    def delete(self, chunk_ids: list[str], project_id: str) -> None:
        if not chunk_ids:
            return
        collection = self._collection_name(project_id)
        if collection not in self._collection_names():
            return
        self._client.delete(
            collection_name=collection,
            points_selector=self._models.PointIdsList(points=chunk_ids),
        )

    def count(self, project_id: str) -> int:
        collection = self._collection_name(project_id)
        if collection not in self._collection_names():
            return 0
        return int(self._client.count(collection_name=collection).count)

    def metadata_for(self, chunk_id: str) -> dict[str, str]:
        return self._last_metadata.get(chunk_id, {})

    def _ensure_collection(self, project_id: str) -> str:
        collection = self._collection_name(project_id)
        if collection not in self._collection_names():
            self._client.create_collection(
                collection_name=collection,
                vectors_config=self._models.VectorParams(
                    size=VECTOR_DIM,
                    distance=self._models.Distance.COSINE,
                    on_disk=True,
                ),
            )
        return collection

    def _collection_names(self) -> set[str]:
        return {collection.name for collection in self._client.get_collections().collections}

    @staticmethod
    def _collection_name(project_id: str) -> str:
        return f"project_{project_id}"


def get_vector_backend(store, qdrant_path: str | None = None) -> VectorBackend:
    backend = os.environ.get("KI_VECTOR_BACKEND", "qdrant").lower()
    if backend == "sqlite":
        return SqliteVectorBackend(store)
    try:
        return QdrantVectorBackend(path=qdrant_path or "runtime/qdrant")
    except ImportError:
        warnings.warn("qdrant-client 未安装，自动降级到 SQLite 全扫描")
        return SqliteVectorBackend(store)
