from __future__ import annotations

import asyncio
import re
from pathlib import Path
from typing import Annotated, Any, Literal
from uuid import uuid4

from fastapi import FastAPI, Header, Query, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.openapi.utils import get_openapi
from pydantic import TypeAdapter
from starlette.concurrency import run_in_threadpool
from starlette.exceptions import HTTPException as StarletteHTTPException

from backend.api.v3.models import (
    AgentEvent,
    ApprovalData,
    ApprovalListData,
    ApprovalMutationData,
    ApprovalResolveRequest,
    ArtifactData,
    ArtifactListData,
    BackupMutationData,
    DocumentListData,
    ErrorEnvelope,
    HealthData,
    ProjectCreateRequest,
    ProjectListData,
    ProjectInsightData,
    ProjectMutationData,
    SourceListData,
    SourceScanData,
    RestoreMutationData,
    RestoreRequest,
    RunCreateRequest,
    RunControlData,
    RunControlRequest,
    RunData,
    RunListData,
    RunMutationData,
    RunStepsData,
    SuccessEnvelope,
    StoragePreflightData,
    StoragePreflightRequest,
    TaskCreateRequest,
    TaskData,
    TaskListData,
    TaskMessageListData,
    TaskMessageMutationData,
    TaskMessageRequest,
    TaskMutationData,
    WorkflowArchiveData,
    WorkflowArchiveRequest,
    WorkflowBindRequest,
    WorkflowBindingListData,
    WorkflowBindingMutationData,
    WorkflowCreateRequest,
    WorkflowData,
    WorkflowDraftRequest,
    WorkflowGraphInput,
    WorkflowListData,
    WorkflowMutationData,
    WorkflowPublishRequest,
    WorkflowValidationData,
)
from backend.api.v3.responses import failure, success
from backend.api.v3.sse import stream_run_events
from backend.application.agent_service import (
    AgentApplication,
    ApplicationValidationError,
    ProjectRootUnavailableError,
    request_hash,
)
from backend.storage.v3.errors import (
    IdempotencyConflictError,
    RecordNotFoundError,
    StateConflictError,
)
from backend.storage.v3.maintenance import (
    BackupError,
    BackupValidationError,
    RestoreError,
    RestoreRollbackError,
    StoragePreflightError,
    create_v3_backup,
    preflight_storage_target,
    restore_v3_backup,
    validate_v3_backup,
)


IdempotencyHeader = Annotated[str, Header(alias="Idempotency-Key")]
_RESTORE_PATH = re.compile(
    r"^(?:/api/v3)?/system/backups/[^/]+/restore$"
)
_MANAGED_BACKUP_ID = re.compile(r"^backup-[0-9a-f]{32}$")


class _RestoreMaintenanceMiddleware:
    """Hold the maintenance lease until the complete ASGI response is sent."""

    def __init__(self, app: Any, *, runtime_state: Any) -> None:
        self.app = app
        self.runtime_state = runtime_state

    async def __call__(self, scope: dict[str, Any], receive: Any, send: Any) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request = Request(scope, receive=receive)
        state = self.runtime_state
        restore_request = bool(
            request.method == "POST" and _RESTORE_PATH.fullmatch(request.url.path)
        )
        lock = state.maintenance_lock
        async with lock:
            if restore_request:
                if state.restore_in_progress:
                    response = failure(
                        request,
                        status_code=409,
                        code="restore_in_progress",
                        message="another database restore is already in progress",
                    )
                    await response(scope, receive, send)
                    return
                if state.active_requests:
                    response = failure(
                        request,
                        status_code=409,
                        code="restore_busy",
                        message="database restore requires all other v3 requests to finish",
                        details={"active_requests": state.active_requests},
                    )
                    await response(scope, receive, send)
                    return
                state.restore_in_progress = True
            else:
                if state.restore_in_progress:
                    response = failure(
                        request,
                        status_code=503,
                        code="maintenance_in_progress",
                        message="the v3 database is temporarily unavailable during restore",
                    )
                    await response(scope, receive, send)
                    return
                state.active_requests += 1
        try:
            await self.app(scope, receive, send)
        finally:
            async with lock:
                if restore_request:
                    state.restore_in_progress = False
                else:
                    state.active_requests -= 1


def create_v3_app(
    *,
    store: Any,
    application: AgentApplication | None = None,
    executor: Any | None = None,
    database_info: dict[str, Any] | None = None,
    current_data_root: Path | None = None,
    legacy_data_root: Path | None = None,
    backups_dir: Path | None = None,
    backup_retention: int = 7,
) -> FastAPI:
    app = FastAPI(
        title="Knowledge Island Agent API",
        version="3.0.0-alpha.2",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        responses={
            404: {"model": ErrorEnvelope, "description": "Resource not found"},
            409: {"model": ErrorEnvelope, "description": "State conflict"},
            422: {"model": ErrorEnvelope, "description": "Validation error"},
        },
    )
    app.state.store = store
    app.state.application = application or AgentApplication(store)
    app.state.executor = executor
    app.state.database_info = dict(database_info or {})
    fallback_db_path = Path(
        getattr(store, "db_path", Path.cwd() / "runtime" / "v3" / "app.db")
    )
    app.state.current_data_root = Path(
        current_data_root or fallback_db_path.parent
    ).resolve()
    app.state.legacy_data_root = Path(
        legacy_data_root or app.state.current_data_root.parent / "v2"
    ).resolve()
    app.state.backups_dir = Path(
        backups_dir or app.state.current_data_root / "backups"
    ).resolve()
    app.state.backup_retention = int(backup_retention)
    app.state.maintenance_lock = asyncio.Lock()
    app.state.active_requests = 0
    app.state.restore_in_progress = False
    app.add_middleware(_RestoreMaintenanceMiddleware, runtime_state=app.state)

    @app.middleware("http")
    async def attach_request_id(request: Request, call_next):
        incoming = request.headers.get("x-request-id", "").strip()
        request.state.request_id = incoming[:200] if incoming else str(uuid4())
        response = await call_next(request)
        response.headers["X-Request-ID"] = request.state.request_id
        return response

    @app.exception_handler(RequestValidationError)
    async def request_validation_error(
        request: Request,
        exc: RequestValidationError,
    ):
        return failure(
            request,
            status_code=422,
            code="validation_error",
            message="request validation failed",
            details={"issues": jsonable_encoder(exc.errors())},
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_error(request: Request, exc: StarletteHTTPException):
        return failure(
            request,
            status_code=exc.status_code,
            code="not_found" if exc.status_code == 404 else "http_error",
            message=str(exc.detail),
        )

    @app.exception_handler(ApplicationValidationError)
    async def application_validation_error(
        request: Request,
        exc: ApplicationValidationError,
    ):
        return failure(
            request,
            status_code=422,
            code="application_validation_error",
            message=str(exc),
        )

    @app.exception_handler(RecordNotFoundError)
    async def record_not_found(request: Request, exc: RecordNotFoundError):
        return failure(
            request,
            status_code=404,
            code="not_found",
            message=str(exc),
        )

    @app.exception_handler(IdempotencyConflictError)
    async def idempotency_conflict(
        request: Request,
        exc: IdempotencyConflictError,
    ):
        return failure(
            request,
            status_code=409,
            code="idempotency_conflict",
            message=str(exc),
        )

    @app.exception_handler(StateConflictError)
    async def state_conflict(request: Request, exc: StateConflictError):
        return failure(
            request,
            status_code=409,
            code="state_conflict",
            message=str(exc),
        )

    @app.exception_handler(ProjectRootUnavailableError)
    async def project_root_unavailable(
        request: Request,
        exc: ProjectRootUnavailableError,
    ):
        return failure(
            request,
            status_code=409,
            code="project_root_unavailable",
            message=str(exc),
        )

    @app.get("/health", response_model=SuccessEnvelope[HealthData])
    def health(request: Request):
        info = request.app.state.database_info
        worker = request.app.state.executor
        return success(
            request,
            {
                "status": "ok",
                "data_generation": "v3",
                "schema_revision": str(info.get("alembic_revision", "")),
                "executor_running": bool(
                    worker is not None and getattr(worker, "running", False)
                ),
            },
        )

    @app.post(
        "/system/storage/preflight",
        response_model=SuccessEnvelope[StoragePreflightData],
    )
    def storage_preflight(request: Request, body: StoragePreflightRequest):
        try:
            result = preflight_storage_target(
                body.target_path,
                current_data_root=request.app.state.current_data_root,
                legacy_data_root=request.app.state.legacy_data_root,
            )
        except StoragePreflightError as exc:
            return failure(
                request,
                status_code=422,
                code="storage_preflight_invalid_path",
                message=str(exc),
            )
        return success(request, result)

    @app.post(
        "/system/backups",
        response_model=SuccessEnvelope[BackupMutationData],
        status_code=201,
    )
    def create_backup(
        request: Request,
        idempotency_key: IdempotencyHeader,
    ):
        try:
            result = create_v3_backup(
                request.app.state.store.db_path,
                current_data_root=request.app.state.current_data_root,
                backups_dir=request.app.state.backups_dir,
                idempotency_key=idempotency_key,
                retention=request.app.state.backup_retention,
            )
        except BackupValidationError as exc:
            return failure(
                request,
                status_code=409,
                code="backup_validation_failed",
                message=str(exc),
            )
        except BackupError as exc:
            return failure(
                request,
                status_code=422,
                code="backup_failed",
                message=str(exc),
            )
        return success(request, result, status_code=201)

    @app.post(
        "/system/backups/{backup_id}/restore",
        response_model=SuccessEnvelope[RestoreMutationData],
    )
    async def restore_backup(
        request: Request,
        backup_id: str,
        body: RestoreRequest,
        idempotency_key: IdempotencyHeader,
    ):
        if not _MANAGED_BACKUP_ID.fullmatch(backup_id):
            return failure(
                request,
                status_code=404,
                code="backup_not_found",
                message="managed backup was not found",
            )
        clean_idempotency_key = idempotency_key.strip()
        if not clean_idempotency_key or len(clean_idempotency_key) > 200:
            return failure(
                request,
                status_code=422,
                code="validation_error",
                message="Idempotency-Key must contain between 1 and 200 characters",
            )

        store = request.app.state.store
        required_store_methods = (
            "get_restore_replay",
            "record_restore_result",
            "checkpoint",
            "close",
            "initialize",
        )
        if any(not hasattr(store, name) for name in required_store_methods):
            return failure(
                request,
                status_code=503,
                code="restore_unavailable",
                message="database restore is not available for this runtime",
            )

        command_hash = request_hash(
            {
                "backup_id": backup_id,
                "expected_database_sha256": body.expected_database_sha256,
            }
        )
        try:
            replay = await run_in_threadpool(
                lambda: store.get_restore_replay(
                    idempotency_key=clean_idempotency_key,
                    request_hash=command_hash,
                )
            )
        except IdempotencyConflictError:
            raise
        if replay is not None:
            return success(request, replay)

        current_info = dict(request.app.state.database_info)
        if not current_info.get("alembic_head"):
            current_info = await run_in_threadpool(store.initialize)
            request.app.state.database_info = current_info
        expected_revision = str(
            current_info.get("alembic_head")
            or current_info.get("alembic_revision")
            or ""
        )
        backup_dir = request.app.state.backups_dir / backup_id
        try:
            manifest = await run_in_threadpool(
                lambda: validate_v3_backup(
                    backup_dir,
                    expected_generation="v3",
                    expected_revision=expected_revision,
                    expected_backup_id=backup_id,
                )
            )
        except BackupValidationError as exc:
            return failure(
                request,
                status_code=409,
                code="backup_validation_failed",
                message=str(exc),
            )
        if manifest["database_sha256"] != body.expected_database_sha256:
            return failure(
                request,
                status_code=409,
                code="restore_confirmation_mismatch",
                message="selected backup hash does not match confirmation",
            )

        executor = request.app.state.executor
        executor_was_running = bool(
            executor is not None and getattr(executor, "running", False)
        )
        executor_stopped = False
        restored = False
        try:
            if executor_was_running:
                await executor.stop()
                executor_stopped = True
            await run_in_threadpool(store.checkpoint)
            await run_in_threadpool(store.close)
            result = await run_in_threadpool(
                lambda: restore_v3_backup(
                    store.db_path,
                    backup_dir,
                    expected_backup_sha256=body.expected_database_sha256,
                    expected_revision=expected_revision,
                    activate=store.initialize,
                )
            )
            restored = True
            sanitized_info = _public_database_info(result["database_info"])
            response = {
                "backup": result["backup"],
                "database_info": sanitized_info,
                "restored": True,
                "replayed": False,
            }
            response = await run_in_threadpool(
                lambda: store.record_restore_result(
                    idempotency_key=clean_idempotency_key,
                    request_hash=command_hash,
                    response=response,
                )
            )
            request.app.state.database_info = dict(result["database_info"])
            if executor_was_running:
                await executor.start()
                executor_stopped = False
            return success(request, response)
        except RestoreRollbackError as exc:
            return failure(
                request,
                status_code=500,
                code="restore_rollback_failed",
                message=str(exc),
                details={"data_state": "uncertain", "executor_restarted": False},
            )
        except RestoreError as exc:
            info = await run_in_threadpool(store.initialize)
            request.app.state.database_info = info
            if executor_was_running and executor_stopped:
                await executor.start()
                executor_stopped = False
            return failure(
                request,
                status_code=409,
                code="restore_failed",
                message=str(exc),
                details={"original_database_reactivated": True},
            )
        except Exception as exc:
            if restored:
                if executor_was_running and executor_stopped:
                    try:
                        await executor.start()
                        executor_stopped = False
                    except Exception:
                        pass
                return failure(
                    request,
                    status_code=503,
                    code="restore_finalization_failed",
                    message="database was restored but runtime finalization failed",
                    details={
                        "restored": True,
                        "executor_restarted": not executor_stopped,
                        "error_type": type(exc).__name__,
                    },
                )
            try:
                info = await run_in_threadpool(store.initialize)
                request.app.state.database_info = info
            except Exception:
                info = None
            if executor_was_running and executor_stopped and info is not None:
                try:
                    await executor.start()
                    executor_stopped = False
                except Exception:
                    pass
            return failure(
                request,
                status_code=503,
                code="restore_failed",
                message="database restore could not be completed",
                details={
                    "restored": False,
                    "executor_restarted": not executor_stopped,
                    "error_type": type(exc).__name__,
                },
            )

    @app.post(
        "/projects",
        response_model=SuccessEnvelope[ProjectMutationData],
        status_code=201,
    )
    def create_project(
        request: Request,
        body: ProjectCreateRequest,
        idempotency_key: IdempotencyHeader,
    ):
        result = _application(request).create_project(
            name=body.name,
            root_path=body.root_path,
            idempotency_key=idempotency_key,
        )
        return success(request, result, status_code=201)

    @app.get("/projects", response_model=SuccessEnvelope[ProjectListData])
    def list_projects(request: Request):
        return success(request, {"items": _application(request).list_projects()})

    @app.post(
        "/projects/{project_id}/sources/scan",
        response_model=SuccessEnvelope[SourceScanData],
        status_code=201,
    )
    def scan_project_sources(
        request: Request,
        project_id: str,
        idempotency_key: IdempotencyHeader,
    ):
        result = _application(request).scan_project_sources(
            project_id=project_id,
            idempotency_key=idempotency_key,
        )
        return success(request, result, status_code=201)

    @app.get(
        "/projects/{project_id}/sources",
        response_model=SuccessEnvelope[SourceListData],
    )
    def list_project_sources(
        request: Request,
        project_id: str,
        status: Literal["active", "indexing", "ready", "failed", "archived"] | None = None,
        limit: Annotated[int, Query(ge=1, le=500)] = 100,
        offset: Annotated[int, Query(ge=0)] = 0,
    ):
        items = _application(request).list_sources(
            project_id=project_id,
            status=status,
            limit=limit,
            offset=offset,
        )
        return success(request, {"items": items})

    @app.get(
        "/projects/{project_id}/documents",
        response_model=SuccessEnvelope[DocumentListData],
    )
    def list_project_documents(
        request: Request,
        project_id: str,
        source_id: str | None = None,
        limit: Annotated[int, Query(ge=1, le=500)] = 100,
        offset: Annotated[int, Query(ge=0)] = 0,
    ):
        items = _application(request).list_documents(
            project_id=project_id,
            source_id=source_id,
            limit=limit,
            offset=offset,
        )
        return success(request, {"items": items})

    @app.get(
        "/projects/{project_id}/insights/overview",
        response_model=SuccessEnvelope[ProjectInsightData],
    )
    def get_project_insight_overview(request: Request, project_id: str):
        overview = _application(request).get_project_insight_overview(project_id)
        return success(request, {"overview": overview})

    @app.post(
        "/tasks",
        response_model=SuccessEnvelope[TaskMutationData],
        status_code=201,
    )
    def create_task(
        request: Request,
        body: TaskCreateRequest,
        idempotency_key: IdempotencyHeader,
    ):
        result = _application(request).create_task(
            project_id=body.project_id,
            title=body.title,
            message=body.message,
            idempotency_key=idempotency_key,
        )
        return success(request, result, status_code=201)

    @app.get("/tasks", response_model=SuccessEnvelope[TaskListData])
    def list_tasks(
        request: Request,
        project_id: str | None = None,
        status: str | None = None,
        limit: Annotated[int, Query(ge=1, le=500)] = 100,
        offset: Annotated[int, Query(ge=0)] = 0,
    ):
        items = _application(request).list_tasks(
            project_id=project_id,
            status=status,
            limit=limit,
            offset=offset,
        )
        return success(request, {"items": items})

    @app.get("/tasks/{task_id}", response_model=SuccessEnvelope[TaskData])
    def get_task(request: Request, task_id: str):
        task = _application(request).get_task(task_id)
        return success(request, {"task": task})

    @app.post(
        "/tasks/{task_id}/messages",
        response_model=SuccessEnvelope[TaskMessageMutationData],
        status_code=201,
    )
    def add_task_message(
        request: Request,
        task_id: str,
        body: TaskMessageRequest,
        idempotency_key: IdempotencyHeader,
    ):
        result = _application(request).add_task_message(
            task_id=task_id,
            content=body.content,
            idempotency_key=idempotency_key,
        )
        return success(request, result, status_code=201)

    @app.get(
        "/tasks/{task_id}/messages",
        response_model=SuccessEnvelope[TaskMessageListData],
    )
    def list_task_messages(request: Request, task_id: str):
        return success(
            request,
            {"items": _application(request).list_task_messages(task_id)},
        )

    @app.post(
        "/tasks/{task_id}/runs",
        response_model=SuccessEnvelope[RunMutationData],
        status_code=202,
    )
    def create_run(
        request: Request,
        task_id: str,
        body: RunCreateRequest,
        idempotency_key: IdempotencyHeader,
    ):
        result = _application(request).create_run(
            task_id=task_id,
            input_message_id=body.input_message_id,
            workflow_key=body.workflow_key,
            depth=body.depth,
            idempotency_key=idempotency_key,
        )
        return success(request, result, status_code=202)

    @app.get(
        "/tasks/{task_id}/runs",
        response_model=SuccessEnvelope[RunListData],
    )
    def list_task_runs(
        request: Request,
        task_id: str,
        limit: Annotated[int, Query(ge=1, le=500)] = 100,
        offset: Annotated[int, Query(ge=0)] = 0,
    ):
        items = _application(request).list_task_runs(
            task_id,
            limit=limit,
            offset=offset,
        )
        return success(request, {"items": items})

    @app.get("/runs/{run_id}", response_model=SuccessEnvelope[RunData])
    def get_run(request: Request, run_id: str):
        run = _application(request).get_run(run_id)
        return success(request, {"run": run})

    @app.post(
        "/runs/{run_id}/pause",
        response_model=SuccessEnvelope[RunControlData],
    )
    def pause_run(
        request: Request,
        run_id: str,
        body: RunControlRequest,
        idempotency_key: IdempotencyHeader,
    ):
        return success(
            request,
            _application(request).control_run(
                run_id=run_id,
                action="pause",
                expected_version=body.expected_version,
                idempotency_key=idempotency_key,
            ),
        )

    @app.post(
        "/runs/{run_id}/resume",
        response_model=SuccessEnvelope[RunControlData],
    )
    def resume_run(
        request: Request,
        run_id: str,
        body: RunControlRequest,
        idempotency_key: IdempotencyHeader,
    ):
        return success(
            request,
            _application(request).control_run(
                run_id=run_id,
                action="resume",
                expected_version=body.expected_version,
                idempotency_key=idempotency_key,
            ),
        )

    @app.post(
        "/runs/{run_id}/cancel",
        response_model=SuccessEnvelope[RunControlData],
    )
    def cancel_run(
        request: Request,
        run_id: str,
        body: RunControlRequest,
        idempotency_key: IdempotencyHeader,
    ):
        return success(
            request,
            _application(request).control_run(
                run_id=run_id,
                action="cancel",
                expected_version=body.expected_version,
                idempotency_key=idempotency_key,
            ),
        )

    @app.post(
        "/runs/{run_id}/retry",
        response_model=SuccessEnvelope[RunMutationData],
        status_code=202,
    )
    def retry_run(
        request: Request,
        run_id: str,
        body: RunControlRequest,
        idempotency_key: IdempotencyHeader,
    ):
        return success(
            request,
            _application(request).retry_run(
                run_id=run_id,
                expected_version=body.expected_version,
                idempotency_key=idempotency_key,
            ),
            status_code=202,
        )

    @app.get(
        "/runs/{run_id}/steps",
        response_model=SuccessEnvelope[RunStepsData],
    )
    def list_run_steps(request: Request, run_id: str):
        return success(
            request,
            {"items": _application(request).list_run_steps(run_id)},
        )

    @app.get(
        "/runs/{run_id}/events",
        response_model=None,
        responses={
            200: {
                "description": "Persisted run event stream",
                "content": {"text/event-stream": {}},
            }
        },
    )
    def run_events(
        request: Request,
        run_id: str,
        after_sequence: Annotated[int, Query(ge=0)] = 0,
    ):
        return stream_run_events(
            request,
            store=_application(request),
            run_id=run_id,
            after_sequence=after_sequence,
        )

    @app.get(
        "/approvals",
        response_model=SuccessEnvelope[ApprovalListData],
    )
    def list_approvals(
        request: Request,
        project_id: str | None = None,
        task_id: str | None = None,
        run_id: str | None = None,
        status: str | None = None,
    ):
        return success(
            request,
            {
                "items": _application(request).list_approvals(
                    project_id=project_id,
                    task_id=task_id,
                    run_id=run_id,
                    status=status,
                )
            },
        )

    @app.get(
        "/approvals/{approval_id}",
        response_model=SuccessEnvelope[ApprovalData],
    )
    def get_approval(request: Request, approval_id: str):
        return success(
            request,
            {"approval": _application(request).get_approval(approval_id)},
        )

    @app.post(
        "/approvals/{approval_id}/resolve",
        response_model=SuccessEnvelope[ApprovalMutationData],
    )
    def resolve_approval(
        request: Request,
        approval_id: str,
        body: ApprovalResolveRequest,
        idempotency_key: IdempotencyHeader,
    ):
        return success(
            request,
            _application(request).resolve_approval(
                approval_id=approval_id,
                decision=body.decision,
                expected_version=body.expected_version,
                expected_request_hash=body.expected_request_hash,
                note=body.note,
                idempotency_key=idempotency_key,
            ),
        )

    @app.get(
        "/artifacts",
        response_model=SuccessEnvelope[ArtifactListData],
    )
    def list_artifacts(
        request: Request,
        project_id: str | None = None,
        task_id: str | None = None,
        run_id: str | None = None,
    ):
        return success(
            request,
            {
                "items": _application(request).list_artifacts(
                    project_id=project_id,
                    task_id=task_id,
                    run_id=run_id,
                )
            },
        )

    @app.get(
        "/artifacts/{artifact_id}",
        response_model=SuccessEnvelope[ArtifactData],
    )
    def get_artifact(request: Request, artifact_id: str):
        return success(
            request,
            {"artifact": _application(request).get_artifact(artifact_id)},
        )

    @app.get(
        "/artifacts/{artifact_id}/preview",
        response_model=SuccessEnvelope[ArtifactData],
    )
    def preview_artifact(request: Request, artifact_id: str):
        return success(
            request,
            {"artifact": _application(request).get_artifact(artifact_id)},
        )

    @app.post(
        "/workflows/validate",
        response_model=SuccessEnvelope[WorkflowValidationData],
    )
    def validate_workflow(request: Request, body: WorkflowGraphInput):
        result = _application(request).validate_workflow_graph(body.model_dump())
        return success(request, result)

    @app.post(
        "/workflows",
        response_model=SuccessEnvelope[WorkflowMutationData],
        status_code=201,
    )
    def create_workflow(
        request: Request,
        body: WorkflowCreateRequest,
        idempotency_key: IdempotencyHeader,
    ):
        return success(
            request,
            _application(request).create_workflow(
                workflow_key=body.workflow_key,
                name=body.name,
                description=body.description,
                scope_type=body.scope_type,
                project_id=body.project_id,
                graph=body.graph.model_dump(),
                idempotency_key=idempotency_key,
            ),
            status_code=201,
        )

    @app.get(
        "/workflows",
        response_model=SuccessEnvelope[WorkflowListData],
    )
    def list_workflows(
        request: Request,
        project_id: str | None = None,
        scope_type: str | None = None,
        status: str | None = "active",
    ):
        return success(
            request,
            {
                "items": _application(request).list_workflows(
                    project_id=project_id,
                    scope_type=scope_type,
                    status=status,
                )
            },
        )

    @app.get(
        "/workflows/{workflow_id}",
        response_model=SuccessEnvelope[WorkflowData],
    )
    def get_workflow(request: Request, workflow_id: str):
        return success(
            request,
            _application(request).get_workflow_with_versions(workflow_id),
        )

    @app.post(
        "/workflows/{workflow_id}/drafts",
        response_model=SuccessEnvelope[WorkflowMutationData],
        status_code=201,
    )
    def create_workflow_draft(
        request: Request,
        workflow_id: str,
        body: WorkflowDraftRequest,
        idempotency_key: IdempotencyHeader,
    ):
        return success(
            request,
            _application(request).create_workflow_version(
                workflow_id=workflow_id,
                graph=body.graph.model_dump(),
                expected_version=body.expected_version,
                idempotency_key=idempotency_key,
            ),
            status_code=201,
        )

    @app.post(
        "/workflows/{workflow_id}/publish",
        response_model=SuccessEnvelope[WorkflowMutationData],
    )
    def publish_workflow(
        request: Request,
        workflow_id: str,
        body: WorkflowPublishRequest,
        idempotency_key: IdempotencyHeader,
    ):
        return success(
            request,
            _application(request).publish_workflow(
                workflow_id=workflow_id,
                version_id=body.version_id,
                expected_checksum=body.expected_checksum,
                expected_version=body.expected_version,
                idempotency_key=idempotency_key,
            ),
        )

    @app.post(
        "/workflows/{workflow_id}/archive",
        response_model=SuccessEnvelope[WorkflowArchiveData],
    )
    def archive_workflow(
        request: Request,
        workflow_id: str,
        body: WorkflowArchiveRequest,
        idempotency_key: IdempotencyHeader,
    ):
        return success(
            request,
            _application(request).archive_workflow(
                workflow_id=workflow_id,
                expected_version=body.expected_version,
                idempotency_key=idempotency_key,
            ),
        )

    @app.post(
        "/workflows/{workflow_id}/bindings",
        response_model=SuccessEnvelope[WorkflowBindingMutationData],
    )
    def bind_workflow(
        request: Request,
        workflow_id: str,
        body: WorkflowBindRequest,
        idempotency_key: IdempotencyHeader,
    ):
        return success(
            request,
            _application(request).bind_workflow(
                workflow_id=workflow_id,
                project_id=body.project_id,
                workflow_version_id=body.workflow_version_id,
                expected_workflow_version=body.expected_workflow_version,
                expected_binding_version=body.expected_binding_version,
                idempotency_key=idempotency_key,
            ),
        )

    @app.get(
        "/workflow-bindings",
        response_model=SuccessEnvelope[WorkflowBindingListData],
    )
    def list_workflow_bindings(
        request: Request,
        project_id: str | None = None,
        workflow_id: str | None = None,
        enabled: bool | None = None,
    ):
        return success(
            request,
            {
                "items": _application(request).list_workflow_bindings(
                    project_id=project_id,
                    workflow_id=workflow_id,
                    enabled=enabled,
                )
            },
        )

    def custom_openapi() -> dict[str, Any]:
        if app.openapi_schema is not None:
            return app.openapi_schema
        schema = get_openapi(
            title=app.title,
            version=app.version,
            description=app.description,
            routes=app.routes,
        )
        event_schema = TypeAdapter(AgentEvent).json_schema(
            ref_template="#/components/schemas/{model}"
        )
        definitions = event_schema.pop("$defs", {})
        components = schema.setdefault("components", {}).setdefault("schemas", {})
        components.update(definitions)
        components["AgentEvent"] = event_schema
        schema["paths"]["/runs/{run_id}/events"]["get"]["responses"]["200"][
            "content"
        ]["text/event-stream"]["schema"] = {
            "$ref": "#/components/schemas/AgentEvent"
        }
        app.openapi_schema = schema
        return schema

    app.openapi = custom_openapi
    return app


def _application(request: Request) -> AgentApplication:
    return request.app.state.application


def _public_database_info(value: dict[str, Any]) -> dict[str, Any]:
    """Expose operational facts without leaking the absolute database path."""

    return {
        "data_generation": str(value.get("data_generation") or ""),
        "schema_version": str(value.get("schema_version") or ""),
        "alembic_revision": str(value.get("alembic_revision") or ""),
        "alembic_head": str(value.get("alembic_head") or ""),
        "journal_mode": str(value.get("journal_mode") or ""),
        "foreign_keys": int(value.get("foreign_keys") or 0),
        "busy_timeout_ms": int(value.get("busy_timeout_ms") or 0),
    }


__all__ = ["create_v3_app"]
