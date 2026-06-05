from __future__ import annotations

import os
from typing import Any

from backend.knowledge_island.models import ApiResponse
from backend.knowledge_island.storage import KnowledgeStore


def handle_admin_route(
    store: KnowledgeStore,
    method: str,
    path: str,
    query: dict[str, list[str]],
    payload: dict[str, Any],
) -> ApiResponse | None:
    if method == "GET" and path == "/api/admin/stats":
        return ApiResponse(
            200,
            {
                "db_size_bytes": os.path.getsize(store.db_path) if store.db_path.exists() else 0,
                "chunk_count": _total_chunks(store),
                "vector_count": _total_vectors(store),
                "project_count": len(store.list_projects()),
            },
        )

    if method == "POST" and path == "/api/admin/rebuild-index":
        from backend.knowledge_island.vector_backend import get_vector_backend
        from backend.knowledge_island.vector_index import text_vector

        vector_backend = get_vector_backend(store)
        for project in store.list_projects():
            for chunk in store.list_chunks(project.id):
                vector = text_vector(chunk.content)
                vector_backend.upsert(
                    chunk.id,
                    project.id,
                    vector,
                    {
                        "project_id": project.id,
                        "document_id": chunk.document.id,
                        "provider": "local",
                        "model": "hashing-96",
                    },
                )
        return ApiResponse(200, {"status": "rebuild complete"})

    return None


def _total_chunks(store: KnowledgeStore) -> int:
    return sum(len(store.list_chunks(project.id)) for project in store.list_projects())


def _total_vectors(store: KnowledgeStore) -> int:
    return sum(store.count_chunk_vectors(project.id) for project in store.list_projects())
