from __future__ import annotations

from typing import Any

from backend.knowledge_island.answer_api import answer_response
from backend.knowledge_island.models import ApiResponse
from backend.knowledge_island.storage import KnowledgeStore

ANSWER_FEEDBACK_RATINGS = {"useful", "not_useful", "source_wrong", "need_more_context"}


def handle_answer_route(
    store: KnowledgeStore,
    method: str,
    path: str,
    query: dict[str, list[str]],
    payload: dict[str, Any],
    llm_client: Any | None = None,
) -> ApiResponse | None:
    if method == "POST" and path == "/api/answer/feedback":
        project_id = str(payload.get("project_id", "")).strip()
        message_id = str(payload.get("message_id", "")).strip()
        rating = str(payload.get("rating", "")).strip()
        if not project_id:
            return ApiResponse(400, {"error": "project_id is required"})
        if not message_id:
            return ApiResponse(400, {"error": "message_id is required"})
        if rating not in ANSWER_FEEDBACK_RATINGS:
            return ApiResponse(400, {"error": "rating is invalid"})
        if not store.get_project(project_id):
            return ApiResponse(404, {"error": "project not found"})
        message = store.get_chat_message(message_id)
        if not message or message.project_id != project_id:
            return ApiResponse(404, {"error": "chat message not found"})
        feedback = store.create_answer_feedback(
            project_id=project_id,
            message_id=message_id,
            rating=rating,
            note=str(payload.get("note", "")),
        )
        return ApiResponse(200, {"feedback": feedback.to_dict()})

    if method == "POST" and path == "/api/answer":
        return answer_response(store, payload, llm_client)

    return None
