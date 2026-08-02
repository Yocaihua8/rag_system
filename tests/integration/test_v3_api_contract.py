from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi.testclient import TestClient

from backend.api.v3.app import create_v3_app
from backend.storage.v3.errors import IdempotencyConflictError


NOW = "2026-08-02T10:00:00.000Z"


class FakeStore:
    def __init__(self) -> None:
        self.raise_task_conflict = False
        self.projects = [
            {
                "id": "project-1",
                "name": "Knowledge Island",
                "root_path": "E:/Dev/Projects/knowledage_island",
                "status": "active",
                "version": 1,
                "created_at": NOW,
                "updated_at": NOW,
            }
        ]

    def create_project(self, **kwargs: Any) -> dict[str, Any]:
        return {"project": self.projects[0], "replayed": False}

    def list_projects(self) -> list[dict[str, Any]]:
        return list(self.projects)

    def get_task(self, task_id: str) -> dict[str, Any] | None:
        return None

    def list_tasks(self, **kwargs: Any) -> list[dict[str, Any]]:
        return []

    def create_task(self, **kwargs: Any) -> dict[str, Any]:
        if self.raise_task_conflict:
            raise IdempotencyConflictError(
                "idempotency key was already used with a different request hash"
            )
        return {
            "task": {
                "id": "task-1",
                "project_id": kwargs["project_id"],
                "title": kwargs["title"],
                "prompt": kwargs["prompt"],
                "depth": kwargs["depth"],
                "status": "queued",
                "version": 1,
                "created_at": NOW,
                "updated_at": NOW,
            },
            "replayed": False,
        }


def _client(store: FakeStore | None = None) -> tuple[TestClient, FakeStore]:
    fake_store = store or FakeStore()
    app = create_v3_app(
        store=fake_store,
        database_info={"alembic_revision": "0001_v3_baseline"},
    )
    return TestClient(app), fake_store


def test_success_envelope_and_request_id_are_consistent():
    client, _ = _client()

    response = client.get("/health", headers={"X-Request-ID": "trace-123"})

    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == "trace-123"
    assert response.json() == {
        "data": {
            "status": "ok",
            "data_generation": "v3",
            "schema_revision": "0001_v3_baseline",
            "executor_running": False,
        },
        "meta": {"request_id": "trace-123"},
    }

    generated = client.get("/projects")
    generated_id = generated.headers["X-Request-ID"]
    assert generated.status_code == 200
    assert generated_id
    assert generated.json()["meta"]["request_id"] == generated_id
    assert generated.json()["data"]["items"][0]["id"] == "project-1"


def test_missing_idempotency_key_uses_error_envelope(tmp_path: Path):
    client, _ = _client()
    project_root = tmp_path / "project"
    project_root.mkdir()

    response = client.post(
        "/projects",
        headers={"X-Request-ID": "missing-idempotency"},
        json={"name": "Demo", "root_path": str(project_root)},
    )

    assert response.status_code == 422
    assert response.headers["X-Request-ID"] == "missing-idempotency"
    assert response.json() == {
        "error": {
            "code": "application_validation_error",
            "message": "Idempotency-Key header is required",
            "details": {},
        },
        "request_id": "missing-idempotency",
    }


def test_not_found_and_idempotency_conflict_use_error_envelope():
    client, store = _client()

    missing = client.get(
        "/tasks/missing",
        headers={"X-Request-ID": "missing-task"},
    )
    assert missing.status_code == 404
    assert missing.json() == {
        "error": {
            "code": "not_found",
            "message": "task not found",
            "details": {},
        },
        "request_id": "missing-task",
    }

    store.raise_task_conflict = True
    conflict = client.post(
        "/tasks",
        headers={
            "Idempotency-Key": "task-command-1",
            "X-Request-ID": "task-conflict",
        },
        json={
            "project_id": "project-1",
            "title": "Inspect",
            "message": "Inspect this project",
        },
    )
    assert conflict.status_code == 409
    assert conflict.json() == {
        "error": {
            "code": "idempotency_conflict",
            "message": (
                "idempotency key was already used with a different request hash"
            ),
            "details": {},
        },
        "request_id": "task-conflict",
    }


def test_openapi_lists_real_paths_and_success_envelope_schemas():
    client, _ = _client()

    schema = client.get("/openapi.json").json()

    assert set(schema["paths"]) == {
        "/health",
        "/projects",
        "/tasks",
        "/tasks/{task_id}",
        "/tasks/{task_id}/messages",
        "/tasks/{task_id}/runs",
        "/runs/{run_id}",
        "/runs/{run_id}/pause",
        "/runs/{run_id}/resume",
        "/runs/{run_id}/cancel",
        "/runs/{run_id}/retry",
        "/runs/{run_id}/steps",
        "/runs/{run_id}/events",
        "/approvals",
        "/approvals/{approval_id}",
        "/approvals/{approval_id}/resolve",
        "/artifacts",
        "/artifacts/{artifact_id}",
        "/artifacts/{artifact_id}/preview",
        "/workflows/validate",
        "/workflows",
        "/workflows/{workflow_id}",
        "/workflows/{workflow_id}/drafts",
        "/workflows/{workflow_id}/publish",
        "/workflows/{workflow_id}/archive",
        "/workflows/{workflow_id}/bindings",
        "/workflow-bindings",
    }
    assert schema["paths"]["/health"]["get"]["responses"]["200"]["content"][
        "application/json"
    ]["schema"] == {
        "$ref": "#/components/schemas/SuccessEnvelope_HealthData_"
    }
    assert schema["paths"]["/tasks"]["post"]["responses"]["201"]["content"][
        "application/json"
    ]["schema"] == {
        "$ref": "#/components/schemas/SuccessEnvelope_TaskMutationData_"
    }
    success_schema = schema["components"]["schemas"][
        "SuccessEnvelope_TaskMutationData_"
    ]
    assert success_schema["required"] == ["data", "meta"]
    assert success_schema["properties"]["data"] == {
        "$ref": "#/components/schemas/TaskMutationData"
    }
    assert success_schema["properties"]["meta"] == {
        "$ref": "#/components/schemas/ResponseMeta"
    }


def test_openapi_documents_runtime_error_envelope_for_422_404_and_409():
    client, _ = _client()

    schema = client.get("/openapi.json").json()
    components = schema["components"]["schemas"]

    assert "ErrorEnvelope" in components
    expected = {"$ref": "#/components/schemas/ErrorEnvelope"}
    assert schema["paths"]["/projects"]["post"]["responses"]["422"]["content"][
        "application/json"
    ]["schema"] == expected
    assert schema["paths"]["/tasks/{task_id}"]["get"]["responses"]["404"][
        "content"
    ]["application/json"]["schema"] == expected
    assert schema["paths"]["/tasks"]["post"]["responses"]["409"]["content"][
        "application/json"
    ]["schema"] == expected
