from __future__ import annotations

from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

from webapp.answers import compose_answer
from webapp.ingestion import import_directory
from webapp.models import ApiResponse
from webapp.search import search_documents
from webapp.storage import KnowledgeStore


def dispatch(
    store: KnowledgeStore,
    method: str,
    raw_path: str,
    payload: dict[str, Any] | None = None,
) -> ApiResponse:
    payload = payload or {}
    parsed = urlparse(raw_path)
    path = parsed.path
    query = parse_qs(parsed.query)

    if method == "GET" and path == "/api/health":
        return ApiResponse(200, {"status": "ok"})

    if method == "GET" and path == "/api/projects":
        return ApiResponse(200, {"projects": [project.to_dict() for project in store.list_projects()]})

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

    if method == "GET" and path == "/api/documents":
        project_id = _value(query, "project_id")
        if not project_id:
            return ApiResponse(400, {"error": "project_id is required"})
        documents = [doc.to_dict() for doc in store.list_documents(project_id)]
        return ApiResponse(200, {"documents": documents})

    if method == "GET" and path == "/api/document":
        document_id = _value(query, "document_id")
        if not document_id:
            return ApiResponse(400, {"error": "document_id is required"})
        document = store.get_document(document_id)
        if not document:
            return ApiResponse(404, {"error": "document not found"})
        return ApiResponse(200, {"document": document.to_dict(include_content=True)})

    if method == "POST" and path == "/api/documents/delete":
        document_id = str(payload.get("document_id", ""))
        document = store.delete_document(document_id)
        if not document:
            return ApiResponse(404, {"error": "document not found"})
        documents = [doc.to_dict() for doc in store.list_documents(document.project_id)]
        return ApiResponse(200, {"deleted": True, "documents": documents})

    if method == "POST" and path == "/api/import":
        project_id = str(payload.get("project_id", ""))
        project = store.get_project(project_id)
        if not project:
            return ApiResponse(404, {"error": "project not found"})
        if not project.root_path.exists() or not project.root_path.is_dir():
            return ApiResponse(400, {"error": "project root path does not exist"})
        result = import_directory(store, project.id, project.root_path)
        documents = [doc.to_dict() for doc in store.list_documents(project.id)]
        return ApiResponse(200, {"result": result.to_dict(), "documents": documents})

    if method == "POST" and path == "/api/search":
        project_id = str(payload.get("project_id", ""))
        query_text = str(payload.get("query", ""))
        hits = search_documents(store, project_id, query_text)
        return ApiResponse(200, {"hits": [hit.to_dict() for hit in hits if hit.score > 0]})

    if method == "POST" and path == "/api/answer":
        project_id = str(payload.get("project_id", ""))
        question = str(payload.get("question", ""))
        hits = search_documents(store, project_id, question)
        useful_hits = [hit for hit in hits if hit.score > 0]
        return ApiResponse(
            200,
            {
                "answer": compose_answer(question, hits),
                "sources": [hit.to_dict() for hit in useful_hits[:5]],
            },
        )

    return ApiResponse(404, {"error": "not found"})


def _value(query: dict[str, list[str]], key: str) -> str:
    values = query.get(key, [])
    return values[0] if values else ""
