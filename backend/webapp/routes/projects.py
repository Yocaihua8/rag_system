from __future__ import annotations

from pathlib import Path
from typing import Any

from backend.webapp.api_support import bool_value, default_retrieval_settings, float_value, int_value, query_value
from backend.webapp.models import ApiResponse
from backend.webapp.storage import KnowledgeStore


def handle_projects_route(
    store: KnowledgeStore,
    method: str,
    path: str,
    query: dict[str, list[str]],
    payload: dict[str, Any],
) -> ApiResponse | None:
    if method == "GET" and path == "/api/projects":
        return ApiResponse(200, {"projects": [project.to_dict() for project in store.list_projects()]})

    if method == "GET" and path == "/api/projects/summary":
        project_id = query_value(query, "project_id")
        if not project_id:
            return ApiResponse(400, {"error": "project_id is required"})
        summary = store.get_project_summary(project_id)
        if not summary:
            return ApiResponse(404, {"error": "project not found"})
        return ApiResponse(200, {"summary": summary})

    if method == "GET" and path == "/api/projects/retrieval-settings":
        project_id = query_value(query, "project_id")
        if not project_id:
            return ApiResponse(400, {"error": "project_id is required"})
        settings = store.get_project_retrieval_settings(project_id)
        if not settings:
            return ApiResponse(404, {"error": "project not found"})
        return ApiResponse(200, {"settings": settings})

    if method == "POST" and path == "/api/projects/retrieval-settings":
        project_id = str(payload.get("project_id", "")).strip()
        if not project_id:
            return ApiResponse(400, {"error": "project_id is required"})
        if not store.get_project(project_id):
            return ApiResponse(404, {"error": "project not found"})
        current = store.get_project_retrieval_settings(project_id) or default_retrieval_settings(project_id)
        settings = store.update_project_retrieval_settings(
            project_id,
            int_value(payload.get("top_k"), int(current["top_k"]), minimum=1, maximum=20),
            float_value(payload.get("min_score"), float(current["min_score"]), minimum=0.0),
            bool_value(payload.get("use_keyword"), bool(current["use_keyword"])),
            bool_value(payload.get("use_vector"), bool(current["use_vector"])),
        )
        return ApiResponse(200, {"settings": settings})

    if method == "POST" and path == "/api/projects":
        root = Path(str(payload.get("path", ""))).expanduser()
        if not root.exists() or not root.is_dir():
            return ApiResponse(400, {"error": "path must be an existing directory"})
        project = store.create_project(str(payload.get("name", "")), root)
        return ApiResponse(201, {"project": project.to_dict()})

    if method == "POST" and path == "/api/projects/rename":
        project_id = str(payload.get("project_id", ""))
        name = str(payload.get("name", "")).strip()
        if not name:
            return ApiResponse(400, {"error": "name is required"})
        project = store.rename_project(project_id, name)
        if not project:
            return ApiResponse(404, {"error": "project not found"})
        return ApiResponse(200, {"project": project.to_dict()})

    if method == "POST" and path == "/api/projects/delete":
        project_id = str(payload.get("project_id", ""))
        if not store.delete_project(project_id):
            return ApiResponse(404, {"error": "project not found"})
        return ApiResponse(200, {"deleted": True})

    return None
