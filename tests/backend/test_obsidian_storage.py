from __future__ import annotations

import sqlite3

import pytest

from backend.storage import KnowledgeStore


def _store_project(tmp_path):
    store = KnowledgeStore(tmp_path / "app.db", vector_store=None)
    project = store.create_project("桥接项目", tmp_path / "project")
    return store, project


def _connection(store, project, suffix="one"):
    pairing = store.create_obsidian_pairing(
        project.id,
        f"code-hash-{suffix}",
        "Knowledge Island/桥接项目",
        "2999-01-01T00:00:00+00:00",
    )
    return store.consume_obsidian_pairing_and_create_connection(
        pairing.id,
        token_hash=f"token-hash-{suffix}",
        vault_id=f"vault-{suffix}",
        vault_name=f"Vault {suffix}",
        output_root=pairing.output_root,
    )


def test_obsidian_schema_and_public_views_hide_credential_hashes(tmp_path):
    store, project = _store_project(tmp_path)
    pairing = store.create_obsidian_pairing(
        project.id,
        "pairing-secret-hash",
        "Knowledge Island/桥接项目",
        "2999-01-01T00:00:00+00:00",
    )
    connection = store.consume_obsidian_pairing_and_create_connection(
        pairing.id,
        token_hash="connection-secret-hash",
        vault_id="vault-id",
        vault_name="学习 Vault",
        output_root=pairing.output_root,
    )

    assert "code_hash" not in pairing.to_dict()
    assert "token_hash" not in connection.to_dict()
    assert connection.vault_name == "学习 Vault"
    with sqlite3.connect(store.db_path) as conn:
        tables = {
            row[0]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            )
        }
    assert {
        "obsidian_pairings",
        "obsidian_connections",
        "obsidian_sync_events",
        "obsidian_publications",
        "obsidian_publication_revisions",
        "obsidian_publication_results",
    } <= tables


def test_pairing_is_one_time_and_project_has_at_most_one_active_connection(
    tmp_path,
):
    store, project = _store_project(tmp_path)
    first = _connection(store, project)
    second_pairing = store.create_obsidian_pairing(
        project.id,
        "code-hash-two",
        "Knowledge Island/桥接项目",
        "2999-01-01T00:00:00+00:00",
    )

    with pytest.raises(ValueError, match="active Obsidian connection"):
        store.consume_obsidian_pairing_and_create_connection(
            second_pairing.id,
            token_hash="token-hash-two",
            vault_id="vault-two",
            vault_name="Vault two",
            output_root=second_pairing.output_root,
        )

    revoked = store.revoke_obsidian_connection(project.id, first.id)
    second = store.consume_obsidian_pairing_and_create_connection(
        second_pairing.id,
        token_hash="token-hash-two",
        vault_id="vault-two",
        vault_name="Vault two",
        output_root=second_pairing.output_root,
    )
    assert revoked.status == "revoked"
    assert second.status == "active"
    with pytest.raises(ValueError, match="already used"):
        store.consume_obsidian_pairing_and_create_connection(
            second_pairing.id,
            token_hash="another-token",
            vault_id="another-vault",
            vault_name="Another",
            output_root=second_pairing.output_root,
        )


def test_sync_events_are_idempotent_per_connection(tmp_path):
    store, project = _store_project(tmp_path)
    connection = _connection(store, project)
    event, created = store.create_obsidian_sync_event(
        project.id,
        connection.id,
        "event-1",
        "upsert",
        "notes/topic.md",
        content_hash="hash-1",
        payload={"content": "# Topic"},
    )
    completed = store.complete_obsidian_sync_event(
        connection.id,
        "event-1",
        "applied",
        {"event_id": "event-1", "action": "created"},
    )
    replay, replay_created = store.create_obsidian_sync_event(
        project.id,
        connection.id,
        "event-1",
        "upsert",
        "notes/topic.md",
        content_hash="different",
        payload={"content": "different"},
    )

    assert created is True
    assert event.status == "received"
    assert completed.status == "applied"
    assert replay_created is False
    assert replay.status == "applied"
    assert replay.content_hash == "hash-1"
    assert replay.result["action"] == "created"


def test_publication_keeps_immutable_artifacts_and_aggregates_results(tmp_path):
    store, project = _store_project(tmp_path)
    connection = _connection(store, project)
    publication = store.create_obsidian_publication(
        project.id,
        connection.id,
        [
            {
                "artifact_type": "project_understanding",
                "stable_id": "stable-overview",
                "target_path": "Knowledge Island/桥接项目/项目理解.md",
                "content": "overview",
                "content_hash": "hash-overview",
                "expected_vault_hash": "",
            },
            {
                "artifact_type": "learning_plan",
                "stable_id": "stable-plan",
                "target_path": "Knowledge Island/桥接项目/学习计划.md",
                "content": "plan",
                "content_hash": "hash-plan",
                "expected_vault_hash": "old-plan-hash",
            },
        ],
    )
    queued = store.confirm_obsidian_publication(project.id, publication.id)
    artifacts = {item.stable_id: item for item in queued.artifacts}
    first_artifact = artifacts["stable-overview"]
    second_artifact = artifacts["stable-plan"]
    partial, first_results = store.record_obsidian_publication_results(
        project.id,
        connection.id,
        publication.id,
        [
            {
                "revision_id": first_artifact.id,
                "status": "applied",
                "actual_hash": "actual-overview",
            }
        ],
    )
    applied, second_results = store.record_obsidian_publication_results(
        project.id,
        connection.id,
        publication.id,
        [
            {
                "revision_id": second_artifact.id,
                "status": "applied",
                "actual_hash": "actual-plan",
            }
        ],
    )

    assert publication.status == "draft"
    assert publication.revision == 1
    assert queued.status == "queued"
    assert partial.status == "queued"
    assert applied.status == "applied"
    assert first_results[0].status == "applied"
    assert second_results[0].actual_hash == "actual-plan"
    persisted = store.get_obsidian_publication(project.id, publication.id)
    assert persisted.artifacts[0].content in {"overview", "plan"}
    baseline = store.latest_obsidian_artifact_baseline(
        project.id,
        connection.id,
        "stable-plan",
    )
    assert baseline["actual_hash"] == "actual-plan"
