from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi.testclient import TestClient

import backend.api.v3.app as v3_api
from backend.api.v3.app import create_v3_app
from backend.storage.v3.errors import IdempotencyConflictError, StateConflictError
from backend.storage.v3.store import AgentStore


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


class FakeExecutor:
    def __init__(self) -> None:
        self.running = True
        self.start_calls = 0
        self.stop_calls = 0

    async def start(self) -> None:
        self.start_calls += 1
        self.running = True

    async def stop(self) -> None:
        self.stop_calls += 1
        self.running = False


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


def test_storage_preflight_is_read_only_and_reports_stable_checks(tmp_path: Path):
    current = tmp_path / "runtime" / "v3"
    legacy = tmp_path / "runtime" / "v2"
    target = tmp_path / "migrated" / "v3"
    current.mkdir(parents=True)
    legacy.mkdir(parents=True)
    (current / "app.db").write_bytes(b"agent-data")
    app = create_v3_app(
        store=FakeStore(),
        current_data_root=current,
        legacy_data_root=legacy,
    )
    client = TestClient(app)

    response = client.post(
        "/system/storage/preflight",
        headers={"X-Request-ID": "storage-preflight"},
        json={"target_path": str(target)},
    )

    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == "storage-preflight"
    body = response.json()
    assert body["meta"] == {"request_id": "storage-preflight"}
    assert body["data"]["ready"] is True
    assert body["data"]["target_path"] == str(target.resolve())
    assert {check["code"] for check in body["data"]["checks"]} == {
        "outside_current_v3",
        "outside_legacy_v2",
        "target_is_directory",
        "target_is_not_symlink",
        "target_is_empty",
        "parent_is_writable",
        "source_is_readable",
        "sufficient_free_space",
    }
    assert not target.exists()


def test_storage_preflight_rejects_blank_path_with_error_envelope():
    client, _ = _client()

    response = client.post(
        "/system/storage/preflight",
        headers={"X-Request-ID": "blank-storage-path"},
        json={"target_path": "   "},
    )

    assert response.status_code == 422
    assert response.json()["request_id"] == "blank-storage-path"
    assert response.json()["error"]["code"] == "validation_error"

    invalid_response = client.post(
        "/system/storage/preflight",
        headers={"X-Request-ID": "invalid-storage-path"},
        json={"target_path": "invalid\u0000path"},
    )

    assert invalid_response.status_code == 422
    assert invalid_response.json() == {
        "error": {
            "code": "storage_preflight_invalid_path",
            "message": "storage path cannot be resolved",
            "details": {},
        },
        "request_id": "invalid-storage-path",
    }


def test_system_backup_api_requires_idempotency_and_replays(tmp_path: Path):
    data_root = tmp_path / "runtime" / "v3"
    data_root.mkdir(parents=True)
    store = AgentStore(data_root / "app.db")
    store.initialize()
    app = create_v3_app(
        store=store,
        current_data_root=data_root,
        legacy_data_root=tmp_path / "runtime" / "v2",
        backups_dir=data_root / "backups",
        backup_retention=2,
    )
    client = TestClient(app)
    try:
        missing = client.post("/system/backups")
        created = client.post(
            "/system/backups",
            headers={
                "Idempotency-Key": "api-backup-1",
                "X-Request-ID": "create-backup",
            },
        )
        replayed = client.post(
            "/system/backups",
            headers={"Idempotency-Key": "api-backup-1"},
        )
    finally:
        store.close()

    assert missing.status_code == 422
    assert created.status_code == 201
    assert created.headers["X-Request-ID"] == "create-backup"
    assert created.json()["data"]["replayed"] is False
    assert replayed.status_code == 201
    assert replayed.json()["data"]["replayed"] is True
    assert replayed.json()["data"]["backup"] == created.json()["data"]["backup"]


def test_system_restore_api_is_controlled_persistent_and_idempotent(tmp_path: Path):
    data_root = tmp_path / "runtime" / "v3"
    data_root.mkdir(parents=True)
    store = AgentStore(data_root / "app.db")
    database_info = store.initialize()
    store.create_project(
        name="Before backup",
        root_path=tmp_path / "before-backup",
        idempotency_key="project-before-backup",
        request_hash="project-before-backup-hash",
    )
    executor = FakeExecutor()
    app = create_v3_app(
        store=store,
        executor=executor,
        database_info=database_info,
        current_data_root=data_root,
        legacy_data_root=tmp_path / "runtime" / "v2",
        backups_dir=data_root / "backups",
    )
    client = TestClient(app)
    try:
        created_backup = client.post(
            "/system/backups",
            headers={"Idempotency-Key": "restore-source-backup"},
        ).json()["data"]["backup"]
        store.create_project(
            name="After backup",
            root_path=tmp_path / "after-backup",
            idempotency_key="project-after-backup",
            request_hash="project-after-backup-hash",
        )
        restore_path = (
            f"/system/backups/{created_backup['backup_id']}/restore"
        )
        restore_body = {
            "expected_database_sha256": created_backup["database_sha256"]
        }
        restored = client.post(
            restore_path,
            headers={
                "Idempotency-Key": "restore-command-1",
                "X-Request-ID": "restore-request",
            },
            json=restore_body,
        )
        store.close()
        store.initialize()
        replayed = client.post(
            restore_path,
            headers={"Idempotency-Key": "restore-command-1"},
            json=restore_body,
        )
        conflict = client.post(
            restore_path,
            headers={"Idempotency-Key": "restore-command-1"},
            json={"expected_database_sha256": "0" * 64},
        )
        project_names = {item["name"] for item in store.list_projects()}
    finally:
        store.close()

    assert restored.status_code == 200
    assert restored.headers["X-Request-ID"] == "restore-request"
    restored_data = restored.json()["data"]
    assert restored_data["restored"] is True
    assert restored_data["replayed"] is False
    assert restored_data["backup"] == created_backup
    assert restored_data["database_info"]["data_generation"] == "v3"
    assert "db_path" not in restored_data["database_info"]
    assert project_names == {"Before backup"}
    assert replayed.status_code == 200
    assert replayed.json()["data"]["replayed"] is True
    assert replayed.json()["data"]["backup"] == created_backup
    assert conflict.status_code == 409
    assert conflict.json()["error"]["code"] == "idempotency_conflict"
    assert executor.stop_calls == 1
    assert executor.start_calls == 1
    assert executor.running is True


def test_system_restore_gate_rejects_active_or_maintenance_requests(tmp_path: Path):
    data_root = tmp_path / "runtime" / "v3"
    data_root.mkdir(parents=True)
    store = AgentStore(data_root / "app.db")
    database_info = store.initialize()
    app = create_v3_app(
        store=store,
        database_info=database_info,
        current_data_root=data_root,
        legacy_data_root=tmp_path / "runtime" / "v2",
        backups_dir=data_root / "backups",
    )
    client = TestClient(app)
    try:
        app.state.active_requests = 1
        busy = client.post(
            "/system/backups/backup-00000000000000000000000000000000/restore",
            headers={
                "Idempotency-Key": "busy-restore",
                "X-Request-ID": "busy-restore-request",
            },
            json={"expected_database_sha256": "0" * 64},
        )
        app.state.active_requests = 0
        app.state.restore_in_progress = True
        unavailable = client.get(
            "/health",
            headers={"X-Request-ID": "maintenance-health"},
        )
    finally:
        app.state.restore_in_progress = False
        store.close()

    assert busy.status_code == 409
    assert busy.headers["X-Request-ID"] == "busy-restore-request"
    assert busy.json()["error"]["code"] == "restore_busy"
    assert busy.json()["error"]["details"] == {"active_requests": 1}
    assert unavailable.status_code == 503
    assert unavailable.headers["X-Request-ID"] == "maintenance-health"
    assert unavailable.json()["error"]["code"] == "maintenance_in_progress"


def test_system_restore_api_reactivates_original_after_restore_failure(
    tmp_path: Path,
    monkeypatch,
):
    data_root = tmp_path / "runtime" / "v3"
    data_root.mkdir(parents=True)
    store = AgentStore(data_root / "app.db")
    database_info = store.initialize()
    store.create_project(
        name="Original data",
        root_path=tmp_path / "original-project",
        idempotency_key="original-project",
        request_hash="original-project-hash",
    )
    backup = v3_api.create_v3_backup(
        store.db_path,
        current_data_root=data_root,
        backups_dir=data_root / "backups",
        idempotency_key="failed-restore-source",
    )["backup"]
    executor = FakeExecutor()
    app = create_v3_app(
        store=store,
        executor=executor,
        database_info=database_info,
        current_data_root=data_root,
        legacy_data_root=tmp_path / "runtime" / "v2",
        backups_dir=data_root / "backups",
    )
    client = TestClient(app)

    def fail_restore(*_args: Any, **_kwargs: Any) -> dict[str, Any]:
        raise v3_api.RestoreError(
            "restored database failed activation; original database was restored"
        )

    monkeypatch.setattr(v3_api, "restore_v3_backup", fail_restore)
    try:
        response = client.post(
            f"/system/backups/{backup['backup_id']}/restore",
            headers={"Idempotency-Key": "failed-restore-command"},
            json={"expected_database_sha256": backup["database_sha256"]},
        )
        project_names = {item["name"] for item in store.list_projects()}
    finally:
        store.close()

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "restore_failed"
    assert response.json()["error"]["details"] == {
        "original_database_reactivated": True
    }
    assert project_names == {"Original data"}
    assert executor.stop_calls == 1
    assert executor.start_calls == 1
    assert executor.running is True


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
        "/system/backups",
        "/system/backups/{backup_id}/restore",
        "/system/storage/preflight",
        "/projects",
        "/projects/{project_id}/sources/scan",
        "/projects/{project_id}/sources",
        "/projects/{project_id}/documents",
        "/projects/{project_id}/insights/overview",
        "/model-profiles",
        "/model-profiles/{profile_id}/update",
        "/model-profiles/{profile_id}/default",
        "/model-profiles/{profile_id}/delete",
        "/projects/{project_id}/insights/overview",
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
    assert schema["paths"]["/system/storage/preflight"]["post"]["responses"][
        "200"
    ]["content"]["application/json"]["schema"] == {
        "$ref": "#/components/schemas/SuccessEnvelope_StoragePreflightData_"
    }
    assert schema["paths"]["/system/backups"]["post"]["responses"]["201"][
        "content"
    ]["application/json"]["schema"] == {
        "$ref": "#/components/schemas/SuccessEnvelope_BackupMutationData_"
    }
    assert schema["paths"]["/system/backups/{backup_id}/restore"]["post"][
        "responses"
    ]["200"]["content"]["application/json"]["schema"] == {
        "$ref": "#/components/schemas/SuccessEnvelope_RestoreMutationData_"
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
    assert "locator" not in schema["components"]["schemas"]["SourceResource"][
        "properties"
    ]
    assert "content" not in schema["components"]["schemas"]["DocumentResource"][
        "properties"
    ]
    assert schema["paths"]["/projects/{project_id}/insights/overview"]["get"][
        "responses"
    ]["200"]["content"]["application/json"]["schema"] == {
        "$ref": "#/components/schemas/SuccessEnvelope_ProjectInsightData_"
    }
    assert schema["paths"]["/model-profiles"]["post"]["responses"]["201"][
        "content"
    ]["application/json"]["schema"] == {
        "$ref": "#/components/schemas/SuccessEnvelope_ModelProfileMutationData_"
    }
    assert schema["paths"]["/model-profiles/{profile_id}/delete"]["post"][
        "responses"
    ]["200"]["content"]["application/json"]["schema"] == {
        "$ref": "#/components/schemas/SuccessEnvelope_ModelProfileDeleteData_"
    }
    assert schema["paths"]["/projects/{project_id}/insights/overview"]["get"][
        "responses"
    ]["200"]["content"]["application/json"]["schema"] == {
        "$ref": "#/components/schemas/SuccessEnvelope_ProjectInsightData_"
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
