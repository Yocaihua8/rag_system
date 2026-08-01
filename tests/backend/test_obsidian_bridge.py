from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from backend.domain.obsidian_bridge import (
    ObsidianBridgeAuthenticationError,
    ObsidianBridgeConflictError,
    authenticate_obsidian_connection,
    complete_obsidian_pairing,
    process_obsidian_sync_events,
    start_obsidian_pairing,
)
from backend.domain.obsidian_protocol import text_sha256
from backend.domain.project_analysis import analyze_project
from backend.storage import KnowledgeStore


def _store_project(tmp_path):
    store = KnowledgeStore(tmp_path / "app.db", vector_store=None)
    project = store.create_project("Obsidian 学习", tmp_path / "project")
    return store, project


def _paired(store, project, now=None):
    started = start_obsidian_pairing(store, project.id, now=now)
    completed = complete_obsidian_pairing(
        store,
        started["pairing"]["code"],
        "vault-id",
        "学习 Vault",
        now=now,
    )
    return completed


def _event(event_id, action, path, content="", **extra):
    event = {
        "event_id": event_id,
        "type": action,
        "path": path,
        "frontmatter": {"topic": "local"},
        "tags": ["learning"],
        "resolved_links": ["README.md"],
        "unresolved_links": ["Missing note"],
        "occurred_at": "2026-07-23T10:00:00Z",
    }
    if action != "delete":
        event["content"] = content
        event["content_hash"] = text_sha256(content)
    event.update(extra)
    return event


def test_pairing_returns_secrets_once_and_connection_token_is_route_scoped(
    tmp_path,
):
    store, project = _store_project(tmp_path)
    started = start_obsidian_pairing(
        store,
        project.id,
        output_root="Knowledge Island/自定义",
    )
    code = started["pairing"]["code"]
    completed = complete_obsidian_pairing(
        store,
        code,
        "vault-id",
        "学习 Vault",
    )
    token = completed["token"]
    connection = authenticate_obsidian_connection(
        store,
        {"authorization": f"Bearer {token}"},
    )

    assert connection.project_id == project.id
    assert connection.output_root == "Knowledge Island/自定义"
    assert connection.token_hash != token
    assert "token_hash" not in completed["connection"]
    with pytest.raises(ObsidianBridgeAuthenticationError):
        authenticate_obsidian_connection(
            store,
            {"authorization": "Bearer wrong"},
        )
    with pytest.raises(ObsidianBridgeConflictError, match="already used"):
        complete_obsidian_pairing(
            store,
            code,
            "other-vault",
            "Other",
        )


def test_pairing_code_expires_and_active_connection_blocks_new_pairing(tmp_path):
    store, project = _store_project(tmp_path)
    now = datetime(2026, 7, 23, tzinfo=timezone.utc)
    started = start_obsidian_pairing(store, project.id, now=now)

    with pytest.raises(ObsidianBridgeAuthenticationError, match="expired"):
        complete_obsidian_pairing(
            store,
            started["pairing"]["code"],
            "vault-id",
            "Vault",
            now=now + timedelta(seconds=301),
        )

    completed = complete_obsidian_pairing(
        store,
        started["pairing"]["code"],
        "vault-id",
        "Vault",
        now=now,
    )
    assert completed["connection"]["status"] == "active"
    with pytest.raises(ObsidianBridgeConflictError, match="active"):
        start_obsidian_pairing(store, project.id, now=now)


def test_sync_upsert_replay_rename_modify_delete_preserves_document_identity(
    tmp_path,
):
    store, project = _store_project(tmp_path)
    completed = _paired(store, project)
    connection = authenticate_obsidian_connection(
        store,
        {"authorization": f"Bearer {completed['token']}"},
    )
    first_content = "# Topic\n\nFirst body with local evidence."
    first = process_obsidian_sync_events(
        store,
        connection,
        [_event("event-1", "upsert", "notes/topic.md", first_content)],
    )
    created_id = first["results"][0]["document_id"]
    replay = process_obsidian_sync_events(
        store,
        connection,
        [_event("event-1", "upsert", "notes/topic.md", "different")],
    )
    renamed = process_obsidian_sync_events(
        store,
        connection,
        [
            _event(
                "event-2",
                "rename",
                "notes/renamed.md",
                first_content,
                old_path="notes/topic.md",
            )
        ],
    )
    changed_content = "# Topic\n\nChanged body with current evidence."
    modified = process_obsidian_sync_events(
        store,
        connection,
        [_event("event-3", "upsert", "notes/renamed.md", changed_content)],
    )
    deleted = process_obsidian_sync_events(
        store,
        connection,
        [_event("event-4", "delete", "notes/renamed.md")],
    )

    assert first["results"][0]["action"] == "created"
    assert replay["results"][0]["replayed"] is True
    assert replay["results"][0]["document_id"] == created_id
    assert renamed["results"][0]["document_id"] == created_id
    assert renamed["results"][0]["action"] == "renamed"
    assert modified["results"][0]["document_id"] == created_id
    assert modified["results"][0]["action"] == "updated"
    assert deleted["results"][0]["document_id"] == created_id
    assert store.get_document(created_id) is None


def test_sync_marks_analysis_stale_and_excludes_only_exact_output_root(tmp_path):
    store, project = _store_project(tmp_path)
    completed = _paired(store, project)
    connection = authenticate_obsidian_connection(
        store,
        {"authorization": f"Bearer {completed['token']}"},
    )
    source = "# Source\n\nInitial current project note."
    result = process_obsidian_sync_events(
        store,
        connection,
        [_event("event-1", "upsert", "source.md", source)],
    )
    analyze_project(store, project.id)
    ignored = process_obsidian_sync_events(
        store,
        connection,
        [
            _event(
                "event-2",
                "upsert",
                f"{connection.output_root}/项目理解.md",
                "# Managed",
            )
        ],
    )
    similar = process_obsidian_sync_events(
        store,
        connection,
        [
            _event(
                "event-3",
                "upsert",
                f"{connection.output_root}2/user.md",
                "# User note",
            )
        ],
    )
    changed = process_obsidian_sync_events(
        store,
        connection,
        [_event("event-4", "upsert", "source.md", f"{source}\nChanged")],
    )

    assert result["results"][0]["status"] == "applied"
    assert ignored["results"][0]["status"] == "ignored"
    assert similar["results"][0]["status"] == "applied"
    assert changed["results"][0]["status"] == "applied"
    assert store.get_latest_coach_analysis_run(project.id).status == "stale"


def test_sync_rejects_traversal_and_hash_mismatch_without_writing(tmp_path):
    store, project = _store_project(tmp_path)
    completed = _paired(store, project)
    connection = authenticate_obsidian_connection(
        store,
        {"authorization": f"Bearer {completed['token']}"},
    )
    invalid_path = _event(
        "event-1",
        "upsert",
        "../escape.md",
        "# Escape",
    )
    invalid_hash = _event(
        "event-2",
        "upsert",
        "notes/topic.md",
        "# Topic",
    )
    invalid_hash["content_hash"] = "wrong"

    result = process_obsidian_sync_events(
        store,
        connection,
        [invalid_path, invalid_hash],
    )

    assert [item["status"] for item in result["results"]] == [
        "failed",
        "failed",
    ]
    assert store.list_documents(project.id) == []
    assert result["connection"]["sync_status"] == "error"
