from __future__ import annotations

from typing import Any, Callable

from backend.api.answer_handlers import default_model_profile_client
from backend.api.support import query_value
from backend.domain.models import ApiResponse
from backend.domain.project_analysis import (
    analyze_project,
    build_coach_overview,
    build_knowledge_points_view,
    build_skills_view,
)
from backend.storage import KnowledgeStore


CoachViewBuilder = Callable[[KnowledgeStore, str], Any | None]


def handle_coach_route(
    store: KnowledgeStore,
    method: str,
    path: str,
    query: dict[str, list[str]],
    payload: dict[str, Any],
    llm_client: Any | None = None,
) -> ApiResponse | None:
    if method == "POST" and path == "/api/coach/analyze":
        project_id = str(payload.get("project_id") or "").strip()
        project_error = _project_error(store, project_id)
        if project_error is not None:
            return project_error
        try:
            analysis_client = llm_client
            if analysis_client is None:
                analysis_client = default_model_profile_client(store)
            analysis = analyze_project(store, project_id, llm_client=analysis_client)
        except ValueError as exc:
            return ApiResponse(400, {"error": str(exc)})
        return ApiResponse(200, {"analysis": analysis})

    get_routes: dict[str, tuple[str, CoachViewBuilder]] = {
        "/api/coach/overview": ("overview", build_coach_overview),
        "/api/coach/knowledge-points": ("knowledge_points", build_knowledge_points_view),
        "/api/coach/skills": ("skills", build_skills_view),
    }
    if method == "GET" and path in get_routes:
        project_id = query_value(query, "project_id").strip()
        project_error = _project_error(store, project_id)
        if project_error is not None:
            return project_error
        response_key, builder = get_routes[path]
        try:
            view = builder(store, project_id)
        except ValueError as exc:
            if str(exc) == "coach analysis not found":
                return ApiResponse(404, {"error": str(exc)})
            return ApiResponse(400, {"error": str(exc)})
        if view is None:
            return ApiResponse(404, {"error": "coach analysis not found"})
        return ApiResponse(200, {response_key: view})

    return None


def _project_error(store: KnowledgeStore, project_id: str) -> ApiResponse | None:
    if not project_id:
        return ApiResponse(400, {"error": "project_id is required"})
    if not store.get_project(project_id):
        return ApiResponse(404, {"error": "project not found"})
    return None
