from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Callable

from backend.api.support import query_value
from backend.domain.models import ApiResponse
from backend.domain.obsidian_bridge import (
    ObsidianBridgeAuthenticationError,
    ObsidianBridgeConflictError,
    ObsidianBridgeNotFoundError,
    authenticate_obsidian_connection,
    complete_obsidian_pairing,
    list_obsidian_connections,
    process_obsidian_sync_events,
    revoke_obsidian_connection,
    start_obsidian_pairing,
)
from backend.domain.obsidian_publications import (
    ObsidianPublicationConflictError,
    ObsidianPublicationNotFoundError,
    confirm_obsidian_publication,
    pending_obsidian_publications,
    preview_obsidian_publication,
    record_obsidian_publication_result,
)
from backend.storage import KnowledgeStore


ObsidianAction = Callable[[], dict[str, Any]]


def handle_obsidian_route(
    store: KnowledgeStore,
    method: str,
    path: str,
    query: dict[str, list[str]],
    payload: dict[str, Any],
    request_context: Mapping[str, str] | None = None,
) -> ApiResponse | None:
    if method == "POST" and path == "/api/obsidian/pairing/start":
        project_id = _payload_project_id(payload)
        if not project_id:
            return ApiResponse(400, {"error": "project_id is required"})
        return _run(
            lambda: start_obsidian_pairing(
                store,
                project_id,
                output_root=payload.get("output_root", ""),
            )
        )

    if method == "POST" and path == "/api/obsidian/pairing/complete":
        return _run(
            lambda: complete_obsidian_pairing(
                store,
                payload.get("code"),
                payload.get("vault_id"),
                payload.get("vault_name"),
                output_root=payload.get("output_root", ""),
            )
        )

    if method == "GET" and path == "/api/obsidian/connections":
        project_id = query_value(query, "project_id").strip()
        if not project_id:
            return ApiResponse(400, {"error": "project_id is required"})
        return _run(lambda: list_obsidian_connections(store, project_id))

    if method == "POST" and path == "/api/obsidian/connections/revoke":
        project_id = _payload_project_id(payload)
        connection_id = str(payload.get("connection_id") or "").strip()
        if project_id:
            if (
                request_context is not None
                and "app_authenticated" in request_context
                and request_context["app_authenticated"] != "true"
            ):
                return ApiResponse(
                    401,
                    {"error": "application authentication required"},
                )
            return _run(
                lambda: revoke_obsidian_connection(
                    store,
                    project_id,
                    connection_id,
                )
            )
        try:
            connection = authenticate_obsidian_connection(
                store,
                request_context,
            )
        except ObsidianBridgeAuthenticationError as exc:
            return ApiResponse(401, {"error": str(exc)})
        if not connection_id:
            return ApiResponse(400, {"error": "connection_id is required"})
        if connection_id != connection.id:
            return ApiResponse(
                403,
                {"error": "connection token may only revoke itself"},
            )
        return _run(
            lambda: revoke_obsidian_connection(
                store,
                connection.project_id,
                connection.id,
            )
        )

    if method == "POST" and path == "/api/obsidian/sync/events":
        return _run_plugin(
            store,
            request_context,
            lambda connection: process_obsidian_sync_events(
                store,
                connection,
                payload.get("events"),
            ),
        )

    if method == "POST" and path == "/api/obsidian/publications/preview":
        project_id = _payload_project_id(payload)
        if not project_id:
            return ApiResponse(400, {"error": "project_id is required"})
        return _run(
            lambda: preview_obsidian_publication(
                store,
                project_id,
                artifact_types=payload.get("artifact_types"),
                assessment_session_ids=payload.get(
                    "assessment_session_ids"
                ),
                source_publication_id=str(
                    payload.get("source_publication_id") or ""
                ),
            )
        )

    if method == "POST" and path == "/api/obsidian/publications/confirm":
        project_id = _payload_project_id(payload)
        if not project_id:
            return ApiResponse(400, {"error": "project_id is required"})
        return _run(
            lambda: confirm_obsidian_publication(
                store,
                project_id,
                str(payload.get("publication_id") or ""),
            )
        )

    if method == "GET" and path == "/api/obsidian/publications/pending":
        return _run_plugin(
            store,
            request_context,
            lambda connection: pending_obsidian_publications(
                store,
                connection,
            ),
        )

    if method == "POST" and path == "/api/obsidian/publications/result":
        return _run_plugin(
            store,
            request_context,
            lambda connection: record_obsidian_publication_result(
                store,
                connection,
                payload.get("publication_id"),
                payload.get("results"),
            ),
        )

    return None


def _run_plugin(
    store: KnowledgeStore,
    request_context: Mapping[str, str] | None,
    action: Callable[[Any], dict[str, Any]],
) -> ApiResponse:
    try:
        connection = authenticate_obsidian_connection(
            store,
            request_context,
        )
        return ApiResponse(200, action(connection))
    except ObsidianBridgeAuthenticationError as exc:
        return ApiResponse(401, {"error": str(exc)})
    except (
        ObsidianBridgeNotFoundError,
        ObsidianPublicationNotFoundError,
    ) as exc:
        return ApiResponse(404, {"error": str(exc)})
    except (
        ObsidianBridgeConflictError,
        ObsidianPublicationConflictError,
    ) as exc:
        return ApiResponse(409, {"error": str(exc)})
    except ValueError as exc:
        return ApiResponse(400, {"error": str(exc)})


def _run(action: ObsidianAction) -> ApiResponse:
    try:
        return ApiResponse(200, action())
    except ObsidianBridgeAuthenticationError as exc:
        return ApiResponse(401, {"error": str(exc)})
    except (
        ObsidianBridgeNotFoundError,
        ObsidianPublicationNotFoundError,
    ) as exc:
        return ApiResponse(404, {"error": str(exc)})
    except (
        ObsidianBridgeConflictError,
        ObsidianPublicationConflictError,
    ) as exc:
        return ApiResponse(409, {"error": str(exc)})
    except ValueError as exc:
        return ApiResponse(400, {"error": str(exc)})


def _payload_project_id(payload: Mapping[str, Any]) -> str:
    return str(payload.get("project_id") or "").strip()


__all__ = ["handle_obsidian_route"]
