from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from backend.api.server import create_app
from backend.config.v3 import V3RuntimeSettings


def _headers(key: str) -> dict[str, str]:
    return {"Idempotency-Key": key}


def _ready_artifact(client: TestClient):
    store = client.app.state.v3_store
    project = store.create_project(name="Export", root_path=store.db_path.parent / "project", idempotency_key="project", request_hash="project")
    task = store.create_task(project_id=project["project"]["id"], title="Export", prompt="prepare", depth="standard", idempotency_key="task", request_hash="task")
    task_id = task["task"]["id"]
    message_id = store.list_task_messages(task_id)[0]["id"]
    run = store.create_run_with_steps(task_id=task_id, input_message_id=message_id, workflow_key="project.inspect", workflow_version=1, workflow_checksum="run", depth="standard", steps=[{"step_key": "artifact", "node_type": "artifact.create", "effect_kind": "analysis", "input": {}}], idempotency_key="run", request_hash="run")
    return store.create_artifact(task_id=task_id, run_id=run["run"]["id"], kind="report", title="Report", content="exported content", metadata={}, idempotency_key="artifact", request_hash="artifact")["artifact"]


def _v3_data_root(client: TestClient) -> Path:
    v3_route = next(route for route in client.app.routes if getattr(route, "path", "") == "/api/v3")
    return Path(v3_route.app.state.current_data_root)


def test_v3_artifact_export_requires_confirmed_snapshot_and_uses_managed_path(tmp_path):
    data_root = tmp_path / "runtime" / "v3"
    v3_settings = V3RuntimeSettings(
        data_root=data_root,
        db_path=data_root / "app.db",
        vector_dir=data_root / "vectors",
        artifacts_dir=data_root / "artifacts",
        logs_dir=data_root / "logs",
        backups_dir=data_root / "backups",
        max_concurrency=1,
        lease_seconds=30,
        poll_interval_ms=100,
    )
    app = create_app(db_path=tmp_path / "v2.db", v3_settings=v3_settings)
    with TestClient(app) as client:
        artifact = _ready_artifact(client)
        preview = client.get(f"/api/v3/artifacts/{artifact['id']}/export-preview")
        assert preview.status_code == 200, preview.text
        data = preview.json()["data"]["preview"]
        assert data["target_filename"] == f"artifact-{artifact['id']}.txt"

        stale = client.post(f"/api/v3/artifacts/{artifact['id']}/export-confirm", headers=_headers("stale"), json={"expected_version": data["version"], "expected_checksum": "0" * 64})
        assert stale.status_code == 422, stale.text
        assert not (_v3_data_root(client) / "artifacts" / "exports" / data["target_filename"]).exists()

        confirmed = client.post(f"/api/v3/artifacts/{artifact['id']}/export-confirm", headers=_headers("export"), json={"expected_version": data["version"], "expected_checksum": data["checksum"]})
        assert confirmed.status_code == 200, confirmed.text
        result = confirmed.json()["data"]
        assert result["artifact"]["status"] == "exported"
        assert result["content_ref"] == f"exports/{data['target_filename']}"
        exported = _v3_data_root(client) / "artifacts" / "exports" / data["target_filename"]
        assert exported.read_text(encoding="utf-8") == "exported content"

        replay = client.post(f"/api/v3/artifacts/{artifact['id']}/export-confirm", headers=_headers("export"), json={"expected_version": data["version"], "expected_checksum": data["checksum"]})
        assert replay.status_code == 200, replay.text
        assert replay.json()["data"]["replayed"] is True
