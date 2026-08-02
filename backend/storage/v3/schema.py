"""SQLAlchemy Core metadata for the v3 data generation."""
from __future__ import annotations

from sqlalchemy import (
    CheckConstraint,
    Column,
    Float,
    ForeignKey,
    Index,
    Integer,
    MetaData,
    String,
    Table,
    Text,
    UniqueConstraint,
    text,
)


metadata = MetaData()

TASK_STATUSES = (
    "queued",
    "running",
    "waiting_approval",
    "paused",
    "completed",
    "failed",
    "cancelled",
)
RUN_STATUSES = (*TASK_STATUSES[:4], "recovering", *TASK_STATUSES[4:])
STEP_STATUSES = (
    "pending",
    "queued",
    "running",
    "waiting_approval",
    "succeeded",
    "failed",
    "skipped",
    "cancelled",
    "recovery_required",
)
APPROVAL_STATUSES = ("pending", "approved", "rejected", "expired")
ARTIFACT_STATUSES = ("draft", "ready", "exported", "failed")
DEPTH_VALUES = ("quick", "standard", "deep")
EFFECT_KINDS = (
    "none",
    "read",
    "analysis",
    "project_write",
    "external_write",
)


def _quoted(values: tuple[str, ...]) -> str:
    return ", ".join(f"'{value}'" for value in values)


app_metadata = Table(
    "app_metadata",
    metadata,
    Column("key", String(100), primary_key=True),
    Column("value", Text, nullable=False),
    Column("updated_at", String(35), nullable=False),
)

projects = Table(
    "projects",
    metadata,
    Column("id", String(36), primary_key=True),
    Column("name", String(200), nullable=False),
    Column("root_path", Text, nullable=False, unique=True),
    Column("status", String(20), nullable=False, server_default="active"),
    Column("version", Integer, nullable=False, server_default="1"),
    Column("created_at", String(35), nullable=False),
    Column("updated_at", String(35), nullable=False),
    CheckConstraint("status IN ('active', 'archived')", name="ck_projects_status"),
    CheckConstraint("version > 0", name="ck_projects_version"),
)

sources = Table(
    "sources",
    metadata,
    Column("id", String(36), primary_key=True),
    Column("project_id", String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
    Column("source_type", String(30), nullable=False),
    Column("name", String(200), nullable=False),
    Column("locator", Text, nullable=False),
    Column("status", String(20), nullable=False, server_default="active"),
    Column("config_json", Text, nullable=False, server_default="{}"),
    Column("created_at", String(35), nullable=False),
    Column("updated_at", String(35), nullable=False),
    UniqueConstraint("project_id", "locator", name="uq_sources_project_locator"),
    CheckConstraint(
        "status IN ('active', 'indexing', 'ready', 'failed', 'archived')",
        name="ck_sources_status",
    ),
)
Index("ix_sources_project_status", sources.c.project_id, sources.c.status)

documents = Table(
    "documents",
    metadata,
    Column("id", String(36), primary_key=True),
    Column("project_id", String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
    Column("source_id", String(36), ForeignKey("sources.id", ondelete="SET NULL")),
    Column("relative_path", Text, nullable=False),
    Column("source_path", Text, nullable=False, server_default=""),
    Column("content", Text, nullable=False, server_default=""),
    Column("checksum", String(128), nullable=False),
    Column("mime_type", String(120), nullable=False, server_default="text/plain"),
    Column("size_bytes", Integer, nullable=False, server_default="0"),
    Column("version", Integer, nullable=False, server_default="1"),
    Column("created_at", String(35), nullable=False),
    Column("updated_at", String(35), nullable=False),
    UniqueConstraint("project_id", "relative_path", name="uq_documents_project_path"),
    CheckConstraint("size_bytes >= 0", name="ck_documents_size"),
    CheckConstraint("version > 0", name="ck_documents_version"),
)
Index("ix_documents_project_source", documents.c.project_id, documents.c.source_id)

document_chunks = Table(
    "document_chunks",
    metadata,
    Column("id", String(36), primary_key=True),
    Column("document_id", String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False),
    Column("project_id", String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
    Column("chunk_index", Integer, nullable=False),
    Column("content", Text, nullable=False),
    Column("token_count", Integer, nullable=False, server_default="0"),
    Column("content_hash", String(128), nullable=False),
    Column("metadata_json", Text, nullable=False, server_default="{}"),
    Column("created_at", String(35), nullable=False),
    UniqueConstraint("document_id", "chunk_index", name="uq_chunks_document_index"),
    CheckConstraint("chunk_index >= 0", name="ck_chunks_index"),
    CheckConstraint("token_count >= 0", name="ck_chunks_tokens"),
)
Index("ix_chunks_project", document_chunks.c.project_id)

chunk_vectors = Table(
    "chunk_vectors",
    metadata,
    Column("chunk_id", String(36), ForeignKey("document_chunks.id", ondelete="CASCADE"), primary_key=True),
    Column("project_id", String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
    Column("provider", String(80), nullable=False),
    Column("model", String(200), nullable=False),
    Column("dimension", Integer, nullable=False),
    Column("vector_json", Text, nullable=False),
    Column("updated_at", String(35), nullable=False),
    CheckConstraint("dimension > 0", name="ck_vectors_dimension"),
)
Index("ix_vectors_project_model", chunk_vectors.c.project_id, chunk_vectors.c.provider, chunk_vectors.c.model)

model_profiles = Table(
    "model_profiles",
    metadata,
    Column("id", String(36), primary_key=True),
    Column("name", String(200), nullable=False, unique=True),
    Column("provider", String(80), nullable=False),
    Column("api_base", Text, nullable=False, server_default=""),
    Column("model", String(200), nullable=False),
    Column("temperature", Float, nullable=False, server_default="0.7"),
    Column("max_tokens", Integer, nullable=False, server_default="2048"),
    Column("api_key_ref", Text, nullable=False, server_default=""),
    Column("is_default", Integer, nullable=False, server_default="0"),
    Column("status", String(20), nullable=False, server_default="active"),
    Column("created_at", String(35), nullable=False),
    Column("updated_at", String(35), nullable=False),
    CheckConstraint("temperature >= 0", name="ck_model_profiles_temperature"),
    CheckConstraint("max_tokens > 0", name="ck_model_profiles_max_tokens"),
    CheckConstraint("is_default IN (0, 1)", name="ck_model_profiles_default"),
    CheckConstraint("status IN ('active', 'disabled')", name="ck_model_profiles_status"),
)
Index(
    "uq_model_profiles_single_default",
    model_profiles.c.is_default,
    unique=True,
    sqlite_where=text("is_default = 1"),
)

settings = Table(
    "settings",
    metadata,
    Column("id", String(36), primary_key=True),
    Column("scope_type", String(20), nullable=False),
    Column("scope_id", String(36), nullable=False, server_default=""),
    Column("key", String(200), nullable=False),
    Column("value_json", Text, nullable=False),
    Column("version", Integer, nullable=False, server_default="1"),
    Column("updated_at", String(35), nullable=False),
    UniqueConstraint("scope_type", "scope_id", "key", name="uq_settings_scope_key"),
    CheckConstraint("scope_type IN ('global', 'project')", name="ck_settings_scope"),
    CheckConstraint("version > 0", name="ck_settings_version"),
)

integrations = Table(
    "integrations",
    metadata,
    Column("id", String(36), primary_key=True),
    Column("project_id", String(36), ForeignKey("projects.id", ondelete="CASCADE")),
    Column("integration_type", String(80), nullable=False),
    Column("name", String(200), nullable=False),
    Column("status", String(20), nullable=False, server_default="disconnected"),
    Column("config_json", Text, nullable=False, server_default="{}"),
    Column("secret_refs_json", Text, nullable=False, server_default="{}"),
    Column("created_at", String(35), nullable=False),
    Column("updated_at", String(35), nullable=False),
    UniqueConstraint("project_id", "integration_type", "name", name="uq_integrations_project_type_name"),
    CheckConstraint(
        "status IN ('disconnected', 'connected', 'error', 'disabled')",
        name="ck_integrations_status",
    ),
)

workflow_definitions = Table(
    "workflow_definitions",
    metadata,
    Column("id", String(36), primary_key=True),
    Column("scope_type", String(20), nullable=False),
    Column("project_id", String(36), ForeignKey("projects.id", ondelete="CASCADE")),
    Column("workflow_key", String(200), nullable=False),
    Column("name", String(200), nullable=False),
    Column("description", Text, nullable=False, server_default=""),
    Column("status", String(20), nullable=False, server_default="active"),
    Column("current_published_version_id", String(36)),
    Column("version", Integer, nullable=False, server_default="1"),
    Column("created_at", String(35), nullable=False),
    Column("updated_at", String(35), nullable=False),
    CheckConstraint("scope_type IN ('global', 'project')", name="ck_workflows_scope"),
    CheckConstraint(
        "(scope_type = 'global' AND project_id IS NULL) OR "
        "(scope_type = 'project' AND project_id IS NOT NULL)",
        name="ck_workflows_scope_project",
    ),
    CheckConstraint("status IN ('active', 'archived')", name="ck_workflows_status"),
    CheckConstraint("version > 0", name="ck_workflows_version"),
)
Index("ix_workflows_project_status", workflow_definitions.c.project_id, workflow_definitions.c.status)
Index(
    "uq_workflows_global_key",
    workflow_definitions.c.workflow_key,
    unique=True,
    sqlite_where=text("scope_type = 'global'"),
)
Index(
    "uq_workflows_project_key",
    workflow_definitions.c.project_id,
    workflow_definitions.c.workflow_key,
    unique=True,
    sqlite_where=text("scope_type = 'project'"),
)

workflow_versions = Table(
    "workflow_versions",
    metadata,
    Column("id", String(36), primary_key=True),
    Column("workflow_id", String(36), ForeignKey("workflow_definitions.id", ondelete="CASCADE"), nullable=False),
    Column("version_number", Integer, nullable=False),
    Column("status", String(20), nullable=False, server_default="draft"),
    Column("dag_json", Text, nullable=False),
    Column("input_schema_json", Text, nullable=False, server_default="{}"),
    Column("checksum", String(128), nullable=False),
    Column("created_at", String(35), nullable=False),
    Column("published_at", String(35)),
    UniqueConstraint("workflow_id", "version_number", name="uq_workflow_versions_number"),
    UniqueConstraint("workflow_id", "checksum", name="uq_workflow_versions_checksum"),
    CheckConstraint("version_number > 0", name="ck_workflow_versions_number"),
    CheckConstraint("status IN ('draft', 'published', 'archived')", name="ck_workflow_versions_status"),
)

workflow_bindings = Table(
    "workflow_bindings",
    metadata,
    Column("id", String(36), primary_key=True),
    Column("project_id", String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
    Column("workflow_id", String(36), ForeignKey("workflow_definitions.id", ondelete="CASCADE"), nullable=False),
    Column("workflow_version_id", String(36), ForeignKey("workflow_versions.id", ondelete="RESTRICT"), nullable=False),
    Column("parameters_json", Text, nullable=False, server_default="{}"),
    Column("enabled", Integer, nullable=False, server_default="1"),
    Column("version", Integer, nullable=False, server_default="1"),
    Column("created_at", String(35), nullable=False),
    Column("updated_at", String(35), nullable=False),
    UniqueConstraint("project_id", "workflow_id", name="uq_workflow_bindings_project_workflow"),
    CheckConstraint("enabled IN (0, 1)", name="ck_workflow_bindings_enabled"),
    CheckConstraint("version > 0", name="ck_workflow_bindings_version"),
)

agent_tasks = Table(
    "agent_tasks",
    metadata,
    Column("id", String(36), primary_key=True),
    Column("project_id", String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
    Column("title", String(300), nullable=False),
    Column("prompt", Text, nullable=False),
    Column("depth", String(20), nullable=False, server_default="standard"),
    Column("status", String(30), nullable=False, server_default="queued"),
    Column("version", Integer, nullable=False, server_default="1"),
    Column("created_at", String(35), nullable=False),
    Column("updated_at", String(35), nullable=False),
    CheckConstraint(f"depth IN ({_quoted(DEPTH_VALUES)})", name="ck_agent_tasks_depth"),
    CheckConstraint(f"status IN ({_quoted(TASK_STATUSES)})", name="ck_agent_tasks_status"),
    CheckConstraint("version > 0", name="ck_agent_tasks_version"),
)
Index("ix_agent_tasks_project_updated", agent_tasks.c.project_id, agent_tasks.c.updated_at)
Index("ix_agent_tasks_status_updated", agent_tasks.c.status, agent_tasks.c.updated_at)

agent_task_messages = Table(
    "agent_task_messages",
    metadata,
    Column("id", String(36), primary_key=True),
    Column("task_id", String(36), ForeignKey("agent_tasks.id", ondelete="CASCADE"), nullable=False),
    Column("run_id", String(36), ForeignKey("agent_runs.id", ondelete="SET NULL")),
    Column("role", String(20), nullable=False),
    Column("message_type", String(40), nullable=False, server_default="message"),
    Column("content", Text, nullable=False),
    Column("metadata_json", Text, nullable=False, server_default="{}"),
    Column("created_at", String(35), nullable=False),
    CheckConstraint("role IN ('user', 'agent', 'system', 'tool')", name="ck_agent_messages_role"),
)
Index("ix_agent_messages_task_created", agent_task_messages.c.task_id, agent_task_messages.c.created_at)

agent_runs = Table(
    "agent_runs",
    metadata,
    Column("id", String(36), primary_key=True),
    Column("task_id", String(36), ForeignKey("agent_tasks.id", ondelete="CASCADE"), nullable=False),
    Column("workflow_version_id", String(36), ForeignKey("workflow_versions.id", ondelete="SET NULL")),
    Column("workflow_key", String(200), nullable=False),
    Column("workflow_version", Integer, nullable=False),
    Column("workflow_checksum", String(128), nullable=False),
    Column("depth", String(20), nullable=False),
    Column("status", String(30), nullable=False, server_default="queued"),
    Column("priority", Integer, nullable=False, server_default="0"),
    Column("attempt_no", Integer, nullable=False, server_default="1"),
    Column("retry_of_run_id", String(36), ForeignKey("agent_runs.id", ondelete="SET NULL")),
    Column("version", Integer, nullable=False, server_default="1"),
    Column("queued_at", String(35), nullable=False),
    Column("started_at", String(35)),
    Column("finished_at", String(35)),
    Column("paused_at", String(35)),
    Column("cancel_requested_at", String(35)),
    Column("lease_owner", String(100), nullable=False, server_default=""),
    Column("lease_expires_at", String(35)),
    Column("error_code", String(100), nullable=False, server_default=""),
    Column("error_message", Text, nullable=False, server_default=""),
    Column("result_json", Text, nullable=False, server_default="{}"),
    Column("created_at", String(35), nullable=False),
    Column("updated_at", String(35), nullable=False),
    CheckConstraint(f"depth IN ({_quoted(DEPTH_VALUES)})", name="ck_agent_runs_depth"),
    CheckConstraint(f"status IN ({_quoted(RUN_STATUSES)})", name="ck_agent_runs_status"),
    CheckConstraint("workflow_version > 0", name="ck_agent_runs_workflow_version"),
    CheckConstraint("attempt_no > 0", name="ck_agent_runs_attempt"),
    CheckConstraint("version > 0", name="ck_agent_runs_version"),
)
Index("ix_agent_runs_queue", agent_runs.c.status, agent_runs.c.priority, agent_runs.c.queued_at)
Index("ix_agent_runs_task_created", agent_runs.c.task_id, agent_runs.c.created_at)
Index("ix_agent_runs_lease", agent_runs.c.status, agent_runs.c.lease_expires_at)

agent_steps = Table(
    "agent_steps",
    metadata,
    Column("id", String(36), primary_key=True),
    Column("run_id", String(36), ForeignKey("agent_runs.id", ondelete="CASCADE"), nullable=False),
    Column("step_key", String(200), nullable=False),
    Column("node_type", String(100), nullable=False),
    Column("effect_kind", String(30), nullable=False, server_default="read"),
    Column("ordinal", Integer, nullable=False),
    Column("status", String(30), nullable=False, server_default="pending"),
    Column("input_json", Text, nullable=False, server_default="{}"),
    Column("output_json", Text, nullable=False, server_default="{}"),
    Column("error_json", Text, nullable=False, server_default="{}"),
    Column("attempt_count", Integer, nullable=False, server_default="0"),
    Column("max_attempts", Integer, nullable=False, server_default="3"),
    Column("version", Integer, nullable=False, server_default="1"),
    Column("started_at", String(35)),
    Column("finished_at", String(35)),
    Column("created_at", String(35), nullable=False),
    Column("updated_at", String(35), nullable=False),
    UniqueConstraint("run_id", "step_key", name="uq_agent_steps_run_key"),
    UniqueConstraint("run_id", "ordinal", name="uq_agent_steps_run_ordinal"),
    CheckConstraint(f"effect_kind IN ({_quoted(EFFECT_KINDS)})", name="ck_agent_steps_effect"),
    CheckConstraint(f"status IN ({_quoted(STEP_STATUSES)})", name="ck_agent_steps_status"),
    CheckConstraint("ordinal >= 0", name="ck_agent_steps_ordinal"),
    CheckConstraint("attempt_count >= 0", name="ck_agent_steps_attempt_count"),
    CheckConstraint("max_attempts > 0", name="ck_agent_steps_max_attempts"),
    CheckConstraint("version > 0", name="ck_agent_steps_version"),
)
Index("ix_agent_steps_run_status", agent_steps.c.run_id, agent_steps.c.status, agent_steps.c.ordinal)

agent_step_attempts = Table(
    "agent_step_attempts",
    metadata,
    Column("id", String(36), primary_key=True),
    Column("run_id", String(36), ForeignKey("agent_runs.id", ondelete="CASCADE"), nullable=False),
    Column("step_id", String(36), ForeignKey("agent_steps.id", ondelete="CASCADE"), nullable=False),
    Column("attempt_no", Integer, nullable=False),
    Column("status", String(20), nullable=False),
    Column("worker_id", String(100), nullable=False, server_default=""),
    Column("lease_owner", String(100), nullable=False, server_default=""),
    Column("lease_expires_at", String(35)),
    Column("input_hash", String(128), nullable=False, server_default=""),
    Column("output_json", Text, nullable=False, server_default="{}"),
    Column("error_code", String(100), nullable=False, server_default=""),
    Column("error_message", Text, nullable=False, server_default=""),
    Column("started_at", String(35), nullable=False),
    Column("finished_at", String(35)),
    Column("created_at", String(35), nullable=False),
    UniqueConstraint("step_id", "attempt_no", name="uq_agent_attempts_step_number"),
    CheckConstraint("attempt_no > 0", name="ck_agent_attempts_number"),
    CheckConstraint(
        "status IN ('running', 'succeeded', 'failed', 'cancelled')",
        name="ck_agent_attempts_status",
    ),
)
Index("ix_agent_attempts_run_step", agent_step_attempts.c.run_id, agent_step_attempts.c.step_id)

agent_events = Table(
    "agent_events",
    metadata,
    Column("id", String(36), primary_key=True),
    Column("run_id", String(36), ForeignKey("agent_runs.id", ondelete="CASCADE"), nullable=False),
    Column("step_id", String(36), ForeignKey("agent_steps.id", ondelete="SET NULL")),
    Column("sequence", Integer, nullable=False),
    Column("event_type", String(100), nullable=False),
    Column("event_schema_version", Integer, nullable=False, server_default="1"),
    Column("payload_json", Text, nullable=False, server_default="{}"),
    Column("created_at", String(35), nullable=False),
    UniqueConstraint("run_id", "sequence", name="uq_agent_events_run_sequence"),
    CheckConstraint("sequence > 0", name="ck_agent_events_sequence"),
    CheckConstraint("event_schema_version > 0", name="ck_agent_events_schema_version"),
)
Index("ix_agent_events_run_sequence", agent_events.c.run_id, agent_events.c.sequence)

agent_approvals = Table(
    "agent_approvals",
    metadata,
    Column("id", String(36), primary_key=True),
    Column("project_id", String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
    Column("task_id", String(36), ForeignKey("agent_tasks.id", ondelete="CASCADE"), nullable=False),
    Column("run_id", String(36), ForeignKey("agent_runs.id", ondelete="CASCADE"), nullable=False),
    Column("step_id", String(36), ForeignKey("agent_steps.id", ondelete="CASCADE"), nullable=False),
    Column("action_type", String(100), nullable=False),
    Column("target", Text, nullable=False),
    Column("payload_json", Text, nullable=False),
    Column("request_hash", String(128), nullable=False),
    Column("resource_version", String(200), nullable=False, server_default=""),
    Column("status", String(20), nullable=False, server_default="pending"),
    Column("version", Integer, nullable=False, server_default="1"),
    Column("decided_by", String(100), nullable=False, server_default=""),
    Column("decision_note", Text, nullable=False, server_default=""),
    Column("created_at", String(35), nullable=False),
    Column("expires_at", String(35)),
    Column("resolved_at", String(35)),
    CheckConstraint(f"status IN ({_quoted(APPROVAL_STATUSES)})", name="ck_agent_approvals_status"),
    CheckConstraint("version > 0", name="ck_agent_approvals_version"),
)
Index("ix_agent_approvals_run_status", agent_approvals.c.run_id, agent_approvals.c.status)

agent_artifacts = Table(
    "agent_artifacts",
    metadata,
    Column("id", String(36), primary_key=True),
    Column("project_id", String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
    Column("task_id", String(36), ForeignKey("agent_tasks.id", ondelete="CASCADE"), nullable=False),
    Column("run_id", String(36), ForeignKey("agent_runs.id", ondelete="CASCADE"), nullable=False),
    Column("step_id", String(36), ForeignKey("agent_steps.id", ondelete="SET NULL")),
    Column("artifact_type", String(100), nullable=False),
    Column("name", String(300), nullable=False),
    Column("status", String(20), nullable=False, server_default="draft"),
    Column("content", Text, nullable=False, server_default=""),
    Column("content_ref", Text, nullable=False, server_default=""),
    Column("checksum", String(128), nullable=False, server_default=""),
    Column("metadata_json", Text, nullable=False, server_default="{}"),
    Column("version", Integer, nullable=False, server_default="1"),
    Column("created_at", String(35), nullable=False),
    Column("updated_at", String(35), nullable=False),
    Column("exported_at", String(35)),
    CheckConstraint(f"status IN ({_quoted(ARTIFACT_STATUSES)})", name="ck_agent_artifacts_status"),
    CheckConstraint("version > 0", name="ck_agent_artifacts_version"),
)
Index("ix_agent_artifacts_task_created", agent_artifacts.c.task_id, agent_artifacts.c.created_at)
Index("ix_agent_artifacts_run_created", agent_artifacts.c.run_id, agent_artifacts.c.created_at)

idempotency_records = Table(
    "idempotency_records",
    metadata,
    Column("id", String(36), primary_key=True),
    Column("scope", String(200), nullable=False),
    Column("idempotency_key", String(200), nullable=False),
    Column("request_hash", String(128), nullable=False),
    Column("response_kind", String(100), nullable=False),
    Column("response_id", String(36), nullable=False),
    Column("response_json", Text, nullable=False, server_default="{}"),
    Column("status", String(20), nullable=False, server_default="completed"),
    Column("created_at", String(35), nullable=False),
    Column("updated_at", String(35), nullable=False),
    UniqueConstraint("scope", "idempotency_key", name="uq_idempotency_scope_key"),
    CheckConstraint("status IN ('pending', 'completed', 'failed')", name="ck_idempotency_status"),
)


ALL_TABLES = {
    table.name: table
    for table in metadata.sorted_tables
}


__all__ = [
    "ALL_TABLES",
    "APPROVAL_STATUSES",
    "ARTIFACT_STATUSES",
    "DEPTH_VALUES",
    "EFFECT_KINDS",
    "STEP_STATUSES",
    "RUN_STATUSES",
    "TASK_STATUSES",
    "agent_approvals",
    "agent_artifacts",
    "agent_events",
    "agent_runs",
    "agent_step_attempts",
    "agent_steps",
    "agent_task_messages",
    "agent_tasks",
    "app_metadata",
    "chunk_vectors",
    "document_chunks",
    "documents",
    "idempotency_records",
    "integrations",
    "metadata",
    "model_profiles",
    "projects",
    "settings",
    "sources",
    "workflow_bindings",
    "workflow_definitions",
    "workflow_versions",
]
