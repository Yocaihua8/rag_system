from __future__ import annotations

import hashlib
import sys
from collections.abc import Callable, Mapping, Sequence
from pathlib import Path

from backend.providers.base import BaseVectorStore, VectorSearchHit, VectorUpsertRecord

DEFAULT_QDRANT_VECTOR_SIZE = 96


class QdrantVectorStore(BaseVectorStore):
    def __init__(
        self,
        *,
        path: Path,
        collection: str,
        vector_size: int = DEFAULT_QDRANT_VECTOR_SIZE,
        client_factory: Callable[[Path], object] | None = None,
        models_module: object | None = None,
    ) -> None:
        self.path = Path(path)
        self.collection = collection
        self.vector_size = vector_size
        self._models = models_module
        self._collection_ready = False

        if client_factory is None or self._models is None:
            client_factory, self._models = _load_qdrant(client_factory, self._models)
        self._client = client_factory(self.path)

    def search(
        self,
        project_id: str,
        query_vector: Mapping[str, float],
        limit: int,
    ) -> list[VectorSearchHit]:
        self._ensure_collection()
        response = self._client.query_points(
            collection_name=self.collection,
            query=vector_dict_to_dense(query_vector, size=self.vector_size),
            query_filter=self._project_filter(project_id),
            limit=limit,
            with_payload=True,
        )
        points = getattr(response, "points", response)
        hits: list[VectorSearchHit] = []
        for point in points:
            payload = getattr(point, "payload", {}) or {}
            chunk_id = str(payload.get("chunk_id") or getattr(point, "id", ""))
            if not chunk_id:
                continue
            hits.append(
                VectorSearchHit(
                    chunk_id=chunk_id,
                    score=float(getattr(point, "score", 0.0) or 0.0),
                    provider=str(payload.get("provider") or "local"),
                    model=str(payload.get("model") or "hashing-96"),
                )
            )
        return hits

    def upsert(self, records: Sequence[VectorUpsertRecord]) -> None:
        if not records:
            return
        self._ensure_collection()
        points = [
            self._models.PointStruct(
                id=record.chunk_id,
                vector=vector_dict_to_dense(record.vector, size=self.vector_size),
                payload={
                    "project_id": record.project_id,
                    "document_id": record.document_id,
                    "chunk_id": record.chunk_id,
                    "chunk_index": record.chunk_index,
                    "path": record.path,
                    "content": record.content,
                    "provider": record.provider,
                    "model": record.model,
                },
            )
            for record in records
        ]
        self._client.upsert(collection_name=self.collection, points=points)

    def delete(self, project_id: str, chunk_ids: Sequence[str] | None = None) -> None:
        self._ensure_collection()
        if chunk_ids:
            selector_factory = getattr(self._models, "PointIdsList", None)
            selector = selector_factory(points=list(chunk_ids)) if selector_factory else list(chunk_ids)
        else:
            filter_selector_factory = getattr(self._models, "FilterSelector", None)
            project_filter = self._project_filter(project_id)
            selector = (
                filter_selector_factory(filter=project_filter)
                if filter_selector_factory
                else project_filter
            )
        self._client.delete(collection_name=self.collection, points_selector=selector)

    def is_available(self) -> bool:
        try:
            self._ensure_collection()
        except Exception as exc:  # pragma: no cover - defensive availability check.
            print(f"WARNING: Qdrant vector store unavailable: {exc}", file=sys.stderr)
            return False
        return True

    def _ensure_collection(self) -> None:
        if self._collection_ready:
            return
        if not self._client.collection_exists(self.collection):
            self._client.create_collection(
                collection_name=self.collection,
                vectors_config=self._models.VectorParams(
                    size=self.vector_size,
                    distance=self._models.Distance.COSINE,
                ),
            )
        self._collection_ready = True

    def _project_filter(self, project_id: str) -> object:
        return self._models.Filter(
            must=[
                self._models.FieldCondition(
                    key="project_id",
                    match=self._models.MatchValue(value=project_id),
                )
            ]
        )


def vector_dict_to_dense(vector: Mapping[str, float], *, size: int) -> list[float]:
    dense = [0.0] * size
    for key, raw_value in vector.items():
        try:
            value = float(raw_value)
        except (TypeError, ValueError):
            continue
        index = _dimension_index(str(key), size)
        if index is None:
            continue
        dense[index] += value
    return dense


def _dimension_index(key: str, size: int) -> int | None:
    try:
        index = int(key)
    except ValueError:
        digest = hashlib.sha256(key.encode("utf-8")).digest()
        return int.from_bytes(digest[:4], "big") % size if size > 0 else None
    return index if 0 <= index < size else None


def _load_qdrant(
    client_factory: Callable[[Path], object] | None,
    models_module: object | None,
) -> tuple[Callable[[Path], object], object]:
    try:
        from qdrant_client import QdrantClient, models
    except ImportError as exc:  # pragma: no cover - config layer handles soft dependency.
        raise RuntimeError("qdrant-client is not installed") from exc

    resolved_models = models_module or models

    if client_factory is None:

        def default_client_factory(path: Path) -> object:
            path.mkdir(parents=True, exist_ok=True)
            return QdrantClient(path=str(path))

        return default_client_factory, resolved_models
    return client_factory, resolved_models


__all__ = ["DEFAULT_QDRANT_VECTOR_SIZE", "QdrantVectorStore", "vector_dict_to_dense"]
