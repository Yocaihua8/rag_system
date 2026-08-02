from __future__ import annotations

from collections import deque
from pathlib import Path
from threading import Lock
from typing import Any

import anyio
import pytest

from backend.config.v3 import V3RuntimeSettings
from backend.runtime.executor import AgentExecutor
from backend.runtime.project_inspector import ProjectInspectionError
from backend.storage.v3.errors import StateConflictError


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


def _settings(tmp_path: Path, *, max_concurrency: int = 2) -> V3RuntimeSettings:
    data_root = tmp_path / "runtime" / "v3"
    return V3RuntimeSettings(
        data_root=data_root,
        db_path=data_root / "app.db",
        vector_dir=data_root / "vectors",
        artifacts_dir=data_root / "artifacts",
        logs_dir=data_root / "logs",
        backups_dir=data_root / "backups",
        max_concurrency=max_concurrency,
        lease_seconds=300,
        poll_interval_ms=10,
    )


def _claim(index: int) -> dict[str, Any]:
    return {
        "run_id": f"run-{index}",
        "task_id": f"task-{index}",
        "project_id": "project-1",
        "step": {
            "id": f"step-{index}",
            "node_type": "trigger.manual",
            "effect_kind": "none",
        },
    }


class FakeStore:
    def __init__(
        self,
        *,
        claims: list[dict[str, Any]] | None = None,
        run_status: str = "running",
    ) -> None:
        self._claims = deque(claims or [])
        self._lock = Lock()
        self.run_status = run_status
        self.events: list[str] = []
        self.complete_calls: list[dict[str, Any]] = []
        self.fail_calls: list[dict[str, Any]] = []
        self.complete_conflict = False
        self.fail_conflict = False

    def recover_expired_runs(self) -> list[dict[str, Any]]:
        self.events.append("recover")
        return []

    def expire_pending_approvals(self) -> list[dict[str, Any]]:
        self.events.append("expire-approvals")
        return []

    def claim_next_run(self, **kwargs: Any) -> dict[str, Any] | None:
        with self._lock:
            self.events.append("claim")
            return self._claims.popleft() if self._claims else None

    def complete_step(self, **kwargs: Any) -> dict[str, Any]:
        self.complete_calls.append(kwargs)
        if self.complete_conflict:
            raise StateConflictError("run was paused or cancelled")
        return {"status": "succeeded"}

    def get_run(self, run_id: str) -> dict[str, Any]:
        return {"id": run_id, "status": self.run_status}

    def fail_run(self, **kwargs: Any) -> dict[str, Any]:
        self.fail_calls.append(kwargs)
        if self.fail_conflict:
            raise StateConflictError("run state changed")
        return {"status": "failed"}

    def heartbeat_run(self, **kwargs: Any) -> dict[str, Any]:
        return {"status": "running"}


@pytest.mark.anyio
async def test_start_recovers_before_workers_and_never_processes_more_than_two(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    store = FakeStore(claims=[_claim(1), _claim(2), _claim(3)])
    executor = AgentExecutor(store, _settings(tmp_path, max_concurrency=2))
    two_started = anyio.Event()
    release = anyio.Event()
    processed: list[str] = []
    active = 0
    max_active = 0

    async def process_claim(worker_id: str, claim: dict[str, Any]) -> None:
        nonlocal active, max_active
        assert store.events[:2] == ["recover", "expire-approvals"]
        processed.append(str(claim["run_id"]))
        active += 1
        max_active = max(max_active, active)
        if active == 2:
            two_started.set()
        try:
            await release.wait()
        finally:
            active -= 1

    monkeypatch.setattr(executor, "_process_claim", process_claim)

    await executor.start()
    with anyio.fail_after(2):
        await two_started.wait()
    with anyio.fail_after(2):
        while store.events.count("expire-approvals") < 2:
            await anyio.sleep(0.01)
    assert executor.running is True
    assert len(processed) == 2
    assert max_active == 2
    assert store.events.count("expire-approvals") >= 2

    release.set()
    with anyio.fail_after(2):
        while len(processed) < 3:
            await anyio.sleep(0.01)

    assert max_active == 2
    await executor.stop()


@pytest.mark.anyio
async def test_stop_cancels_workers_and_clears_task_group_state(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    store = FakeStore()
    executor = AgentExecutor(store, _settings(tmp_path, max_concurrency=2))
    all_started = anyio.Event()
    all_stopped = anyio.Event()
    started = 0
    stopped = 0

    async def blocked_worker(worker_id: str) -> None:
        nonlocal started, stopped
        started += 1
        if started == 2:
            all_started.set()
        try:
            await anyio.sleep_forever()
        finally:
            stopped += 1
            if stopped == 2:
                all_stopped.set()

    monkeypatch.setattr(executor, "_worker_loop", blocked_worker)

    await executor.start()
    with anyio.fail_after(2):
        await all_started.wait()
    await executor.stop()

    with anyio.fail_after(2):
        await all_stopped.wait()
    assert store.events == ["recover", "expire-approvals"]
    assert executor.running is False
    assert executor._task_group is None
    assert executor._task_group_manager is None

    await executor.stop()
    assert stopped == 2


@pytest.mark.anyio
async def test_complete_state_conflict_after_pause_or_cancel_never_calls_fail_run(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    store = FakeStore(run_status="paused")
    store.complete_conflict = True
    executor = AgentExecutor(store, _settings(tmp_path))

    async def execute_step(claim: dict[str, Any]) -> dict[str, Any]:
        return {"prompt": "demo"}

    monkeypatch.setattr(executor, "_execute_step", execute_step)

    await executor._process_claim("worker-1", _claim(1))

    assert len(store.complete_calls) == 1
    assert store.fail_calls == []


@pytest.mark.anyio
@pytest.mark.parametrize("status", ["paused", "cancelled"])
async def test_execution_error_does_not_fail_a_paused_or_cancelled_run(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    status: str,
):
    store = FakeStore(run_status=status)
    executor = AgentExecutor(store, _settings(tmp_path))

    async def execute_step(claim: dict[str, Any]) -> dict[str, Any]:
        raise ProjectInspectionError("inspection cancelled")

    monkeypatch.setattr(executor, "_execute_step", execute_step)

    await executor._process_claim("worker-1", _claim(1))

    assert store.complete_calls == []
    assert store.fail_calls == []


@pytest.mark.anyio
async def test_fail_run_state_conflict_from_concurrent_control_is_swallowed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    store = FakeStore(run_status="running")
    store.fail_conflict = True
    executor = AgentExecutor(store, _settings(tmp_path))

    async def execute_step(claim: dict[str, Any]) -> dict[str, Any]:
        raise OSError("project became unavailable")

    monkeypatch.setattr(executor, "_execute_step", execute_step)

    await executor._process_claim("worker-1", _claim(1))

    assert store.complete_calls == []
    assert len(store.fail_calls) == 1
    assert store.fail_calls[0]["error_code"] == "step_execution_failed"


@pytest.mark.anyio
async def test_artifact_keeps_persisted_workflow_version_for_resumed_v1_run(
    tmp_path: Path,
):
    class ArtifactStore(FakeStore):
        def __init__(self) -> None:
            super().__init__()
            self.artifact_payload: dict[str, Any] | None = None

        def list_run_steps(self, run_id: str) -> list[dict[str, Any]]:
            return [
                {
                    "node_type": "project.analyze",
                    "status": "succeeded",
                    "output": {"inspection": {"total_files": 1}},
                }
            ]

        def create_artifact(self, **kwargs: Any) -> dict[str, Any]:
            self.artifact_payload = kwargs
            return {
                "artifact": {
                    "id": "artifact-v1",
                    "artifact_type": "project_inspection",
                    "status": "ready",
                    "checksum": "artifact-checksum",
                }
            }

    store = ArtifactStore()
    executor = AgentExecutor(store, _settings(tmp_path))
    claim = {
        "run_id": "run-v1",
        "task_id": "task-v1",
        "project_id": "project-v1",
        "run": {"workflow_version": 1},
        "step": {
            "id": "artifact-step-v1",
            "node_type": "artifact.create",
            "effect_kind": "analysis",
        },
    }

    await executor._execute_step(claim)

    assert store.artifact_payload is not None
    assert store.artifact_payload["metadata"]["workflow_version"] == 1
