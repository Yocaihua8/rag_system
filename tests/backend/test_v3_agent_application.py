from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from backend.application.agent_service import (
    PROJECT_INSPECT_STEPS,
    PROJECT_INSPECT_WORKFLOW_CHECKSUM,
    PROJECT_INSPECT_WORKFLOW_KEY,
    PROJECT_INSPECT_WORKFLOW_VERSION,
    AgentApplication,
    ApplicationValidationError,
    request_hash,
)


class FakeStore:
    def __init__(self) -> None:
        self.calls: list[tuple[str, dict[str, Any]]] = []

    def create_project(self, **kwargs: Any) -> dict[str, Any]:
        self.calls.append(("create_project", kwargs))
        return {"project": kwargs, "replayed": False}

    def create_task(self, **kwargs: Any) -> dict[str, Any]:
        self.calls.append(("create_task", kwargs))
        return {"task": kwargs, "initial_message": kwargs, "replayed": False}

    def add_task_message(self, **kwargs: Any) -> dict[str, Any]:
        self.calls.append(("add_task_message", kwargs))
        return {"message": kwargs, "replayed": False}

    def create_run_with_steps(self, **kwargs: Any) -> dict[str, Any]:
        self.calls.append(("create_run_with_steps", kwargs))
        return {"run": kwargs, "steps": kwargs["steps"], "replayed": False}


def test_create_project_requires_an_existing_directory_and_resolves_root(
    tmp_path: Path,
):
    store = FakeStore()
    application = AgentApplication(store)
    project_root = tmp_path / "project"
    project_root.mkdir()

    result = application.create_project(
        name=" Demo project ",
        root_path=str(project_root / ".." / "project"),
        idempotency_key=" project-command-1 ",
    )

    method, call = store.calls[-1]
    assert method == "create_project"
    assert call["name"] == " Demo project "
    assert call["root_path"] == str(project_root.resolve())
    assert call["idempotency_key"] == "project-command-1"
    assert call["request_hash"] == request_hash(
        {"name": " Demo project ", "root_path": str(project_root.resolve())}
    )
    assert result["replayed"] is False


def test_create_project_rejects_missing_or_file_root_without_calling_store(
    tmp_path: Path,
):
    store = FakeStore()
    application = AgentApplication(store)
    regular_file = tmp_path / "not-a-project.txt"
    regular_file.write_text("demo", encoding="utf-8")

    with pytest.raises(
        ApplicationValidationError,
        match="project root must be an existing directory",
    ):
        application.create_project(
            name="Missing",
            root_path=str(tmp_path / "missing"),
            idempotency_key="missing-root",
        )

    with pytest.raises(
        ApplicationValidationError,
        match="project root must be an existing directory",
    ):
        application.create_project(
            name="File",
            root_path=str(regular_file),
            idempotency_key="file-root",
        )

    assert store.calls == []


def test_request_hash_is_canonical_and_excludes_idempotency_key():
    store = FakeStore()
    application = AgentApplication(store)

    application.create_task(
        project_id="project-1",
        title="Inspect",
        message="Inspect this project",
        idempotency_key=" command-a ",
    )
    application.create_task(
        project_id="project-1",
        title="Inspect",
        message="Inspect this project",
        idempotency_key="command-b",
    )
    application.create_task(
        project_id="project-1",
        title="Inspect",
        message="Inspect a different project state",
        idempotency_key="command-c",
    )

    calls = [call for method, call in store.calls if method == "create_task"]
    assert calls[0]["idempotency_key"] == "command-a"
    assert calls[0]["request_hash"] == calls[1]["request_hash"]
    assert calls[0]["request_hash"] != calls[2]["request_hash"]
    assert request_hash({"b": 2, "a": 1}) == request_hash({"a": 1, "b": 2})


def test_missing_or_oversized_idempotency_key_is_rejected_before_store_call():
    store = FakeStore()
    application = AgentApplication(store)

    with pytest.raises(
        ApplicationValidationError,
        match="Idempotency-Key header is required",
    ):
        application.create_task(
            project_id="project-1",
            title="Inspect",
            message="Inspect",
            idempotency_key="   ",
        )

    with pytest.raises(
        ApplicationValidationError,
        match="must not exceed 200 characters",
    ):
        application.create_task(
            project_id="project-1",
            title="Inspect",
            message="Inspect",
            idempotency_key="x" * 201,
        )

    assert store.calls == []


def test_project_inspect_run_uses_fixed_version_checksum_and_steps():
    store = FakeStore()
    application = AgentApplication(store)

    application.create_run(
        task_id="task-1",
        input_message_id="message-1",
        workflow_key=PROJECT_INSPECT_WORKFLOW_KEY,
        depth="standard",
        idempotency_key="run-command-1",
    )
    application.create_run(
        task_id="task-1",
        input_message_id="message-1",
        workflow_key=PROJECT_INSPECT_WORKFLOW_KEY,
        depth="standard",
        idempotency_key="run-command-2",
    )

    calls = [
        call for method, call in store.calls if method == "create_run_with_steps"
    ]
    assert len(calls) == 2
    first = calls[0]
    assert first["workflow_key"] == "project.inspect.v1"
    assert first["workflow_version"] == PROJECT_INSPECT_WORKFLOW_VERSION == 2
    assert first["workflow_checksum"] == PROJECT_INSPECT_WORKFLOW_CHECKSUM
    assert first["steps"] == list(PROJECT_INSPECT_STEPS)
    assert [step["step_key"] for step in first["steps"]] == [
        "trigger",
        "inspect",
        "artifact",
        "respond",
    ]
    assert [step["status"] for step in first["steps"]] == [
        "queued",
        "pending",
        "pending",
        "pending",
    ]
    assert first["request_hash"] == calls[1]["request_hash"]
    expected_payload = {
        "task_id": "task-1",
        "input_message_id": "message-1",
        "workflow_key": PROJECT_INSPECT_WORKFLOW_KEY,
        "workflow_version": PROJECT_INSPECT_WORKFLOW_VERSION,
        "workflow_checksum": PROJECT_INSPECT_WORKFLOW_CHECKSUM,
        "depth": "standard",
        "steps": list(PROJECT_INSPECT_STEPS),
    }
    assert first["request_hash"] == request_hash(expected_payload)


def test_create_run_rejects_non_executable_workflow_before_store_call():
    store = FakeStore()
    application = AgentApplication(store)

    with pytest.raises(
        ApplicationValidationError,
        match="workflow is not executable in this slice",
    ):
        application.create_run(
            task_id="task-1",
            input_message_id="message-1",
            workflow_key="custom.workflow.v1",
            depth="standard",
            idempotency_key="run-command",
        )

    assert store.calls == []
