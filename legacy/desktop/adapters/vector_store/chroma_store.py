from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Tuple

from legacy.desktop.ports.vector_store import IVectorStore, VectorSearchResult

try:
    import chromadb
    from chromadb.config import Settings
except ImportError:  # pragma: no cover - exercised only when optional dependency is absent
    class _MissingChromaDB:
        def PersistentClient(self, *args, **kwargs):
            raise ImportError("chromadb is not installed")

    chromadb = _MissingChromaDB()

    class Settings:  # type: ignore[no-redef]
        def __init__(self, **kwargs):
            self.kwargs = kwargs


class ChromaVectorStore(IVectorStore):
    """ChromaDB-backed vector store for the legacy desktop retrieval path."""

    _COLLECTION_NAME = "knowledge_island_chunks"

    def __init__(self, persist_dir: Path) -> None:
        self._persist_dir = Path(persist_dir)
        self._persist_dir.mkdir(parents=True, exist_ok=True)
        self._client = chromadb.PersistentClient(
            path=str(self._persist_dir),
            settings=Settings(anonymized_telemetry=False),
        )
        self._collection = None

    def upsert(
        self,
        chunk_id: str,
        vector: List[float],
        metadata: Dict[str, str],
    ) -> None:
        self.upsert_batch([(chunk_id, vector, metadata)])

    def upsert_batch(
        self,
        items: List[Tuple[str, List[float], Dict[str, str]]],
    ) -> None:
        if not items:
            return
        collection = self._get_collection()
        collection.upsert(
            ids=[chunk_id for chunk_id, _, _ in items],
            embeddings=[vector for _, vector, _ in items],
            metadatas=[metadata for _, _, metadata in items],
        )

    def search(
        self,
        query_vector: List[float],
        top_k: int,
        workspace_id: str,
        domain: str = "",
    ) -> List[VectorSearchResult]:
        collection = self._get_collection()
        where: dict[str, str] = {"workspace_id": workspace_id}
        if domain:
            where["domain"] = domain
        raw = collection.query(
            query_embeddings=[query_vector],
            n_results=top_k,
            where=where,
            include=["distances"],
        )
        ids = raw.get("ids", [[]])[0]
        distances = raw.get("distances", [[]])[0]
        results: list[VectorSearchResult] = []
        for chunk_id, distance in zip(ids, distances):
            score = 1.0 - (float(distance) / 2.0)
            results.append(VectorSearchResult(chunk_id=str(chunk_id), score=score))
        results.sort(key=lambda result: result.score, reverse=True)
        return results

    def delete_by_workspace(self, workspace_id: str) -> None:
        self._get_collection().delete(where={"workspace_id": workspace_id})

    def delete_by_document(self, document_id: str) -> None:
        self._get_collection().delete(where={"document_id": document_id})

    def count(self, workspace_id: str) -> int:
        collection = self._get_collection()
        raw = collection.get(where={"workspace_id": workspace_id}, include=[])
        return len(raw.get("ids", []))

    def _get_collection(self):
        if self._collection is None:
            self._collection = self._client.get_or_create_collection(
                name=self._COLLECTION_NAME,
                metadata={"hnsw:space": "cosine"},
            )
        return self._collection
