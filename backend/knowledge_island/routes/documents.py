from __future__ import annotations

from typing import Any

from backend.knowledge_island.api_support import query_value
from backend.knowledge_island.models import ApiResponse
from backend.knowledge_island.storage import KnowledgeStore


def handle_documents_route(
    store: KnowledgeStore,
    method: str,
    path: str,
    query: dict[str, list[str]],
    payload: dict[str, Any],
) -> ApiResponse | None:
    if method == "GET" and path == "/api/documents":
        project_id = query_value(query, "project_id")
        collection_id = query_value(query, "collection_id")
        if not project_id:
            return ApiResponse(400, {"error": "project_id is required"})
        if collection_id and collection_id != "unassigned":
            collection = store.get_document_collection(collection_id)
            if not collection or collection.project_id != project_id:
                return ApiResponse(404, {"error": "document collection not found"})
        documents = [doc.to_dict() for doc in store.list_documents(project_id, collection_id=collection_id or None)]
        return ApiResponse(200, {"documents": documents})

    if method == "GET" and path == "/api/document":
        document_id = query_value(query, "document_id")
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

    collection_response = _handle_document_collections_route(store, method, path, query, payload)
    if collection_response is not None:
        return collection_response

    return None


def _handle_document_collections_route(
    store: KnowledgeStore,
    method: str,
    path: str,
    query: dict[str, list[str]],
    payload: dict[str, Any],
) -> ApiResponse | None:
    if method == "GET" and path == "/api/document-collections":
        project_id = query_value(query, "project_id")
        if not project_id:
            return ApiResponse(400, {"error": "project_id is required"})
        if not store.get_project(project_id):
            return ApiResponse(404, {"error": "project not found"})
        collections = [collection.to_dict() for collection in store.list_document_collections(project_id)]
        return ApiResponse(200, {"collections": collections})

    if method == "POST" and path == "/api/document-collections":
        project_id = str(payload.get("project_id", "")).strip()
        if not project_id:
            return ApiResponse(400, {"error": "project_id is required"})
        if not store.get_project(project_id):
            return ApiResponse(404, {"error": "project not found"})
        error = _document_collection_validation_error(payload)
        if error:
            return ApiResponse(400, {"error": error})
        collection = store.create_document_collection(
            project_id,
            str(payload.get("name", "")),
            str(payload.get("description", "")),
            str(payload.get("color", "")),
        )
        return ApiResponse(200, {"collection": collection.to_dict()})

    if method == "POST" and path == "/api/document-collections/update":
        collection_id = str(payload.get("collection_id", "")).strip()
        if not collection_id:
            return ApiResponse(400, {"error": "collection_id is required"})
        if not store.get_document_collection(collection_id):
            return ApiResponse(404, {"error": "document collection not found"})
        error = _document_collection_validation_error(payload)
        if error:
            return ApiResponse(400, {"error": error})
        collection = store.update_document_collection(
            collection_id,
            str(payload.get("name", "")),
            str(payload.get("description", "")),
            str(payload.get("color", "")),
        )
        if not collection:
            return ApiResponse(404, {"error": "document collection not found"})
        return ApiResponse(200, {"collection": collection.to_dict()})

    if method == "POST" and path == "/api/document-collections/delete":
        collection_id = str(payload.get("collection_id", "")).strip()
        if not collection_id:
            return ApiResponse(400, {"error": "collection_id is required"})
        collection = store.delete_document_collection(collection_id)
        if not collection:
            return ApiResponse(404, {"error": "document collection not found"})
        collections = [entry.to_dict() for entry in store.list_document_collections(collection.project_id)]
        return ApiResponse(200, {"deleted": True, "collections": collections})

    if method == "POST" and path == "/api/document-collections/items/add":
        return _document_collection_item_response(store, payload, add=True)

    if method == "POST" and path == "/api/document-collections/items/remove":
        return _document_collection_item_response(store, payload, add=False)

    return None


def _document_collection_validation_error(payload: dict[str, Any]) -> str:
    name = str(payload.get("name", "")).strip()
    if not name:
        return "name is required"
    return ""


def _document_ids_from_payload(payload: dict[str, Any]) -> list[str]:
    raw_ids = payload.get("document_ids")
    if isinstance(raw_ids, list):
        return [str(document_id).strip() for document_id in raw_ids if str(document_id).strip()]
    raw_id = str(payload.get("document_id", "")).strip()
    return [raw_id] if raw_id else []


def _document_collection_item_response(
    store: KnowledgeStore,
    payload: dict[str, Any],
    add: bool,
) -> ApiResponse:
    collection_id = str(payload.get("collection_id", "")).strip()
    if not collection_id:
        return ApiResponse(400, {"error": "collection_id is required"})
    if not store.get_document_collection(collection_id):
        return ApiResponse(404, {"error": "document collection not found"})
    document_ids = _document_ids_from_payload(payload)
    if not document_ids:
        return ApiResponse(400, {"error": "document_ids is required"})
    if add:
        collection = store.add_documents_to_collection(collection_id, document_ids)
    else:
        collection = store.remove_documents_from_collection(collection_id, document_ids)
    if not collection:
        return ApiResponse(404, {"error": "document not found"})
    return ApiResponse(200, {"collection": collection.to_dict()})
