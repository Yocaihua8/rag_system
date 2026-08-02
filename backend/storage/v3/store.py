"""SQLAlchemy Core repository for the isolated v3 Agent runtime."""
from __future__ import annotations

import hashlib
import json
import uuid
from collections.abc import Mapping, Sequence
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from sqlalchemy import and_, func, insert, or_, select, update
from sqlalchemy.engine import Connection
from sqlalchemy.exc import IntegrityError

from backend.config.v3 import V3_DATA_GENERATION
from backend.storage.v3.database import V3Database
from backend.storage.v3.errors import (
    IdempotencyConflictError,
    RecordNotFoundError,
    StateConflictError,
)
from backend.storage.v3.schema import (
    APPROVAL_STATUSES,
    ARTIFACT_STATUSES,
    DEPTH_VALUES,
    EFFECT_KINDS,
    STEP_STATUSES,
    RUN_STATUSES,
    TASK_STATUSES,
    agent_approvals,
    agent_artifacts,
    agent_events,
    agent_runs,
    agent_step_attempts,
    agent_steps,
    agent_task_messages,
    agent_tasks,
    idempotency_records,
    projects,
    workflow_bindings,
    workflow_definitions,
    workflow_versions,
)


JSON_FIELDS = {
    "config_json",
    "metadata_json",
    "vector_json",
    "value_json",
    "secret_refs_json",
    "dag_json",
    "input_schema_json",
    "parameters_json",
    "result_json",
    "input_json",
    "output_json",
    "error_json",
    "payload_json",
    "response_json",
}
BOOLEAN_FIELDS = {"enabled", "is_default"}
TERMINAL_RUN_STATUSES = {"completed", "failed", "cancelled"}
TERMINAL_STEP_STATUSES = {"succeeded", "failed", "skipped", "cancelled"}


class AgentStore:
    def __init__(
        self,
        db_path: Path,
        *,
        expected_generation: str = V3_DATA_GENERATION,
        busy_timeout_ms: int = 30_000,
    ) -> None:
        self.db_path = Path(db_path).expanduser().resolve()
        self._database = V3Database(
            self.db_path,
            expected_generation=expected_generation,
            busy_timeout_ms=busy_timeout_ms,
        )

    def initialize(self) -> dict[str, Any]:
        return self._database.initialize()

    def close(self) -> dict[str, bool]:
        return self._database.close()

    def create_project(
        self,
        *,
        name: str,
        root_path: str | Path,
        idempotency_key: str,
        request_hash: str,
        project_id: str | None = None,
    ) -> dict[str, Any]:
        clean_name = _required(name, "name")
        clean_root = str(Path(root_path).expanduser().resolve())
        scope = "project.create"
        now = _utc_now()
        try:
            with self._database.transaction() as connection:
                replay = _idempotency_replay(
                    connection, scope, idempotency_key, request_hash
                )
                if replay is not None:
                    return replay
                project = {
                    "id": _identifier(project_id),
                    "name": clean_name,
                    "root_path": clean_root,
                    "status": "active",
                    "version": 1,
                    "created_at": now,
                    "updated_at": now,
                }
                connection.execute(insert(projects).values(**project))
                response = {"project": project, "replayed": False}
                _record_idempotency(
                    connection,
                    scope=scope,
                    idempotency_key=idempotency_key,
                    request_hash=request_hash,
                    response_kind="project",
                    response_id=project["id"],
                    response=response,
                    now=now,
                )
                return response
        except IntegrityError as exc:
            raise StateConflictError("project root path already exists") from exc

    def list_projects(self) -> list[dict[str, Any]]:
        with self._database.read_connection() as connection:
            rows = connection.execute(
                select(projects).order_by(projects.c.updated_at.desc(), projects.c.id)
            ).mappings()
            return [_public_row(row) for row in rows]

    def get_project(self, project_id: str) -> dict[str, Any] | None:
        with self._database.read_connection() as connection:
            row = connection.execute(
                select(projects).where(projects.c.id == str(project_id))
            ).mappings().first()
            return _public_row(row) if row else None

    def create_workflow(
        self,
        *,
        workflow_key: str,
        name: str,
        dag: Mapping[str, Any],
        idempotency_key: str,
        request_hash: str,
        scope_type: str = "global",
        project_id: str | None = None,
        description: str = "",
        input_schema: Mapping[str, Any] | None = None,
        checksum: str | None = None,
        workflow_id: str | None = None,
        version_id: str | None = None,
    ) -> dict[str, Any]:
        """Create a workflow definition with an immutable-content draft v1."""

        clean_scope = _enum(scope_type, "scope_type", {"global", "project"})
        clean_project_id = str(project_id).strip() if project_id else None
        if clean_scope == "global" and clean_project_id is not None:
            raise ValueError("global workflow must not have project_id")
        if clean_scope == "project" and clean_project_id is None:
            raise ValueError("project workflow requires project_id")
        clean_dag = dict(dag)
        clean_input_schema = dict(input_schema or {})
        computed_checksum = _workflow_checksum(clean_dag, clean_input_schema)
        if checksum and str(checksum) != computed_checksum:
            raise StateConflictError("workflow checksum does not match draft content")
        scope = f"workflow.create:{clean_scope}:{clean_project_id or 'global'}"
        now = _utc_now()
        try:
            with self._database.transaction() as connection:
                replay = _idempotency_replay(
                    connection, scope, idempotency_key, request_hash
                )
                if replay is not None:
                    return replay
                if clean_project_id:
                    _require_row(connection, projects, clean_project_id, "project")
                workflow = {
                    "id": _identifier(workflow_id),
                    "scope_type": clean_scope,
                    "project_id": clean_project_id,
                    "workflow_key": _required(workflow_key, "workflow_key"),
                    "name": _required(name, "name"),
                    "description": str(description),
                    "status": "active",
                    "current_published_version_id": None,
                    "version": 1,
                    "created_at": now,
                    "updated_at": now,
                }
                version = {
                    "id": _identifier(version_id),
                    "workflow_id": workflow["id"],
                    "version_number": 1,
                    "status": "draft",
                    "dag_json": _dump_json(clean_dag),
                    "input_schema_json": _dump_json(clean_input_schema),
                    "checksum": computed_checksum,
                    "created_at": now,
                    "published_at": None,
                }
                connection.execute(insert(workflow_definitions).values(**workflow))
                connection.execute(insert(workflow_versions).values(**version))
                response = {
                    "workflow": _public_row(workflow),
                    "version": _public_row(version),
                    "replayed": False,
                }
                _record_idempotency(
                    connection,
                    scope=scope,
                    idempotency_key=idempotency_key,
                    request_hash=request_hash,
                    response_kind="workflow",
                    response_id=workflow["id"],
                    response=response,
                    now=now,
                )
                return response
        except IntegrityError as exc:
            raise StateConflictError("workflow key or draft content already exists") from exc

    def create_workflow_draft(self, **kwargs: Any) -> dict[str, Any]:
        """Compatibility name for callers that model definition creation as draft creation."""

        return self.create_workflow(**kwargs)

    def list_workflows(
        self,
        *,
        project_id: str | None = None,
        scope_type: str | None = None,
        status: str | None = "active",
    ) -> list[dict[str, Any]]:
        statement = select(workflow_definitions)
        if scope_type:
            statement = statement.where(
                workflow_definitions.c.scope_type
                == _enum(scope_type, "scope_type", {"global", "project"})
            )
        elif project_id:
            statement = statement.where(
                or_(
                    workflow_definitions.c.scope_type == "global",
                    workflow_definitions.c.project_id == str(project_id),
                )
            )
        if project_id and scope_type == "project":
            statement = statement.where(
                workflow_definitions.c.project_id == str(project_id)
            )
        if status:
            statement = statement.where(
                workflow_definitions.c.status
                == _enum(status, "status", {"active", "archived"})
            )
        statement = statement.order_by(
            workflow_definitions.c.updated_at.desc(), workflow_definitions.c.id
        )
        with self._database.read_connection() as connection:
            return [
                _public_row(row)
                for row in connection.execute(statement).mappings()
            ]

    def get_workflow(self, workflow_id: str) -> dict[str, Any] | None:
        with self._database.read_connection() as connection:
            row = connection.execute(
                select(workflow_definitions).where(
                    workflow_definitions.c.id == str(workflow_id)
                )
            ).mappings().first()
            return _public_row(row) if row else None

    def list_workflow_versions(self, workflow_id: str) -> list[dict[str, Any]]:
        with self._database.read_connection() as connection:
            rows = connection.execute(
                select(workflow_versions)
                .where(workflow_versions.c.workflow_id == str(workflow_id))
                .order_by(workflow_versions.c.version_number.desc())
            ).mappings()
            return [_public_row(row) for row in rows]

    def get_workflow_version(self, version_id: str) -> dict[str, Any] | None:
        with self._database.read_connection() as connection:
            row = connection.execute(
                select(workflow_versions).where(
                    workflow_versions.c.id == str(version_id)
                )
            ).mappings().first()
            return _public_row(row) if row else None

    def create_workflow_version(
        self,
        *,
        workflow_id: str,
        dag: Mapping[str, Any],
        idempotency_key: str,
        request_hash: str,
        expected_version: int | None = None,
        input_schema: Mapping[str, Any] | None = None,
        checksum: str | None = None,
        version_id: str | None = None,
    ) -> dict[str, Any]:
        clean_workflow_id = _required(workflow_id, "workflow_id")
        clean_dag = dict(dag)
        clean_input_schema = dict(input_schema or {})
        computed_checksum = _workflow_checksum(clean_dag, clean_input_schema)
        if checksum and str(checksum) != computed_checksum:
            raise StateConflictError("workflow checksum does not match draft content")
        scope = f"workflow.version.create:{clean_workflow_id}"
        now = _utc_now()
        try:
            with self._database.transaction() as connection:
                replay = _idempotency_replay(
                    connection, scope, idempotency_key, request_hash
                )
                if replay is not None:
                    return replay
                workflow = _require_row(
                    connection, workflow_definitions, clean_workflow_id, "workflow"
                )
                _require_version(workflow, expected_version, "workflow")
                if workflow["status"] != "active":
                    raise StateConflictError("archived workflow cannot accept a draft")
                number = int(
                    connection.execute(
                        select(
                            func.coalesce(
                                func.max(workflow_versions.c.version_number), 0
                            )
                        ).where(
                            workflow_versions.c.workflow_id == clean_workflow_id
                        )
                    ).scalar_one()
                ) + 1
                version = {
                    "id": _identifier(version_id),
                    "workflow_id": clean_workflow_id,
                    "version_number": number,
                    "status": "draft",
                    "dag_json": _dump_json(clean_dag),
                    "input_schema_json": _dump_json(clean_input_schema),
                    "checksum": computed_checksum,
                    "created_at": now,
                    "published_at": None,
                }
                connection.execute(insert(workflow_versions).values(**version))
                connection.execute(
                    update(workflow_definitions)
                    .where(
                        workflow_definitions.c.id == clean_workflow_id,
                        workflow_definitions.c.version == workflow["version"],
                    )
                    .values(
                        version=workflow_definitions.c.version + 1,
                        updated_at=now,
                    )
                )
                current = _require_row(
                    connection, workflow_definitions, clean_workflow_id, "workflow"
                )
                response = {
                    "workflow": _public_row(current),
                    "version": _public_row(version),
                    "replayed": False,
                }
                _record_idempotency(
                    connection,
                    scope=scope,
                    idempotency_key=idempotency_key,
                    request_hash=request_hash,
                    response_kind="workflow_version",
                    response_id=version["id"],
                    response=response,
                    now=now,
                )
                return response
        except IntegrityError as exc:
            raise StateConflictError("workflow draft content already exists") from exc

    def publish_workflow_version(
        self,
        *,
        workflow_id: str,
        version_id: str,
        expected_checksum: str,
        idempotency_key: str,
        request_hash: str,
        expected_version: int | None = None,
    ) -> dict[str, Any]:
        clean_workflow_id = _required(workflow_id, "workflow_id")
        clean_version_id = _required(version_id, "version_id")
        scope = f"workflow.version.publish:{clean_workflow_id}"
        now = _utc_now()
        with self._database.transaction() as connection:
            replay = _idempotency_replay(
                connection, scope, idempotency_key, request_hash
            )
            if replay is not None:
                return replay
            workflow = _require_row(
                connection, workflow_definitions, clean_workflow_id, "workflow"
            )
            _require_version(workflow, expected_version, "workflow")
            version = _require_row(
                connection, workflow_versions, clean_version_id, "workflow version"
            )
            if str(version["workflow_id"]) != clean_workflow_id:
                raise StateConflictError("workflow version does not belong to workflow")
            if version["status"] != "draft":
                raise StateConflictError("only draft workflow versions can be published")
            if str(version["checksum"]) != _required(
                expected_checksum, "expected_checksum"
            ):
                raise StateConflictError("workflow draft checksum changed")
            connection.execute(
                update(workflow_versions)
                .where(workflow_versions.c.id == clean_version_id)
                .values(status="published", published_at=now)
            )
            connection.execute(
                update(workflow_definitions)
                .where(
                    workflow_definitions.c.id == clean_workflow_id,
                    workflow_definitions.c.version == workflow["version"],
                )
                .values(
                    current_published_version_id=clean_version_id,
                    version=workflow_definitions.c.version + 1,
                    updated_at=now,
                )
            )
            current_workflow = _require_row(
                connection, workflow_definitions, clean_workflow_id, "workflow"
            )
            current_version = _require_row(
                connection, workflow_versions, clean_version_id, "workflow version"
            )
            response = {
                "workflow": _public_row(current_workflow),
                "version": _public_row(current_version),
                "replayed": False,
            }
            _record_idempotency(
                connection,
                scope=scope,
                idempotency_key=idempotency_key,
                request_hash=request_hash,
                response_kind="workflow_version",
                response_id=clean_version_id,
                response=response,
                now=now,
            )
            return response

    def archive_workflow(
        self,
        *,
        workflow_id: str,
        expected_version: int,
        idempotency_key: str,
        request_hash: str,
    ) -> dict[str, Any]:
        """Archive a definition without deleting published versions or bindings."""

        clean_workflow_id = _required(workflow_id, "workflow_id")
        scope = f"workflow.archive:{clean_workflow_id}"
        now = _utc_now()
        with self._database.transaction() as connection:
            replay = _idempotency_replay(
                connection, scope, idempotency_key, request_hash
            )
            if replay is not None:
                return replay
            workflow = _require_row(
                connection, workflow_definitions, clean_workflow_id, "workflow"
            )
            _require_version(workflow, expected_version, "workflow")
            if workflow["status"] != "active":
                raise StateConflictError("workflow is already archived")
            connection.execute(
                update(workflow_definitions)
                .where(
                    workflow_definitions.c.id == clean_workflow_id,
                    workflow_definitions.c.version == workflow["version"],
                )
                .values(
                    status="archived",
                    version=workflow_definitions.c.version + 1,
                    updated_at=now,
                )
            )
            current = _require_row(
                connection, workflow_definitions, clean_workflow_id, "workflow"
            )
            response = {"workflow": _public_row(current), "replayed": False}
            _record_idempotency(
                connection,
                scope=scope,
                idempotency_key=idempotency_key,
                request_hash=request_hash,
                response_kind="workflow",
                response_id=clean_workflow_id,
                response=response,
                now=now,
            )
            return response

    def bind_workflow(
        self,
        *,
        project_id: str,
        workflow_id: str,
        workflow_version_id: str,
        idempotency_key: str,
        request_hash: str,
        parameters: Mapping[str, Any] | None = None,
        enabled: bool = True,
        expected_version: int | None = None,
        expected_workflow_version: int | None = None,
        binding_id: str | None = None,
    ) -> dict[str, Any]:
        clean_project_id = _required(project_id, "project_id")
        clean_workflow_id = _required(workflow_id, "workflow_id")
        clean_version_id = _required(workflow_version_id, "workflow_version_id")
        scope = f"workflow.bind:{clean_project_id}:{clean_workflow_id}"
        now = _utc_now()
        with self._database.transaction() as connection:
            replay = _idempotency_replay(
                connection, scope, idempotency_key, request_hash
            )
            if replay is not None:
                return replay
            _require_row(connection, projects, clean_project_id, "project")
            workflow = _require_row(
                connection, workflow_definitions, clean_workflow_id, "workflow"
            )
            _require_version(workflow, expected_workflow_version, "workflow")
            if workflow["status"] != "active":
                raise StateConflictError("archived workflow cannot be bound")
            if (
                workflow["scope_type"] == "project"
                and str(workflow["project_id"]) != clean_project_id
            ):
                raise StateConflictError("project workflow belongs to another project")
            version = _require_row(
                connection, workflow_versions, clean_version_id, "workflow version"
            )
            if str(version["workflow_id"]) != clean_workflow_id:
                raise StateConflictError("workflow version does not belong to workflow")
            if version["status"] != "published":
                raise StateConflictError("only published workflow versions can be bound")
            existing = connection.execute(
                select(workflow_bindings).where(
                    workflow_bindings.c.project_id == clean_project_id,
                    workflow_bindings.c.workflow_id == clean_workflow_id,
                )
            ).mappings().first()
            if existing is None:
                if expected_version not in (None, 0):
                    raise StateConflictError("workflow binding does not exist")
                binding = {
                    "id": _identifier(binding_id),
                    "project_id": clean_project_id,
                    "workflow_id": clean_workflow_id,
                    "workflow_version_id": clean_version_id,
                    "parameters_json": _dump_json(parameters or {}),
                    "enabled": 1 if enabled else 0,
                    "version": 1,
                    "created_at": now,
                    "updated_at": now,
                }
                connection.execute(insert(workflow_bindings).values(**binding))
            else:
                _require_version(existing, expected_version, "workflow binding")
                connection.execute(
                    update(workflow_bindings)
                    .where(
                        workflow_bindings.c.id == existing["id"],
                        workflow_bindings.c.version == existing["version"],
                    )
                    .values(
                        workflow_version_id=clean_version_id,
                        parameters_json=_dump_json(parameters or {}),
                        enabled=1 if enabled else 0,
                        version=workflow_bindings.c.version + 1,
                        updated_at=now,
                    )
                )
                binding = _require_row(
                    connection, workflow_bindings, existing["id"], "workflow binding"
                )
            public_binding = _public_row(binding)
            response = {"binding": public_binding, "replayed": False}
            _record_idempotency(
                connection,
                scope=scope,
                idempotency_key=idempotency_key,
                request_hash=request_hash,
                response_kind="workflow_binding",
                response_id=str(binding["id"]),
                response=response,
                now=now,
            )
            return response

    def get_workflow_binding(self, binding_id: str) -> dict[str, Any] | None:
        with self._database.read_connection() as connection:
            row = connection.execute(
                select(workflow_bindings).where(
                    workflow_bindings.c.id == str(binding_id)
                )
            ).mappings().first()
            return _public_row(row) if row else None

    def list_workflow_bindings(
        self,
        *,
        project_id: str | None = None,
        workflow_id: str | None = None,
        enabled: bool | None = None,
    ) -> list[dict[str, Any]]:
        statement = select(workflow_bindings)
        if project_id:
            statement = statement.where(
                workflow_bindings.c.project_id == str(project_id)
            )
        if workflow_id:
            statement = statement.where(
                workflow_bindings.c.workflow_id == str(workflow_id)
            )
        if enabled is not None:
            statement = statement.where(
                workflow_bindings.c.enabled == (1 if enabled else 0)
            )
        statement = statement.order_by(
            workflow_bindings.c.updated_at.desc(), workflow_bindings.c.id
        )
        with self._database.read_connection() as connection:
            return [
                _public_row(row)
                for row in connection.execute(statement).mappings()
            ]

    def create_task(
        self,
        *,
        project_id: str,
        title: str,
        prompt: str,
        idempotency_key: str,
        request_hash: str,
        depth: str = "standard",
        task_id: str | None = None,
    ) -> dict[str, Any]:
        clean_title = _required(title, "title")
        clean_prompt = _required(prompt, "prompt")
        clean_depth = _enum(depth, "depth", set(DEPTH_VALUES))
        clean_project_id = _required(project_id, "project_id")
        scope = "task.create"
        now = _utc_now()
        with self._database.transaction() as connection:
            replay = _idempotency_replay(
                connection, scope, idempotency_key, request_hash
            )
            if replay is not None:
                return replay
            _require_row(connection, projects, clean_project_id, "project")
            task = {
                "id": _identifier(task_id),
                "project_id": clean_project_id,
                "title": clean_title,
                "prompt": clean_prompt,
                "depth": clean_depth,
                "status": "queued",
                "version": 1,
                "created_at": now,
                "updated_at": now,
            }
            connection.execute(insert(agent_tasks).values(**task))
            initial_message = {
                "id": _identifier(),
                "task_id": task["id"],
                "run_id": None,
                "role": "user",
                "message_type": "message",
                "content": clean_prompt,
                "metadata_json": "{}",
                "created_at": now,
            }
            connection.execute(insert(agent_task_messages).values(**initial_message))
            response = {
                "task": task,
                "initial_message": _public_row(initial_message),
                "replayed": False,
            }
            _record_idempotency(
                connection,
                scope=scope,
                idempotency_key=idempotency_key,
                request_hash=request_hash,
                response_kind="task",
                response_id=task["id"],
                response=response,
                now=now,
            )
            return response

    def add_task_message(
        self,
        *,
        task_id: str,
        role: str,
        content: str,
        idempotency_key: str,
        request_hash: str,
        message_type: str = "message",
        metadata: Mapping[str, Any] | None = None,
        run_id: str | None = None,
        message_id: str | None = None,
    ) -> dict[str, Any]:
        clean_task_id = _required(task_id, "task_id")
        clean_role = _enum(role, "role", {"user", "agent", "system", "tool"})
        clean_type = _required(message_type, "message_type")
        clean_content = str(content)
        scope = f"task.message:{clean_task_id}"
        now = _utc_now()
        with self._database.transaction() as connection:
            replay = _idempotency_replay(
                connection, scope, idempotency_key, request_hash
            )
            if replay is not None:
                return replay
            _require_row(connection, agent_tasks, clean_task_id, "task")
            if run_id:
                run = _require_row(connection, agent_runs, run_id, "run")
                if str(run["task_id"]) != clean_task_id:
                    raise StateConflictError("run does not belong to task")
            message = {
                "id": _identifier(message_id),
                "task_id": clean_task_id,
                "run_id": str(run_id) if run_id else None,
                "role": clean_role,
                "message_type": clean_type,
                "content": clean_content,
                "metadata_json": _dump_json(metadata or {}),
                "created_at": now,
            }
            connection.execute(insert(agent_task_messages).values(**message))
            public_message = _public_row(message)
            response = {"message": public_message, "replayed": False}
            _record_idempotency(
                connection,
                scope=scope,
                idempotency_key=idempotency_key,
                request_hash=request_hash,
                response_kind="task_message",
                response_id=message["id"],
                response=response,
                now=now,
            )
            return response

    def list_task_messages(self, task_id: str) -> list[dict[str, Any]]:
        with self._database.read_connection() as connection:
            rows = connection.execute(
                select(agent_task_messages)
                .where(agent_task_messages.c.task_id == str(task_id))
                .order_by(agent_task_messages.c.created_at, agent_task_messages.c.id)
            ).mappings()
            return [_public_row(row) for row in rows]

    def get_task_message(self, message_id: str) -> dict[str, Any] | None:
        with self._database.read_connection() as connection:
            row = connection.execute(
                select(agent_task_messages).where(
                    agent_task_messages.c.id == str(message_id)
                )
            ).mappings().first()
            return _public_row(row) if row else None

    def list_tasks(
        self,
        *,
        project_id: str | None = None,
        status: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        bounded_limit = max(1, min(int(limit), 500))
        bounded_offset = max(0, int(offset))
        statement = select(agent_tasks)
        if project_id:
            statement = statement.where(agent_tasks.c.project_id == str(project_id))
        if status:
            statement = statement.where(
                agent_tasks.c.status == _enum(status, "status", set(TASK_STATUSES))
            )
        statement = statement.order_by(
            agent_tasks.c.updated_at.desc(), agent_tasks.c.id
        ).limit(bounded_limit).offset(bounded_offset)
        with self._database.read_connection() as connection:
            rows = connection.execute(statement).mappings()
            return [_public_row(row) for row in rows]

    def get_task(self, task_id: str) -> dict[str, Any] | None:
        with self._database.read_connection() as connection:
            row = connection.execute(
                select(agent_tasks).where(agent_tasks.c.id == str(task_id))
            ).mappings().first()
            return _public_row(row) if row else None

    def create_run_with_steps(
        self,
        *,
        task_id: str,
        input_message_id: str,
        workflow_key: str,
        workflow_version: int,
        workflow_checksum: str,
        depth: str,
        steps: Sequence[Mapping[str, Any]],
        idempotency_key: str,
        request_hash: str,
        workflow_version_id: str | None = None,
        priority: int = 0,
        run_id: str | None = None,
    ) -> dict[str, Any]:
        clean_task_id = _required(task_id, "task_id")
        clean_message_id = _required(input_message_id, "input_message_id")
        clean_workflow_key = _required(workflow_key, "workflow_key")
        clean_checksum = _required(workflow_checksum, "workflow_checksum")
        clean_depth = _enum(depth, "depth", set(DEPTH_VALUES))
        clean_version = _positive_int(workflow_version, "workflow_version")
        normalized_steps = _normalize_steps(steps)
        scope = f"run.create:{clean_task_id}"
        now = _utc_now()
        with self._database.transaction() as connection:
            replay = _idempotency_replay(
                connection, scope, idempotency_key, request_hash
            )
            if replay is not None:
                return replay
            task = _require_row(connection, agent_tasks, clean_task_id, "task")
            input_message = _require_row(
                connection, agent_task_messages, clean_message_id, "task message"
            )
            if str(input_message["task_id"]) != clean_task_id:
                raise StateConflictError("input message does not belong to task")
            if str(input_message["role"]) != "user":
                raise StateConflictError("input message must have the user role")
            frozen_message = {
                "input_message_id": clean_message_id,
                "input_message_hash": _sha256(str(input_message["content"])),
            }
            if workflow_version_id:
                _require_row(
                    connection,
                    workflow_versions,
                    workflow_version_id,
                    "workflow version",
                )
            run = {
                "id": _identifier(run_id),
                "task_id": clean_task_id,
                "workflow_version_id": str(workflow_version_id) if workflow_version_id else None,
                "workflow_key": clean_workflow_key,
                "workflow_version": clean_version,
                "workflow_checksum": clean_checksum,
                "depth": clean_depth,
                "status": "queued",
                "priority": int(priority),
                "attempt_no": 1,
                "retry_of_run_id": None,
                "version": 1,
                "queued_at": now,
                "started_at": None,
                "finished_at": None,
                "paused_at": None,
                "cancel_requested_at": None,
                "lease_owner": "",
                "lease_expires_at": None,
                "error_code": "",
                "error_message": "",
                "result_json": "{}",
                "created_at": now,
                "updated_at": now,
            }
            connection.execute(insert(agent_runs).values(**run))
            step_rows: list[dict[str, Any]] = []
            for step_index, item in enumerate(normalized_steps):
                step_input = dict(item["input"])
                if step_index == 0:
                    step_input.update(frozen_message)
                step = {
                    "id": _identifier(item.get("id")),
                    "run_id": run["id"],
                    "step_key": item["step_key"],
                    "node_type": item["node_type"],
                    "effect_kind": item["effect_kind"],
                    "ordinal": item["ordinal"],
                    "status": item["status"],
                    "input_json": _dump_json(step_input),
                    "output_json": "{}",
                    "error_json": "{}",
                    "attempt_count": 0,
                    "max_attempts": item["max_attempts"],
                    "version": 1,
                    "started_at": None,
                    "finished_at": None,
                    "created_at": now,
                    "updated_at": now,
                }
                connection.execute(insert(agent_steps).values(**step))
                step_rows.append(step)
            connection.execute(
                update(agent_tasks)
                .where(agent_tasks.c.id == clean_task_id)
                .values(status="queued", version=agent_tasks.c.version + 1, updated_at=now)
            )
            event = _append_event(
                connection,
                run_id=run["id"],
                event_type="run.queued",
                payload={
                    "task_id": clean_task_id,
                    "status": "queued",
                    "workflow_key": clean_workflow_key,
                    "workflow_version": clean_version,
                    "input_message_id": clean_message_id,
                    "input_message_hash": frozen_message["input_message_hash"],
                },
                now=now,
            )
            response = {
                "run": _public_row(run),
                "steps": [_public_row(step) for step in step_rows],
                "event": event,
                "project_id": str(task["project_id"]),
                "replayed": False,
            }
            _record_idempotency(
                connection,
                scope=scope,
                idempotency_key=idempotency_key,
                request_hash=request_hash,
                response_kind="run",
                response_id=run["id"],
                response=response,
                now=now,
            )
            return response

    def get_run(self, run_id: str) -> dict[str, Any] | None:
        statement = (
            select(agent_runs, agent_tasks.c.project_id.label("project_id"))
            .join(agent_tasks, agent_tasks.c.id == agent_runs.c.task_id)
            .where(agent_runs.c.id == str(run_id))
        )
        with self._database.read_connection() as connection:
            row = connection.execute(statement).mappings().first()
            return _public_row(row) if row else None

    def list_run_steps(self, run_id: str) -> list[dict[str, Any]]:
        with self._database.read_connection() as connection:
            rows = connection.execute(
                select(agent_steps)
                .where(agent_steps.c.run_id == str(run_id))
                .order_by(agent_steps.c.ordinal, agent_steps.c.id)
            ).mappings()
            return [_public_row(row) for row in rows]

    def claim_next_run(
        self,
        *,
        worker_id: str,
        lease_seconds: int,
        now: datetime | str | None = None,
    ) -> dict[str, Any] | None:
        """Atomically claim the next queued run and its first runnable step."""

        clean_worker_id = _required(worker_id, "worker_id")
        clean_lease_seconds = _positive_int(lease_seconds, "lease_seconds")
        now_value = _timestamp(now)
        lease_expires_at = _add_seconds(now_value, clean_lease_seconds)
        with self._database.transaction() as connection:
            candidates = list(
                connection.execute(
                    select(agent_runs, agent_tasks.c.project_id.label("project_id"))
                    .join(agent_tasks, agent_tasks.c.id == agent_runs.c.task_id)
                    .where(agent_runs.c.status == "queued")
                    .order_by(
                        agent_runs.c.priority.desc(),
                        agent_runs.c.queued_at,
                        agent_runs.c.id,
                    )
                ).mappings()
            )
            if not candidates:
                return None
            run = None
            step = None
            for candidate in candidates:
                candidate_step = connection.execute(
                    select(agent_steps)
                    .where(
                        agent_steps.c.run_id == candidate["id"],
                        agent_steps.c.status.in_(("pending", "queued")),
                    )
                    .order_by(agent_steps.c.ordinal, agent_steps.c.id)
                    .limit(1)
                ).mappings().first()
                if candidate_step is None:
                    raise StateConflictError("queued run has no runnable step")
                if candidate_step["effect_kind"] in {
                    "project_write",
                    "external_write",
                }:
                    blocking_project_writes = int(
                        connection.execute(
                            select(func.count())
                            .select_from(
                                agent_steps.join(
                                    agent_runs,
                                    agent_runs.c.id == agent_steps.c.run_id,
                                ).join(
                                    agent_tasks,
                                    agent_tasks.c.id == agent_runs.c.task_id,
                                )
                            )
                            .where(
                                agent_tasks.c.project_id == candidate["project_id"],
                                or_(
                                    and_(
                                        agent_runs.c.status == "running",
                                        agent_steps.c.status == "running",
                                    ),
                                    and_(
                                        agent_runs.c.status == "recovering",
                                        agent_steps.c.status == "recovery_required",
                                    ),
                                ),
                                agent_steps.c.effect_kind.in_(
                                    ("project_write", "external_write")
                                ),
                            )
                        ).scalar_one()
                    )
                    if blocking_project_writes:
                        continue
                run = candidate
                step = candidate_step
                break
            if run is None or step is None:
                return None

            started_at = run["started_at"] or now_value
            connection.execute(
                update(agent_runs)
                .where(agent_runs.c.id == run["id"], agent_runs.c.version == run["version"])
                .values(
                    status="running",
                    started_at=started_at,
                    lease_owner=clean_worker_id,
                    lease_expires_at=lease_expires_at,
                    version=agent_runs.c.version + 1,
                    updated_at=now_value,
                )
            )
            connection.execute(
                update(agent_tasks)
                .where(agent_tasks.c.id == run["task_id"])
                .values(
                    status="running",
                    version=agent_tasks.c.version + 1,
                    updated_at=now_value,
                )
            )
            attempt_no = int(step["attempt_count"]) + 1
            connection.execute(
                update(agent_steps)
                .where(agent_steps.c.id == step["id"], agent_steps.c.version == step["version"])
                .values(
                    status="running",
                    attempt_count=attempt_no,
                    started_at=step["started_at"] or now_value,
                    version=agent_steps.c.version + 1,
                    updated_at=now_value,
                )
            )
            attempt = {
                "id": _identifier(),
                "run_id": str(run["id"]),
                "step_id": str(step["id"]),
                "attempt_no": attempt_no,
                "status": "running",
                "worker_id": clean_worker_id,
                "lease_owner": clean_worker_id,
                "lease_expires_at": lease_expires_at,
                "input_hash": _sha256(str(step["input_json"])),
                "output_json": "{}",
                "error_code": "",
                "error_message": "",
                "started_at": now_value,
                "finished_at": None,
                "created_at": now_value,
            }
            connection.execute(insert(agent_step_attempts).values(**attempt))
            run_event = _append_event(
                connection,
                run_id=str(run["id"]),
                event_type="run.started" if run["started_at"] is None else "run.resumed",
                payload={"worker_id": clean_worker_id, "lease_expires_at": lease_expires_at},
                now=now_value,
            )
            step_event = _append_event(
                connection,
                run_id=str(run["id"]),
                step_id=str(step["id"]),
                event_type="step.started",
                payload={"step_key": step["step_key"], "attempt_no": attempt_no},
                now=now_value,
            )
            current_run = _require_row(connection, agent_runs, str(run["id"]), "run")
            current_step = _require_row(connection, agent_steps, str(step["id"]), "step")
            return {
                "run_id": str(run["id"]),
                "task_id": str(run["task_id"]),
                "project_id": str(run["project_id"]),
                "lease": {
                    "owner": clean_worker_id,
                    "expires_at": lease_expires_at,
                },
                "run": _public_row(current_run),
                "step": _public_row(current_step),
                "attempt": _public_row(attempt),
                "events": [run_event, step_event],
            }

    def heartbeat_run(
        self,
        *,
        run_id: str,
        worker_id: str,
        lease_seconds: int,
        now: datetime | str | None = None,
    ) -> dict[str, Any]:
        clean_run_id = _required(run_id, "run_id")
        clean_worker_id = _required(worker_id, "worker_id")
        now_value = _timestamp(now)
        lease_expires_at = _add_seconds(
            now_value, _positive_int(lease_seconds, "lease_seconds")
        )
        with self._database.transaction() as connection:
            run = _require_worker_lease(
                connection, clean_run_id, clean_worker_id, now_value
            )
            connection.execute(
                update(agent_runs)
                .where(agent_runs.c.id == clean_run_id, agent_runs.c.version == run["version"])
                .values(
                    lease_expires_at=lease_expires_at,
                    version=agent_runs.c.version + 1,
                    updated_at=now_value,
                )
            )
            connection.execute(
                update(agent_step_attempts)
                .where(
                    agent_step_attempts.c.run_id == clean_run_id,
                    agent_step_attempts.c.status == "running",
                    agent_step_attempts.c.lease_owner == clean_worker_id,
                )
                .values(lease_expires_at=lease_expires_at)
            )
            current = _require_row(connection, agent_runs, clean_run_id, "run")
            return {
                "run": _public_row(current),
                "lease": {"owner": clean_worker_id, "expires_at": lease_expires_at},
            }

    def complete_step(
        self,
        *,
        run_id: str,
        step_id: str,
        worker_id: str,
        output: Mapping[str, Any] | Sequence[Any] | str | int | float | bool | None = None,
        now: datetime | str | None = None,
    ) -> dict[str, Any]:
        """Finish one leased step and either queue the next step or finish the run."""

        clean_run_id = _required(run_id, "run_id")
        clean_step_id = _required(step_id, "step_id")
        clean_worker_id = _required(worker_id, "worker_id")
        now_value = _timestamp(now)
        output_json = _dump_json(output if output is not None else {})
        with self._database.transaction() as connection:
            run = _require_worker_lease(
                connection, clean_run_id, clean_worker_id, now_value
            )
            step = _require_row(connection, agent_steps, clean_step_id, "step")
            if str(step["run_id"]) != clean_run_id or step["status"] != "running":
                raise StateConflictError("step is not the active running step")
            connection.execute(
                update(agent_steps)
                .where(agent_steps.c.id == clean_step_id, agent_steps.c.version == step["version"])
                .values(
                    status="succeeded",
                    output_json=output_json,
                    error_json="{}",
                    finished_at=now_value,
                    version=agent_steps.c.version + 1,
                    updated_at=now_value,
                )
            )
            connection.execute(
                update(agent_step_attempts)
                .where(
                    agent_step_attempts.c.step_id == clean_step_id,
                    agent_step_attempts.c.attempt_no == step["attempt_count"],
                    agent_step_attempts.c.status == "running",
                )
                .values(
                    status="succeeded",
                    output_json=output_json,
                    lease_expires_at=None,
                    finished_at=now_value,
                )
            )
            events = [
                _append_event(
                    connection,
                    run_id=clean_run_id,
                    step_id=clean_step_id,
                    event_type="step.succeeded",
                    payload={"step_key": step["step_key"], "output": output or {}},
                    now=now_value,
                )
            ]
            next_step = connection.execute(
                select(agent_steps)
                .where(
                    agent_steps.c.run_id == clean_run_id,
                    agent_steps.c.status.in_(("pending", "queued")),
                )
                .order_by(agent_steps.c.ordinal, agent_steps.c.id)
                .limit(1)
            ).mappings().first()
            if next_step is None:
                connection.execute(
                    update(agent_runs)
                    .where(agent_runs.c.id == clean_run_id, agent_runs.c.version == run["version"])
                    .values(
                        status="completed",
                        result_json=output_json,
                        finished_at=now_value,
                        lease_owner="",
                        lease_expires_at=None,
                        version=agent_runs.c.version + 1,
                        updated_at=now_value,
                    )
                )
                connection.execute(
                    update(agent_tasks)
                    .where(agent_tasks.c.id == run["task_id"])
                    .values(
                        status="completed",
                        version=agent_tasks.c.version + 1,
                        updated_at=now_value,
                    )
                )
                events.append(
                    _append_event(
                        connection,
                        run_id=clean_run_id,
                        event_type="run.completed",
                        payload={"result": output or {}},
                        now=now_value,
                    )
                )
            else:
                connection.execute(
                    update(agent_runs)
                    .where(agent_runs.c.id == clean_run_id, agent_runs.c.version == run["version"])
                    .values(
                        status="queued",
                        lease_owner="",
                        lease_expires_at=None,
                        queued_at=now_value,
                        version=agent_runs.c.version + 1,
                        updated_at=now_value,
                    )
                )
                connection.execute(
                    update(agent_tasks)
                    .where(agent_tasks.c.id == run["task_id"])
                    .values(
                        status="queued",
                        version=agent_tasks.c.version + 1,
                        updated_at=now_value,
                    )
                )
                if next_step["status"] == "pending":
                    connection.execute(
                        update(agent_steps)
                        .where(agent_steps.c.id == next_step["id"])
                        .values(
                            status="queued",
                            version=agent_steps.c.version + 1,
                            updated_at=now_value,
                        )
                    )
                events.append(
                    _append_event(
                        connection,
                        run_id=clean_run_id,
                        step_id=str(next_step["id"]),
                        event_type="step.queued",
                        payload={"step_key": next_step["step_key"]},
                        now=now_value,
                    )
                )
            current_run = _require_row(connection, agent_runs, clean_run_id, "run")
            current_step = _require_row(connection, agent_steps, clean_step_id, "step")
            current_next = (
                _require_row(connection, agent_steps, str(next_step["id"]), "step")
                if next_step is not None
                else None
            )
            return {
                "run": _public_row(current_run),
                "step": _public_row(current_step),
                "next_step": _public_row(current_next) if current_next else None,
                "events": events,
            }

    def complete_run(
        self,
        *,
        run_id: str,
        worker_id: str,
        result: Mapping[str, Any] | Sequence[Any] | str | int | float | bool | None = None,
        now: datetime | str | None = None,
    ) -> dict[str, Any]:
        """Complete a single-step run; multi-step callers should use complete_step."""

        with self._database.read_connection() as connection:
            active = connection.execute(
                select(agent_steps.c.id)
                .where(
                    agent_steps.c.run_id == str(run_id),
                    agent_steps.c.status == "running",
                )
                .order_by(agent_steps.c.ordinal)
                .limit(1)
            ).scalar_one_or_none()
        if active is None:
            raise StateConflictError("run has no active step")
        return self.complete_step(
            run_id=run_id,
            step_id=str(active),
            worker_id=worker_id,
            output=result,
            now=now,
        )

    def fail_run(
        self,
        *,
        run_id: str,
        worker_id: str,
        error_code: str,
        error_message: str,
        retryable: bool = False,
        now: datetime | str | None = None,
    ) -> dict[str, Any]:
        clean_run_id = _required(run_id, "run_id")
        clean_worker_id = _required(worker_id, "worker_id")
        clean_error_code = _required(error_code, "error_code")
        now_value = _timestamp(now)
        with self._database.transaction() as connection:
            run = _require_worker_lease(
                connection, clean_run_id, clean_worker_id, now_value
            )
            step = connection.execute(
                select(agent_steps)
                .where(
                    agent_steps.c.run_id == clean_run_id,
                    agent_steps.c.status == "running",
                )
                .order_by(agent_steps.c.ordinal)
                .limit(1)
            ).mappings().first()
            can_retry = bool(
                retryable
                and step is not None
                and step["effect_kind"] in {"none", "read", "analysis"}
                and int(step["attempt_count"]) < int(step["max_attempts"])
            )
            if can_retry and step is not None:
                error = {"code": clean_error_code, "message": str(error_message)}
                connection.execute(
                    update(agent_steps)
                    .where(agent_steps.c.id == step["id"])
                    .values(
                        status="queued",
                        error_json=_dump_json(error),
                        finished_at=None,
                        version=agent_steps.c.version + 1,
                        updated_at=now_value,
                    )
                )
                connection.execute(
                    update(agent_step_attempts)
                    .where(
                        agent_step_attempts.c.step_id == step["id"],
                        agent_step_attempts.c.status == "running",
                    )
                    .values(
                        status="failed",
                        error_code=clean_error_code,
                        error_message=str(error_message),
                        lease_expires_at=None,
                        finished_at=now_value,
                    )
                )
                connection.execute(
                    update(agent_runs)
                    .where(
                        agent_runs.c.id == clean_run_id,
                        agent_runs.c.version == run["version"],
                    )
                    .values(
                        status="queued",
                        queued_at=now_value,
                        lease_owner="",
                        lease_expires_at=None,
                        error_code=clean_error_code,
                        error_message=str(error_message),
                        version=agent_runs.c.version + 1,
                        updated_at=now_value,
                    )
                )
                connection.execute(
                    update(agent_tasks)
                    .where(agent_tasks.c.id == run["task_id"])
                    .values(
                        status="queued",
                        version=agent_tasks.c.version + 1,
                        updated_at=now_value,
                    )
                )
                event = _append_event(
                    connection,
                    run_id=clean_run_id,
                    step_id=str(step["id"]),
                    event_type="step.retry_scheduled",
                    payload={
                        "error_code": clean_error_code,
                        "error_message": str(error_message),
                        "attempt_count": int(step["attempt_count"]),
                        "max_attempts": int(step["max_attempts"]),
                    },
                    now=now_value,
                )
                current = _require_row(connection, agent_runs, clean_run_id, "run")
                return {
                    "run": _public_row(current),
                    "event": event,
                    "retry_scheduled": True,
                }
            if step is not None:
                connection.execute(
                    update(agent_steps)
                    .where(agent_steps.c.id == step["id"])
                    .values(
                        status="failed",
                        error_json=_dump_json(
                            {"code": clean_error_code, "message": str(error_message)}
                        ),
                        finished_at=now_value,
                        version=agent_steps.c.version + 1,
                        updated_at=now_value,
                    )
                )
                connection.execute(
                    update(agent_step_attempts)
                    .where(
                        agent_step_attempts.c.step_id == step["id"],
                        agent_step_attempts.c.status == "running",
                    )
                    .values(
                        status="failed",
                        error_code=clean_error_code,
                        error_message=str(error_message),
                        lease_expires_at=None,
                        finished_at=now_value,
                    )
                )
            connection.execute(
                update(agent_runs)
                .where(agent_runs.c.id == clean_run_id, agent_runs.c.version == run["version"])
                .values(
                    status="failed",
                    error_code=clean_error_code,
                    error_message=str(error_message),
                    finished_at=now_value,
                    lease_owner="",
                    lease_expires_at=None,
                    version=agent_runs.c.version + 1,
                    updated_at=now_value,
                )
            )
            connection.execute(
                update(agent_tasks)
                .where(agent_tasks.c.id == run["task_id"])
                .values(
                    status="failed",
                    version=agent_tasks.c.version + 1,
                    updated_at=now_value,
                )
            )
            events: list[dict[str, Any]] = []
            if step is not None:
                events.extend(
                    _interrupt_open_assistant_messages(
                        connection,
                        task_id=str(run["task_id"]),
                        run_id=clean_run_id,
                        step_id=str(step["id"]),
                        reason=clean_error_code,
                        recoverable=bool(retryable),
                        now=now_value,
                    )
                )
                events.append(
                    _append_event(
                        connection,
                        run_id=clean_run_id,
                        step_id=str(step["id"]),
                        event_type="step.failed",
                        payload={
                            "step_key": step["step_key"],
                            "error_code": clean_error_code,
                            "error_message": str(error_message),
                        },
                        now=now_value,
                    )
                )
            event = _append_event(
                connection,
                run_id=clean_run_id,
                step_id=str(step["id"]) if step else None,
                event_type="run.failed",
                payload={
                    "error_code": clean_error_code,
                    "error_message": str(error_message),
                    "retryable": bool(retryable),
                },
                now=now_value,
            )
            events.append(event)
            current = _require_row(connection, agent_runs, clean_run_id, "run")
            return {
                "run": _public_row(current),
                "event": event,
                "events": events,
                "retry_scheduled": False,
            }

    def recover_expired_runs(
        self, *, now: datetime | str | None = None
    ) -> list[dict[str, Any]]:
        """Recover safe work and fail closed for expired write-effect steps."""

        now_value = _timestamp(now)
        recovered: list[dict[str, Any]] = []
        with self._database.transaction() as connection:
            rows = list(
                connection.execute(
                    select(agent_runs)
                    .where(
                        agent_runs.c.status == "running",
                        agent_runs.c.lease_expires_at.is_not(None),
                        agent_runs.c.lease_expires_at <= now_value,
                    )
                    .order_by(agent_runs.c.lease_expires_at, agent_runs.c.id)
                ).mappings()
            )
            for run in rows:
                events: list[dict[str, Any]] = []
                step = connection.execute(
                    select(agent_steps)
                    .where(
                        agent_steps.c.run_id == run["id"],
                        agent_steps.c.status == "running",
                    )
                    .order_by(agent_steps.c.ordinal)
                    .limit(1)
                ).mappings().first()
                write_effect = bool(
                    step and step["effect_kind"] in {"project_write", "external_write"}
                )
                run_status = "recovering" if write_effect else "queued"
                task_status = "paused" if write_effect else "queued"
                step_status = "recovery_required" if write_effect else "queued"
                if step is not None:
                    connection.execute(
                        update(agent_steps)
                        .where(agent_steps.c.id == step["id"])
                        .values(
                            status=step_status,
                            error_json=_dump_json(
                                {
                                    "code": "lease_expired",
                                    "message": "worker lease expired",
                                    "manual_recovery_required": write_effect,
                                }
                            ),
                            version=agent_steps.c.version + 1,
                            updated_at=now_value,
                        )
                    )
                    connection.execute(
                        update(agent_step_attempts)
                        .where(
                            agent_step_attempts.c.step_id == step["id"],
                            agent_step_attempts.c.status == "running",
                        )
                        .values(
                            status="failed",
                            error_code="lease_expired",
                            error_message="worker lease expired",
                            lease_expires_at=None,
                            finished_at=now_value,
                        )
                    )
                connection.execute(
                    update(agent_runs)
                    .where(agent_runs.c.id == run["id"], agent_runs.c.version == run["version"])
                    .values(
                        status=run_status,
                        queued_at=now_value if not write_effect else run["queued_at"],
                        lease_owner="",
                        lease_expires_at=None,
                        error_code="recovery_required" if write_effect else "lease_expired",
                        error_message=(
                            "write-effect step requires manual recovery"
                            if write_effect
                            else "worker lease expired; run was requeued"
                        ),
                        version=agent_runs.c.version + 1,
                        updated_at=now_value,
                    )
                )
                connection.execute(
                    update(agent_tasks)
                    .where(agent_tasks.c.id == run["task_id"])
                    .values(
                        status=task_status,
                        version=agent_tasks.c.version + 1,
                        updated_at=now_value,
                    )
                )
                if step is not None:
                    events.append(
                        _append_event(
                            connection,
                            run_id=str(run["id"]),
                            step_id=str(step["id"]),
                            event_type=(
                                "step.recovery_required"
                                if write_effect
                                else "step.queued"
                            ),
                            payload={
                                "step_key": step["step_key"],
                                "reason": "lease_expired",
                            },
                            now=now_value,
                        )
                    )
                event = _append_event(
                    connection,
                    run_id=str(run["id"]),
                    step_id=str(step["id"]) if step else None,
                    event_type=("run.recovery_required" if write_effect else "run.requeued"),
                    payload={
                        "reason": "lease_expired",
                        "effect_kind": step["effect_kind"] if step else "none",
                    },
                    now=now_value,
                )
                events.append(event)
                recovered.append(
                    {
                        "run_id": str(run["id"]),
                        "task_id": str(run["task_id"]),
                        "status": run_status,
                        "step_status": step_status if step else None,
                        "event": event,
                        "events": events,
                    }
                )
        return recovered

    def pause_run(
        self,
        *,
        run_id: str,
        idempotency_key: str,
        request_hash: str,
        expected_version: int | None = None,
    ) -> dict[str, Any]:
        return self._control_run(
            run_id=run_id,
            action="pause",
            idempotency_key=idempotency_key,
            request_hash=request_hash,
            expected_version=expected_version,
        )

    def resume_run(
        self,
        *,
        run_id: str,
        idempotency_key: str,
        request_hash: str,
        expected_version: int | None = None,
    ) -> dict[str, Any]:
        return self._control_run(
            run_id=run_id,
            action="resume",
            idempotency_key=idempotency_key,
            request_hash=request_hash,
            expected_version=expected_version,
        )

    def cancel_run(
        self,
        *,
        run_id: str,
        idempotency_key: str,
        request_hash: str,
        expected_version: int | None = None,
    ) -> dict[str, Any]:
        return self._control_run(
            run_id=run_id,
            action="cancel",
            idempotency_key=idempotency_key,
            request_hash=request_hash,
            expected_version=expected_version,
        )

    def retry_run(
        self,
        *,
        run_id: str,
        idempotency_key: str,
        request_hash: str,
        expected_version: int | None = None,
        new_run_id: str | None = None,
    ) -> dict[str, Any]:
        """Create a new queued attempt from a terminal failed run."""

        clean_run_id = _required(run_id, "run_id")
        scope = f"run.retry:{clean_run_id}"
        now = _utc_now()
        with self._database.transaction() as connection:
            replay = _idempotency_replay(
                connection, scope, idempotency_key, request_hash
            )
            if replay is not None:
                return replay
            source = _require_row(connection, agent_runs, clean_run_id, "run")
            _require_version(source, expected_version, "run")
            if source["status"] != "failed":
                raise StateConflictError("only failed runs can be retried")
            source_steps = list(
                connection.execute(
                    select(agent_steps)
                    .where(agent_steps.c.run_id == clean_run_id)
                    .order_by(agent_steps.c.ordinal, agent_steps.c.id)
                ).mappings()
            )
            if not source_steps:
                raise StateConflictError("failed run has no steps to retry")
            new_id = _identifier(new_run_id)
            run = {
                "id": new_id,
                "task_id": str(source["task_id"]),
                "workflow_version_id": source["workflow_version_id"],
                "workflow_key": str(source["workflow_key"]),
                "workflow_version": int(source["workflow_version"]),
                "workflow_checksum": str(source["workflow_checksum"]),
                "depth": str(source["depth"]),
                "status": "queued",
                "priority": int(source["priority"]),
                "attempt_no": int(source["attempt_no"]) + 1,
                "retry_of_run_id": clean_run_id,
                "version": 1,
                "queued_at": now,
                "started_at": None,
                "finished_at": None,
                "paused_at": None,
                "cancel_requested_at": None,
                "lease_owner": "",
                "lease_expires_at": None,
                "error_code": "",
                "error_message": "",
                "result_json": "{}",
                "created_at": now,
                "updated_at": now,
            }
            connection.execute(insert(agent_runs).values(**run))
            steps: list[dict[str, Any]] = []
            for index, source_step in enumerate(source_steps):
                step = {
                    "id": _identifier(),
                    "run_id": new_id,
                    "step_key": str(source_step["step_key"]),
                    "node_type": str(source_step["node_type"]),
                    "effect_kind": str(source_step["effect_kind"]),
                    "ordinal": int(source_step["ordinal"]),
                    "status": "queued" if index == 0 else "pending",
                    "input_json": str(source_step["input_json"]),
                    "output_json": "{}",
                    "error_json": "{}",
                    "attempt_count": 0,
                    "max_attempts": int(source_step["max_attempts"]),
                    "version": 1,
                    "started_at": None,
                    "finished_at": None,
                    "created_at": now,
                    "updated_at": now,
                }
                connection.execute(insert(agent_steps).values(**step))
                steps.append(step)
            connection.execute(
                update(agent_tasks)
                .where(agent_tasks.c.id == source["task_id"])
                .values(
                    status="queued",
                    version=agent_tasks.c.version + 1,
                    updated_at=now,
                )
            )
            event = _append_event(
                connection,
                run_id=new_id,
                event_type="run.queued",
                payload={
                    "retry_of_run_id": clean_run_id,
                    "attempt_no": run["attempt_no"],
                },
                now=now,
            )
            task = _require_row(connection, agent_tasks, source["task_id"], "task")
            response = {
                "run": _public_row(run),
                "steps": [_public_row(step) for step in steps],
                "event": event,
                "project_id": str(task["project_id"]),
                "replayed": False,
            }
            _record_idempotency(
                connection,
                scope=scope,
                idempotency_key=idempotency_key,
                request_hash=request_hash,
                response_kind="run",
                response_id=new_id,
                response=response,
                now=now,
            )
            return response

    def _control_run(
        self,
        *,
        run_id: str,
        action: str,
        idempotency_key: str,
        request_hash: str,
        expected_version: int | None,
    ) -> dict[str, Any]:
        clean_run_id = _required(run_id, "run_id")
        scope = f"run.{action}:{clean_run_id}"
        now = _utc_now()
        with self._database.transaction() as connection:
            replay = _idempotency_replay(
                connection, scope, idempotency_key, request_hash
            )
            if replay is not None:
                return replay
            run = _require_row(connection, agent_runs, clean_run_id, "run")
            _require_version(run, expected_version, "run")
            transition_events: list[dict[str, Any]] = []
            if action == "pause":
                if run["status"] not in {"queued", "running"}:
                    raise StateConflictError("only queued or running runs can be paused")
                active_step = connection.execute(
                    select(agent_steps)
                    .where(
                        agent_steps.c.run_id == clean_run_id,
                        agent_steps.c.status == "running",
                    )
                    .order_by(agent_steps.c.ordinal)
                    .limit(1)
                ).mappings().first()
                write_effect = bool(
                    active_step
                    and active_step["effect_kind"] in {"project_write", "external_write"}
                )
                new_run_status = "recovering" if write_effect else "paused"
                new_step_status = "recovery_required" if write_effect else "queued"
                if active_step:
                    connection.execute(
                        update(agent_steps)
                        .where(agent_steps.c.id == active_step["id"])
                        .values(
                            status=new_step_status,
                            version=agent_steps.c.version + 1,
                            updated_at=now,
                        )
                    )
                    transition_events.append(
                        _append_event(
                            connection,
                            run_id=clean_run_id,
                            step_id=str(active_step["id"]),
                            event_type=(
                                "step.recovery_required"
                                if write_effect
                                else "step.queued"
                            ),
                            payload={
                                "step_key": active_step["step_key"],
                                "reason": (
                                    "pause_requested_during_write"
                                    if write_effect
                                    else "run_paused"
                                ),
                            },
                            now=now,
                        )
                    )
                event_type = "run.recovery_required" if write_effect else "run.paused"
                task_status = "paused"
                values = {
                    "status": new_run_status,
                    "paused_at": now,
                    "lease_owner": "",
                    "lease_expires_at": None,
                    "version": agent_runs.c.version + 1,
                    "updated_at": now,
                }
            elif action == "resume":
                if run["status"] != "paused":
                    raise StateConflictError("only paused runs can be resumed")
                event_type = "run.queued"
                task_status = "queued"
                values = {
                    "status": "queued",
                    "queued_at": now,
                    "paused_at": None,
                    "version": agent_runs.c.version + 1,
                    "updated_at": now,
                }
            elif action == "cancel":
                if run["status"] in TERMINAL_RUN_STATUSES:
                    raise StateConflictError("terminal run cannot be cancelled")
                event_type = "run.cancelled"
                task_status = "cancelled"
                values = {
                    "status": "cancelled",
                    "cancel_requested_at": now,
                    "finished_at": now,
                    "lease_owner": "",
                    "lease_expires_at": None,
                    "version": agent_runs.c.version + 1,
                    "updated_at": now,
                }
                cancelled_steps = list(
                    connection.execute(
                        select(agent_steps)
                        .where(
                            agent_steps.c.run_id == clean_run_id,
                            agent_steps.c.status.not_in(TERMINAL_STEP_STATUSES),
                        )
                        .order_by(agent_steps.c.ordinal, agent_steps.c.id)
                    ).mappings()
                )
                pending_approvals = list(
                    connection.execute(
                        select(agent_approvals)
                        .where(
                            agent_approvals.c.run_id == clean_run_id,
                            agent_approvals.c.status == "pending",
                        )
                        .order_by(agent_approvals.c.created_at, agent_approvals.c.id)
                    ).mappings()
                )
                for cancelled_step in cancelled_steps:
                    transition_events.extend(
                        _interrupt_open_assistant_messages(
                            connection,
                            task_id=str(run["task_id"]),
                            run_id=clean_run_id,
                            step_id=str(cancelled_step["id"]),
                            reason="run_cancelled",
                            recoverable=False,
                            now=now,
                        )
                    )
                connection.execute(
                    update(agent_steps)
                    .where(
                        agent_steps.c.run_id == clean_run_id,
                        agent_steps.c.status.not_in(TERMINAL_STEP_STATUSES),
                    )
                    .values(
                        status="cancelled",
                        finished_at=now,
                        version=agent_steps.c.version + 1,
                        updated_at=now,
                    )
                )
                connection.execute(
                    update(agent_approvals)
                    .where(
                        agent_approvals.c.run_id == clean_run_id,
                        agent_approvals.c.status == "pending",
                    )
                    .values(
                        status="rejected",
                        decided_by="system",
                        decision_note="run cancelled",
                        resolved_at=now,
                        version=agent_approvals.c.version + 1,
                    )
                )
                for cancelled_step in cancelled_steps:
                    transition_events.append(
                        _append_event(
                            connection,
                            run_id=clean_run_id,
                            step_id=str(cancelled_step["id"]),
                            event_type="step.cancelled",
                            payload={
                                "step_key": cancelled_step["step_key"],
                                "reason": "run_cancelled",
                            },
                            now=now,
                        )
                    )
                for approval in pending_approvals:
                    transition_events.append(
                        _append_event(
                            connection,
                            run_id=clean_run_id,
                            step_id=str(approval["step_id"]),
                            event_type="approval.rejected",
                            payload={
                                "approval_id": approval["id"],
                                "decided_by": "system",
                                "reason": "run_cancelled",
                            },
                            now=now,
                        )
                    )
            else:
                raise ValueError(f"unsupported run action: {action}")
            connection.execute(
                update(agent_step_attempts)
                .where(
                    agent_step_attempts.c.run_id == clean_run_id,
                    agent_step_attempts.c.status == "running",
                )
                .values(
                    status="cancelled",
                    error_code=f"run_{action}d",
                    error_message=f"run {action} requested",
                    lease_expires_at=None,
                    finished_at=now,
                )
            )
            connection.execute(
                update(agent_runs)
                .where(agent_runs.c.id == clean_run_id, agent_runs.c.version == run["version"])
                .values(**values)
            )
            connection.execute(
                update(agent_tasks)
                .where(agent_tasks.c.id == run["task_id"])
                .values(
                    status=task_status,
                    version=agent_tasks.c.version + 1,
                    updated_at=now,
                )
            )
            event = _append_event(
                connection,
                run_id=clean_run_id,
                event_type=event_type,
                payload={"action": action, "previous_status": run["status"]},
                now=now,
            )
            transition_events.append(event)
            current = _require_row(connection, agent_runs, clean_run_id, "run")
            response = {
                "run": _public_row(current),
                "event": event,
                "events": transition_events,
                "replayed": False,
            }
            _record_idempotency(
                connection,
                scope=scope,
                idempotency_key=idempotency_key,
                request_hash=request_hash,
                response_kind="run",
                response_id=clean_run_id,
                response=response,
                now=now,
            )
            return response

    def append_event(
        self,
        *,
        run_id: str,
        event_type: str,
        payload: Mapping[str, Any] | None = None,
        step_id: str | None = None,
    ) -> dict[str, Any]:
        now = _utc_now()
        with self._database.transaction() as connection:
            _require_row(connection, agent_runs, run_id, "run")
            if step_id:
                step = _require_row(connection, agent_steps, step_id, "step")
                if str(step["run_id"]) != str(run_id):
                    raise StateConflictError("step does not belong to run")
            return _append_event(
                connection,
                run_id=str(run_id),
                step_id=str(step_id) if step_id else None,
                event_type=_required(event_type, "event_type"),
                payload=payload or {},
                now=now,
            )

    def append_assistant_message_event(
        self,
        *,
        task_id: str,
        run_id: str,
        step_id: str,
        message_id: str,
        event_type: str,
        payload: Mapping[str, Any],
        idempotency_key: str,
        request_hash: str,
    ) -> dict[str, Any]:
        """Persist one replayable assistant started/delta event idempotently."""

        clean_task_id = _required(task_id, "task_id")
        clean_run_id = _required(run_id, "run_id")
        clean_step_id = _required(step_id, "step_id")
        clean_message_id = _required(message_id, "message_id")
        clean_event_type = _enum(
            event_type,
            "event_type",
            {"assistant.message.started", "assistant.message.delta"},
        )
        clean_payload = dict(payload)
        if str(clean_payload.get("message_id", "")) != clean_message_id:
            raise StateConflictError("assistant event message id changed")
        scope = f"assistant.message.event:{clean_run_id}:{clean_message_id}"
        now = _utc_now()
        with self._database.transaction() as connection:
            replay = _idempotency_replay(
                connection, scope, idempotency_key, request_hash
            )
            if replay is not None:
                return replay
            run, step = _require_message_context(
                connection,
                task_id=clean_task_id,
                run_id=clean_run_id,
                step_id=clean_step_id,
            )
            if run["status"] != "running" or step["status"] != "running":
                raise StateConflictError("assistant message step is not running")
            event = _append_event(
                connection,
                run_id=clean_run_id,
                step_id=clean_step_id,
                event_type=clean_event_type,
                payload=clean_payload,
                now=now,
            )
            response = {"event": event, "replayed": False}
            _record_idempotency(
                connection,
                scope=scope,
                idempotency_key=idempotency_key,
                request_hash=request_hash,
                response_kind="assistant_message_event",
                response_id=event["id"],
                response=response,
                now=now,
            )
            return response

    def finalize_assistant_message(
        self,
        *,
        task_id: str,
        run_id: str,
        step_id: str,
        message_id: str,
        content: str,
        chunk_count: int,
        idempotency_key: str,
        request_hash: str,
        message_type: str = "answer",
        format: str = "markdown",
        interrupted_reason: str | None = None,
        recoverable: bool = False,
        worker_id: str | None = None,
    ) -> dict[str, Any]:
        """Atomically save the canonical message and its terminal lifecycle event."""

        clean_task_id = _required(task_id, "task_id")
        clean_run_id = _required(run_id, "run_id")
        clean_step_id = _required(step_id, "step_id")
        clean_message_id = _required(message_id, "message_id")
        clean_type = _required(message_type, "message_type")
        clean_format = _enum(format, "format", {"markdown", "text"})
        clean_chunk_count = max(0, int(chunk_count))
        clean_content = str(content)
        content_hash = _sha256(clean_content)
        interrupted = interrupted_reason is not None
        scope = f"assistant.message.finalize:{clean_run_id}:{clean_message_id}"
        now = _utc_now()
        with self._database.transaction() as connection:
            replay = _idempotency_replay(
                connection, scope, idempotency_key, request_hash
            )
            if replay is not None:
                return replay
            run, step = _require_message_context(
                connection,
                task_id=clean_task_id,
                run_id=clean_run_id,
                step_id=clean_step_id,
            )
            if run["status"] != "running" or step["status"] != "running":
                raise StateConflictError("assistant message step is not running")
            if worker_id is not None:
                run = _require_worker_lease(
                    connection, clean_run_id, _required(worker_id, "worker_id"), now
                )
            existing = connection.execute(
                select(agent_task_messages).where(
                    agent_task_messages.c.id == clean_message_id
                )
            ).mappings().first()
            if existing is not None:
                raise StateConflictError("assistant message already exists")
            metadata = {
                "format": clean_format,
                "chunk_count": clean_chunk_count,
                "content_hash": content_hash,
                "complete": not interrupted,
            }
            message = {
                "id": clean_message_id,
                "task_id": clean_task_id,
                "run_id": clean_run_id,
                "role": "agent",
                "message_type": clean_type,
                "content": clean_content,
                "metadata_json": _dump_json(metadata),
                "created_at": now,
            }
            connection.execute(insert(agent_task_messages).values(**message))
            if interrupted:
                event_type = "assistant.message.interrupted"
                event_payload = {
                    "message_id": clean_message_id,
                    "reason": str(interrupted_reason),
                    "recoverable": bool(recoverable),
                }
            else:
                event_type = "assistant.message.completed"
                event_payload = {
                    "message_id": clean_message_id,
                    "chunk_count": clean_chunk_count,
                    "char_count": len(clean_content),
                    "content_hash": content_hash,
                }
            event = _append_event(
                connection,
                run_id=clean_run_id,
                step_id=clean_step_id,
                event_type=event_type,
                payload=event_payload,
                now=now,
            )
            events = [event]
            step_completed = False
            if worker_id is not None and not interrupted:
                next_step = connection.execute(
                    select(agent_steps.c.id)
                    .where(
                        agent_steps.c.run_id == clean_run_id,
                        agent_steps.c.id != clean_step_id,
                        agent_steps.c.status.in_(("pending", "queued", "running")),
                    )
                    .limit(1)
                ).scalar_one_or_none()
                if next_step is not None:
                    raise StateConflictError(
                        "assistant response must be the terminal workflow step"
                    )
                output = {
                    "message_id": clean_message_id,
                    "chunk_count": clean_chunk_count,
                    "content_hash": content_hash,
                }
                output_json = _dump_json(output)
                connection.execute(
                    update(agent_steps)
                    .where(
                        agent_steps.c.id == clean_step_id,
                        agent_steps.c.version == step["version"],
                    )
                    .values(
                        status="succeeded",
                        output_json=output_json,
                        error_json="{}",
                        finished_at=now,
                        version=agent_steps.c.version + 1,
                        updated_at=now,
                    )
                )
                connection.execute(
                    update(agent_step_attempts)
                    .where(
                        agent_step_attempts.c.step_id == clean_step_id,
                        agent_step_attempts.c.attempt_no == step["attempt_count"],
                        agent_step_attempts.c.status == "running",
                    )
                    .values(
                        status="succeeded",
                        output_json=output_json,
                        lease_expires_at=None,
                        finished_at=now,
                    )
                )
                connection.execute(
                    update(agent_runs)
                    .where(
                        agent_runs.c.id == clean_run_id,
                        agent_runs.c.version == run["version"],
                    )
                    .values(
                        status="completed",
                        result_json=output_json,
                        finished_at=now,
                        lease_owner="",
                        lease_expires_at=None,
                        version=agent_runs.c.version + 1,
                        updated_at=now,
                    )
                )
                connection.execute(
                    update(agent_tasks)
                    .where(agent_tasks.c.id == clean_task_id)
                    .values(
                        status="completed",
                        version=agent_tasks.c.version + 1,
                        updated_at=now,
                    )
                )
                events.append(
                    _append_event(
                        connection,
                        run_id=clean_run_id,
                        step_id=clean_step_id,
                        event_type="step.succeeded",
                        payload={"step_key": step["step_key"], "output": output},
                        now=now,
                    )
                )
                events.append(
                    _append_event(
                        connection,
                        run_id=clean_run_id,
                        event_type="run.completed",
                        payload={"result": output},
                        now=now,
                    )
                )
                step_completed = True
            response = {
                "message": _public_row(message),
                "event": event,
                "events": events,
                "step_completed": step_completed,
                "replayed": False,
            }
            _record_idempotency(
                connection,
                scope=scope,
                idempotency_key=idempotency_key,
                request_hash=request_hash,
                response_kind="task_message",
                response_id=clean_message_id,
                response=response,
                now=now,
            )
            return response

    def list_events(
        self,
        run_id: str,
        *,
        after_sequence: int = 0,
        limit: int = 500,
    ) -> list[dict[str, Any]]:
        bounded_limit = max(1, min(int(limit), 1000))
        with self._database.read_connection() as connection:
            rows = connection.execute(
                select(agent_events)
                .where(
                    agent_events.c.run_id == str(run_id),
                    agent_events.c.sequence > max(0, int(after_sequence)),
                )
                .order_by(agent_events.c.sequence)
                .limit(bounded_limit)
            ).mappings()
            return [_public_row(row) for row in rows]

    def request_approval(
        self,
        *,
        task_id: str,
        run_id: str,
        step_id: str,
        action_type: str,
        target: str,
        payload: Mapping[str, Any],
        request_hash: str,
        idempotency_key: str,
        idempotency_request_hash: str,
        resource_version: str = "",
        expires_at: datetime | str | None = None,
        approval_id: str | None = None,
    ) -> dict[str, Any]:
        clean_task_id = _required(task_id, "task_id")
        clean_run_id = _required(run_id, "run_id")
        clean_step_id = _required(step_id, "step_id")
        clean_request_hash = _required(request_hash, "request_hash")
        scope = f"approval.request:{clean_run_id}"
        now = _utc_now()
        with self._database.transaction() as connection:
            replay = _idempotency_replay(
                connection, scope, idempotency_key, idempotency_request_hash
            )
            if replay is not None:
                return replay
            task = _require_row(connection, agent_tasks, clean_task_id, "task")
            run = _require_row(connection, agent_runs, clean_run_id, "run")
            step = _require_row(connection, agent_steps, clean_step_id, "step")
            if str(run["task_id"]) != clean_task_id or str(step["run_id"]) != clean_run_id:
                raise StateConflictError("approval resources do not share one task/run")
            if run["status"] != "running" or step["status"] != "running":
                raise StateConflictError("approval can only be requested by a running step")
            approval = {
                "id": _identifier(approval_id),
                "project_id": str(task["project_id"]),
                "task_id": clean_task_id,
                "run_id": clean_run_id,
                "step_id": clean_step_id,
                "action_type": _required(action_type, "action_type"),
                "target": _required(target, "target"),
                "payload_json": _dump_json(payload),
                "request_hash": clean_request_hash,
                "resource_version": str(resource_version),
                "status": "pending",
                "version": 1,
                "decided_by": "",
                "decision_note": "",
                "created_at": now,
                "expires_at": _timestamp(expires_at) if expires_at else None,
                "resolved_at": None,
            }
            connection.execute(insert(agent_approvals).values(**approval))
            connection.execute(
                update(agent_steps)
                .where(agent_steps.c.id == clean_step_id)
                .values(
                    status="waiting_approval",
                    version=agent_steps.c.version + 1,
                    updated_at=now,
                )
            )
            connection.execute(
                update(agent_runs)
                .where(agent_runs.c.id == clean_run_id)
                .values(
                    status="waiting_approval",
                    lease_owner="",
                    lease_expires_at=None,
                    version=agent_runs.c.version + 1,
                    updated_at=now,
                )
            )
            connection.execute(
                update(agent_tasks)
                .where(agent_tasks.c.id == clean_task_id)
                .values(
                    status="waiting_approval",
                    version=agent_tasks.c.version + 1,
                    updated_at=now,
                )
            )
            connection.execute(
                update(agent_step_attempts)
                .where(
                    agent_step_attempts.c.step_id == clean_step_id,
                    agent_step_attempts.c.status == "running",
                )
                .values(
                    status="cancelled",
                    error_code="approval_required",
                    error_message="step is waiting for approval",
                    lease_expires_at=None,
                    finished_at=now,
                )
            )
            step_event = _append_event(
                connection,
                run_id=clean_run_id,
                step_id=clean_step_id,
                event_type="step.waiting_approval",
                payload={
                    "step_key": step["step_key"],
                    "approval_id": approval["id"],
                },
                now=now,
            )
            event = _append_event(
                connection,
                run_id=clean_run_id,
                step_id=clean_step_id,
                event_type="approval.requested",
                payload={
                    "approval_id": approval["id"],
                    "action_type": approval["action_type"],
                    "target": approval["target"],
                    "request_hash": clean_request_hash,
                },
                now=now,
            )
            response = {
                "approval": _public_row(approval),
                "event": event,
                "events": [step_event, event],
                "replayed": False,
            }
            _record_idempotency(
                connection,
                scope=scope,
                idempotency_key=idempotency_key,
                request_hash=idempotency_request_hash,
                response_kind="approval",
                response_id=approval["id"],
                response=response,
                now=now,
            )
            return response

    def expire_pending_approvals(
        self, *, now: datetime | str | None = None
    ) -> list[dict[str, Any]]:
        """Expire due approvals and fail closed without leaving waiting work behind."""

        now_value = _timestamp(now)
        expired_items: list[dict[str, Any]] = []
        with self._database.transaction() as connection:
            approvals = list(
                connection.execute(
                    select(agent_approvals)
                    .where(
                        agent_approvals.c.status == "pending",
                        agent_approvals.c.expires_at.is_not(None),
                        agent_approvals.c.expires_at <= now_value,
                    )
                    .order_by(agent_approvals.c.expires_at, agent_approvals.c.id)
                ).mappings()
            )
            for approval in approvals:
                step = _require_row(
                    connection, agent_steps, approval["step_id"], "step"
                )
                run = _require_row(connection, agent_runs, approval["run_id"], "run")
                step_changed = step["status"] == "waiting_approval"
                run_changed = run["status"] == "waiting_approval"
                connection.execute(
                    update(agent_approvals)
                    .where(
                        agent_approvals.c.id == approval["id"],
                        agent_approvals.c.version == approval["version"],
                    )
                    .values(
                        status="expired",
                        decided_by="system",
                        decision_note="approval expired",
                        resolved_at=now_value,
                        version=agent_approvals.c.version + 1,
                    )
                )
                if step_changed:
                    connection.execute(
                        update(agent_steps)
                        .where(agent_steps.c.id == step["id"])
                        .values(
                            status="cancelled",
                            finished_at=now_value,
                            version=agent_steps.c.version + 1,
                            updated_at=now_value,
                        )
                    )
                if run_changed:
                    connection.execute(
                        update(agent_runs)
                        .where(agent_runs.c.id == run["id"])
                        .values(
                            status="cancelled",
                            finished_at=now_value,
                            error_code="approval_expired",
                            error_message="approval request expired",
                            version=agent_runs.c.version + 1,
                            updated_at=now_value,
                        )
                    )
                    connection.execute(
                        update(agent_tasks)
                        .where(
                            agent_tasks.c.id == approval["task_id"],
                            agent_tasks.c.status == "waiting_approval",
                        )
                        .values(
                            status="cancelled",
                            version=agent_tasks.c.version + 1,
                            updated_at=now_value,
                        )
                    )
                events: list[dict[str, Any]] = []
                if step_changed:
                    events.append(
                        _append_event(
                            connection,
                            run_id=str(approval["run_id"]),
                            step_id=str(approval["step_id"]),
                            event_type="step.cancelled",
                            payload={
                                "step_key": step["step_key"],
                                "reason": "approval_expired",
                            },
                            now=now_value,
                        )
                    )
                approval_event = _append_event(
                    connection,
                    run_id=str(approval["run_id"]),
                    step_id=str(approval["step_id"]),
                    event_type="approval.expired",
                    payload={
                        "approval_id": approval["id"],
                        "reason": "deadline_reached",
                    },
                    now=now_value,
                )
                events.append(approval_event)
                if run_changed:
                    events.append(
                        _append_event(
                            connection,
                            run_id=str(approval["run_id"]),
                            event_type="run.cancelled",
                            payload={
                                "action": "approval_expired",
                                "previous_status": run["status"],
                            },
                            now=now_value,
                        )
                    )
                current = _require_row(
                    connection, agent_approvals, approval["id"], "approval"
                )
                expired_items.append(
                    {"approval": _public_row(current), "events": events}
                )
        return expired_items

    def resolve_approval(
        self,
        *,
        approval_id: str,
        decision: str,
        decided_by: str,
        expected_request_hash: str,
        idempotency_key: str,
        request_hash: str,
        expected_version: int | None = None,
        decision_note: str = "",
    ) -> dict[str, Any]:
        self.expire_pending_approvals()
        clean_approval_id = _required(approval_id, "approval_id")
        clean_decision = _enum(decision, "decision", {"approved", "rejected"})
        scope = f"approval.resolve:{clean_approval_id}"
        now = _utc_now()
        with self._database.transaction() as connection:
            replay = _idempotency_replay(
                connection, scope, idempotency_key, request_hash
            )
            if replay is not None:
                return replay
            approval = _require_row(
                connection, agent_approvals, clean_approval_id, "approval"
            )
            step = _require_row(connection, agent_steps, approval["step_id"], "step")
            _require_version(approval, expected_version, "approval")
            if approval["status"] != "pending":
                raise StateConflictError("approval is already resolved")
            if str(approval["request_hash"]) != _required(
                expected_request_hash, "expected_request_hash"
            ):
                raise StateConflictError("approval request hash changed")
            if approval["expires_at"] and str(approval["expires_at"]) <= now:
                raise StateConflictError("approval request has expired")
            approved = clean_decision == "approved"
            connection.execute(
                update(agent_approvals)
                .where(
                    agent_approvals.c.id == clean_approval_id,
                    agent_approvals.c.version == approval["version"],
                )
                .values(
                    status=clean_decision,
                    decided_by=_required(decided_by, "decided_by"),
                    decision_note=str(decision_note),
                    resolved_at=now,
                    version=agent_approvals.c.version + 1,
                )
            )
            step_status = "queued" if approved else "cancelled"
            run_status = "queued" if approved else "cancelled"
            task_status = "queued" if approved else "cancelled"
            connection.execute(
                update(agent_steps)
                .where(agent_steps.c.id == approval["step_id"])
                .values(
                    status=step_status,
                    finished_at=None if approved else now,
                    version=agent_steps.c.version + 1,
                    updated_at=now,
                )
            )
            connection.execute(
                update(agent_runs)
                .where(agent_runs.c.id == approval["run_id"])
                .values(
                    status=run_status,
                    queued_at=now if approved else agent_runs.c.queued_at,
                    finished_at=None if approved else now,
                    lease_owner="",
                    lease_expires_at=None,
                    version=agent_runs.c.version + 1,
                    updated_at=now,
                )
            )
            connection.execute(
                update(agent_tasks)
                .where(agent_tasks.c.id == approval["task_id"])
                .values(
                    status=task_status,
                    version=agent_tasks.c.version + 1,
                    updated_at=now,
                )
            )
            events: list[dict[str, Any]] = []
            if not approved:
                events.append(
                    _append_event(
                        connection,
                        run_id=str(approval["run_id"]),
                        step_id=str(approval["step_id"]),
                        event_type="step.cancelled",
                        payload={
                            "step_key": step["step_key"],
                            "reason": "approval_rejected",
                        },
                        now=now,
                    )
                )
            event = _append_event(
                connection,
                run_id=str(approval["run_id"]),
                step_id=str(approval["step_id"]),
                event_type=f"approval.{clean_decision}",
                payload={"approval_id": clean_approval_id, "decided_by": decided_by},
                now=now,
            )
            events.append(event)
            if approved:
                events.append(
                    _append_event(
                        connection,
                        run_id=str(approval["run_id"]),
                        step_id=str(approval["step_id"]),
                        event_type="step.queued",
                        payload={
                            "step_key": step["step_key"],
                            "reason": "approval_approved",
                        },
                        now=now,
                    )
                )
            else:
                events.append(
                    _append_event(
                        connection,
                        run_id=str(approval["run_id"]),
                        event_type="run.cancelled",
                        payload={
                            "action": "approval_rejected",
                            "previous_status": "waiting_approval",
                        },
                        now=now,
                    )
                )
            current = _require_row(
                connection, agent_approvals, clean_approval_id, "approval"
            )
            response = {
                "approval": _public_row(current),
                "event": event,
                "events": events,
                "replayed": False,
            }
            _record_idempotency(
                connection,
                scope=scope,
                idempotency_key=idempotency_key,
                request_hash=request_hash,
                response_kind="approval",
                response_id=clean_approval_id,
                response=response,
                now=now,
            )
            return response

    def get_approval(self, approval_id: str) -> dict[str, Any] | None:
        with self._database.read_connection() as connection:
            row = connection.execute(
                select(agent_approvals).where(agent_approvals.c.id == str(approval_id))
            ).mappings().first()
            return _public_row(row) if row else None

    def list_approvals(
        self,
        *,
        project_id: str | None = None,
        task_id: str | None = None,
        run_id: str | None = None,
        status: str | None = None,
    ) -> list[dict[str, Any]]:
        statement = select(agent_approvals)
        for column, value in (
            (agent_approvals.c.project_id, project_id),
            (agent_approvals.c.task_id, task_id),
            (agent_approvals.c.run_id, run_id),
        ):
            if value:
                statement = statement.where(column == str(value))
        if status:
            statement = statement.where(
                agent_approvals.c.status
                == _enum(status, "status", set(APPROVAL_STATUSES))
            )
        statement = statement.order_by(
            agent_approvals.c.created_at.desc(), agent_approvals.c.id
        )
        with self._database.read_connection() as connection:
            return [
                _public_row(row)
                for row in connection.execute(statement).mappings()
            ]

    def create_artifact(
        self,
        *,
        task_id: str,
        run_id: str,
        kind: str,
        title: str,
        content: str,
        metadata: Mapping[str, Any] | None,
        idempotency_key: str,
        request_hash: str,
        status: str = "ready",
        artifact_id: str | None = None,
        step_id: str | None = None,
    ) -> dict[str, Any]:
        clean_task_id = _required(task_id, "task_id")
        clean_run_id = _required(run_id, "run_id")
        clean_status = _enum(status, "status", set(ARTIFACT_STATUSES))
        scope = f"artifact.create:{clean_run_id}"
        now = _utc_now()
        with self._database.transaction() as connection:
            replay = _idempotency_replay(
                connection, scope, idempotency_key, request_hash
            )
            if replay is not None:
                return replay
            task = _require_row(connection, agent_tasks, clean_task_id, "task")
            run = _require_row(connection, agent_runs, clean_run_id, "run")
            if str(run["task_id"]) != clean_task_id:
                raise StateConflictError("run does not belong to task")
            if step_id:
                step = _require_row(connection, agent_steps, step_id, "step")
                if str(step["run_id"]) != clean_run_id:
                    raise StateConflictError("step does not belong to run")
            artifact = {
                "id": _identifier(artifact_id),
                "project_id": str(task["project_id"]),
                "task_id": clean_task_id,
                "run_id": clean_run_id,
                "step_id": str(step_id) if step_id else None,
                "artifact_type": _required(kind, "kind"),
                "name": _required(title, "title"),
                "status": clean_status,
                "content": str(content),
                "content_ref": "",
                "checksum": _sha256(str(content)),
                "metadata_json": _dump_json(metadata or {}),
                "version": 1,
                "created_at": now,
                "updated_at": now,
                "exported_at": now if clean_status == "exported" else None,
            }
            connection.execute(insert(agent_artifacts).values(**artifact))
            event = _append_event(
                connection,
                run_id=clean_run_id,
                step_id=str(step_id) if step_id else None,
                event_type="artifact.created",
                payload={
                    "artifact_id": artifact["id"],
                    "kind": artifact["artifact_type"],
                    "title": artifact["name"],
                    "status": clean_status,
                    "checksum": artifact["checksum"],
                },
                now=now,
            )
            response = {
                "artifact": _public_row(artifact),
                "event": event,
                "replayed": False,
            }
            _record_idempotency(
                connection,
                scope=scope,
                idempotency_key=idempotency_key,
                request_hash=request_hash,
                response_kind="artifact",
                response_id=artifact["id"],
                response=response,
                now=now,
            )
            return response

    def get_artifact(self, artifact_id: str) -> dict[str, Any] | None:
        with self._database.read_connection() as connection:
            row = connection.execute(
                select(agent_artifacts).where(agent_artifacts.c.id == str(artifact_id))
            ).mappings().first()
            return _public_row(row) if row else None

    def list_artifacts(
        self,
        *,
        project_id: str | None = None,
        task_id: str | None = None,
        run_id: str | None = None,
    ) -> list[dict[str, Any]]:
        statement = select(agent_artifacts)
        for column, value in (
            (agent_artifacts.c.project_id, project_id),
            (agent_artifacts.c.task_id, task_id),
            (agent_artifacts.c.run_id, run_id),
        ):
            if value:
                statement = statement.where(column == str(value))
        statement = statement.order_by(
            agent_artifacts.c.created_at.desc(), agent_artifacts.c.id
        )
        with self._database.read_connection() as connection:
            return [
                _public_row(row)
                for row in connection.execute(statement).mappings()
            ]


def _required(value: object, name: str) -> str:
    clean = str(value or "").strip()
    if not clean:
        raise ValueError(f"{name} is required")
    return clean


def _identifier(value: object | None = None) -> str:
    clean = str(value or "").strip()
    return clean or str(uuid.uuid4())


def _enum(value: object, name: str, allowed: set[str]) -> str:
    clean = _required(value, name)
    if clean not in allowed:
        raise ValueError(f"{name} must be one of: {', '.join(sorted(allowed))}")
    return clean


def _positive_int(value: object, name: str) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be an integer") from exc
    if parsed <= 0:
        raise ValueError(f"{name} must be positive")
    return parsed


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace(
        "+00:00", "Z"
    )


def _timestamp(value: datetime | str | None) -> str:
    if value is None:
        return _utc_now()
    if isinstance(value, datetime):
        parsed = value
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc).isoformat(timespec="milliseconds").replace(
            "+00:00", "Z"
        )
    clean = _required(value, "timestamp")
    try:
        parsed = datetime.fromisoformat(clean.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("timestamp must be ISO-8601") from exc
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc).isoformat(timespec="milliseconds").replace(
        "+00:00", "Z"
    )


def _add_seconds(timestamp: str, seconds: int) -> str:
    parsed = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    return (parsed + timedelta(seconds=seconds)).isoformat(
        timespec="milliseconds"
    ).replace("+00:00", "Z")


def _dump_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _load_json(value: object) -> Any:
    if value is None or value == "":
        return {}
    if not isinstance(value, str):
        return value
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return value


def _public_row(row: Mapping[str, Any] | None) -> dict[str, Any]:
    if row is None:
        return {}
    result: dict[str, Any] = {}
    for key, value in dict(row).items():
        if key in JSON_FIELDS or key.endswith("_json"):
            result[key.removesuffix("_json")] = _load_json(value)
        elif key in BOOLEAN_FIELDS:
            result[key] = bool(value)
        else:
            result[key] = value
    return result


def _require_row(
    connection: Connection, table, record_id: object, label: str
) -> Mapping[str, Any]:
    row = connection.execute(
        select(table).where(table.c.id == str(record_id))
    ).mappings().first()
    if row is None:
        raise RecordNotFoundError(f"{label} not found")
    return row


def _require_message_context(
    connection: Connection,
    *,
    task_id: str,
    run_id: str,
    step_id: str,
) -> tuple[Mapping[str, Any], Mapping[str, Any]]:
    run = _require_row(connection, agent_runs, run_id, "run")
    step = _require_row(connection, agent_steps, step_id, "step")
    if str(run["task_id"]) != str(task_id):
        raise StateConflictError("run does not belong to task")
    if str(step["run_id"]) != str(run_id):
        raise StateConflictError("step does not belong to run")
    return run, step


def _require_version(
    row: Mapping[str, Any], expected_version: int | None, label: str
) -> None:
    if expected_version is None:
        return
    if int(row["version"]) != int(expected_version):
        raise StateConflictError(f"{label} version changed")


def _idempotency_replay(
    connection: Connection,
    scope: str,
    idempotency_key: str,
    request_hash: str,
) -> dict[str, Any] | None:
    clean_key = _required(idempotency_key, "idempotency_key")
    clean_hash = _required(request_hash, "request_hash")
    row = connection.execute(
        select(idempotency_records).where(
            idempotency_records.c.scope == scope,
            idempotency_records.c.idempotency_key == clean_key,
        )
    ).mappings().first()
    if row is None:
        return None
    if str(row["request_hash"]) != clean_hash:
        raise IdempotencyConflictError(
            "idempotency key was already used with a different request hash"
        )
    response = _load_json(row["response_json"])
    if not isinstance(response, dict):
        raise StateConflictError("stored idempotency response is invalid")
    return {**response, "replayed": True}


def _record_idempotency(
    connection: Connection,
    *,
    scope: str,
    idempotency_key: str,
    request_hash: str,
    response_kind: str,
    response_id: str,
    response: Mapping[str, Any],
    now: str,
) -> None:
    connection.execute(
        insert(idempotency_records).values(
            id=_identifier(),
            scope=scope,
            idempotency_key=_required(idempotency_key, "idempotency_key"),
            request_hash=_required(request_hash, "request_hash"),
            response_kind=response_kind,
            response_id=response_id,
            response_json=_dump_json(response),
            status="completed",
            created_at=now,
            updated_at=now,
        )
    )


def _normalize_steps(steps: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    if not steps:
        raise ValueError("steps must not be empty")
    result: list[dict[str, Any]] = []
    keys: set[str] = set()
    ordinals: set[int] = set()
    for index, raw in enumerate(steps):
        step_key = _required(raw.get("step_key") or raw.get("key"), "step_key")
        ordinal = int(raw.get("ordinal", index))
        if ordinal < 0:
            raise ValueError("step ordinal must not be negative")
        if step_key in keys or ordinal in ordinals:
            raise ValueError("step keys and ordinals must be unique")
        keys.add(step_key)
        ordinals.add(ordinal)
        status = str(raw.get("status") or ("queued" if index == 0 else "pending"))
        result.append(
            {
                "id": raw.get("id"),
                "step_key": step_key,
                "node_type": _required(raw.get("node_type") or step_key, "node_type"),
                "effect_kind": _enum(
                    raw.get("effect_kind", "read"),
                    "effect_kind",
                    set(EFFECT_KINDS),
                ),
                "ordinal": ordinal,
                "status": _enum(status, "status", {"pending", "queued"}),
                "input": raw.get("input") or {},
                "max_attempts": _positive_int(raw.get("max_attempts", 3), "max_attempts"),
            }
        )
    return sorted(result, key=lambda item: (item["ordinal"], item["step_key"]))


def _sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _workflow_checksum(
    dag: Mapping[str, Any], input_schema: Mapping[str, Any]
) -> str:
    return _sha256(
        _dump_json({"dag": dict(dag), "input_schema": dict(input_schema)})
    )


def _sanitize_event_payload(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {
            str(key): (
                "[REDACTED]"
                if any(
                    marker in str(key).lower()
                    for marker in ("api_key", "password", "secret", "token")
                )
                else _sanitize_event_payload(item)
            )
            for key, item in value.items()
        }
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return [_sanitize_event_payload(item) for item in value]
    return value


def _append_event(
    connection: Connection,
    *,
    run_id: str,
    event_type: str,
    payload: Mapping[str, Any],
    now: str,
    step_id: str | None = None,
) -> dict[str, Any]:
    sequence = int(
        connection.execute(
            select(func.coalesce(func.max(agent_events.c.sequence), 0)).where(
                agent_events.c.run_id == str(run_id)
            )
        ).scalar_one()
    ) + 1
    event_row = {
        "id": _identifier(),
        "run_id": str(run_id),
        "step_id": str(step_id) if step_id else None,
        "sequence": sequence,
        "event_type": _required(event_type, "event_type"),
        "event_schema_version": 1,
        "payload_json": _dump_json(_sanitize_event_payload(payload)),
        "created_at": now,
    }
    connection.execute(insert(agent_events).values(**event_row))
    return _public_row(event_row)


def _interrupt_open_assistant_messages(
    connection: Connection,
    *,
    task_id: str,
    run_id: str,
    step_id: str,
    reason: str,
    recoverable: bool,
    now: str,
) -> list[dict[str, Any]]:
    rows = [
        _public_row(row)
        for row in connection.execute(
            select(agent_events)
            .where(
                agent_events.c.run_id == str(run_id),
                agent_events.c.step_id == str(step_id),
                agent_events.c.event_type.like("assistant.message.%"),
            )
            .order_by(agent_events.c.sequence)
        ).mappings()
    ]
    started: dict[str, dict[str, Any]] = {}
    chunks: dict[str, dict[int, str]] = {}
    terminal: set[str] = set()
    for event in rows:
        payload = dict(event.get("payload") or {})
        message_id = str(payload.get("message_id", ""))
        if not message_id:
            continue
        if event["event_type"] == "assistant.message.started":
            started[message_id] = payload
        elif event["event_type"] == "assistant.message.delta":
            chunks.setdefault(message_id, {})[int(payload.get("chunk_index", 0))] = str(
                payload.get("text", "")
            )
        elif event["event_type"] in {
            "assistant.message.completed",
            "assistant.message.interrupted",
        }:
            terminal.add(message_id)

    interrupted_events: list[dict[str, Any]] = []
    for message_id, start_payload in started.items():
        if message_id in terminal:
            continue
        ordered_chunks = [
            text
            for _, text in sorted(chunks.get(message_id, {}).items())
            if text
        ]
        content = "\n\n".join(ordered_chunks)
        content_hash = _sha256(content)
        existing = connection.execute(
            select(agent_task_messages.c.id).where(
                agent_task_messages.c.id == message_id
            )
        ).scalar_one_or_none()
        if existing is None:
            message = {
                "id": message_id,
                "task_id": str(task_id),
                "run_id": str(run_id),
                "role": "agent",
                "message_type": str(start_payload.get("message_type") or "answer"),
                "content": content,
                "metadata_json": _dump_json(
                    {
                        "format": str(start_payload.get("format") or "markdown"),
                        "chunk_count": len(ordered_chunks),
                        "content_hash": content_hash,
                        "complete": False,
                    }
                ),
                "created_at": now,
            }
            connection.execute(insert(agent_task_messages).values(**message))
        interrupted_events.append(
            _append_event(
                connection,
                run_id=str(run_id),
                step_id=str(step_id),
                event_type="assistant.message.interrupted",
                payload={
                    "message_id": message_id,
                    "reason": str(reason),
                    "recoverable": bool(recoverable),
                },
                now=now,
            )
        )
    return interrupted_events


def _require_worker_lease(
    connection: Connection,
    run_id: str,
    worker_id: str,
    now: str,
) -> Mapping[str, Any]:
    run = _require_row(connection, agent_runs, run_id, "run")
    if run["status"] != "running":
        raise StateConflictError("run is not running")
    if str(run["lease_owner"]) != worker_id:
        raise StateConflictError("run lease is owned by another worker")
    if not run["lease_expires_at"] or str(run["lease_expires_at"]) <= now:
        raise StateConflictError("run lease has expired")
    return run
