from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any
from uuid import uuid4

import anyio

from backend.application.agent_service import request_hash
from backend.config.v3 import V3RuntimeSettings
from backend.runtime.project_inspector import ProjectInspectionError, inspect_project
from backend.storage.v3.errors import StateConflictError


logger = logging.getLogger(__name__)


class UnsupportedRuntimeNodeError(RuntimeError):
    pass


class AgentExecutor:
    """Lifespan-owned worker pool for persisted v3 runs."""

    def __init__(self, store: Any, settings: V3RuntimeSettings) -> None:
        self.store = store
        self.settings = settings
        self._running = False
        self._task_group_manager: Any | None = None
        self._task_group: Any | None = None
        self._instance_id = str(uuid4())

    @property
    def running(self) -> bool:
        return self._running

    async def start(self) -> None:
        if self._running:
            return
        await anyio.to_thread.run_sync(self.store.recover_expired_runs)
        manager = anyio.create_task_group()
        task_group = await manager.__aenter__()
        self._task_group_manager = manager
        self._task_group = task_group
        self._running = True
        for index in range(self.settings.max_concurrency):
            task_group.start_soon(
                self._worker_loop,
                f"{self._instance_id}:{index + 1}",
            )

    async def stop(self) -> None:
        if not self._running:
            return
        self._running = False
        manager = self._task_group_manager
        task_group = self._task_group
        self._task_group_manager = None
        self._task_group = None
        if task_group is not None:
            task_group.cancel_scope.cancel()
        if manager is not None:
            await manager.__aexit__(None, None, None)

    async def _worker_loop(self, worker_id: str) -> None:
        while self._running:
            try:
                claim = await anyio.to_thread.run_sync(
                    lambda: self.store.claim_next_run(
                        worker_id=worker_id,
                        lease_seconds=self.settings.lease_seconds,
                    )
                )
                if claim is None:
                    await anyio.sleep(self.settings.poll_interval_ms / 1000)
                    continue
                await self._process_claim(worker_id, claim)
            except anyio.get_cancelled_exc_class():
                raise
            except Exception:
                logger.exception("v3 executor worker loop failed")
                await anyio.sleep(self.settings.poll_interval_ms / 1000)

    async def _process_claim(
        self,
        worker_id: str,
        claim: dict[str, Any],
    ) -> None:
        run_id = str(claim["run_id"])
        step = dict(claim["step"])
        step_id = str(step["id"])
        done = anyio.Event()
        execution_error: Exception | None = None
        try:
            async with anyio.create_task_group() as task_group:
                task_group.start_soon(
                    self._heartbeat_loop,
                    done,
                    run_id,
                    worker_id,
                )
                try:
                    output = await self._execute_step(claim)
                except anyio.get_cancelled_exc_class():
                    raise
                except Exception as exc:
                    execution_error = exc
                    output = {}
                finally:
                    done.set()
            if execution_error is not None:
                raise execution_error
            await anyio.to_thread.run_sync(
                lambda: self.store.complete_step(
                    run_id=run_id,
                    step_id=step_id,
                    worker_id=worker_id,
                    output=output,
                )
            )
        except anyio.get_cancelled_exc_class():
            done.set()
            raise
        except (ProjectInspectionError, UnsupportedRuntimeNodeError, OSError) as exc:
            done.set()
            current = await anyio.to_thread.run_sync(
                lambda: self.store.get_run(run_id)
            )
            if current is None or str(current["status"]) in {
                "paused",
                "cancelled",
                "recovering",
            }:
                return
            retryable = str(step.get("effect_kind")) in {"read", "analysis"}
            try:
                await anyio.to_thread.run_sync(
                    lambda: self.store.fail_run(
                        run_id=run_id,
                        worker_id=worker_id,
                        error_code="step_execution_failed",
                        error_message=str(exc),
                        retryable=retryable,
                    )
                )
            except StateConflictError:
                return
        except Exception:
            done.set()
            logger.exception("unexpected v3 step execution failure")
            current = await anyio.to_thread.run_sync(
                lambda: self.store.get_run(run_id)
            )
            if current is None or str(current["status"]) in {
                "paused",
                "cancelled",
                "recovering",
            }:
                return
            retryable = str(step.get("effect_kind")) in {"none", "read", "analysis"}
            try:
                await anyio.to_thread.run_sync(
                    lambda: self.store.fail_run(
                        run_id=run_id,
                        worker_id=worker_id,
                        error_code="unexpected_executor_error",
                        error_message="unexpected executor error",
                        retryable=retryable,
                    )
                )
            except StateConflictError:
                return

    async def _heartbeat_loop(
        self,
        done: anyio.Event,
        run_id: str,
        worker_id: str,
    ) -> None:
        interval = max(1.0, self.settings.lease_seconds / 3)
        while not done.is_set():
            with anyio.move_on_after(interval):
                await done.wait()
            if done.is_set():
                return
            try:
                await anyio.to_thread.run_sync(
                    lambda: self.store.heartbeat_run(
                        run_id=run_id,
                        worker_id=worker_id,
                        lease_seconds=self.settings.lease_seconds,
                    )
                )
            except StateConflictError:
                return
            except Exception:
                logger.exception("v3 executor heartbeat failed")
                return

    async def _execute_step(self, claim: dict[str, Any]) -> dict[str, Any]:
        step = dict(claim["step"])
        node_type = str(step["node_type"])
        if node_type == "trigger.manual":
            task = await anyio.to_thread.run_sync(
                lambda: self.store.get_task(str(claim["task_id"]))
            )
            if task is None:
                raise ProjectInspectionError("task disappeared before execution")
            return {"prompt": str(task["prompt"]), "trigger": "manual"}

        if node_type == "project.analyze":
            project = await anyio.to_thread.run_sync(
                lambda: self.store.get_project(str(claim["project_id"]))
            )
            if project is None:
                raise ProjectInspectionError("project disappeared before inspection")
            run_id = str(claim["run_id"])

            def cancellation_requested() -> bool:
                current = self.store.get_run(run_id)
                return current is None or str(current["status"]) != "running"

            result = await anyio.to_thread.run_sync(
                lambda: inspect_project(
                    Path(str(project["root_path"])),
                    cancellation_requested=cancellation_requested,
                )
            )
            return {"inspection": result}

        if node_type == "artifact.create":
            steps = await anyio.to_thread.run_sync(
                lambda: self.store.list_run_steps(str(claim["run_id"]))
            )
            inspection_step = next(
                (
                    item
                    for item in steps
                    if item["node_type"] == "project.analyze"
                    and item["status"] == "succeeded"
                ),
                None,
            )
            if inspection_step is None:
                raise ProjectInspectionError("project inspection output is unavailable")
            inspection = dict(inspection_step.get("output") or {}).get(
                "inspection", {}
            )
            content = json.dumps(
                inspection,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            )
            artifact_payload = {
                "task_id": str(claim["task_id"]),
                "run_id": str(claim["run_id"]),
                "step_id": str(step["id"]),
                "kind": "project_inspection",
                "title": "Project structure inspection",
                "content": content,
                "metadata": {"source": "project.inspect.v1", "content_type": "json"},
                "status": "ready",
            }
            artifact_result = await anyio.to_thread.run_sync(
                lambda: self.store.create_artifact(
                    **artifact_payload,
                    idempotency_key=f"executor:{claim['run_id']}:{step['id']}",
                    request_hash=request_hash(artifact_payload),
                )
            )
            artifact = dict(artifact_result["artifact"])
            return {
                "artifact_id": artifact["id"],
                "artifact_type": artifact["artifact_type"],
                "status": artifact["status"],
                "checksum": artifact["checksum"],
            }

        raise UnsupportedRuntimeNodeError(
            f"runtime node is not executable: {node_type}"
        )


__all__ = ["AgentExecutor", "UnsupportedRuntimeNodeError"]
