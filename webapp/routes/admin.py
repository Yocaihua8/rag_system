from __future__ import annotations

from typing import Any

from webapp.models import ApiResponse
from webapp.storage import KnowledgeStore


def handle_admin_route(
    store: KnowledgeStore,
    method: str,
    path: str,
    payload: dict[str, Any],
) -> ApiResponse | None:
    if method == "POST" and path == "/api/admin/rebuild-index":
        project_id = str(payload.get("project_id", "")).strip()
        if project_id:
            if not store.get_project(project_id):
                return ApiResponse(404, {"error": "project not found"})
            project_ids = [project_id]
        else:
            project_ids = [project.id for project in store.list_projects()]
        summary = store.rebuild_index(project_id)
        return ApiResponse(200, {"rebuilt": True, "project_ids": project_ids, "summary": summary})

    return None
