from __future__ import annotations

import pytest

from backend.domain.agent_runtime import (
    ApprovalStatus,
    ArtifactStatus,
    DepthProfile,
    EffectKind,
    RunStatus,
    StepStatus,
    TaskStatus,
    get_depth_limits,
)
from backend.domain.workflow_registry import (
    SAFE_NODE_REGISTRY,
    WorkflowDefinition,
    WorkflowEdge,
    WorkflowNode,
    WorkflowValidationCode,
    list_safe_node_definitions,
    validate_workflow,
)


def _node(node_id: str, type_id: str, **config: object) -> WorkflowNode:
    return WorkflowNode(id=node_id, type_id=type_id, config=config)


def _edge(
    source_node_id: str,
    target_node_id: str,
    *,
    source_port: str = "out",
    target_port: str = "in",
    edge_id: str = "",
) -> WorkflowEdge:
    return WorkflowEdge(
        source_node_id=source_node_id,
        source_port=source_port,
        target_node_id=target_node_id,
        target_port=target_port,
        id=edge_id,
    )


def _codes(workflow: WorkflowDefinition) -> set[WorkflowValidationCode]:
    return {error.code for error in validate_workflow(workflow).errors}


def _valid_export_workflow() -> WorkflowDefinition:
    nodes = (
        _node("trigger", "trigger.manual"),
        _node("plan", "agent.plan", depth="standard"),
        _node("search", "source.search"),
        _node("read", "source.read", max_documents=8),
        _node("analyze", "project.analyze", analysis_kind="architecture"),
        _node("synthesize", "llm.synthesize", model_profile_id="profile-1"),
        _node("artifact", "artifact.create", format="markdown"),
        _node("approval", "approval.request", action_summary="Export report"),
        _node("export", "artifact.export", target="project_exports"),
    )
    edges = tuple(
        _edge(source, target, edge_id=f"{source}-{target}")
        for source, target in zip(
            ("trigger", "plan", "search", "read", "analyze", "synthesize", "artifact", "approval"),
            ("plan", "search", "read", "analyze", "synthesize", "artifact", "approval", "export"),
            strict=True,
        )
    )
    return WorkflowDefinition(nodes=nodes, edges=edges)


def test_agent_runtime_statuses_and_depth_limits_are_stable_string_contracts():
    assert {status.value for status in TaskStatus} == {
        "queued",
        "running",
        "waiting_approval",
        "paused",
        "completed",
        "failed",
        "cancelled",
    }
    assert RunStatus.RECOVERING == "recovering"
    assert StepStatus.RECOVERY_REQUIRED == "recovery_required"
    assert ApprovalStatus.APPROVED == "approved"
    assert ArtifactStatus.EXPORTED == "exported"
    assert get_depth_limits(DepthProfile.QUICK).max_steps == 4
    assert get_depth_limits("standard").max_tool_iterations == 3
    assert get_depth_limits(DepthProfile.DEEP).max_steps == 16
    assert EffectKind.READ.requires_approval is False
    assert EffectKind.PROJECT_WRITE.requires_approval is True
    assert EffectKind.EXTERNAL_WRITE.requires_approval is True

    with pytest.raises(ValueError, match="unknown depth profile"):
        get_depth_limits("unbounded")


def test_safe_node_registry_is_allowlist_only_and_has_typed_effects():
    assert set(SAFE_NODE_REGISTRY) == {
        "trigger.manual",
        "agent.plan",
        "source.search",
        "source.read",
        "project.analyze",
        "llm.synthesize",
        "llm.compare",
        "insight.assess",
        "learning.plan",
        "artifact.create",
        "approval.request",
        "artifact.export",
        "obsidian.publish",
        "control.branch",
        "control.join",
    }
    assert tuple(item.type_id for item in list_safe_node_definitions()) == tuple(
        SAFE_NODE_REGISTRY
    )
    assert SAFE_NODE_REGISTRY["source.read"].effect is EffectKind.READ
    assert SAFE_NODE_REGISTRY["artifact.export"].effect is EffectKind.PROJECT_WRITE
    assert SAFE_NODE_REGISTRY["obsidian.publish"].effect is EffectKind.EXTERNAL_WRITE
    assert not any(
        blocked in type_id
        for type_id in SAFE_NODE_REGISTRY
        for blocked in ("shell", "script", "http", "mcp", "filesystem", "path")
    )


def test_valid_typed_dag_with_dominating_approval_passes():
    result = validate_workflow(_valid_export_workflow())

    assert result.valid is True
    assert result.errors == ()
    assert result.to_dict() == {"valid": True, "errors": []}


def test_workflow_requires_exactly_one_manual_trigger_and_a_terminal():
    no_trigger = WorkflowDefinition(
        nodes=(_node("plan", "agent.plan", depth="quick"),),
        edges=(),
    )
    trigger_only = WorkflowDefinition(
        nodes=(_node("trigger", "trigger.manual"),),
        edges=(),
    )
    two_triggers = WorkflowDefinition(
        nodes=(
            _node("first", "trigger.manual"),
            _node("second", "trigger.manual"),
        ),
        edges=(),
    )

    assert WorkflowValidationCode.MANUAL_TRIGGER_COUNT in _codes(no_trigger)
    assert WorkflowValidationCode.MISSING_TERMINAL in _codes(trigger_only)
    assert WorkflowValidationCode.MANUAL_TRIGGER_COUNT in _codes(two_triggers)


def test_workflow_reports_unknown_references_ports_and_type_mismatch():
    workflow = WorkflowDefinition(
        nodes=(
            _node("trigger", "trigger.manual"),
            _node("search", "source.search"),
        ),
        edges=(
            _edge("trigger", "search", edge_id="type-mismatch"),
            _edge("missing", "search", edge_id="missing-source"),
            _edge(
                "trigger",
                "search",
                source_port="missing-port",
                edge_id="missing-port",
            ),
        ),
    )

    result = validate_workflow(workflow)
    codes = {error.code for error in result.errors}

    assert WorkflowValidationCode.PORT_TYPE_MISMATCH in codes
    assert WorkflowValidationCode.UNKNOWN_SOURCE_NODE in codes
    assert WorkflowValidationCode.UNKNOWN_SOURCE_PORT in codes
    assert result.to_dict()["valid"] is False
    assert all("code" in error for error in result.to_dict()["errors"])


def test_workflow_reports_missing_and_unsafe_config():
    missing_required = WorkflowDefinition(
        nodes=(
            _node("trigger", "trigger.manual"),
            _node("plan", "agent.plan"),
        ),
        edges=(_edge("trigger", "plan"),),
    )
    invalid_and_unexpected = WorkflowDefinition(
        nodes=(
            _node("trigger", "trigger.manual"),
            _node(
                "plan",
                "agent.plan",
                depth="unbounded",
                path="C:/arbitrary",
            ),
        ),
        edges=(_edge("trigger", "plan"),),
    )

    assert WorkflowValidationCode.MISSING_REQUIRED_CONFIG in _codes(missing_required)
    assert WorkflowValidationCode.INVALID_CONFIG in _codes(invalid_and_unexpected)
    assert WorkflowValidationCode.UNEXPECTED_CONFIG in _codes(invalid_and_unexpected)


@pytest.mark.parametrize(
    "type_id",
    [
        "shell.execute",
        "script.python",
        "http.request",
        "mcp.call",
        "path.write",
        "filesystem.read",
    ],
)
def test_forbidden_capability_node_types_are_rejected(type_id: str):
    workflow = WorkflowDefinition(
        nodes=(
            _node("trigger", "trigger.manual"),
            _node("unsafe", type_id),
        ),
        edges=(_edge("trigger", "unsafe"),),
    )

    result = validate_workflow(workflow)

    assert WorkflowValidationCode.FORBIDDEN_NODE_TYPE in {
        error.code for error in result.errors
    }
    forbidden_error = next(
        error
        for error in result.errors
        if error.code is WorkflowValidationCode.FORBIDDEN_NODE_TYPE
    )
    assert forbidden_error.node_id == "unsafe"
    assert forbidden_error.details["type_id"] == type_id


def test_unknown_but_not_explicitly_forbidden_node_type_is_rejected():
    workflow = WorkflowDefinition(
        nodes=(
            _node("trigger", "trigger.manual"),
            _node("unknown", "custom.magic"),
        ),
        edges=(_edge("trigger", "unknown"),),
    )

    assert WorkflowValidationCode.UNKNOWN_NODE_TYPE in _codes(workflow)


def test_cycle_and_unreachable_nodes_are_reported():
    workflow = WorkflowDefinition(
        nodes=(
            _node("trigger", "trigger.manual"),
            _node("branch", "control.branch", condition="has_sources"),
            _node("join", "control.join", strategy="all"),
            _node("orphan", "control.branch", condition="unused"),
        ),
        edges=(
            _edge("trigger", "branch"),
            _edge("branch", "join", source_port="true"),
            _edge("join", "branch"),
        ),
    )

    result = validate_workflow(workflow)
    codes = {error.code for error in result.errors}

    assert WorkflowValidationCode.CYCLE_DETECTED in codes
    assert WorkflowValidationCode.ORPHAN_NODE in codes
    cycle_error = next(
        error
        for error in result.errors
        if error.code is WorkflowValidationCode.CYCLE_DETECTED
    )
    assert cycle_error.details["node_ids"] == ["branch", "join"]


def test_write_node_without_approval_is_rejected():
    workflow = WorkflowDefinition(
        nodes=(
            _node("trigger", "trigger.manual"),
            _node("branch", "control.branch", condition="always"),
            _node("export", "artifact.export", target="download"),
        ),
        edges=(
            _edge("trigger", "branch"),
            _edge("branch", "export", source_port="true"),
        ),
    )

    result = validate_workflow(workflow)

    error = next(
        error
        for error in result.errors
        if error.code is WorkflowValidationCode.WRITE_REQUIRES_APPROVAL
    )
    assert error.node_id == "export"
    assert error.details == {"effect": "project_write"}


def test_approval_must_dominate_write_on_every_branch():
    workflow = WorkflowDefinition(
        nodes=(
            _node("trigger", "trigger.manual"),
            _node("branch", "control.branch", condition="user_choice"),
            _node("approval", "approval.request", action_summary="Export"),
            _node("export", "artifact.export", target="download"),
        ),
        edges=(
            _edge("trigger", "branch"),
            _edge("branch", "approval", source_port="true"),
            _edge("approval", "export"),
            _edge("branch", "export", source_port="false"),
        ),
    )

    assert WorkflowValidationCode.WRITE_REQUIRES_APPROVAL in _codes(workflow)


def test_approval_that_dominates_write_on_all_paths_is_accepted():
    workflow = WorkflowDefinition(
        nodes=(
            _node("trigger", "trigger.manual"),
            _node("branch", "control.branch", condition="always"),
            _node("approval", "approval.request", action_summary="Export"),
            _node("export", "artifact.export", target="download"),
        ),
        edges=(
            _edge("trigger", "branch"),
            _edge("branch", "approval", source_port="true"),
            _edge("approval", "export"),
        ),
    )

    assert validate_workflow(workflow).valid is True
