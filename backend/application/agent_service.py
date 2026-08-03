from __future__ import annotations

import hashlib
import json
import mimetypes
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from backend.domain.agent_runtime import DepthProfile, get_depth_limits
from backend.domain.project_insights import build_project_insight_overview
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
PROJECT_SOURCE_FACTS_WORKFLOW_KEY = "project.source-facts.v1"
PROJECT_SOURCE_FACTS_WORKFLOW_VERSION = 1
PROJECT_SOURCE_FACTS_STEPS: tuple[dict[str, Any], ...] = (
    PROJECT_INSPECT_STEPS[0],
    {
        "step_key": "analyze_sources",
        "node_type": "project.analyze",
        "effect_kind": "analysis",
        "ordinal": 1,
        "status": "pending",
        "input": {"analysis_kind": "persisted_source_facts"},
        "max_attempts": 3,
    },
    {
        "step_key": "artifact",
        "node_type": "artifact.create",
        "effect_kind": "analysis",
        "ordinal": 2,
        "status": "pending",
        "input": {"artifact_type": "project_source_facts", "format": "json"},
        "max_attempts": 1,
    },
    PROJECT_INSPECT_STEPS[3],
)
PROJECT_SOURCE_FACTS_WORKFLOW_CHECKSUM = hashlib.sha256(
    json.dumps(
        PROJECT_SOURCE_FACTS_STEPS,
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

    def get_project_insight_overview(self, project_id: str) -> dict[str, Any]:
        if self.store.get_project(project_id) is None:
            raise RecordNotFoundError("project not found")
        snapshot = self.store.get_project_source_snapshot(project_id)
        return build_project_insight_overview(
            project_id=project_id,
            source_count=int(snapshot["source_count"]),
            documents=snapshot["documents"],
        )

    def list_model_profiles(self) -> list[dict[str, Any]]:
        return self.store.list_model_profiles()

    def create_model_profile(
        self,
        *,
        fields: Mapping[str, Any],
        idempotency_key: str,
    ) -> dict[str, Any]:
        payload = {"profile": dict(fields)}
        return self.store.create_model_profile(
            fields=fields,
            idempotency_key=_required_idempotency_key(idempotency_key),
            request_hash=request_hash(payload),
        )

    def update_model_profile(
        self,
        *,
        profile_id: str,
        fields: Mapping[str, Any],
        idempotency_key: str,
    ) -> dict[str, Any]:
        payload = {"profile_id": profile_id, "profile": dict(fields)}
        return self.store.update_model_profile(
            profile_id=profile_id,
            fields=fields,
            idempotency_key=_required_idempotency_key(idempotency_key),
            request_hash=request_hash(payload),
        )

    def set_default_model_profile(
        self,
        *,
        profile_id: str,
        idempotency_key: str,
    ) -> dict[str, Any]:
        payload = {"profile_id": profile_id, "operation": "set_default"}
        return self.store.set_default_model_profile(
            profile_id=profile_id,
            idempotency_key=_required_idempotency_key(idempotency_key),
            request_hash=request_hash(payload),
        )

    def delete_model_profile(
        self,
        *,
        profile_id: str,
        idempotency_key: str,
    ) -> dict[str, Any]:
        payload = {"profile_id": profile_id, "operation": "delete"}
        return self.store.delete_model_profile(
            profile_id=profile_id,
            idempotency_key=_required_idempotency_key(idempotency_key),
            request_hash=request_hash(payload),
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
        workflow_version_id: str | None = None,
    ) -> dict[str, Any]:
        if workflow_version_id:
            return self._create_bound_workflow_run(
                task_id=task_id,
                input_message_id=input_message_id,
                workflow_key=workflow_key,
                workflow_version_id=workflow_version_id,
                depth=depth,
                idempotency_key=idempotency_key,
            )
        builtin_workflow = _builtin_workflow(workflow_key)
        if builtin_workflow is None:
            raise ApplicationValidationError("workflow is not executable in this slice")
        limits = get_depth_limits(depth)
        if len(builtin_workflow["steps"]) > limits.max_steps:
            raise ApplicationValidationError("workflow exceeds the selected depth limit")
        payload = {
            "task_id": task_id,
            "input_message_id": input_message_id,
            "workflow_key": workflow_key,
            "workflow_version": builtin_workflow["version"],
            "workflow_checksum": builtin_workflow["checksum"],
            "depth": depth,
            "steps": list(builtin_workflow["steps"]),
        }
        return self.store.create_run_with_steps(
            **payload,
            idempotency_key=_required_idempotency_key(idempotency_key),
            request_hash=request_hash(payload),
        )

    def _create_bound_workflow_run(
        self,
        *,
        task_id: str,
        input_message_id: str,
        workflow_key: str,
        workflow_version_id: str,
        depth: str,
        idempotency_key: str,
    ) -> dict[str, Any]:
        task = self.get_task(task_id)
        version = self.store.get_workflow_version(workflow_version_id)
        if version is None or str(version["status"]) != "published":
            raise ApplicationValidationError("workflow version is not published")
        workflow = self.get_workflow(str(version["workflow_id"]))
        if (
            workflow["status"] != "active"
            or workflow["workflow_key"] != workflow_key
            or workflow["current_published_version_id"] != workflow_version_id
        ):
            raise ApplicationValidationError("workflow version is not executable")
        binding = next(
            (
                item
                for item in self.store.list_workflow_bindings(
                    project_id=str(task["project_id"]),
                    workflow_id=str(workflow["id"]),
                    enabled=True,
                )
                if item["workflow_version_id"] == workflow_version_id
            ),
            None,
        )
        if binding is None:
            raise ApplicationValidationError("workflow version is not bound to the task project")
        steps = _executable_workflow_steps(dict(version.get("dag") or {}))
        limits = get_depth_limits(depth)
        if len(steps) > limits.max_steps:
            raise ApplicationValidationError("workflow exceeds the selected depth limit")
        payload = {
            "task_id": task_id,
            "input_message_id": input_message_id,
            "workflow_key": workflow_key,
            "workflow_version_id": workflow_version_id,
            "workflow_version": int(version["version_number"]),
            "workflow_checksum": str(version["checksum"]),
            "depth": depth,
            "steps": steps,
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

    def preview_artifact_export(self, artifact_id: str) -> dict[str, Any]:
        artifact = self.get_artifact(artifact_id)
        if artifact["status"] != "ready":
            raise ApplicationValidationError("artifact is not ready for export")
        return {
            "artifact_id": str(artifact["id"]),
            "name": str(artifact["name"]),
            "checksum": str(artifact["checksum"]),
            "version": int(artifact["version"]),
            "content_bytes": len(str(artifact["content"]).encode("utf-8")),
            "target_filename": _artifact_export_filename(artifact),
        }

    def confirm_artifact_export(
        self,
        *,
        artifact_id: str,
        expected_version: int,
        expected_checksum: str,
        idempotency_key: str,
        artifact_export_dir: Path,
    ) -> dict[str, Any]:
        target_filename = _artifact_export_filename({"id": artifact_id})
        payload = {
            "artifact_id": artifact_id,
            "expected_version": expected_version,
            "expected_checksum": expected_checksum,
            "content_ref": f"exports/{target_filename}",
        }
        clean_idempotency_key = _required_idempotency_key(idempotency_key)
        replay = self.store.get_artifact_export_replay(
            artifact_id=artifact_id,
            idempotency_key=clean_idempotency_key,
            request_hash=request_hash(payload),
        )
        if replay is not None:
            return replay
        artifact = self.get_artifact(artifact_id)
        preview = self.preview_artifact_export(artifact_id)
        if int(expected_version) != preview["version"]:
            raise ApplicationValidationError("artifact version changed")
        if str(expected_checksum) != preview["checksum"]:
            raise ApplicationValidationError("artifact checksum changed")
        export_dir = Path(artifact_export_dir).resolve()
        target = export_dir / str(preview["target_filename"])
        if target.parent != export_dir:
            raise ApplicationValidationError("artifact export target is unavailable")
        export_dir.mkdir(parents=True, exist_ok=True)
        if target.exists():
            try:
                matching_snapshot = target.is_file() and target.read_text(encoding="utf-8") == str(
                    artifact["content"]
                )
            except OSError:
                matching_snapshot = False
            if not matching_snapshot:
                raise ApplicationValidationError("artifact export target is unavailable")
            return self.store.mark_artifact_exported(
                artifact_id=artifact_id,
                expected_version=expected_version,
                expected_checksum=expected_checksum,
                content_ref=payload["content_ref"],
                idempotency_key=clean_idempotency_key,
                request_hash=request_hash(payload),
            )
        created_target = False
        try:
            with target.open("x", encoding="utf-8", newline="\n") as handle:
                handle.write(str(artifact["content"]))
            created_target = True
            return self.store.mark_artifact_exported(
                artifact_id=artifact_id,
                expected_version=expected_version,
                expected_checksum=expected_checksum,
                content_ref=payload["content_ref"],
                idempotency_key=clean_idempotency_key,
                request_hash=request_hash(payload),
            )
        except Exception:
            if created_target and target.exists():
                target.unlink()
            raise

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


def _artifact_export_filename(artifact: Mapping[str, Any]) -> str:
    return f"artifact-{str(artifact['id'])}.txt"


def _builtin_workflow(workflow_key: str) -> Mapping[str, Any] | None:
    if workflow_key == PROJECT_INSPECT_WORKFLOW_KEY:
        return {
            "version": PROJECT_INSPECT_WORKFLOW_VERSION,
            "checksum": PROJECT_INSPECT_WORKFLOW_CHECKSUM,
            "steps": PROJECT_INSPECT_STEPS,
        }
    if workflow_key == PROJECT_SOURCE_FACTS_WORKFLOW_KEY:
        return {
            "version": PROJECT_SOURCE_FACTS_WORKFLOW_VERSION,
            "checksum": PROJECT_SOURCE_FACTS_WORKFLOW_CHECKSUM,
            "steps": PROJECT_SOURCE_FACTS_STEPS,
        }
    return None


def _executable_workflow_steps(graph: Mapping[str, Any]) -> list[dict[str, Any]]:
    nodes = list(graph.get("nodes") or [])
    expected_types = ("trigger.manual", "project.analyze", "artifact.create", "agent.respond")
    if len(nodes) != len(expected_types):
        raise ApplicationValidationError("workflow graph is not executable in this slice")
    types = [str(item.get("type") or "") for item in nodes if isinstance(item, Mapping)]
    if len(types) != len(expected_types) or set(types) != set(expected_types):
        raise ApplicationValidationError("workflow graph contains unsupported executable nodes")
    ids_by_type = {str(item["type"]): str(item["id"]) for item in nodes if isinstance(item, Mapping)}
    required_edges = {
        (ids_by_type[expected_types[index]], ids_by_type[expected_types[index + 1]])
        for index in range(len(expected_types) - 1)
    }
    actual_edges = {
        (str(edge.get("source") or ""), str(edge.get("target") or ""))
        for edge in list(graph.get("edges") or [])
        if isinstance(edge, Mapping)
    }
    if actual_edges != required_edges:
        raise ApplicationValidationError("workflow graph has unsupported execution order")
    return [
        {
            "step_key": node_type.replace(".", "_"),
            "node_type": node_type,
            "effect_kind": "none" if node_type == "trigger.manual" else "analysis",
            "ordinal": index,
            "status": "queued" if index == 0 else "pending",
            "input": {},
            "max_attempts": 1,
        }
        for index, node_type in enumerate(expected_types)
    ]


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
    "PROJECT_SOURCE_FACTS_STEPS",
    "PROJECT_SOURCE_FACTS_WORKFLOW_CHECKSUM",
    "PROJECT_SOURCE_FACTS_WORKFLOW_KEY",
    "PROJECT_SOURCE_FACTS_WORKFLOW_VERSION",
    "ProjectRootUnavailableError",
    "request_hash",
]
