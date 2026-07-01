from __future__ import annotations

from pathlib import Path
from typing import Any

from backend.api.support import query_value
from backend.domain.models import ApiResponse
from backend.domain.result_export import export_chat_message_result
from backend.api.settings_handlers import get_llm_settings_body
from backend.storage import KnowledgeStore


def handle_export_route(
    store: KnowledgeStore,
    method: str,
    path: str,
    query: dict[str, list[str]],
    payload: dict[str, Any],
) -> ApiResponse | None:
    if method == "GET" and path == "/api/export/project":
        project_id = query_value(query, "project_id")
        if not project_id:
            return ApiResponse(400, {"error": "project_id is required"})
        project = store.get_project(project_id)
        if not project:
            return ApiResponse(404, {"error": "project not found"})
        return ApiResponse(200, {"export": _project_export_body(store, project_id)})

    if method == "POST" and path == "/api/export/project/restore":
        try:
            return ApiResponse(200, _restore_project_export(store, payload))
        except ValueError as exc:
            return ApiResponse(400, {"error": str(exc)})

    if method == "POST" and path == "/api/export/result":
        return _handle_result_export(store, payload)

    return None


def _handle_result_export(store: KnowledgeStore, payload: dict[str, Any]) -> ApiResponse:
    project_id = str(payload.get("project_id", "")).strip()
    if not project_id:
        return ApiResponse(400, {"error": "project_id is required"})
    project = store.get_project(project_id)
    if not project:
        return ApiResponse(404, {"error": "project not found"})

    message_id = str(payload.get("message_id", "")).strip()
    if not message_id:
        return ApiResponse(400, {"error": "message_id is required"})
    message = store.get_chat_message(message_id)
    if not message or message.project_id != project_id:
        return ApiResponse(404, {"error": "chat message not found"})

    export_format = str(payload.get("format", "")).strip()
    title = str(payload.get("title", "")).strip()
    try:
        export = export_chat_message_result(
            message=message,
            project_name=project.name,
            export_format=export_format,
            title=title,
        )
    except ValueError as exc:
        return ApiResponse(400, {"error": str(exc)})
    except OSError as exc:
        return ApiResponse(500, {"error": f"failed to write export: {exc}"})
    return ApiResponse(200, {"export": export})


def _project_export_body(store: KnowledgeStore, project_id: str) -> dict[str, Any]:
    project = store.get_project(project_id)
    vector_records = {
        str(record["chunk_id"]): record
        for record in store.list_chunk_vector_records(project_id)
    }
    chunks_by_document: dict[str, list[dict[str, Any]]] = {}
    for chunk in store.list_chunks(project_id):
        chunk_body: dict[str, Any] = {
            "id": chunk.id,
            "chunk_index": chunk.chunk_index,
            "content": chunk.content,
            "token_count": chunk.token_count,
            "created_at": chunk.created_at,
        }
        vector_record = vector_records.get(chunk.id)
        if vector_record:
            chunk_body["vector"] = {
                "values": vector_record["vector"],
                "provider": vector_record["provider"],
                "model": vector_record["model"],
                "updated_at": vector_record["updated_at"],
            }
        chunks_by_document.setdefault(chunk.document.id, []).append(chunk_body)
    documents = [
        {
            "id": document.id,
            "relative_path": document.relative_path,
            "source_path": str(document.source_path),
            "checksum": document.checksum,
            "updated_at": document.updated_at,
            "content": document.content,
            "chunks": chunks_by_document.get(document.id, []),
        }
        for document in store.list_documents(project_id)
    ]
    settings = get_llm_settings_body()["settings"]
    return {
        "version": 1,
        "project": project.to_dict() if project else {},
        "documents": documents,
        "chat_sessions": [session.to_dict() for session in store.list_chat_sessions(project_id)],
        "chat_messages": [message.to_dict() for message in store.list_all_chat_messages(project_id)],
        "settings_summary": {
            "provider": settings.get("provider", ""),
            "api_base": settings.get("api_base", ""),
            "model": settings.get("model", ""),
            "key_configured": bool(settings.get("has_api_key")),
        },
    }


def _restore_project_export(store: KnowledgeStore, payload: dict[str, Any]) -> dict[str, Any]:
    export_body = payload.get("export")
    if not isinstance(export_body, dict):
        raise ValueError("export is required")
    if str(export_body.get("version", "")).strip() != "1":
        raise ValueError("unsupported export version")
    project_data = export_body.get("project")
    if not isinstance(project_data, dict) or not str(project_data.get("name", "")).strip():
        raise ValueError("export project is required")

    project_name = str(payload.get("name", "")).strip() or f"{project_data['name']}恢复"
    restored_project = store.create_project(project_name, Path(f"browser-upload:{project_name}"))

    document_id_map: dict[str, str] = {}
    chunk_id_map: dict[str, str] = {}
    restored_document_count = 0
    restored_chunk_count = 0
    restored_vector_count = 0
    for item in export_body.get("documents", []):
        if not isinstance(item, dict):
            continue
        relative_path = str(item.get("relative_path", "")).strip()
        if not relative_path:
            continue
        raw_chunks = item.get("chunks")
        if "content" in item or isinstance(raw_chunks, list):
            restored_document, document_chunk_id_map, chunk_count, vector_count = store.restore_document_snapshot(
                project_id=restored_project.id,
                source_path=str(item.get("source_path", "")),
                relative_path=relative_path,
                content=str(item.get("content", "")),
                checksum=str(item.get("checksum", "")),
                updated_at=str(item.get("updated_at", "")),
                chunks=raw_chunks if isinstance(raw_chunks, list) else [],
            )
            chunk_id_map.update(document_chunk_id_map)
            restored_chunk_count += chunk_count
            restored_vector_count += vector_count
        else:
            restored_document = store.restore_document_metadata(
                project_id=restored_project.id,
                source_path=str(item.get("source_path", "")),
                relative_path=relative_path,
                checksum=str(item.get("checksum", "")),
                updated_at=str(item.get("updated_at", "")),
            )
        original_id = str(item.get("id", "")).strip()
        if original_id:
            document_id_map[original_id] = restored_document.id
        restored_document_count += 1

    session_id_map: dict[str, str] = {}
    for item in export_body.get("chat_sessions", []):
        if not isinstance(item, dict):
            continue
        original_id = str(item.get("id", "")).strip()
        if not original_id:
            continue
        restored_session = store.restore_chat_session(
            project_id=restored_project.id,
            title=str(item.get("title", "")),
            created_at=str(item.get("created_at", "")),
            updated_at=str(item.get("updated_at", "")),
        )
        session_id_map[original_id] = restored_session.id

    restored_message_count = 0
    for item in export_body.get("chat_messages", []):
        if not isinstance(item, dict):
            continue
        original_session_id = str(item.get("session_id", "")).strip()
        store.restore_chat_message(
            project_id=restored_project.id,
            question=str(item.get("question", "")),
            answer=str(item.get("answer", "")),
            mode=str(item.get("mode", "local")),
            provider=str(item.get("provider", "local")),
            warning=str(item.get("warning", "")),
            sources=_remap_source_document_ids(item.get("sources"), document_id_map, chunk_id_map),
            created_at=str(item.get("created_at", "")),
            session_id=session_id_map.get(original_session_id, ""),
        )
        restored_message_count += 1

    return {
        "project": restored_project.to_dict(),
        "restored": {
            "documents": restored_document_count,
            "chunks": restored_chunk_count,
            "vectors": restored_vector_count,
            "chat_sessions": len(session_id_map),
            "chat_messages": restored_message_count,
        },
    }


def _remap_source_document_ids(
    raw_sources: Any,
    document_id_map: dict[str, str],
    chunk_id_map: dict[str, str] | None = None,
) -> list[dict[str, object]]:
    if not isinstance(raw_sources, list):
        return []
    chunk_id_map = chunk_id_map or {}
    sources = []
    for source in raw_sources:
        if not isinstance(source, dict):
            continue
        copied = dict(source)
        original_document_id = str(copied.get("document_id", "")).strip()
        if original_document_id in document_id_map:
            copied["document_id"] = document_id_map[original_document_id]
        original_chunk_id = str(copied.get("chunk_id", "")).strip()
        if original_chunk_id in chunk_id_map:
            copied["chunk_id"] = chunk_id_map[original_chunk_id]
        sources.append(copied)
    return sources
