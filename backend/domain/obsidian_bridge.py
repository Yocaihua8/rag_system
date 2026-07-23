from __future__ import annotations

import hashlib
import secrets
from collections.abc import Mapping
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from backend.domain.import_rules import MAX_TEXT_FILE_BYTES
from backend.domain.obsidian_models import ObsidianConnection
from backend.domain.obsidian_protocol import (
    default_output_root,
    normalize_output_root,
    normalize_vault_path,
    path_is_within_root,
    text_sha256,
)
from backend.storage import KnowledgeStore


PAIRING_TTL_SECONDS = 300
MAX_SYNC_EVENTS = 100
MAX_EVENT_ID_CHARS = 200
OBSIDIAN_PLUGIN_SOURCE_PREFIX = "obsidian-plugin:"
OBSIDIAN_RELATIVE_PREFIX = "obsidian/"


class ObsidianBridgeNotFoundError(LookupError):
    pass


class ObsidianBridgeConflictError(RuntimeError):
    pass


class ObsidianBridgeAuthenticationError(PermissionError):
    pass


def start_obsidian_pairing(
    store: KnowledgeStore,
    project_id: str,
    *,
    output_root: object = "",
    now: datetime | None = None,
) -> dict[str, Any]:
    project = store.get_project(project_id)
    if project is None:
        raise ObsidianBridgeNotFoundError("project not found")
    if store.get_active_obsidian_connection(project_id):
        raise ObsidianBridgeConflictError(
            "project already has an active Obsidian connection"
        )
    clean_root = (
        normalize_output_root(output_root)
        if str(output_root or "").strip()
        else default_output_root(project.name)
    )
    code = secrets.token_urlsafe(9)
    current = _utc_datetime(now)
    expires_at = current + timedelta(seconds=PAIRING_TTL_SECONDS)
    pairing = store.create_obsidian_pairing(
        project_id,
        _secret_hash(code),
        clean_root,
        expires_at.isoformat(),
    )
    return {
        "pairing": {
            **pairing.to_dict(),
            "code": code,
            "ttl_seconds": PAIRING_TTL_SECONDS,
        }
    }


def complete_obsidian_pairing(
    store: KnowledgeStore,
    code: object,
    vault_id: object,
    vault_name: object,
    *,
    output_root: object = "",
    now: datetime | None = None,
) -> dict[str, Any]:
    clean_code = _required_text(code, "code")
    clean_vault_id = _required_text(vault_id, "vault_id")
    clean_vault_name = _required_text(vault_name, "vault_name")
    pairing = store.get_obsidian_pairing_by_code_hash(
        _secret_hash(clean_code)
    )
    if pairing is None:
        raise ObsidianBridgeAuthenticationError("invalid pairing code")
    if pairing.consumed_at:
        raise ObsidianBridgeConflictError("pairing code already used")
    current = _utc_datetime(now)
    if _parse_timestamp(pairing.expires_at) <= current:
        raise ObsidianBridgeAuthenticationError("pairing code expired")
    clean_root = (
        normalize_output_root(output_root)
        if str(output_root or "").strip()
        else pairing.output_root
    )
    token = secrets.token_urlsafe(32)
    try:
        connection = store.consume_obsidian_pairing_and_create_connection(
            pairing.id,
            token_hash=_secret_hash(token),
            vault_id=clean_vault_id,
            vault_name=clean_vault_name,
            output_root=clean_root,
        )
    except ValueError as exc:
        raise ObsidianBridgeConflictError(str(exc)) from exc
    return {
        "connection": connection.to_dict(),
        "token": token,
        "token_type": "Bearer",
    }


def authenticate_obsidian_connection(
    store: KnowledgeStore,
    request_context: Mapping[str, str] | None,
) -> ObsidianConnection:
    authorization = str(
        (request_context or {}).get("authorization") or ""
    ).strip()
    scheme, separator, token = authorization.partition(" ")
    if (
        not separator
        or scheme.casefold() != "bearer"
        or not token.strip()
    ):
        raise ObsidianBridgeAuthenticationError(
            "Obsidian connection token required"
        )
    connection = store.get_obsidian_connection_by_token_hash(
        _secret_hash(token.strip())
    )
    if connection is None:
        raise ObsidianBridgeAuthenticationError(
            "invalid or revoked Obsidian connection token"
        )
    return connection


def list_obsidian_connections(
    store: KnowledgeStore,
    project_id: str,
) -> dict[str, Any]:
    if store.get_project(project_id) is None:
        raise ObsidianBridgeNotFoundError("project not found")
    return {
        "connections": [
            connection.to_dict()
            for connection in store.list_obsidian_connections(project_id)
        ]
    }


def revoke_obsidian_connection(
    store: KnowledgeStore,
    project_id: str,
    connection_id: str,
) -> dict[str, Any]:
    connection = store.revoke_obsidian_connection(
        project_id,
        _required_text(connection_id, "connection_id"),
    )
    if connection is None:
        raise ObsidianBridgeNotFoundError(
            "active Obsidian connection not found"
        )
    return {"connection": connection.to_dict()}


def process_obsidian_sync_events(
    store: KnowledgeStore,
    connection: ObsidianConnection,
    events: object,
) -> dict[str, Any]:
    if not isinstance(events, list) or not events:
        raise ValueError("events must be a non-empty array")
    if len(events) > MAX_SYNC_EVENTS:
        raise ValueError(
            f"events must not exceed {MAX_SYNC_EVENTS} items"
        )
    store.update_obsidian_connection_sync(connection.id, "syncing")
    results: list[dict[str, Any]] = []
    had_failure = False
    for raw_event in events:
        try:
            event = _validated_event(raw_event)
            result = _process_sync_event(store, connection, event)
        except (ValueError, ObsidianBridgeConflictError) as exc:
            had_failure = True
            event_id = (
                str(raw_event.get("event_id") or "").strip()
                if isinstance(raw_event, Mapping)
                else ""
            )
            result = {
                "event_id": event_id,
                "status": "failed",
                "error": str(exc),
                "replayed": False,
            }
        results.append(result)
    updated = store.update_obsidian_connection_sync(
        connection.id,
        "error" if had_failure else "idle",
        mark_synced=True,
    )
    return {
        "connection": (
            updated.to_dict() if updated else connection.to_dict()
        ),
        "results": results,
    }


def _process_sync_event(
    store: KnowledgeStore,
    connection: ObsidianConnection,
    event: dict[str, Any],
) -> dict[str, Any]:
    stored, created = store.create_obsidian_sync_event(
        connection.project_id,
        connection.id,
        event["event_id"],
        event["type"],
        event["path"],
        old_path=event["old_path"],
        content_hash=event["content_hash"],
        payload=event,
    )
    if not created and stored.status != "received":
        return {
            "event_id": stored.event_id,
            "status": stored.status,
            **stored.result,
            "replayed": True,
        }
    try:
        outcome_status, outcome = _apply_sync_event(
            store,
            connection,
            event,
        )
    except (ValueError, ObsidianBridgeConflictError) as exc:
        outcome_status = "failed"
        outcome = {"error": str(exc)}
    completed = store.complete_obsidian_sync_event(
        connection.id,
        event["event_id"],
        outcome_status,
        outcome,
    )
    return {
        "event_id": completed.event_id,
        "status": completed.status,
        **completed.result,
        "replayed": not created,
    }


def _apply_sync_event(
    store: KnowledgeStore,
    connection: ObsidianConnection,
    event: Mapping[str, Any],
) -> tuple[str, dict[str, Any]]:
    action = str(event["type"])
    path = str(event["path"])
    old_path = str(event["old_path"])
    path_in_output = path_is_within_root(path, connection.output_root)
    old_in_output = bool(
        old_path
        and path_is_within_root(old_path, connection.output_root)
    )
    if action != "rename" and path_in_output:
        return "ignored", {"action": "ignored_output_root"}
    if action == "rename" and old_in_output and path_in_output:
        return "ignored", {"action": "ignored_output_root"}
    if action == "delete":
        deleted = _delete_synced_document(store, connection, path)
        return "applied", {
            "action": "deleted" if deleted else "unchanged",
            "document_id": deleted.id if deleted else "",
        }
    if action == "rename":
        if path_in_output:
            deleted = _delete_synced_document(
                store,
                connection,
                old_path,
            )
            return "applied", {
                "action": "removed_from_ingestion",
                "document_id": deleted.id if deleted else "",
            }
        if old_in_output:
            written = _upsert_synced_document(
                store,
                connection,
                path,
                str(event["content"]),
            )
            return "applied", {
                "action": written.action,
                "document_id": written.document.id,
            }
        old_relative = _relative_path(old_path)
        new_relative = _relative_path(path)
        renamed = store.rename_document_preserving_identity(
            connection.project_id,
            old_relative,
            new_relative,
            _source_path(connection.id, path),
        )
        if renamed is None:
            written = _upsert_synced_document(
                store,
                connection,
                path,
                str(event["content"]),
            )
            return "applied", {
                "action": written.action,
                "document_id": written.document.id,
            }
        if event["content"] and text_sha256(str(event["content"])) != renamed.checksum:
            written = _upsert_synced_document(
                store,
                connection,
                path,
                str(event["content"]),
            )
            renamed = written.document
        return "applied", {
            "action": "renamed",
            "document_id": renamed.id,
        }
    written = _upsert_synced_document(
        store,
        connection,
        path,
        str(event["content"]),
    )
    return "applied", {
        "action": written.action,
        "document_id": written.document.id,
    }


def _validated_event(value: object) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise ValueError("sync events must be objects")
    event_id = _required_text(value.get("event_id"), "event_id")
    if len(event_id) > MAX_EVENT_ID_CHARS:
        raise ValueError(
            f"event_id must not exceed {MAX_EVENT_ID_CHARS} characters"
        )
    action = _required_text(value.get("type"), "type")
    if action not in {"upsert", "rename", "delete"}:
        raise ValueError("type must be upsert, rename or delete")
    path = normalize_vault_path(value.get("path"))
    old_path = ""
    if action == "rename":
        old_path = normalize_vault_path(
            value.get("old_path"),
            field="old_path",
        )
        if old_path == path:
            raise ValueError("rename paths must be different")
    content = value.get("content", "")
    content_hash = str(value.get("content_hash") or "").strip()
    if action in {"upsert", "rename"}:
        if not isinstance(content, str):
            raise ValueError("content must be a string")
        if len(content.encode("utf-8")) > MAX_TEXT_FILE_BYTES:
            raise ValueError("content is too large")
        if not content_hash:
            raise ValueError("content_hash is required")
        if text_sha256(content) != content_hash:
            raise ValueError("content hash does not match")
    elif content not in {"", None}:
        raise ValueError("delete events must not include content")
    frontmatter = value.get("frontmatter", {})
    if not isinstance(frontmatter, Mapping):
        raise ValueError("frontmatter must be an object")
    tags = _string_list(value.get("tags", []), "tags")
    resolved_links = _string_list(
        value.get("resolved_links", []),
        "resolved_links",
    )
    unresolved_links = _string_list(
        value.get("unresolved_links", []),
        "unresolved_links",
    )
    return {
        "event_id": event_id,
        "type": action,
        "path": path,
        "old_path": old_path,
        "content": content if isinstance(content, str) else "",
        "content_hash": content_hash,
        "frontmatter": dict(frontmatter),
        "tags": tags,
        "resolved_links": resolved_links,
        "unresolved_links": unresolved_links,
        "occurred_at": str(value.get("occurred_at") or "").strip(),
    }


def _upsert_synced_document(
    store: KnowledgeStore,
    connection: ObsidianConnection,
    path: str,
    content: str,
):
    return store.upsert_document(
        connection.project_id,
        _source_path(connection.id, path),
        _relative_path(path),
        content,
    )


def _delete_synced_document(
    store: KnowledgeStore,
    connection: ObsidianConnection,
    path: str,
):
    relative_path = _relative_path(path)
    document = next(
        (
            item
            for item in store.list_documents(connection.project_id)
            if item.relative_path == relative_path
        ),
        None,
    )
    return store.delete_document(document.id) if document else None


def _source_path(connection_id: str, path: str) -> Path:
    return Path(
        f"{OBSIDIAN_PLUGIN_SOURCE_PREFIX}{connection_id}#{path}"
    )


def _relative_path(path: str) -> str:
    return f"{OBSIDIAN_RELATIVE_PREFIX}{path}"


def _string_list(value: object, field: str) -> list[str]:
    if not isinstance(value, list):
        raise ValueError(f"{field} must be an array")
    result: list[str] = []
    for item in value:
        text = str(item or "").strip()
        if not text:
            raise ValueError(f"{field} must contain non-empty strings")
        if text not in result:
            result.append(text)
    return result


def _required_text(value: object, field: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{field} is required")
    text = value.strip()
    if not text:
        raise ValueError(f"{field} is required")
    return text


def _secret_hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _parse_timestamp(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _utc_datetime(value: datetime | None) -> datetime:
    current = value or datetime.now(timezone.utc)
    if current.tzinfo is None:
        return current.replace(tzinfo=timezone.utc)
    return current.astimezone(timezone.utc)


__all__ = [
    "MAX_SYNC_EVENTS",
    "OBSIDIAN_PLUGIN_SOURCE_PREFIX",
    "ObsidianBridgeAuthenticationError",
    "ObsidianBridgeConflictError",
    "ObsidianBridgeNotFoundError",
    "authenticate_obsidian_connection",
    "complete_obsidian_pairing",
    "list_obsidian_connections",
    "process_obsidian_sync_events",
    "revoke_obsidian_connection",
    "start_obsidian_pairing",
]
