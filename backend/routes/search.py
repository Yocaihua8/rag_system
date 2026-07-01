from __future__ import annotations

from typing import Any

from backend.api.support import bool_value, float_value, int_value, project_retrieval_settings, query_value, source_quality
from backend.domain.models import ApiResponse
from backend.domain.search import search_documents
from backend.storage import KnowledgeStore


def handle_search_route(
    store: KnowledgeStore,
    method: str,
    path: str,
    query: dict[str, list[str]],
    payload: dict[str, Any],
) -> ApiResponse | None:
    if method == "POST" and path == "/api/search":
        project_id = str(payload.get("project_id", ""))
        query_text = str(payload.get("query", ""))
        hits = search_documents(store, project_id, query_text)
        return ApiResponse(200, {"hits": [hit.to_dict() for hit in hits if hit.score > 0]})

    if method == "POST" and path == "/api/search/debug":
        project_id = str(payload.get("project_id", ""))
        query_text = str(payload.get("query", ""))
        settings = project_retrieval_settings(store, project_id)
        top_k = int_value(payload.get("top_k"), int(settings["top_k"]), minimum=1, maximum=20)
        min_score = float_value(payload.get("min_score"), float(settings["min_score"]), minimum=0.0)
        use_keyword = bool_value(payload.get("use_keyword"), bool(settings["use_keyword"]))
        use_vector = bool_value(payload.get("use_vector"), bool(settings["use_vector"]))
        hits = search_documents(
            store,
            project_id,
            query_text,
            limit=top_k,
            use_keyword=use_keyword,
            use_vector=use_vector,
        )
        useful_hits = [hit for hit in hits if hit.score >= min_score and hit.score > 0]
        vector_records = store.list_chunk_vector_records(project_id)
        return ApiResponse(
            200,
            {
                "hits": [hit.to_dict() for hit in useful_hits],
                "debug": {
                    "query": query_text,
                    "document_count": len(store.list_documents(project_id)),
                    "chunk_count": len(store.list_chunks(project_id)),
                    "vector_available": bool(vector_records),
                    "parameters": {
                        "top_k": top_k,
                        "min_score": min_score,
                        "use_keyword": use_keyword,
                        "use_vector": use_vector,
                    },
                    "quality": source_quality(useful_hits),
                    "context_preview": [hit.to_dict() for hit in useful_hits[:top_k]],
                },
            },
        )

    review_response = _handle_retrieval_reviews_route(store, method, path, query, payload)
    if review_response is not None:
        return review_response

    return None


def _handle_retrieval_reviews_route(
    store: KnowledgeStore,
    method: str,
    path: str,
    query: dict[str, list[str]],
    payload: dict[str, Any],
) -> ApiResponse | None:
    if method == "GET" and path == "/api/retrieval/reviews":
        project_id = query_value(query, "project_id")
        if not project_id:
            return ApiResponse(400, {"error": "project_id is required"})
        if not store.get_project(project_id):
            return ApiResponse(404, {"error": "project not found"})
        reviews = [review.to_dict() for review in store.list_retrieval_reviews(project_id)]
        return ApiResponse(200, {"reviews": reviews})

    if method == "GET" and path == "/api/retrieval/reviews/detail":
        review_id = query_value(query, "review_id")
        if not review_id:
            return ApiResponse(400, {"error": "review_id is required"})
        review = store.get_retrieval_review(review_id)
        if not review:
            return ApiResponse(404, {"error": "retrieval review not found"})
        return ApiResponse(200, {"review": review.to_dict()})

    if method == "POST" and path == "/api/retrieval/reviews":
        project_id = str(payload.get("project_id", ""))
        if not store.get_project(project_id):
            return ApiResponse(404, {"error": "project not found"})
        query_text = str(payload.get("query", "")).strip()
        if not query_text:
            return ApiResponse(400, {"error": "query is required"})
        top_k = int_value(payload.get("top_k"), 5, minimum=1, maximum=20)
        min_score = float_value(payload.get("min_score"), 0.0, minimum=0.0)
        use_keyword = bool_value(payload.get("use_keyword"), True)
        use_vector = bool_value(payload.get("use_vector"), True)
        hits = search_documents(
            store,
            project_id,
            query_text,
            limit=top_k,
            use_keyword=use_keyword,
            use_vector=use_vector,
        )
        useful_hits = [hit for hit in hits if hit.score >= min_score and hit.score > 0]
        review = store.create_retrieval_review(
            project_id=project_id,
            query=query_text,
            parameters={
                "top_k": top_k,
                "min_score": min_score,
                "use_keyword": use_keyword,
                "use_vector": use_vector,
            },
            hits=[hit.to_dict() for hit in useful_hits],
            source_quality=source_quality(useful_hits),
            note=str(payload.get("note", "")),
        )
        return ApiResponse(200, {"review": review.to_dict()})

    if method == "POST" and path == "/api/retrieval/reviews/delete":
        review_id = str(payload.get("review_id", "")).strip()
        if not review_id:
            return ApiResponse(400, {"error": "review_id is required"})
        review = store.delete_retrieval_review(review_id)
        if not review:
            return ApiResponse(404, {"error": "retrieval review not found"})
        reviews = [entry.to_dict() for entry in store.list_retrieval_reviews(review.project_id)]
        return ApiResponse(200, {"deleted": True, "reviews": reviews})

    return None
