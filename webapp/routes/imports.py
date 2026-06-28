from __future__ import annotations

from typing import Any

from webapp.api_support import query_value
from webapp.ingestion import import_directory, preview_import_directory
from webapp.models import ApiResponse, Document, ImportResult
from webapp.notion_obsidian_import import import_notion_zip, import_obsidian_vault
from webapp.source_import import import_plain_text_note, import_url_excerpt
from webapp.storage import KnowledgeStore
from webapp.upload_import import create_browser_upload_project, import_uploaded_files


def handle_imports_route(
    store: KnowledgeStore,
    method: str,
    path: str,
    query: dict[str, list[str]],
    payload: dict[str, Any],
) -> ApiResponse | None:
    if method == "POST" and path == "/api/import":
        project_id = str(payload.get("project_id", ""))
        project = store.get_project(project_id)
        if not project:
            return ApiResponse(404, {"error": "project not found"})
        if not project.root_path.exists() or not project.root_path.is_dir():
            return ApiResponse(400, {"error": "project root path does not exist"})
        result = import_directory(store, project.id, project.root_path)
        batch = _record_import_batch(store, project.id, "directory_sync", result)
        documents = [doc.to_dict() for doc in store.list_documents(project.id)]
        return ApiResponse(200, {"result": result.to_dict(), "batch": batch.to_dict(), "documents": documents})

    if method == "GET" and path == "/api/import/preview":
        project_id = query_value(query, "project_id")
        if not project_id:
            return ApiResponse(400, {"error": "project_id is required"})
        project = store.get_project(project_id)
        if not project:
            return ApiResponse(404, {"error": "project not found"})
        if not project.root_path.exists() or not project.root_path.is_dir():
            return ApiResponse(400, {"error": "project root path does not exist"})
        preview = preview_import_directory(store, project.id, project.root_path)
        return ApiResponse(200, {"preview": preview})

    if method == "POST" and path == "/api/import/upload":
        files = payload.get("files")
        if not isinstance(files, list):
            return ApiResponse(400, {"error": "files is required"})
        project_id = str(payload.get("project_id", ""))
        project = store.get_project(project_id) if project_id else None
        if project_id and not project:
            return ApiResponse(404, {"error": "project not found"})
        if not project:
            project = create_browser_upload_project(store, str(payload.get("project_name", "")))
        result = import_uploaded_files(store, files, project)
        batch = _record_import_batch(store, project.id, _upload_source_type(payload, bool(project_id)), result)
        documents = [doc.to_dict() for doc in store.list_documents(project.id)]
        return ApiResponse(
            200,
            {
                "project": project.to_dict(),
                "result": result.to_dict(),
                "batch": batch.to_dict(),
                "documents": documents,
            },
        )

    if method == "POST" and path == "/api/import/notion-zip":
        project_id = str(payload.get("project_id", ""))
        if not store.get_project(project_id):
            return ApiResponse(404, {"error": "project not found"})
        try:
            result = import_notion_zip(
                store,
                project_id,
                payload.get("filename", ""),
                payload.get("content_base64", ""),
            )
        except ValueError as exc:
            return ApiResponse(400, {"error": str(exc)})
        batch = _record_import_batch(store, project_id, "notion_zip", result)
        documents = [doc.to_dict() for doc in store.list_documents(project_id)]
        return ApiResponse(200, {"result": result.to_dict(), "batch": batch.to_dict(), "documents": documents})

    if method == "POST" and path == "/api/import/obsidian-vault":
        project_id = str(payload.get("project_id", ""))
        if not store.get_project(project_id):
            return ApiResponse(404, {"error": "project not found"})
        try:
            result = import_obsidian_vault(
                store,
                project_id,
                payload.get("vault_path", ""),
            )
        except ValueError as exc:
            return ApiResponse(400, {"error": str(exc)})
        batch = _record_import_batch(store, project_id, "obsidian_vault", result)
        documents = [doc.to_dict() for doc in store.list_documents(project_id)]
        return ApiResponse(200, {"result": result.to_dict(), "batch": batch.to_dict(), "documents": documents})

    if method == "POST" and path == "/api/import/note":
        project_id = str(payload.get("project_id", ""))
        if not store.get_project(project_id):
            return ApiResponse(404, {"error": "project not found"})
        try:
            write_result, result = import_plain_text_note(
                store,
                project_id,
                payload.get("title", ""),
                payload.get("content", ""),
            )
        except ValueError as exc:
            return ApiResponse(400, {"error": str(exc)})
        batch = _record_import_batch(store, project_id, "text_note", result, document=write_result.document)
        documents = [doc.to_dict() for doc in store.list_documents(project_id)]
        return ApiResponse(
            200,
            {
                "result": result.to_dict(),
                "batch": batch.to_dict(),
                "document": write_result.document.to_dict(),
                "documents": documents,
            },
        )

    if method == "POST" and path == "/api/import/url":
        project_id = str(payload.get("project_id", ""))
        if not store.get_project(project_id):
            return ApiResponse(404, {"error": "project not found"})
        try:
            write_result, result = import_url_excerpt(
                store,
                project_id,
                payload.get("url", ""),
                payload.get("title", ""),
                payload.get("content", ""),
            )
        except ValueError as exc:
            return ApiResponse(400, {"error": str(exc)})
        batch = _record_import_batch(store, project_id, "url_excerpt", result, document=write_result.document)
        documents = [doc.to_dict() for doc in store.list_documents(project_id)]
        return ApiResponse(
            200,
            {
                "result": result.to_dict(),
                "batch": batch.to_dict(),
                "document": write_result.document.to_dict(include_content=True),
                "documents": documents,
            },
        )

    if method == "GET" and path == "/api/import/batches":
        project_id = query_value(query, "project_id")
        if not project_id:
            return ApiResponse(400, {"error": "project_id is required"})
        if not store.get_project(project_id):
            return ApiResponse(404, {"error": "project not found"})
        batches = [batch.to_dict() for batch in store.list_import_batches(project_id)]
        return ApiResponse(200, {"batches": batches})

    if method == "GET" and path == "/api/import/batches/detail":
        batch_id = query_value(query, "batch_id")
        if not batch_id:
            return ApiResponse(400, {"error": "batch_id is required"})
        batch = store.get_import_batch(batch_id)
        if not batch:
            return ApiResponse(404, {"error": "import batch not found"})
        items = [_import_batch_item_payload(item.to_dict()) for item in store.list_import_batch_items(batch.id)]
        return ApiResponse(200, {"batch": batch.to_dict(), "items": items})

    return None


def _record_import_batch(
    store: KnowledgeStore,
    project_id: str,
    source_type: str,
    result: ImportResult,
    document: Document | None = None,
):
    summary = _import_batch_summary(result)
    items = _import_batch_items(result, document)
    return store.create_import_batch(
        project_id=project_id,
        source_type=source_type,
        status=_import_batch_status(summary),
        summary=summary,
        items=items,
    )


def _import_batch_summary(result: ImportResult) -> dict[str, object]:
    return {
        "imported": result.imported,
        "created": result.created,
        "updated": result.updated,
        "unchanged": result.unchanged,
        "deleted": result.deleted,
        "skipped": result.skipped,
        "errors": len(result.errors),
    }


def _import_batch_status(summary: dict[str, object]) -> str:
    imported = int(summary.get("imported", 0) or 0)
    skipped = int(summary.get("skipped", 0) or 0)
    errors = int(summary.get("errors", 0) or 0)
    if imported == 0 and errors > 0 and skipped == 0:
        return "failed"
    if skipped > 0 or errors > 0:
        return "partial"
    return "success"


def _import_batch_items(result: ImportResult, document: Document | None = None) -> list[dict[str, object]]:
    items: list[dict[str, object]] = []
    if document:
        action = "created" if result.created else "updated" if result.updated else "unchanged"
        items.append({
            "kind": action,
            "relative_path": document.relative_path,
            "document_id": document.id,
            "reason": "",
        })
    for detail in result.skipped_details:
        items.append({
            "kind": "skipped",
            "relative_path": str(detail.get("path", "")),
            "document_id": "",
            "reason": str(detail.get("reason", "")),
        })
    for error in result.errors:
        error_text = str(error)
        relative_path = error_text.split(":", 1)[0].strip()
        items.append({
            "kind": "error",
            "relative_path": relative_path,
            "document_id": "",
            "reason": error_text,
        })
    return items


def _import_batch_item_payload(item: dict[str, object]) -> dict[str, object]:
    return {
        "kind": str(item.get("kind", "")),
        "relative_path": str(item.get("relative_path", "")),
        "document_id": str(item.get("document_id", "")),
        "reason": str(item.get("reason", "")),
    }


def _upload_source_type(payload: dict[str, Any], has_project_id: bool) -> str:
    source_type = str(payload.get("source_type", "")).strip()
    if source_type in {"browser_folder_upload", "file_upload"}:
        return source_type
    return "file_upload" if has_project_id else "browser_folder_upload"
