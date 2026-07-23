from __future__ import annotations

from typing import Any, Callable

from backend.api.answer_handlers import default_model_profile_client
from backend.api.support import query_value
from backend.domain.coach_assessment import (
    CoachAssessmentConflictError,
    CoachAssessmentNotFoundError,
    answer_coach_assessment,
    build_coach_coverage,
    start_coach_assessment,
)
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

    if method == "POST" and path == "/api/coach/assessments/start":
        project_id = str(payload.get("project_id") or "").strip()
        project_error = _project_error(store, project_id)
        if project_error is not None:
            return project_error
        restart = payload.get("restart", False)
        if not isinstance(restart, bool):
            return ApiResponse(400, {"error": "restart must be a boolean"})
        try:
            assessment_client = llm_client
            if assessment_client is None:
                assessment_client = default_model_profile_client(store)
            session = start_coach_assessment(
                store,
                project_id,
                str(payload.get("target_type") or ""),
                str(payload.get("target_id") or ""),
                session_id=str(payload.get("session_id") or ""),
                restart=restart,
                llm_client=assessment_client,
            )
        except CoachAssessmentNotFoundError as exc:
            return ApiResponse(404, {"error": str(exc)})
        except CoachAssessmentConflictError as exc:
            return ApiResponse(409, {"error": str(exc)})
        except ValueError as exc:
            return ApiResponse(400, {"error": str(exc)})
        return ApiResponse(200, {"session": session})

    if method == "POST" and path == "/api/coach/assessments/answer":
        project_id = str(payload.get("project_id") or "").strip()
        project_error = _project_error(store, project_id)
        if project_error is not None:
            return project_error
        evaluation_mode = str(payload.get("evaluation_mode") or "auto")
        try:
            assessment_client = llm_client
            if assessment_client is None and evaluation_mode.strip() != "rule":
                assessment_client = default_model_profile_client(store)
            result = answer_coach_assessment(
                store,
                project_id,
                str(payload.get("session_id") or ""),
                str(payload.get("question_id") or ""),
                str(payload.get("answer") or ""),
                evaluation_mode=evaluation_mode,
                llm_client=assessment_client,
            )
        except CoachAssessmentNotFoundError as exc:
            return ApiResponse(404, {"error": str(exc)})
        except CoachAssessmentConflictError as exc:
            return ApiResponse(409, {"error": str(exc)})
        except ValueError as exc:
            return ApiResponse(400, {"error": str(exc)})
        return ApiResponse(200, result)

    get_routes: dict[str, tuple[str, CoachViewBuilder]] = {
        "/api/coach/overview": ("overview", build_coach_overview),
        "/api/coach/knowledge-points": ("knowledge_points", build_knowledge_points_view),
        "/api/coach/skills": ("skills", build_skills_view),
        "/api/coach/coverage": ("coverage", build_coach_coverage),
    }
    if method == "GET" and path in get_routes:
        project_id = query_value(query, "project_id").strip()
        project_error = _project_error(store, project_id)
        if project_error is not None:
            return project_error
        response_key, builder = get_routes[path]
        try:
            view = builder(store, project_id)
        except CoachAssessmentNotFoundError as exc:
            return ApiResponse(404, {"error": str(exc)})
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
