from __future__ import annotations

import time
from pathlib import Path

from fastapi.testclient import TestClient

from backend.api.server import create_app


def _headers(key: str) -> dict[str, str]:
    return {"Idempotency-Key": key}


def _graph() -> dict:
    return {
        "nodes": [
            {"id": "trigger", "type": "trigger.manual", "config": {}},
            {
                "id": "plan",
                "type": "agent.plan",
                "config": {"depth": "quick"},
            },
        ],
        "edges": [
            {
                "id": "trigger-plan",
                "source": "trigger",
                "source_port": "out",
                "target": "plan",
                "target_port": "in",
            }
        ],
    }


def _executable_graph() -> dict:
    return {
        "nodes": [
            {"id": "trigger", "type": "trigger.manual", "config": {}},
            {"id": "analyze", "type": "project.analyze", "config": {"analysis_kind": "sources"}},
            {"id": "artifact", "type": "artifact.create", "config": {"format": "json"}},
            {"id": "respond", "type": "agent.respond", "config": {}},
        ],
        "edges": [
            {"id": "trigger-analyze", "source": "trigger", "source_port": "out", "target": "analyze", "target_port": "in"},
            {"id": "analyze-artifact", "source": "analyze", "source_port": "out", "target": "artifact", "target_port": "in"},
            {"id": "artifact-respond", "source": "artifact", "source_port": "out", "target": "respond", "target_port": "in"},
        ],
    }


def test_workflow_draft_publish_bind_and_archive_are_versioned(tmp_path: Path):
    project_root = tmp_path / "project"
    project_root.mkdir()
    app = create_app(
        db_path=tmp_path / "v2.db",
        v3_db_path=tmp_path / "v3" / "app.db",
    )

    with TestClient(app) as client:
        project_response = client.post(
            "/api/v3/projects",
            headers=_headers("workflow-project"),
            json={"name": "Workflow project", "root_path": str(project_root)},
        )
        project_id = project_response.json()["data"]["project"]["id"]

        validation = client.post("/api/v3/workflows/validate", json=_graph())
        assert validation.status_code == 200
        assert validation.json()["data"] == {"valid": True, "errors": []}

        created = client.post(
            "/api/v3/workflows",
            headers=_headers("workflow-create"),
            json={
                "workflow_key": "quick-plan.v1",
                "name": "Quick plan",
                "description": "Create a small project plan",
                "scope_type": "global",
                "graph": _graph(),
            },
        )
        assert created.status_code == 201, created.text
        created_data = created.json()["data"]
        workflow = created_data["workflow"]
        draft = created_data["version"]
        assert draft["status"] == "draft"

        published = client.post(
            f"/api/v3/workflows/{workflow['id']}/publish",
            headers=_headers("workflow-publish"),
            json={
                "version_id": draft["id"],
                "expected_checksum": draft["checksum"],
                "expected_version": workflow["version"],
            },
        )
        assert published.status_code == 200, published.text
        published_data = published.json()["data"]
        assert published_data["version"]["status"] == "published"
        assert (
            published_data["workflow"]["current_published_version_id"]
            == draft["id"]
        )

        bound = client.post(
            f"/api/v3/workflows/{workflow['id']}/bindings",
            headers=_headers("workflow-bind"),
            json={
                "project_id": project_id,
                "workflow_version_id": draft["id"],
                "expected_workflow_version": published_data["workflow"]["version"],
                "expected_binding_version": 0,
            },
        )
        assert bound.status_code == 200, bound.text
        assert bound.json()["data"]["binding"]["project_id"] == project_id

        archived = client.post(
            f"/api/v3/workflows/{workflow['id']}/archive",
            headers=_headers("workflow-archive"),
            json={"expected_version": published_data["workflow"]["version"]},
        )
        assert archived.status_code == 200, archived.text
        assert archived.json()["data"]["workflow"]["status"] == "archived"

        rejected_draft = client.post(
            f"/api/v3/workflows/{workflow['id']}/drafts",
            headers=_headers("workflow-draft-after-archive"),
            json={
                "graph": _graph(),
                "expected_version": archived.json()["data"]["workflow"]["version"],
            },
        )
        assert rejected_draft.status_code == 409
        assert rejected_draft.json()["error"]["code"] == "state_conflict"


def test_published_bound_safe_workflow_can_create_a_versioned_run(tmp_path: Path):
    project_root = tmp_path / "project"
    project_root.mkdir()
    with TestClient(create_app(db_path=tmp_path / "v2.db", v3_db_path=tmp_path / "v3" / "app.db")) as client:
        project = client.post("/api/v3/projects", headers=_headers("project"), json={"name": "Workflow project", "root_path": str(project_root)}).json()["data"]["project"]
        created = client.post("/api/v3/workflows", headers=_headers("create"), json={"workflow_key": "project.safe.v1", "name": "Safe inspection", "description": "", "scope_type": "global", "graph": _executable_graph()}).json()["data"]
        workflow, version = created["workflow"], created["version"]
        published = client.post(f"/api/v3/workflows/{workflow['id']}/publish", headers=_headers("publish"), json={"version_id": version["id"], "expected_checksum": version["checksum"], "expected_version": workflow["version"]}).json()["data"]
        client.post(f"/api/v3/workflows/{workflow['id']}/bindings", headers=_headers("bind"), json={"project_id": project["id"], "workflow_version_id": version["id"], "expected_workflow_version": published["workflow"]["version"], "expected_binding_version": 0})
        task = client.post("/api/v3/tasks", headers=_headers("task"), json={"project_id": project["id"], "title": "Inspect", "message": "inspect"}).json()["data"]

        response = client.post(f"/api/v3/tasks/{task['task']['id']}/runs", headers=_headers("run"), json={"workflow_key": "project.safe.v1", "workflow_version_id": version["id"], "depth": "standard", "input_message_id": task["initial_message"]["id"]})

        assert response.status_code == 202, response.text
        run = response.json()["data"]["run"]
        assert run["workflow_version_id"] == version["id"]
        assert run["workflow_checksum"] == version["checksum"]
        for _ in range(40):
            current = client.get(f"/api/v3/runs/{run['id']}").json()["data"]["run"]
            if current["status"] == "completed":
                break
            time.sleep(0.05)
        assert current["status"] == "completed"
