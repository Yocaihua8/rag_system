from __future__ import annotations

import json
import time
from pathlib import Path

from fastapi.testclient import TestClient

from backend.api.server import create_app


def _headers(key: str) -> dict[str, str]:
    return {"Idempotency-Key": key, "X-Request-ID": f"request-{key}"}


def _wait_for_terminal(
    client: TestClient,
    run_id: str,
    *,
    timeout_seconds: float = 5.0,
) -> dict:
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        response = client.get(f"/api/v3/runs/{run_id}")
        assert response.status_code == 200, response.text
        run = response.json()["data"]["run"]
        if run["status"] in {"completed", "failed", "cancelled"}:
            return run
        time.sleep(0.02)
    raise AssertionError("v3 run did not reach a terminal state")


def test_v3_lifespan_executes_project_inspection_and_replays_events(
    tmp_path: Path,
):
    project_root = tmp_path / "project"
    project_root.mkdir()
    (project_root / "package.json").write_text(
        '{"name":"demo"}',
        encoding="utf-8",
    )
    (project_root / "README.md").write_text("demo project", encoding="utf-8")
    app = create_app(
        db_path=tmp_path / "v2.db",
        v3_db_path=tmp_path / "v3" / "app.db",
    )

    with TestClient(app) as client:
        health = client.get("/api/v3/health")
        assert health.status_code == 200
        assert health.json()["data"] == {
            "status": "ok",
            "data_generation": "v3",
            "schema_revision": "0001_v3_initial",
            "executor_running": True,
        }

        project_response = client.post(
            "/api/v3/projects",
            headers=_headers("project-1"),
            json={"name": "Demo", "root_path": str(project_root)},
        )
        assert project_response.status_code == 201, project_response.text
        project_id = project_response.json()["data"]["project"]["id"]

        task_response = client.post(
            "/api/v3/tasks",
            headers=_headers("task-1"),
            json={
                "project_id": project_id,
                "title": "Inspect project",
                "message": "Inspect this project's structure",
            },
        )
        assert task_response.status_code == 201, task_response.text
        task_id = task_response.json()["data"]["task"]["id"]

        run_response = client.post(
            f"/api/v3/tasks/{task_id}/runs",
            headers=_headers("run-1"),
            json={"workflow_key": "project.inspect.v1", "depth": "quick"},
        )
        assert run_response.status_code == 202, run_response.text
        run_id = run_response.json()["data"]["run"]["id"]

        run = _wait_for_terminal(client, run_id)
        assert run["status"] == "completed", run

        steps_response = client.get(f"/api/v3/runs/{run_id}/steps")
        steps = steps_response.json()["data"]["items"]
        assert [step["status"] for step in steps] == [
            "succeeded",
            "succeeded",
            "succeeded",
        ]
        assert [step["node_type"] for step in steps] == [
            "trigger.manual",
            "project.analyze",
            "artifact.create",
        ]

        artifacts_response = client.get(
            "/api/v3/artifacts",
            params={"run_id": run_id},
        )
        artifacts = artifacts_response.json()["data"]["items"]
        assert len(artifacts) == 1
        artifact = artifacts[0]
        assert artifact["artifact_type"] == "project_inspection"
        inspection = json.loads(artifact["content"])
        assert inspection["manifest_paths"] == ["package.json"]
        assert str(project_root.resolve()) not in artifact["content"]

        event_response = client.get(
            f"/api/v3/runs/{run_id}/events",
            params={"after_sequence": 0},
        )
        assert event_response.status_code == 200
        assert event_response.headers["content-type"].startswith(
            "text/event-stream"
        )
        assert "event: run.queued" in event_response.text
        assert "event: run.completed" in event_response.text
        assert str(project_root.resolve()) not in event_response.text

        replay_response = client.get(
            f"/api/v3/runs/{run_id}/events",
            headers={"Last-Event-ID": "1"},
            params={"after_sequence": 0},
        )
        assert replay_response.status_code == 200
        assert "id: 1\n" not in replay_response.text
