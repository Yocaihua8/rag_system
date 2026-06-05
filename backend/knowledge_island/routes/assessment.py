from __future__ import annotations

from typing import Any

from backend.knowledge_island.assessment import create_assessment_session, evaluate_assessment_answer
from backend.knowledge_island.models import ApiResponse
from backend.knowledge_island.storage import KnowledgeStore


def handle_assessment_route(
    store: KnowledgeStore,
    method: str,
    path: str,
    query: dict[str, list[str]],
    payload: dict[str, Any],
) -> ApiResponse | None:
    if method == "POST" and path == "/api/assessment/start":
        project_id = str(payload.get("project_id", ""))
        if not store.get_project(project_id):
            return ApiResponse(404, {"error": "project not found"})
        try:
            session = create_assessment_session(store, project_id)
        except ValueError as exc:
            return ApiResponse(400, {"error": str(exc)})
        return ApiResponse(200, {"session": session})

    if method == "POST" and path == "/api/assessment/answer":
        project_id = str(payload.get("project_id", ""))
        if not store.get_project(project_id):
            return ApiResponse(404, {"error": "project not found"})
        try:
            submitted_question = dict(payload.get("question") or {})
            question_id = str(submitted_question.get("id", ""))
            persisted_question = store.get_assessment_question(question_id) if question_id else None
            if persisted_question is None:
                raise ValueError("assessment question not found")
            result = evaluate_assessment_answer(
                project_id=project_id,
                question=persisted_question.to_dict(),
                answer=str(payload.get("answer", "")),
            )
            answer_record = store.create_assessment_answer(
                project_id=project_id,
                question_id=str(result.get("question_id", "")),
                answer=str(payload.get("answer", "")),
            )
            result_record = store.create_assessment_result(
                project_id=project_id,
                question_id=str(result.get("question_id", "")),
                answer_id=answer_record.id,
                status=str(result.get("status", "")),
                score=float(result.get("score", 0.0)),
                matched_points=[str(item) for item in result.get("matched_points", [])],
                missing_points=[str(item) for item in result.get("missing_points", [])],
                feedback=str(result.get("feedback", "")),
                source_path=str(result.get("source_path", "")),
            )
        except ValueError as exc:
            return ApiResponse(400, {"error": str(exc)})
        result = dict(result)
        result["answer_id"] = answer_record.id
        result["result_id"] = result_record.id
        return ApiResponse(200, {"result": result})

    return None
