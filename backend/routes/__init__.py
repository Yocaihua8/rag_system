from __future__ import annotations

from typing import Any

from backend.domain.models import ApiResponse
from backend.routes.admin import handle_admin_route
from backend.routes.agent import handle_agent_route
from backend.routes.answers import handle_answer_route
from backend.routes.assessment import handle_assessment_route
from backend.routes.chat import handle_chat_route
from backend.routes.documents import handle_documents_route
from backend.routes.export import handle_export_route
from backend.routes.health import handle_health_route
from backend.routes.imports import handle_imports_route
from backend.routes.ollama import handle_ollama_route
from backend.routes.projects import handle_projects_route
from backend.routes.search import handle_search_route
from backend.routes.settings import handle_settings_route


def dispatch_to_routes(
    store: Any,
    method: str,
    path: str,
    query: dict[str, list[str]],
    payload: dict[str, Any],
    llm_client: Any | None = None,
) -> ApiResponse | None:
    health_response = handle_health_route(method, path)
    if health_response is not None:
        return health_response

    ollama_response = handle_ollama_route(method, path, query, payload)
    if ollama_response is not None:
        return ollama_response

    admin_response = handle_admin_route(store, method, path, payload)
    if admin_response is not None:
        return admin_response

    projects_response = handle_projects_route(store, method, path, query, payload)
    if projects_response is not None:
        return projects_response

    settings_response = handle_settings_route(store, method, path, query, payload, llm_client=llm_client)
    if settings_response is not None:
        return settings_response

    documents_response = handle_documents_route(store, method, path, query, payload)
    if documents_response is not None:
        return documents_response

    imports_response = handle_imports_route(store, method, path, query, payload)
    if imports_response is not None:
        return imports_response

    search_response = handle_search_route(store, method, path, query, payload)
    if search_response is not None:
        return search_response

    agent_response = handle_agent_route(store, method, path, query, payload)
    if agent_response is not None:
        return agent_response

    chat_response = handle_chat_route(store, method, path, query, payload)
    if chat_response is not None:
        return chat_response

    assessment_response = handle_assessment_route(store, method, path, query, payload)
    if assessment_response is not None:
        return assessment_response

    export_response = handle_export_route(store, method, path, query, payload)
    if export_response is not None:
        return export_response

    return handle_answer_route(store, method, path, query, payload, llm_client=llm_client)
