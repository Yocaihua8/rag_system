from __future__ import annotations

from fastapi.testclient import TestClient

from backend.api.auth import AuthSettings
from backend.api.dispatch import dispatch
from backend.api.openapi_schema import WEB_MVP_API_OPERATIONS
from backend.api.server import create_app
from backend.domain.obsidian_protocol import text_sha256
from backend.domain.project_analysis import analyze_project
from backend.storage import KnowledgeStore


OBSIDIAN_OPERATIONS = {
    ("POST", "/api/obsidian/pairing/start"),
    ("POST", "/api/obsidian/pairing/complete"),
    ("GET", "/api/obsidian/connections"),
    ("POST", "/api/obsidian/connections/revoke"),
    ("POST", "/api/obsidian/sync/events"),
    ("POST", "/api/obsidian/publications/preview"),
    ("POST", "/api/obsidian/publications/confirm"),
    ("POST", "/api/obsidian/publications/result"),
    ("GET", "/api/obsidian/publications/pending"),
}


def _store_project(tmp_path):
    store = KnowledgeStore(tmp_path / "app.db", vector_store=None)
    root = tmp_path / "project"
    root.mkdir()
    project = store.create_project("Obsidian 项目", root)
    return store, project, root


def _pair_with_dispatch(store, project):
    started = dispatch(
        store,
        "POST",
        "/api/obsidian/pairing/start",
        {"project_id": project.id},
    )
    completed = dispatch(
        store,
        "POST",
        "/api/obsidian/pairing/complete",
        {
            "code": started.body["pairing"]["code"],
            "vault_id": "vault-id",
            "vault_name": "学习 Vault",
        },
    )
    return completed.body


def _auth_settings():
    return AuthSettings(
        enabled=True,
        api_key="app-secret",
        jwt_secret="jwt-secret",
        jwt_ttl_seconds=120,
    )


def test_obsidian_operations_are_registered_in_openapi():
    operations = {
        (method, path)
        for method, path, _summary in WEB_MVP_API_OPERATIONS
    }

    assert OBSIDIAN_OPERATIONS <= operations


def test_pairing_connections_and_plugin_self_revoke_dispatch(tmp_path):
    store, project, _ = _store_project(tmp_path)
    completed = _pair_with_dispatch(store, project)
    token = completed["token"]
    connection_id = completed["connection"]["id"]

    listed = dispatch(
        store,
        "GET",
        f"/api/obsidian/connections?project_id={project.id}",
    )
    denied = dispatch(
        store,
        "POST",
        "/api/obsidian/connections/revoke",
        {"connection_id": "another-connection"},
        request_context={"authorization": f"Bearer {token}"},
    )
    revoked = dispatch(
        store,
        "POST",
        "/api/obsidian/connections/revoke",
        {"connection_id": connection_id},
        request_context={"authorization": f"Bearer {token}"},
    )

    assert listed.status == 200
    assert listed.body["connections"][0]["id"] == connection_id
    assert "token_hash" not in listed.body["connections"][0]
    assert denied.status == 403
    assert revoked.status == 200
    assert revoked.body["connection"]["status"] == "revoked"


def test_sync_accepts_obsidian_link_count_maps_and_replays_events(tmp_path):
    store, project, _ = _store_project(tmp_path)
    completed = _pair_with_dispatch(store, project)
    token = completed["token"]
    connection_id = completed["connection"]["id"]
    content = "# Topic\n\nLinked to [[README]] and [[Missing]]."
    event = {
        "event_id": "event-map-1",
        "type": "upsert",
        "path": "notes/topic.md",
        "content": content,
        "content_hash": text_sha256(content),
        "frontmatter": {"topic": "local"},
        "tags": ["learning"],
        "resolved_links": {"README.md": 2},
        "unresolved_links": {"Missing": 1},
    }
    context = {"authorization": f"Bearer {token}"}

    first = dispatch(
        store,
        "POST",
        "/api/obsidian/sync/events",
        {"events": [event]},
        request_context=context,
    )
    replay = dispatch(
        store,
        "POST",
        "/api/obsidian/sync/events",
        {"events": [event]},
        request_context=context,
    )
    stored = store.get_obsidian_sync_event(
        connection_id,
        event["event_id"],
    )

    assert first.status == 200
    assert first.body["results"][0]["status"] == "applied"
    assert replay.body["results"][0]["replayed"] is True
    assert stored.payload["resolved_links"] == {"README.md": 2}
    assert stored.payload["unresolved_links"] == {"Missing": 1}


def test_publication_preview_confirm_pending_and_result_api(tmp_path):
    store, project, root = _store_project(tmp_path)
    source = root / "app.py"
    content = "from fastapi import FastAPI\napp = FastAPI()\n"
    source.write_text(content, encoding="utf-8")
    store.upsert_document(project.id, source, "app.py", content)
    analyze_project(store, project.id)
    completed = _pair_with_dispatch(store, project)
    context = {"authorization": f"Bearer {completed['token']}"}

    preview = dispatch(
        store,
        "POST",
        "/api/obsidian/publications/preview",
        {
            "project_id": project.id,
            "artifact_types": ["project_understanding"],
        },
    )
    publication = preview.body["publication"]
    confirmed = dispatch(
        store,
        "POST",
        "/api/obsidian/publications/confirm",
        {
            "project_id": project.id,
            "publication_id": publication["id"],
        },
    )
    pending = dispatch(
        store,
        "GET",
        "/api/obsidian/publications/pending",
        request_context=context,
    )
    artifact = publication["artifacts"][0]
    result = dispatch(
        store,
        "POST",
        "/api/obsidian/publications/result",
        {
            "publication_id": publication["id"],
            "results": [
                {
                    "revision_id": artifact["revision_id"],
                    "status": "applied",
                    "actual_hash": text_sha256("plugin-final"),
                }
            ],
        },
        request_context=context,
    )

    assert preview.status == 200
    assert publication["status"] == "draft"
    assert confirmed.body["publication"]["status"] == "queued"
    assert pending.body["publications"][0]["id"] == publication["id"]
    assert result.body["publication"]["status"] == "applied"


def test_plugin_routes_self_authenticate_when_application_auth_is_enabled(
    tmp_path,
):
    store, project, _ = _store_project(tmp_path)
    client = TestClient(
        create_app(store=store, auth_settings=_auth_settings())
    )
    blocked_start = client.post(
        "/api/obsidian/pairing/start",
        json={"project_id": project.id},
    )
    started = client.post(
        "/api/obsidian/pairing/start",
        json={"project_id": project.id},
        headers={"X-API-Key": "app-secret"},
    )
    completed = client.post(
        "/api/obsidian/pairing/complete",
        json={
            "code": started.json()["pairing"]["code"],
            "vault_id": "vault-id",
            "vault_name": "学习 Vault",
        },
    )
    token = completed.json()["token"]
    connection_id = completed.json()["connection"]["id"]
    plugin_headers = {"Authorization": f"Bearer {token}"}
    pending = client.get(
        "/api/obsidian/publications/pending",
        headers=plugin_headers,
    )
    content = "# Synced through the plugin route"
    synced = client.post(
        "/api/obsidian/sync/events",
        json={
            "events": [
                {
                    "event_id": "auth-event-1",
                    "type": "upsert",
                    "path": "notes/auth.md",
                    "content": content,
                    "content_hash": text_sha256(content),
                    "frontmatter": {},
                    "tags": [],
                    "resolved_links": {},
                    "unresolved_links": {},
                }
            ]
        },
        headers=plugin_headers,
    )
    unauthorized_main_revoke = client.post(
        "/api/obsidian/connections/revoke",
        json={
            "project_id": project.id,
            "connection_id": connection_id,
        },
        headers=plugin_headers,
    )
    self_revoke = client.post(
        "/api/obsidian/connections/revoke",
        json={"connection_id": connection_id},
        headers=plugin_headers,
    )
    after_revoke = client.get(
        "/api/obsidian/publications/pending",
        headers=plugin_headers,
    )
    second_root = tmp_path / "second-project"
    second_root.mkdir()
    second_project = store.create_project("第二项目", second_root)
    second_start = client.post(
        "/api/obsidian/pairing/start",
        json={"project_id": second_project.id},
        headers={"X-API-Key": "app-secret"},
    )
    second_complete = client.post(
        "/api/obsidian/pairing/complete",
        json={
            "code": second_start.json()["pairing"]["code"],
            "vault_id": "vault-id-2",
            "vault_name": "第二 Vault",
        },
    )
    main_revoke = client.post(
        "/api/obsidian/connections/revoke",
        json={
            "project_id": second_project.id,
            "connection_id": second_complete.json()["connection"]["id"],
        },
        headers={"X-API-Key": "app-secret"},
    )

    assert blocked_start.status_code == 401
    assert completed.status_code == 200
    assert pending.status_code == 200
    assert synced.status_code == 200
    assert synced.json()["results"][0]["status"] == "applied"
    assert unauthorized_main_revoke.status_code == 401
    assert self_revoke.status_code == 200
    assert after_revoke.status_code == 401
    assert main_revoke.status_code == 200
