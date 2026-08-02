from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi.testclient import TestClient

from backend.api.v3.app import create_v3_app
from backend.storage.v3.errors import IdempotencyConflictError, StateConflictError


NOW = "2026-08-02T10:00:00.000Z"


class FakeStore:
    def __init__(self) -> None:
        self.raise_task_conflict = False
        self.raise_retry_conflict = False
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
        self.tasks = {
            "task-1": {
                "id": "task-1",
                "project_id": "project-1",
                "title": "Inspect",
                "prompt": "Inspect this project",
                "depth": "standard",
                "status": "queued",
                "version": 1,
                "created_at": NOW,
                "updated_at": NOW,
            }
        }
        self.runs: list[dict[str, Any]] = []

    def create_project(self, **kwargs: Any) -> dict[str, Any]:
        return {"project": self.projects[0], "replayed": False}

    def list_projects(self) -> list[dict[str, Any]]:
        return list(self.projects)

    def get_task(self, task_id: str) -> dict[str, Any] | None:
        return self.tasks.get(task_id)

    def list_tasks(self, **kwargs: Any) -> list[dict[str, Any]]:
        return []

    def list_task_runs(
        self,
        task_id: str,
        *,
        limit: int,
        offset: int,
    ) -> list[dict[str, Any]]:
        return self.runs[offset : offset + limit]

    def create_task(self, **kwargs: Any) -> dict[str, Any]:
        if self.raise_task_conflict:
            raise IdempotencyConflictError(
                "idempotency key was already used with a different request hash"
            )
        task = {
                "id": "task-1",
                "project_id": kwargs["project_id"],
                "title": kwargs["title"],
                "prompt": kwargs["prompt"],
                "depth": kwargs["depth"],
                "status": "queued",
                "version": 1,
                "created_at": NOW,
                "updated_at": NOW,
            }
        return {
            "task": task,
            "initial_message": {
                "id": "message-1",
                "task_id": "task-1",
                "run_id": None,
                "role": "user",
                "message_type": "message",
                "content": kwargs["prompt"],
                "metadata": {},
                "created_at": NOW,
            },
            "replayed": False,
        }

    def retry_run(self, **kwargs: Any) -> dict[str, Any]:
        if self.raise_retry_conflict:
            raise StateConflictError("failed run already has a retry")
        raise AssertionError("retry_run was not configured for this test")


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
    body = response.json()
    assert body["request_id"] == "missing-idempotency"
    assert body["error"]["code"] == "validation_error"
    assert body["error"]["message"] == "request validation failed"
    assert any(
        issue["loc"] == ["header", "Idempotency-Key"] and issue["type"] == "missing"
        for issue in body["error"]["details"]["issues"]
    )


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


def test_task_runs_list_supports_empty_and_paginated_typed_results():
    client, store = _client()

    empty = client.get("/tasks/task-1/runs")
    assert empty.status_code == 200
    assert empty.json()["data"] == {"items": []}

    store.runs = [
        {
            "id": f"run-{index}",
            "task_id": "task-1",
            "project_id": "project-1",
            "workflow_version_id": None,
            "workflow_key": "project.inspect.v1",
            "workflow_version": 2,
            "workflow_checksum": f"checksum-{index}",
            "depth": "quick",
            "status": "queued",
            "priority": 0,
            "attempt_no": 1,
            "retry_of_run_id": None,
            "version": 1,
            "queued_at": NOW,
            "started_at": None,
            "finished_at": None,
            "paused_at": None,
            "cancel_requested_at": None,
            "lease_owner": "",
            "lease_expires_at": None,
            "error_code": "",
            "error_message": "",
            "result": {},
            "created_at": NOW,
            "updated_at": NOW,
        }
        for index in range(3)
    ]

    page = client.get(
        "/tasks/task-1/runs",
        params={"limit": 1, "offset": 1},
        headers={"X-Request-ID": "task-runs-page"},
    )

    assert page.status_code == 200
    assert page.json()["meta"] == {"request_id": "task-runs-page"}
    assert [run["id"] for run in page.json()["data"]["items"]] == ["run-1"]

    missing = client.get(
        "/tasks/missing/runs",
        headers={"X-Request-ID": "missing-task-runs"},
    )
    assert missing.status_code == 404
    assert missing.json() == {
        "error": {
            "code": "not_found",
            "message": "task not found",
            "details": {},
        },
        "request_id": "missing-task-runs",
    }


def test_second_manual_retry_key_uses_state_conflict_envelope():
    client, store = _client()
    store.raise_retry_conflict = True

    response = client.post(
        "/runs/run-1/retry",
        headers={
            "Idempotency-Key": "retry-second-command",
            "X-Request-ID": "retry-already-created",
        },
        json={"expected_version": 3},
    )

    assert response.status_code == 409
    assert response.json() == {
        "error": {
            "code": "state_conflict",
            "message": "failed run already has a retry",
            "details": {},
        },
        "request_id": "retry-already-created",
    }


def test_openapi_lists_real_paths_and_success_envelope_schemas():
    client, _ = _client()

    schema = client.get("/openapi.json").json()

    assert schema["info"]["version"] == "3.0.0-alpha.2"
    assert schema["paths"]["/runs/{run_id}/events"]["get"]["responses"]["200"][
        "content"
    ]["text/event-stream"]["schema"] == {
        "$ref": "#/components/schemas/AgentEvent"
    }
    assert schema["components"]["schemas"]["AgentEvent"]["discriminator"][
        "propertyName"
    ] == "event_type"

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
    idempotency_parameter = next(
        parameter
        for parameter in schema["paths"]["/tasks"]["post"]["parameters"]
        if parameter["in"] == "header" and parameter["name"] == "Idempotency-Key"
    )
    assert idempotency_parameter["required"] is True
    assert schema["paths"]["/tasks/{task_id}/runs"]["get"]["responses"][
        "200"
    ]["content"]["application/json"]["schema"] == {
        "$ref": "#/components/schemas/SuccessEnvelope_RunListData_"
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
