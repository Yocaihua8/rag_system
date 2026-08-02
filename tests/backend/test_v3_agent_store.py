from __future__ import annotations

import hashlib
import sqlite3
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from threading import Barrier

import pytest
from sqlalchemy import inspect

from backend.storage.v3 import (
    AgentStore,
    IdempotencyConflictError,
    StateConflictError,
    V3DataGenerationMismatchError,
)
from backend.storage.v3.schema import ALL_TABLES


@pytest.fixture
def store(tmp_path):
    instance = AgentStore(tmp_path / "runtime" / "v3" / "app.db")
    instance.initialize()
    try:
        yield instance
    finally:
        instance.close()


def _create_project_task(store: AgentStore, suffix: str = "one") -> tuple[str, str]:
    project_response = store.create_project(
        name=f"Project {suffix}",
        root_path=store.db_path.parent / f"workspace-{suffix}",
        idempotency_key=f"project-{suffix}",
        request_hash=f"project-hash-{suffix}",
    )
    project_id = project_response["project"]["id"]
    task_response = store.create_task(
        project_id=project_id,
        title=f"Inspect {suffix}",
        prompt="Inspect this project",
        depth="standard",
        idempotency_key=f"task-{suffix}",
        request_hash=f"task-hash-{suffix}",
    )
    return project_id, task_response["task"]["id"]


def _create_run(
    store: AgentStore,
    task_id: str,
    suffix: str,
    *,
    effect_kind: str = "read",
    step_count: int = 1,
) -> dict:
    steps = [
        {
            "step_key": f"step-{index}",
            "node_type": "project.inspect",
            "effect_kind": effect_kind if index == 0 else "analysis",
            "input": {"index": index},
        }
        for index in range(step_count)
    ]
    return store.create_run_with_steps(
        task_id=task_id,
        workflow_key="project.inspect",
        workflow_version=1,
        workflow_checksum=f"checksum-{suffix}",
        depth="standard",
        steps=steps,
        idempotency_key=f"run-{suffix}",
        request_hash=f"run-hash-{suffix}",
    )


def test_initialize_runs_alembic_and_enables_sqlite_safety_pragmas(tmp_path):
    store = AgentStore(tmp_path / "runtime" / "v3" / "app.db")

    info = store.initialize()
    table_names = set(inspect(store._database.engine).get_table_names())
    store.close()

    assert info["data_generation"] == "v3"
    assert info["schema_version"] == "0001_v3_initial"
    assert info["alembic_revision"] == info["alembic_head"] == "0001_v3_initial"
    assert info["journal_mode"] == "wal"
    assert info["foreign_keys"] == 1
    assert info["busy_timeout_ms"] == 30_000
    assert set(ALL_TABLES).issubset(table_names)
    assert "alembic_version" in table_names


def test_initialize_refuses_unmarked_existing_database_without_mutating_it(tmp_path):
    db_path = tmp_path / "legacy.db"
    with sqlite3.connect(db_path) as connection:
        connection.execute("CREATE TABLE legacy_items (id INTEGER PRIMARY KEY)")
        connection.execute("INSERT INTO legacy_items (id) VALUES (1)")
    before = hashlib.sha256(db_path.read_bytes()).hexdigest()

    with pytest.raises(V3DataGenerationMismatchError, match="unmarked"):
        AgentStore(db_path).initialize()

    assert hashlib.sha256(db_path.read_bytes()).hexdigest() == before
    with sqlite3.connect(db_path) as connection:
        assert connection.execute("SELECT id FROM legacy_items").fetchall() == [(1,)]
        assert connection.execute(
            "SELECT COUNT(*) FROM sqlite_master WHERE name = 'app_metadata'"
        ).fetchone() == (0,)


def test_project_task_and_run_creation_are_idempotent(store):
    root_path = store.db_path.parent / "workspace"
    first = store.create_project(
        name="Demo",
        root_path=root_path,
        idempotency_key="project-key",
        request_hash="same-request",
    )
    replay = store.create_project(
        name="Demo",
        root_path=root_path,
        idempotency_key="project-key",
        request_hash="same-request",
    )

    assert first["replayed"] is False
    assert replay["replayed"] is True
    assert replay["project"]["id"] == first["project"]["id"]
    with pytest.raises(IdempotencyConflictError):
        store.create_project(
            name="Changed",
            root_path=root_path,
            idempotency_key="project-key",
            request_hash="different-request",
        )

    project_id, task_id = _create_project_task(store, "idempotent")
    run = _create_run(store, task_id, "idempotent", step_count=2)
    replayed_run = _create_run(store, task_id, "idempotent", step_count=2)

    assert store.get_project(project_id)["id"] == project_id
    assert store.get_task(task_id)["status"] == "queued"
    assert replayed_run["replayed"] is True
    assert replayed_run["run"]["id"] == run["run"]["id"]
    assert [event["event_type"] for event in store.list_events(run["run"]["id"])] == [
        "run.queued"
    ]


def test_claim_complete_steps_and_create_artifact(store):
    project_id, task_id = _create_project_task(store, "complete")
    created = _create_run(store, task_id, "complete", step_count=2)
    run_id = created["run"]["id"]

    first_claim = store.claim_next_run(worker_id="worker-1", lease_seconds=30)
    first_completion = store.complete_step(
        run_id=run_id,
        step_id=first_claim["step"]["id"],
        worker_id="worker-1",
        output={"files": 3},
    )
    second_claim = store.claim_next_run(worker_id="worker-1", lease_seconds=30)
    final_completion = store.complete_step(
        run_id=run_id,
        step_id=second_claim["step"]["id"],
        worker_id="worker-1",
        output={"summary": "ready"},
    )
    artifact = store.create_artifact(
        task_id=task_id,
        run_id=run_id,
        kind="project_report",
        title="Inspection report",
        content="# Result\nready",
        metadata={"format": "markdown"},
        status="ready",
        idempotency_key="artifact-complete",
        request_hash="artifact-hash-complete",
    )

    assert first_claim["project_id"] == project_id
    assert first_completion["run"]["status"] == "queued"
    assert first_completion["next_step"]["status"] == "queued"
    assert final_completion["run"]["status"] == "completed"
    assert store.get_task(task_id)["status"] == "completed"
    assert artifact["artifact"]["content"] == "# Result\nready"
    assert artifact["artifact"]["metadata"] == {"format": "markdown"}
    assert store.list_artifacts(run_id=run_id)[0]["id"] == artifact["artifact"]["id"]
    sequences = [event["sequence"] for event in store.list_events(run_id)]
    assert sequences == list(range(1, len(sequences) + 1))


def test_event_payloads_redact_nested_secrets(store):
    _, task_id = _create_project_task(store, "events")
    run_id = _create_run(store, task_id, "events")["run"]["id"]

    event = store.append_event(
        run_id=run_id,
        event_type="tool.output",
        payload={
            "api_key": "secret-a",
            "nested": {"access_token": "secret-b", "safe": "visible"},
        },
    )

    assert event["payload"] == {
        "api_key": "[REDACTED]",
        "nested": {"access_token": "[REDACTED]", "safe": "visible"},
    }


def test_expired_read_is_requeued_but_write_requires_manual_recovery(store):
    start = datetime(2026, 8, 2, 1, 0, tzinfo=timezone.utc)
    expired = start + timedelta(seconds=6)
    _, read_task = _create_project_task(store, "recover-read")
    read_run = _create_run(store, read_task, "recover-read", effect_kind="read")
    store.claim_next_run(worker_id="worker-read", lease_seconds=5, now=start)

    recovered_read = store.recover_expired_runs(now=expired)

    assert recovered_read[0]["run_id"] == read_run["run"]["id"]
    assert recovered_read[0]["status"] == "queued"
    assert store.get_task(read_task)["status"] == "queued"
    assert store.list_run_steps(read_run["run"]["id"])[0]["status"] == "queued"
    store.cancel_run(
        run_id=read_run["run"]["id"],
        idempotency_key="cancel-recovered-read",
        request_hash="cancel-recovered-read-hash",
    )

    _, write_task = _create_project_task(store, "recover-write")
    write_run = _create_run(
        store, write_task, "recover-write", effect_kind="project_write"
    )
    store.claim_next_run(worker_id="worker-write", lease_seconds=5, now=start)

    recovered_write = store.recover_expired_runs(now=expired)

    assert recovered_write[0]["run_id"] == write_run["run"]["id"]
    assert recovered_write[0]["status"] == "recovering"
    assert store.get_task(write_task)["status"] == "paused"
    assert store.list_run_steps(write_run["run"]["id"])[0]["status"] == "recovery_required"


def test_approval_resolution_checks_snapshot_and_requeues_approved_step(store):
    _, task_id = _create_project_task(store, "approval")
    run_id = _create_run(
        store, task_id, "approval", effect_kind="external_write"
    )["run"]["id"]
    claim = store.claim_next_run(worker_id="worker-approval", lease_seconds=30)
    requested = store.request_approval(
        task_id=task_id,
        run_id=run_id,
        step_id=claim["step"]["id"],
        action_type="github.create_issue",
        target="owner/repo",
        payload={"title": "Draft"},
        request_hash="snapshot-hash",
        resource_version="etag-1",
        idempotency_key="approval-request",
        idempotency_request_hash="approval-request-hash",
    )
    approval = requested["approval"]

    with pytest.raises(StateConflictError, match="request hash"):
        store.resolve_approval(
            approval_id=approval["id"],
            decision="approved",
            decided_by="user",
            expected_request_hash="changed-hash",
            expected_version=approval["version"],
            idempotency_key="approval-resolution-bad",
            request_hash="approval-resolution-bad-hash",
        )

    resolved = store.resolve_approval(
        approval_id=approval["id"],
        decision="approved",
        decided_by="user",
        expected_request_hash="snapshot-hash",
        expected_version=approval["version"],
        decision_note="Reviewed",
        idempotency_key="approval-resolution",
        request_hash="approval-resolution-hash",
    )

    assert resolved["approval"]["status"] == "approved"
    assert store.get_run(run_id)["status"] == "queued"
    assert store.get_task(task_id)["status"] == "queued"
    assert store.list_run_steps(run_id)[0]["status"] == "queued"


def test_run_controls_enforce_expected_version_and_idempotency(store):
    _, task_id = _create_project_task(store, "controls")
    run_id = _create_run(store, task_id, "controls")["run"]["id"]
    version = store.get_run(run_id)["version"]

    with pytest.raises(StateConflictError, match="version"):
        store.pause_run(
            run_id=run_id,
            expected_version=version + 1,
            idempotency_key="pause-bad",
            request_hash="pause-bad-hash",
        )

    paused = store.pause_run(
        run_id=run_id,
        expected_version=version,
        idempotency_key="pause",
        request_hash="pause-hash",
    )
    replay = store.pause_run(
        run_id=run_id,
        expected_version=version,
        idempotency_key="pause",
        request_hash="pause-hash",
    )
    resumed = store.resume_run(
        run_id=run_id,
        expected_version=paused["run"]["version"],
        idempotency_key="resume",
        request_hash="resume-hash",
    )

    assert paused["run"]["status"] == "paused"
    assert replay["replayed"] is True
    assert resumed["run"]["status"] == "queued"


def test_safe_failure_retries_in_place_and_manual_retry_creates_new_run(store):
    _, task_id = _create_project_task(store, "retry-read")
    original_id = _create_run(store, task_id, "retry-read")["run"]["id"]
    claim = store.claim_next_run(worker_id="worker-retry", lease_seconds=30)

    scheduled = store.fail_run(
        run_id=original_id,
        worker_id="worker-retry",
        error_code="temporary_read_error",
        error_message="try again",
        retryable=True,
    )

    assert scheduled["retry_scheduled"] is True
    assert scheduled["run"]["status"] == "queued"
    assert scheduled["event"]["event_type"] == "step.retry_scheduled"
    assert store.list_run_steps(original_id)[0]["attempt_count"] == 1

    second_claim = store.claim_next_run(worker_id="worker-retry", lease_seconds=30)
    failed = store.fail_run(
        run_id=original_id,
        worker_id="worker-retry",
        error_code="permanent_read_error",
        error_message="stop",
        retryable=False,
    )
    retried = store.retry_run(
        run_id=original_id,
        expected_version=failed["run"]["version"],
        idempotency_key="manual-retry",
        request_hash="manual-retry-hash",
    )
    replay = store.retry_run(
        run_id=original_id,
        expected_version=failed["run"]["version"],
        idempotency_key="manual-retry",
        request_hash="manual-retry-hash",
    )

    assert second_claim["step"]["attempt_count"] == 2
    assert failed["retry_scheduled"] is False
    assert failed["run"]["status"] == "failed"
    assert retried["run"]["id"] != original_id
    assert retried["run"]["retry_of_run_id"] == original_id
    assert retried["run"]["attempt_no"] == 2
    assert replay["replayed"] is True
    store.cancel_run(
        run_id=retried["run"]["id"],
        idempotency_key="cancel-manual-retry",
        request_hash="cancel-manual-retry-hash",
    )

    _, write_task_id = _create_project_task(store, "retry-write")
    write_run_id = _create_run(
        store, write_task_id, "retry-write", effect_kind="external_write"
    )["run"]["id"]
    store.claim_next_run(worker_id="worker-write-retry", lease_seconds=30)
    write_failure = store.fail_run(
        run_id=write_run_id,
        worker_id="worker-write-retry",
        error_code="external_uncertain",
        error_message="write outcome is unknown",
        retryable=True,
    )

    assert write_failure["retry_scheduled"] is False
    assert write_failure["run"]["status"] == "failed"


def test_claim_serializes_write_steps_per_project_but_not_across_projects(store):
    project_id, first_task_id = _create_project_task(store, "write-project")
    second_task = store.create_task(
        project_id=project_id,
        title="Second write",
        prompt="Write another artifact",
        depth="standard",
        idempotency_key="task-write-project-second",
        request_hash="task-write-project-second-hash",
    )["task"]
    read_task = store.create_task(
        project_id=project_id,
        title="Read while writing",
        prompt="Read without mutating the project",
        depth="standard",
        idempotency_key="task-write-project-read",
        request_hash="task-write-project-read-hash",
    )["task"]
    other_project_id, other_task_id = _create_project_task(store, "other-write")

    def create_run(
        task_id: str,
        suffix: str,
        priority: int,
        *,
        effect_kind: str = "project_write",
    ) -> dict:
        return store.create_run_with_steps(
            task_id=task_id,
            workflow_key="write.test",
            workflow_version=1,
            workflow_checksum=f"write-checksum-{suffix}",
            depth="standard",
            steps=[
                {
                    "step_key": "write",
                    "node_type": "artifact.export",
                    "effect_kind": effect_kind,
                    "input": {},
                    "max_attempts": 1,
                }
            ],
            priority=priority,
            idempotency_key=f"write-run-{suffix}",
            request_hash=f"write-run-{suffix}-hash",
        )

    first = create_run(first_task_id, "first", 30)
    second = create_run(
        second_task["id"],
        "second",
        20,
        effect_kind="external_write",
    )
    read = create_run(read_task["id"], "read", 15, effect_kind="read")
    other = create_run(other_task_id, "other", 10)

    first_claim = store.claim_next_run(worker_id="write-worker-1", lease_seconds=30)
    read_claim = store.claim_next_run(worker_id="read-worker", lease_seconds=30)
    other_claim = store.claim_next_run(worker_id="write-worker-2", lease_seconds=30)
    blocked = store.claim_next_run(worker_id="write-worker-3", lease_seconds=30)

    assert first_claim["run_id"] == first["run"]["id"]
    assert first_claim["project_id"] == project_id
    assert read_claim["run_id"] == read["run"]["id"]
    assert read_claim["project_id"] == project_id
    assert other_claim["run_id"] == other["run"]["id"]
    assert other_claim["project_id"] == other_project_id
    assert blocked is None

    store.complete_step(
        run_id=first_claim["run_id"],
        step_id=first_claim["step"]["id"],
        worker_id="write-worker-1",
        output={"written": True},
    )
    second_claim = store.claim_next_run(
        worker_id="write-worker-3",
        lease_seconds=30,
    )

    assert second_claim["run_id"] == second["run"]["id"]


def test_recovery_required_write_keeps_project_write_slot_locked(store):
    project_id, first_task_id = _create_project_task(store, "recovery-write-lock")
    second_task = store.create_task(
        project_id=project_id,
        title="Second write after recovery",
        prompt="Write only after recovery is resolved",
        depth="standard",
        idempotency_key="task-recovery-write-lock-second",
        request_hash="task-recovery-write-lock-second-hash",
    )["task"]
    first = _create_run(
        store,
        first_task_id,
        "recovery-write-lock-first",
        effect_kind="project_write",
    )
    _create_run(
        store,
        second_task["id"],
        "recovery-write-lock-second",
        effect_kind="external_write",
    )
    started_at = datetime(2026, 8, 2, 1, 0, tzinfo=timezone.utc)

    first_claim = store.claim_next_run(
        worker_id="recovery-write-worker",
        lease_seconds=5,
        now=started_at,
    )
    recovered = store.recover_expired_runs(now=started_at + timedelta(seconds=6))

    assert first_claim["run_id"] == first["run"]["id"]
    assert recovered[0]["status"] == "recovering"
    assert recovered[0]["step_status"] == "recovery_required"
    assert store.claim_next_run(
        worker_id="blocked-by-recovery-worker",
        lease_seconds=30,
    ) is None


def test_concurrent_claims_cannot_start_two_writes_for_the_same_project(store):
    project_id, first_task_id = _create_project_task(store, "concurrent-write")
    second_task = store.create_task(
        project_id=project_id,
        title="Concurrent second write",
        prompt="Must remain queued",
        depth="standard",
        idempotency_key="task-concurrent-write-second",
        request_hash="task-concurrent-write-second-hash",
    )["task"]
    _create_run(
        store,
        first_task_id,
        "concurrent-write-first",
        effect_kind="project_write",
    )
    _create_run(
        store,
        second_task["id"],
        "concurrent-write-second",
        effect_kind="external_write",
    )
    worker_stores = [AgentStore(store.db_path), AgentStore(store.db_path)]
    for worker_store in worker_stores:
        worker_store.initialize()
    start = Barrier(2)

    def claim(index: int):
        start.wait()
        return worker_stores[index].claim_next_run(
            worker_id=f"concurrent-worker-{index}",
            lease_seconds=30,
        )

    try:
        with ThreadPoolExecutor(max_workers=2) as executor:
            results = list(executor.map(claim, range(2)))
    finally:
        for worker_store in worker_stores:
            worker_store.close()

    claimed = [result for result in results if result is not None]
    assert len(claimed) == 1
    assert claimed[0]["project_id"] == project_id


def test_workflow_drafts_publish_immutably_and_bind_with_optimistic_version(store):
    project_id, _ = _create_project_task(store, "workflow")
    created = store.create_workflow(
        workflow_key="inspect.custom",
        name="Custom inspection",
        description="Test workflow",
        dag={"nodes": [{"id": "trigger", "type": "trigger.manual"}], "edges": []},
        input_schema={"type": "object"},
        idempotency_key="workflow-create",
        request_hash="workflow-create-hash",
    )
    workflow = created["workflow"]
    draft = created["version"]

    assert draft["status"] == "draft"
    assert store.create_workflow(
        workflow_key="inspect.custom",
        name="Custom inspection",
        description="Test workflow",
        dag={"nodes": [{"id": "trigger", "type": "trigger.manual"}], "edges": []},
        input_schema={"type": "object"},
        idempotency_key="workflow-create",
        request_hash="workflow-create-hash",
    )["replayed"] is True
    with pytest.raises(StateConflictError, match="checksum"):
        store.publish_workflow_version(
            workflow_id=workflow["id"],
            version_id=draft["id"],
            expected_checksum="changed",
            expected_version=workflow["version"],
            idempotency_key="publish-bad",
            request_hash="publish-bad-hash",
        )

    published = store.publish_workflow_version(
        workflow_id=workflow["id"],
        version_id=draft["id"],
        expected_checksum=draft["checksum"],
        expected_version=workflow["version"],
        idempotency_key="publish-v1",
        request_hash="publish-v1-hash",
    )

    assert published["version"]["status"] == "published"
    assert published["workflow"]["current_published_version_id"] == draft["id"]
    with pytest.raises(StateConflictError, match="only draft"):
        store.publish_workflow_version(
            workflow_id=workflow["id"],
            version_id=draft["id"],
            expected_checksum=draft["checksum"],
            expected_version=published["workflow"]["version"],
            idempotency_key="publish-again",
            request_hash="publish-again-hash",
        )

    bound = store.bind_workflow(
        project_id=project_id,
        workflow_id=workflow["id"],
        workflow_version_id=draft["id"],
        parameters={"depth": "standard"},
        expected_workflow_version=published["workflow"]["version"],
        idempotency_key="bind-v1",
        request_hash="bind-v1-hash",
    )

    assert bound["binding"]["enabled"] is True
    assert bound["binding"]["parameters"] == {"depth": "standard"}
    assert bound["binding"]["version"] == 1

    next_draft = store.create_workflow_version(
        workflow_id=workflow["id"],
        dag={"nodes": [{"id": "trigger", "type": "trigger.manual"}], "edges": [], "revision": 2},
        input_schema={"type": "object"},
        expected_version=published["workflow"]["version"],
        idempotency_key="draft-v2",
        request_hash="draft-v2-hash",
    )
    next_published = store.publish_workflow_version(
        workflow_id=workflow["id"],
        version_id=next_draft["version"]["id"],
        expected_checksum=next_draft["version"]["checksum"],
        expected_version=next_draft["workflow"]["version"],
        idempotency_key="publish-v2",
        request_hash="publish-v2-hash",
    )
    rebound = store.bind_workflow(
        project_id=project_id,
        workflow_id=workflow["id"],
        workflow_version_id=next_draft["version"]["id"],
        parameters={"depth": "deep"},
        expected_version=bound["binding"]["version"],
        expected_workflow_version=next_published["workflow"]["version"],
        idempotency_key="bind-v2",
        request_hash="bind-v2-hash",
    )

    assert rebound["binding"]["workflow_version_id"] == next_draft["version"]["id"]
    assert rebound["binding"]["version"] == 2
    assert [item["version_number"] for item in store.list_workflow_versions(workflow["id"])] == [2, 1]
    assert len(store.list_workflow_bindings(project_id=project_id, enabled=True)) == 1

    archived = store.archive_workflow(
        workflow_id=workflow["id"],
        expected_version=next_published["workflow"]["version"],
        idempotency_key="archive-workflow",
        request_hash="archive-workflow-hash",
    )
    archive_replay = store.archive_workflow(
        workflow_id=workflow["id"],
        expected_version=next_published["workflow"]["version"],
        idempotency_key="archive-workflow",
        request_hash="archive-workflow-hash",
    )

    assert archived["workflow"]["status"] == "archived"
    assert archive_replay["replayed"] is True
    assert len(store.list_workflow_versions(workflow["id"])) == 2
    assert len(store.list_workflow_bindings(project_id=project_id)) == 1
    with pytest.raises(StateConflictError, match="archived"):
        store.create_workflow_version(
            workflow_id=workflow["id"],
            dag={"nodes": [], "edges": []},
            expected_version=archived["workflow"]["version"],
            idempotency_key="draft-archived",
            request_hash="draft-archived-hash",
        )
    with pytest.raises(StateConflictError, match="archived"):
        store.bind_workflow(
            project_id=project_id,
            workflow_id=workflow["id"],
            workflow_version_id=next_draft["version"]["id"],
            expected_version=rebound["binding"]["version"],
            expected_workflow_version=archived["workflow"]["version"],
            idempotency_key="bind-archived",
            request_hash="bind-archived-hash",
        )
