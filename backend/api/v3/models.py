from __future__ import annotations

from typing import Annotated, Any, Generic, Literal, TypeVar

from pydantic import BaseModel, ConfigDict, Field, field_validator


T = TypeVar("T")
Depth = Literal["quick", "standard", "deep"]


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class ResponseMeta(StrictModel):
    request_id: str


class SuccessEnvelope(BaseModel, Generic[T]):
    data: T
    meta: ResponseMeta


class ErrorBody(StrictModel):
    code: str
    message: str
    details: dict[str, Any] = Field(default_factory=dict)


class ErrorEnvelope(StrictModel):
    error: ErrorBody
    request_id: str


class ProjectCreateRequest(StrictModel):
    name: str = Field(min_length=1, max_length=120)
    root_path: str = Field(min_length=1, max_length=2_048)


class TaskCreateRequest(StrictModel):
    project_id: str = Field(min_length=1, max_length=64)
    title: str = Field(min_length=1, max_length=200)
    message: str = Field(min_length=1, max_length=100_000)


class TaskMessageRequest(StrictModel):
    content: str = Field(min_length=1, max_length=100_000)


class RunCreateRequest(StrictModel):
    workflow_key: Literal["project.inspect.v1"] = "project.inspect.v1"
    depth: Depth = "standard"
    input_message_id: str = Field(min_length=1, max_length=64)


class RunControlRequest(StrictModel):
    expected_version: int = Field(ge=1)


class ApprovalResolveRequest(StrictModel):
    decision: Literal["approved", "rejected"]
    expected_version: int = Field(ge=1)
    expected_request_hash: str = Field(min_length=64, max_length=128)
    note: str = Field(default="", max_length=2_000)


class ArtifactExportRequest(StrictModel):
    target_path: str = Field(min_length=1, max_length=2_048)
    expected_version: int = Field(ge=1)


class WorkflowNodeInput(StrictModel):
    id: str = Field(min_length=1, max_length=100)
    type: str = Field(min_length=1, max_length=100)
    config: dict[str, Any] = Field(default_factory=dict)
    position: dict[str, float] = Field(default_factory=dict)


class WorkflowEdgeInput(StrictModel):
    id: str = Field(min_length=1, max_length=100)
    source: str = Field(min_length=1, max_length=100)
    source_port: str = Field(min_length=1, max_length=100)
    target: str = Field(min_length=1, max_length=100)
    target_port: str = Field(min_length=1, max_length=100)


class WorkflowGraphInput(StrictModel):
    nodes: list[WorkflowNodeInput] = Field(min_length=1, max_length=200)
    edges: list[WorkflowEdgeInput] = Field(default_factory=list, max_length=500)

    @field_validator("nodes")
    @classmethod
    def unique_node_ids(cls, nodes: list[WorkflowNodeInput]) -> list[WorkflowNodeInput]:
        ids = [node.id for node in nodes]
        if len(ids) != len(set(ids)):
            raise ValueError("workflow node ids must be unique")
        return nodes


class WorkflowCreateRequest(StrictModel):
    workflow_key: str = Field(min_length=1, max_length=200)
    name: str = Field(min_length=1, max_length=120)
    description: str = Field(default="", max_length=2_000)
    scope_type: Literal["global", "project"] = "global"
    project_id: str | None = Field(default=None, max_length=64)
    graph: WorkflowGraphInput


class WorkflowDraftRequest(StrictModel):
    graph: WorkflowGraphInput
    expected_version: int = Field(ge=1)


class WorkflowPublishRequest(StrictModel):
    version_id: str = Field(min_length=1, max_length=64)
    expected_checksum: str = Field(min_length=64, max_length=128)
    expected_version: int = Field(ge=1)


class WorkflowBindRequest(StrictModel):
    project_id: str = Field(min_length=1, max_length=64)
    workflow_version_id: str = Field(min_length=1, max_length=64)
    expected_workflow_version: int = Field(ge=1)
    expected_binding_version: int = Field(default=0, ge=0)


class WorkflowArchiveRequest(StrictModel):
    expected_version: int = Field(ge=1)


class HealthData(StrictModel):
    status: Literal["ok", "starting", "error"]
    data_generation: Literal["v3"]
    schema_revision: str
    executor_running: bool


class StoragePreflightRequest(StrictModel):
    target_path: str = Field(min_length=1, max_length=2_048)


class StoragePreflightCheck(StrictModel):
    code: Literal[
        "outside_current_v3",
        "outside_legacy_v2",
        "target_is_directory",
        "target_is_not_symlink",
        "target_is_empty",
        "parent_is_writable",
        "source_is_readable",
        "sufficient_free_space",
    ]
    passed: bool
    message: str


class StoragePreflightData(StrictModel):
    ready: bool
    target_path: str
    existing_parent: str
    target_exists: bool
    target_empty: bool
    source_bytes: int = Field(ge=0)
    required_bytes: int = Field(ge=0)
    available_bytes: int = Field(ge=0)
    checks: list[StoragePreflightCheck]


class BackupResource(StrictModel):
    backup_id: str
    created_at: str
    data_generation: Literal["v3"]
    schema_revision: str
    database_bytes: int = Field(ge=0)
    database_sha256: str = Field(min_length=64, max_length=64)


class BackupMutationData(StrictModel):
    backup: BackupResource
    replayed: bool
    pruned_backup_ids: list[str]


class RestoreRequest(StrictModel):
    expected_database_sha256: str = Field(
        min_length=64,
        max_length=64,
        pattern=r"^[0-9a-f]{64}$",
    )


class RestoreDatabaseInfo(StrictModel):
    data_generation: Literal["v3"]
    schema_version: str
    alembic_revision: str
    alembic_head: str
    journal_mode: str
    foreign_keys: int
    busy_timeout_ms: int = Field(ge=0)


class RestoreMutationData(StrictModel):
    backup: BackupResource
    database_info: RestoreDatabaseInfo
    restored: bool
    replayed: bool


class ProjectResource(StrictModel):
    id: str
    name: str
    root_path: str
    status: Literal["active", "archived"]
    version: int
    created_at: str
    updated_at: str


class ProjectMutationData(StrictModel):
    project: ProjectResource
    replayed: bool


class ProjectListData(StrictModel):
    items: list[ProjectResource]


class SourceResource(StrictModel):
    id: str
    project_id: str
    source_type: Literal["project_root"]
    name: str
    status: Literal["active", "indexing", "ready", "failed", "archived"]
    document_count: int = Field(ge=0)
    indexed_at: str


class SourceScanSummary(StrictModel):
    visited_entries: int = Field(ge=0)
    supported_files: int = Field(ge=0)
    skipped_unsupported: int = Field(ge=0)
    skipped_symlinks: int = Field(ge=0)
    skipped_too_large: int = Field(ge=0)
    read_failures: int = Field(ge=0)
    total_bytes: int = Field(ge=0)
    truncated: int = Field(ge=0, le=1)
    inserted: int = Field(ge=0)
    updated: int = Field(ge=0)
    deleted: int = Field(ge=0)
    document_count: int = Field(ge=0)


class SourceScanData(StrictModel):
    source: SourceResource
    summary: SourceScanSummary
    replayed: bool


class SourceListData(StrictModel):
    items: list[SourceResource]


class DocumentResource(StrictModel):
    id: str
    project_id: str
    source_id: str | None = None
    relative_path: str
    mime_type: str
    size_bytes: int = Field(ge=0)
    checksum: str = Field(min_length=64, max_length=128)
    version: int = Field(ge=1)
    updated_at: str


class DocumentListData(StrictModel):
    items: list[DocumentResource]


class ProjectInsightSnapshot(StrictModel):
    source_count: int = Field(ge=0)
    document_count: int = Field(ge=0)
    total_bytes: int = Field(ge=0)
    fingerprint: str = Field(min_length=64, max_length=64)


class ProjectInsightFileType(StrictModel):
    extension: str
    count: int = Field(ge=1)


class ProjectInsightEvidence(StrictModel):
    document_id: str
    source_id: str | None = None
    relative_path: str
    checksum: str = Field(min_length=64, max_length=128)


class ProjectInsightOverview(StrictModel):
    project_id: str
    status: Literal["ready", "source_required"]
    source_snapshot: ProjectInsightSnapshot
    file_types: list[ProjectInsightFileType]
    manifest_paths: list[str]
    evidence: list[ProjectInsightEvidence]


class ProjectInsightData(StrictModel):
    overview: ProjectInsightOverview


class TaskResource(StrictModel):
    id: str
    project_id: str
    title: str
    prompt: str
    depth: Depth
    status: Literal[
        "queued",
        "running",
        "waiting_approval",
        "paused",
        "completed",
        "failed",
        "cancelled",
    ]
    version: int
    created_at: str
    updated_at: str


class TaskData(StrictModel):
    task: TaskResource


class TaskListData(StrictModel):
    items: list[TaskResource]


class TaskMessageResource(StrictModel):
    id: str
    task_id: str
    run_id: str | None = None
    role: Literal["user", "agent", "system", "tool"]
    message_type: str
    content: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: str


class TaskMutationData(StrictModel):
    task: TaskResource
    initial_message: TaskMessageResource
    replayed: bool


class TaskMessageMutationData(StrictModel):
    message: TaskMessageResource
    replayed: bool


class TaskMessageListData(StrictModel):
    items: list[TaskMessageResource]


class RunResource(StrictModel):
    id: str
    task_id: str
    project_id: str | None = None
    workflow_version_id: str | None = None
    workflow_key: str
    workflow_version: int
    workflow_checksum: str
    depth: Depth
    status: Literal[
        "queued",
        "running",
        "waiting_approval",
        "paused",
        "recovering",
        "completed",
        "failed",
        "cancelled",
    ]
    priority: int
    attempt_no: int
    retry_of_run_id: str | None = None
    version: int
    queued_at: str
    started_at: str | None = None
    finished_at: str | None = None
    paused_at: str | None = None
    cancel_requested_at: str | None = None
    lease_owner: str = ""
    lease_expires_at: str | None = None
    error_code: str = ""
    error_message: str = ""
    result: dict[str, Any] = Field(default_factory=dict)
    created_at: str
    updated_at: str


class StepResource(StrictModel):
    id: str
    run_id: str
    step_key: str
    node_type: str
    effect_kind: Literal[
        "none", "read", "analysis", "project_write", "external_write"
    ]
    ordinal: int
    status: Literal[
        "pending",
        "queued",
        "running",
        "waiting_approval",
        "succeeded",
        "failed",
        "skipped",
        "cancelled",
        "recovery_required",
    ]
    input: dict[str, Any] = Field(default_factory=dict)
    output: dict[str, Any] = Field(default_factory=dict)
    error: dict[str, Any] = Field(default_factory=dict)
    attempt_count: int
    max_attempts: int
    version: int
    started_at: str | None = None
    finished_at: str | None = None
    created_at: str
    updated_at: str


class EventResource(StrictModel):
    id: str
    run_id: str
    step_id: str | None = None
    sequence: int
    event_type: str
    event_schema_version: int
    payload: dict[str, Any] = Field(default_factory=dict)
    created_at: str


class RunMutationData(StrictModel):
    run: RunResource
    steps: list[StepResource]
    event: EventResource
    project_id: str
    replayed: bool


class RunControlData(StrictModel):
    run: RunResource
    event: EventResource
    replayed: bool


class RunData(StrictModel):
    run: RunResource


class RunListData(StrictModel):
    items: list[RunResource]


class RunStepsData(StrictModel):
    items: list[StepResource]


class WorkflowValidationData(StrictModel):
    valid: bool
    errors: list[dict[str, Any]] = Field(default_factory=list)


class WorkflowResource(StrictModel):
    id: str
    scope_type: Literal["global", "project"]
    project_id: str | None = None
    workflow_key: str
    name: str
    description: str
    status: Literal["active", "archived"]
    current_published_version_id: str | None = None
    version: int
    created_at: str
    updated_at: str


class WorkflowVersionResource(StrictModel):
    id: str
    workflow_id: str
    version_number: int
    status: Literal["draft", "published", "archived"]
    dag: dict[str, Any]
    input_schema: dict[str, Any]
    checksum: str
    created_at: str
    published_at: str | None = None


class WorkflowMutationData(StrictModel):
    workflow: WorkflowResource
    version: WorkflowVersionResource
    replayed: bool


class WorkflowData(StrictModel):
    workflow: WorkflowResource
    versions: list[WorkflowVersionResource]


class WorkflowListData(StrictModel):
    items: list[WorkflowResource]


class WorkflowArchiveData(StrictModel):
    workflow: WorkflowResource
    replayed: bool


class WorkflowBindingResource(StrictModel):
    id: str
    project_id: str
    workflow_id: str
    workflow_version_id: str
    parameters: dict[str, Any]
    enabled: bool
    version: int
    created_at: str
    updated_at: str


class WorkflowBindingMutationData(StrictModel):
    binding: WorkflowBindingResource
    replayed: bool


class WorkflowBindingListData(StrictModel):
    items: list[WorkflowBindingResource]


class ApprovalResource(StrictModel):
    id: str
    project_id: str
    task_id: str
    run_id: str
    step_id: str
    action_type: str
    target: str
    payload: dict[str, Any]
    request_hash: str
    resource_version: str
    status: Literal["pending", "approved", "rejected", "expired"]
    version: int
    decided_by: str
    decision_note: str
    created_at: str
    expires_at: str | None = None
    resolved_at: str | None = None


class ApprovalData(StrictModel):
    approval: ApprovalResource


class ApprovalMutationData(StrictModel):
    approval: ApprovalResource
    event: EventResource
    replayed: bool


class ApprovalListData(StrictModel):
    items: list[ApprovalResource]


class ArtifactResource(StrictModel):
    id: str
    project_id: str
    task_id: str
    run_id: str
    step_id: str | None = None
    artifact_type: str
    name: str
    status: Literal["draft", "ready", "exported", "failed"]
    content: str
    content_ref: str
    checksum: str
    metadata: dict[str, Any]
    version: int
    created_at: str
    updated_at: str
    exported_at: str | None = None


class ArtifactData(StrictModel):
    artifact: ArtifactResource


class ArtifactListData(StrictModel):
    items: list[ArtifactResource]


class AgentEventBase(StrictModel):
    sequence: int = Field(ge=1)
    run_id: str
    step_id: str | None = None
    event_schema_version: int = Field(default=1, ge=1)
    payload: dict[str, Any] = Field(default_factory=dict)
    created_at: str


class RunLifecycleEvent(AgentEventBase):
    event_type: Literal[
        "run.queued",
        "run.started",
        "run.resumed",
        "run.completed",
        "run.failed",
        "run.recovery_required",
        "run.requeued",
        "run.paused",
        "run.cancelled",
    ]


class StepLifecycleEvent(AgentEventBase):
    event_type: Literal[
        "step.started",
        "step.succeeded",
        "step.queued",
        "step.retry_scheduled",
        "step.waiting_approval",
        "step.failed",
        "step.cancelled",
        "step.recovery_required",
    ]


class ApprovalLifecycleEvent(AgentEventBase):
    event_type: Literal[
        "approval.requested",
        "approval.approved",
        "approval.rejected",
        "approval.expired",
    ]


class ArtifactLifecycleEvent(AgentEventBase):
    event_type: Literal["artifact.created"]


class ToolLifecycleEvent(AgentEventBase):
    event_type: Literal["tool.output"]


class AssistantMessageStartedPayload(StrictModel):
    message_id: str
    message_type: str
    format: Literal["markdown", "text"]


class AssistantMessageDeltaPayload(StrictModel):
    message_id: str
    chunk_index: int = Field(ge=0)
    text: str = Field(min_length=1)


class AssistantMessageCompletedPayload(StrictModel):
    message_id: str
    chunk_count: int = Field(ge=0)
    char_count: int = Field(ge=0)
    content_hash: str = Field(min_length=64, max_length=128)


class AssistantMessageInterruptedPayload(StrictModel):
    message_id: str
    reason: str
    recoverable: bool


class AssistantMessageStartedEvent(AgentEventBase):
    event_type: Literal["assistant.message.started"]
    payload: AssistantMessageStartedPayload


class AssistantMessageDeltaEvent(AgentEventBase):
    event_type: Literal["assistant.message.delta"]
    payload: AssistantMessageDeltaPayload


class AssistantMessageCompletedEvent(AgentEventBase):
    event_type: Literal["assistant.message.completed"]
    payload: AssistantMessageCompletedPayload


class AssistantMessageInterruptedEvent(AgentEventBase):
    event_type: Literal["assistant.message.interrupted"]
    payload: AssistantMessageInterruptedPayload


AgentEvent = Annotated[
    RunLifecycleEvent
    | StepLifecycleEvent
    | ApprovalLifecycleEvent
    | ArtifactLifecycleEvent
    | ToolLifecycleEvent
    | AssistantMessageStartedEvent
    | AssistantMessageDeltaEvent
    | AssistantMessageCompletedEvent
    | AssistantMessageInterruptedEvent,
    Field(discriminator="event_type"),
]
