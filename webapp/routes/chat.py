from __future__ import annotations

from typing import Any

from webapp.api_support import query_value
from webapp.models import ApiResponse
from webapp.storage import KnowledgeStore


def handle_chat_route(
    store: KnowledgeStore,
    method: str,
    path: str,
    query: dict[str, list[str]],
    payload: dict[str, Any],
) -> ApiResponse | None:
    if method == "GET" and path == "/api/chat/messages":
        project_id = query_value(query, "project_id")
        session_id = query_value(query, "session_id")
        if not project_id:
            return ApiResponse(400, {"error": "project_id is required"})
        if not store.get_project(project_id):
            return ApiResponse(404, {"error": "project not found"})
        if session_id and not _chat_session_belongs_to_project(store, session_id, project_id):
            return ApiResponse(404, {"error": "chat session not found"})
        messages = [message.to_dict() for message in store.list_chat_messages(project_id, session_id)]
        return ApiResponse(200, {"messages": messages})

    if method == "GET" and path == "/api/chat/sessions":
        project_id = query_value(query, "project_id")
        if not project_id:
            return ApiResponse(400, {"error": "project_id is required"})
        if not store.get_project(project_id):
            return ApiResponse(404, {"error": "project not found"})
        sessions = [session.to_dict() for session in store.list_chat_sessions(project_id)]
        return ApiResponse(200, {"sessions": sessions})

    if method == "POST" and path == "/api/chat/sessions":
        project_id = str(payload.get("project_id", "")).strip()
        if not project_id:
            return ApiResponse(400, {"error": "project_id is required"})
        if not store.get_project(project_id):
            return ApiResponse(404, {"error": "project not found"})
        session = store.create_chat_session(project_id, str(payload.get("title", "")))
        return ApiResponse(200, {"session": session.to_dict()})

    if method == "POST" and path == "/api/chat/sessions/rename":
        session_id = str(payload.get("session_id", "")).strip()
        title = str(payload.get("title", "")).strip()
        if not session_id:
            return ApiResponse(400, {"error": "session_id is required"})
        if not title:
            return ApiResponse(400, {"error": "title is required"})
        session = store.rename_chat_session(session_id, title)
        if not session:
            return ApiResponse(404, {"error": "chat session not found"})
        return ApiResponse(200, {"session": session.to_dict()})

    if method == "POST" and path == "/api/chat/sessions/delete":
        session_id = str(payload.get("session_id", "")).strip()
        if not session_id:
            return ApiResponse(400, {"error": "session_id is required"})
        session = store.delete_chat_session(session_id)
        if not session:
            return ApiResponse(404, {"error": "chat session not found"})
        sessions = [entry.to_dict() for entry in store.list_chat_sessions(session.project_id)]
        return ApiResponse(200, {"deleted": True, "sessions": sessions})

    if method == "POST" and path == "/api/chat/messages/delete":
        message_id = str(payload.get("message_id", "")).strip()
        if not message_id:
            return ApiResponse(400, {"error": "message_id is required"})
        message = store.delete_chat_message(message_id)
        if not message:
            return ApiResponse(404, {"error": "chat message not found"})
        messages = [entry.to_dict() for entry in store.list_chat_messages(message.project_id, message.session_id)]
        return ApiResponse(200, {"deleted": True, "messages": messages})

    if method == "POST" and path == "/api/chat/messages/clear":
        project_id = str(payload.get("project_id", "")).strip()
        if not project_id:
            return ApiResponse(400, {"error": "project_id is required"})
        if not store.get_project(project_id):
            return ApiResponse(404, {"error": "project not found"})
        deleted = store.clear_chat_messages(project_id)
        return ApiResponse(200, {"deleted": deleted, "messages": []})

    return None


def _chat_session_belongs_to_project(store: KnowledgeStore, session_id: str, project_id: str) -> bool:
    session = store.get_chat_session(session_id)
    return bool(session and session.project_id == project_id)
