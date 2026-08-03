from __future__ import annotations

import hashlib
import json
import mimetypes
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from backend.domain.agent_runtime import DepthProfile, get_depth_limits
from backend.domain.import_rules import (
    IGNORED_DIR_NAMES,
    MAX_TEXT_FILE_BYTES,
    is_supported_text_path,
)
from backend.domain.workflow_registry import (
    WorkflowDefinition,
    WorkflowEdge,
    WorkflowNode,
    validate_workflow,
)
from backend.storage.v3.errors import RecordNotFoundError


PROJECT_INSPECT_WORKFLOW_KEY = "project.inspect.v1"
PROJECT_INSPECT_WORKFLOW_VERSION = 2
PROJECT_INSPECT_STEPS: tuple[dict[str, Any], ...] = (
    {
        "step_key": "trigger",
        "node_type": "trigger.manual",
        "effect_kind": "none",
        "ordinal": 0,
        "status": "queued",
        "input": {},
        "max_attempts": 1,
    },
    {
        "step_key": "inspect",
        "node_type": "project.analyze",
        "effect_kind": "analysis",
        "ordinal": 1,
        "status": "pending",
        "input": {"analysis_kind": "project_structure"},
        "max_attempts": 3,
    },
    {
        "step_key": "artifact",
        "node_type": "artifact.create",
        "effect_kind": "analysis",
        "ordinal": 2,
        "status": "pending",
        "input": {"artifact_type": "project_inspection", "format": "json"},
        "max_attempts": 1,
    },
    {
        "step_key": "respond",
        "node_type": "agent.respond",
        "effect_kind": "analysis",
        "ordinal": 3,
        "status": "pending",
        "input": {"format": "markdown", "message_type": "answer"},
        "max_attempts": 3,
    },
)
PROJECT_INSPECT_WORKFLOW_CHECKSUM = hashlib.sha256(
    json.dumps(
        PROJECT_INSPECT_STEPS,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
).hexdigest()
MAX_SOURCE_SCAN_ENTRIES = 5_000
MAX_SOURCE_SCAN_TOTAL_BYTES = 10_000_000


class ApplicationValidationError(ValueError):
    """A command is structurally valid HTTP but invalid for the application."""


class ProjectRootUnavailableError(RuntimeError):
    """The persisted project root cannot safely be scanned right now."""


class AgentApplication:
    """Use-case boundary between HTTP adapters and the v3 repository."""

    def __init__(self, store: Any) -> None:
        self.store = store

    def create_project(
        self,
        *,
        name: str,
        root_path: str,
        idempotency_key: str,
    ) -> dict[str, Any]:
        root = Path(root_path).expanduser().resolve()
        if not root.exists() or not root.is_dir():
            raise ApplicationValidationError(
                "project root must be an existing directory"
            )
        payload = {"name": name, "root_path": str(root)}
        return self.store.create_project(
            **payload,
            idempotency_key=_required_idempotency_key(idempotency_key),
            request_hash=request_hash(payload),
        )

    def list_projects(self) -> list[dict[str, Any]]:
        return self.store.list_projects()

    def scan_project_sources(
        self,
        *,
        project_id: str,
        idempotency_key: str,
    ) -> dict[str, Any]:
        project = self.store.get_project(project_id)
        if project is None:
            raise RecordNotFoundError("project not found")
        root = Path(str(project["root_path"])).expanduser().resolve()
        if not root.exists() or not root.is_dir():
            raise ProjectRootUnavailableError("project root is unavailable")
        documents, summary = _scan_project_root(root)
        payload = {"project_id": str(project_id), "scan_version": 1}
        return self.store.sync_project_root_source(
            project_id=project_id,
            documents_to_sync=documents,
            summary=summary,
            idempotency_key=_required_idempotency_key(idempotency_key),
            request_hash=request_hash(payload),
        )

    def list_sources(
        self,
        *,
        project_id: str,
        status: str | None,
        limit: int,
        offset: int,
    ) -> list[dict[str, Any]]:
        if self.store.get_project(project_id) is None:
            raise RecordNotFoundError("project not found")
        return self.store.list_sources(
            project_id=project_id,
            status=status,
            limit=limit,
            offset=offset,
        )

    def list_documents(
        self,
        *,
        project_id: str,
        source_id: str | None,
        limit: int,
        offset: int,
    ) -> list[dict[str, Any]]:
        if self.store.get_project(project_id) is None:
            raise RecordNotFoundError("project not found")
        if source_id and not any(
            source["id"] == source_id
            for source in self.store.list_sources(
                project_id=project_id,
                status=None,
                limit=1_000,
                offset=0,
            )
        ):
            raise RecordNotFoundError("source not found")
        return self.store.list_documents(
            project_id=project_id,
            source_id=source_id,
            limit=limit,
            offset=offset,
        )

    def create_task(
        self,
        *,
        project_id: str,
        title: str,
        message: str,
        idempotency_key: str,
    ) -> dict[str, Any]:
        payload = {
            "project_id": project_id,
            "title": title,
            "prompt": message,
            "depth": DepthProfile.STANDARD.value,
        }
        return self.store.create_task(
            **payload,
            idempotency_key=_required_idempotency_key(idempotency_key),
            request_hash=request_hash(payload),
        )

    def list_tasks(
        self,
        *,
        project_id: str | None,
        status: str | None,
        limit: int,
        offset: int,
    ) -> list[dict[str, Any]]:
        return self.store.list_tasks(
            project_id=project_id,
            status=status,
            limit=limit,
            offset=offset,
        )

    def get_task(self, task_id: str) -> dict[str, Any]:
        task = self.store.get_task(task_id)
        if task is None:
            raise RecordNotFoundError("task not found")
        return task

    def add_task_message(
        self,
        *,
        task_id: str,
        content: str,
        idempotency_key: str,
    ) -> dict[str, Any]:
        payload = {"task_id": task_id, "role": "user", "content": content}
        return self.store.add_task_message(
            **payload,
            idempotency_key=_required_idempotency_key(idempotency_key),
            request_hash=request_hash(payload),
        )

    def list_task_messages(self, task_id: str) -> list[dict[str, Any]]:
        self.get_task(task_id)
        return self.store.list_task_messages(task_id)

    def create_run(
        self,
        *,
        task_id: str,
        input_message_id: str,
        workflow_key: str,
        depth: str,
        idempotency_key: str,
    ) -> dict[str, Any]:
        if workflow_key != PROJECT_INSPECT_WORKFLOW_KEY:
            raise ApplicationValidationError("workflow is not executable in this slice")
        limits = get_depth_limits(depth)
        if len(PROJECT_INSPECT_STEPS) > limits.max_steps:
            raise ApplicationValidationError("workflow exceeds the selected depth limit")
        payload = {
            "task_id": task_id,
            "input_message_id": input_message_id,
            "workflow_key": workflow_key,
            "workflow_version": PROJECT_INSPECT_WORKFLOW_VERSION,
            "workflow_checksum": PROJECT_INSPECT_WORKFLOW_CHECKSUM,
            "depth": depth,
            "steps": list(PROJECT_INSPECT_STEPS),
        }
        return self.store.create_run_with_steps(
            **payload,
            idempotency_key=_required_idempotency_key(idempotency_key),
            request_hash=request_hash(payload),
        )

    def control_run(
        self,
        *,
        run_id: str,
        action: str,
        expected_version: int,
        idempotency_key: str,
    ) -> dict[str, Any]:
        if action not in {"pause", "resume", "cancel"}:
            raise ApplicationValidationError("unsupported run control action")
        payload = {
            "run_id": run_id,
            "action": action,
            "expected_version": expected_version,
        }
        method = getattr(self.store, f"{action}_run")
        return method(
            run_id=run_id,
            expected_version=expected_version,
            idempotency_key=_required_idempotency_key(idempotency_key),
            request_hash=request_hash(payload),
        )

    def retry_run(
        self,
        *,
        run_id: str,
        expected_version: int,
        idempotency_key: str,
    ) -> dict[str, Any]:
        payload = {
            "run_id": run_id,
            "action": "retry",
            "expected_version": expected_version,
        }
        return self.store.retry_run(
            run_id=run_id,
            expected_version=expected_version,
            idempotency_key=_required_idempotency_key(idempotency_key),
            request_hash=request_hash(payload),
        )

    def get_run(self, run_id: str) -> dict[str, Any]:
        run = self.store.get_run(run_id)
        if run is None:
            raise RecordNotFoundError("run not found")
        return run

    def list_task_runs(
        self,
        task_id: str,
        *,
        limit: int,
        offset: int,
    ) -> list[dict[str, Any]]:
        self.get_task(task_id)
        return self.store.list_task_runs(
            task_id,
            limit=limit,
            offset=offset,
        )

    def list_run_steps(self, run_id: str) -> list[dict[str, Any]]:
        self.get_run(run_id)
        return self.store.list_run_steps(run_id)

    def list_events(
        self,
        run_id: str,
        *,
        after_sequence: int,
        limit: int,
    ) -> list[dict[str, Any]]:
        self.get_run(run_id)
        return self.store.list_events(
            run_id,
            after_sequence=after_sequence,
            limit=limit,
        )

    def resolve_approval(
        self,
        *,
        approval_id: str,
        decision: str,
        expected_version: int,
        expected_request_hash: str,
        note: str,
        idempotency_key: str,
    ) -> dict[str, Any]:
        payload = {
            "approval_id": approval_id,
            "decision": decision,
            "expected_version": expected_version,
            "expected_request_hash": expected_request_hash,
            "note": note,
        }
        return self.store.resolve_approval(
            approval_id=approval_id,
            decision=decision,
            decided_by="local_user",
            expected_request_hash=expected_request_hash,
            expected_version=expected_version,
            decision_note=note,
            idempotency_key=_required_idempotency_key(idempotency_key),
            request_hash=request_hash(payload),
        )

    def get_approval(self, approval_id: str) -> dict[str, Any]:
        approval = self.store.get_approval(approval_id)
        if approval is None:
            raise RecordNotFoundError("approval not found")
        return approval

    def list_approvals(
        self,
        *,
        project_id: str | None,
        task_id: str | None,
        run_id: str | None,
        status: str | None,
    ) -> list[dict[str, Any]]:
        return self.store.list_approvals(
            project_id=project_id,
            task_id=task_id,
            run_id=run_id,
            status=status,
        )

    def get_artifact(self, artifact_id: str) -> dict[str, Any]:
        artifact = self.store.get_artifact(artifact_id)
        if artifact is None:
            raise RecordNotFoundError("artifact not found")
        return artifact

    def list_artifacts(
        self,
        *,
        project_id: str | None,
        task_id: str | None,
        run_id: str | None,
    ) -> list[dict[str, Any]]:
        return self.store.list_artifacts(
            project_id=project_id,
            task_id=task_id,
            run_id=run_id,
        )

    def validate_workflow_graph(self, graph: Mapping[str, Any]) -> dict[str, Any]:
        nodes = tuple(
            WorkflowNode(
                id=str(item["id"]),
                type_id=str(item["type"]),
                config=dict(item.get("config") or {}),
            )
            for item in graph.get("nodes", [])
        )
        edges = tuple(
            WorkflowEdge(
                id=str(item.get("id") or ""),
                source_node_id=str(item["source"]),
                source_port=str(item["source_port"]),
                target_node_id=str(item["target"]),
                target_port=str(item["target_port"]),
            )
            for item in graph.get("edges", [])
        )
        return validate_workflow(WorkflowDefinition(nodes=nodes, edges=edges)).to_dict()

    def create_workflow(
        self,
        *,
        workflow_key: str,
        name: str,
        description: str,
        scope_type: str,
        project_id: str | None,
        graph: Mapping[str, Any],
        idempotency_key: str,
    ) -> dict[str, Any]:
        self._require_valid_workflow(graph)
        if scope_type == "global" and project_id is not None:
            raise ApplicationValidationError(
                "global workflow must not declare project_id"
            )
        if scope_type == "project" and not project_id:
            raise ApplicationValidationError("project workflow requires project_id")
        payload = {
            "workflow_key": workflow_key,
            "name": name,
            "description": description,
            "scope_type": scope_type,
            "project_id": project_id,
            "dag": dict(graph),
        }
        return self.store.create_workflow(
            **payload,
            idempotency_key=_required_idempotency_key(idempotency_key),
            request_hash=request_hash(payload),
        )

    def create_workflow_version(
        self,
        *,
        workflow_id: str,
        graph: Mapping[str, Any],
        expected_version: int,
        idempotency_key: str,
    ) -> dict[str, Any]:
        self._require_valid_workflow(graph)
        payload = {
            "workflow_id": workflow_id,
            "dag": dict(graph),
            "expected_version": expected_version,
        }
        return self.store.create_workflow_version(
            **payload,
            idempotency_key=_required_idempotency_key(idempotency_key),
            request_hash=request_hash(payload),
        )

    def list_workflows(
        self,
        *,
        project_id: str | None,
        scope_type: str | None,
        status: str | None,
    ) -> list[dict[str, Any]]:
        return self.store.list_workflows(
            project_id=project_id,
            scope_type=scope_type,
            status=status,
        )

    def get_workflow(self, workflow_id: str) -> dict[str, Any]:
        workflow = self.store.get_workflow(workflow_id)
        if workflow is None:
            raise RecordNotFoundError("workflow not found")
        return workflow

    def get_workflow_with_versions(self, workflow_id: str) -> dict[str, Any]:
        workflow = self.get_workflow(workflow_id)
        return {
            "workflow": workflow,
            "versions": self.store.list_workflow_versions(workflow_id),
        }

    def publish_workflow(
        self,
        *,
        workflow_id: str,
        version_id: str,
        expected_checksum: str,
        expected_version: int,
        idempotency_key: str,
    ) -> dict[str, Any]:
        version = self.store.get_workflow_version(version_id)
        if version is None or str(version["workflow_id"]) != workflow_id:
            raise RecordNotFoundError("workflow version not found")
        graph = dict(version.get("dag") or {})
        self._require_valid_workflow(graph, require_resolved_references=True)
        payload = {
            "workflow_id": workflow_id,
            "version_id": version_id,
            "expected_checksum": expected_checksum,
            "expected_version": expected_version,
        }
        return self.store.publish_workflow_version(
            **payload,
            idempotency_key=_required_idempotency_key(idempotency_key),
            request_hash=request_hash(payload),
        )

    def archive_workflow(
        self,
        *,
        workflow_id: str,
        expected_version: int,
        idempotency_key: str,
    ) -> dict[str, Any]:
        payload = {
            "workflow_id": workflow_id,
            "expected_version": expected_version,
        }
        return self.store.archive_workflow(
            **payload,
            idempotency_key=_required_idempotency_key(idempotency_key),
            request_hash=request_hash(payload),
        )

    def bind_workflow(
        self,
        *,
        workflow_id: str,
        project_id: str,
        workflow_version_id: str,
        expected_workflow_version: int,
        expected_binding_version: int,
        idempotency_key: str,
    ) -> dict[str, Any]:
        payload = {
            "workflow_id": workflow_id,
            "project_id": project_id,
            "workflow_version_id": workflow_version_id,
            "expected_workflow_version": expected_workflow_version,
            "expected_version": expected_binding_version,
        }
        return self.store.bind_workflow(
            **payload,
            idempotency_key=_required_idempotency_key(idempotency_key),
            request_hash=request_hash(payload),
        )

    def list_workflow_bindings(
        self,
        *,
        project_id: str | None,
        workflow_id: str | None,
        enabled: bool | None,
    ) -> list[dict[str, Any]]:
        return self.store.list_workflow_bindings(
            project_id=project_id,
            workflow_id=workflow_id,
            enabled=enabled,
        )

    def _require_valid_workflow(
        self,
        graph: Mapping[str, Any],
        *,
        require_resolved_references: bool = False,
    ) -> None:
        result = self.validate_workflow_graph(graph)
        if not result["valid"]:
            codes = ", ".join(error["code"] for error in result["errors"])
            raise ApplicationValidationError(
                f"workflow graph is invalid: {codes}"
            )
        if require_resolved_references:
            unresolved_types = {
                str(node.get("type"))
                for node in graph.get("nodes", [])
                if str(node.get("type"))
                in {"llm.synthesize", "llm.compare", "obsidian.publish"}
            }
            if unresolved_types:
                raise ApplicationValidationError(
                    "workflow resource references cannot be resolved in the current "
                    "backend slice: " + ", ".join(sorted(unresolved_types))
                )


def request_hash(payload: Mapping[str, Any]) -> str:
    canonical = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _required_idempotency_key(value: str) -> str:
    normalized = str(value or "").strip()
    if not normalized:
        raise ApplicationValidationError("Idempotency-Key header is required")
    if len(normalized) > 200:
        raise ApplicationValidationError(
            "Idempotency-Key header must not exceed 200 characters"
        )
    return normalized


def _scan_project_root(root: Path) -> tuple[list[dict[str, Any]], dict[str, int]]:
    """Read bounded text snapshots from a registered root without symlink traversal."""

    documents: list[dict[str, Any]] = []
    summary = {
        "visited_entries": 0,
        "supported_files": 0,
        "skipped_unsupported": 0,
        "skipped_symlinks": 0,
        "skipped_too_large": 0,
        "read_failures": 0,
        "total_bytes": 0,
        "truncated": 0,
    }
    pending = [root]
    while pending:
        directory = pending.pop()
        try:
            children = sorted(directory.iterdir(), key=lambda item: item.name.lower())
        except OSError as exc:
            raise ProjectRootUnavailableError("project root cannot be read") from exc
        for child in children:
            summary["visited_entries"] += 1
            if summary["visited_entries"] > MAX_SOURCE_SCAN_ENTRIES:
                summary["truncated"] = 1
                pending.clear()
                break
            if child.is_symlink():
                summary["skipped_symlinks"] += 1
                continue
            if child.is_dir():
                if child.name.lower() not in IGNORED_DIR_NAMES:
                    pending.append(child)
                continue
            if not child.is_file() or not is_supported_text_path(child):
                summary["skipped_unsupported"] += 1
                continue
            summary["supported_files"] += 1
            try:
                size_bytes = child.stat().st_size
            except OSError:
                summary["read_failures"] += 1
                continue
            if size_bytes > MAX_TEXT_FILE_BYTES or (
                summary["total_bytes"] + size_bytes > MAX_SOURCE_SCAN_TOTAL_BYTES
            ):
                summary["skipped_too_large"] += 1
                continue
            try:
                raw = child.read_bytes()
                content = raw.decode("utf-8")
            except (OSError, UnicodeDecodeError):
                summary["read_failures"] += 1
                continue
            relative_path = child.relative_to(root).as_posix()
            documents.append(
                {
                    "relative_path": relative_path,
                    "content": content,
                    "checksum": hashlib.sha256(raw).hexdigest(),
                    "mime_type": mimetypes.guess_type(child.name)[0] or "text/plain",
                    "size_bytes": len(raw),
                }
            )
            summary["total_bytes"] += len(raw)
    return documents, summary


__all__ = [
    "AgentApplication",
    "ApplicationValidationError",
    "PROJECT_INSPECT_STEPS",
    "PROJECT_INSPECT_WORKFLOW_CHECKSUM",
    "PROJECT_INSPECT_WORKFLOW_KEY",
    "PROJECT_INSPECT_WORKFLOW_VERSION",
    "ProjectRootUnavailableError",
    "request_hash",
]
