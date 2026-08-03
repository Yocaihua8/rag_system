from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field as dataclass_field
from enum import StrEnum
from types import MappingProxyType
from typing import Any, Iterable, Mapping

from backend.domain.agent_runtime import DepthProfile, EffectKind


class PortDataType(StrEnum):
    ANY = "any"
    PROMPT = "prompt"
    PLAN = "plan"
    SOURCES = "sources"
    CONTEXT = "context"
    ANALYSIS = "analysis"
    RESULT = "result"
    INSIGHT = "insight"
    ARTIFACT = "artifact"
    APPROVED_ARTIFACT = "approved_artifact"


class ConfigValueType(StrEnum):
    STRING = "string"
    INTEGER = "integer"
    BOOLEAN = "boolean"


@dataclass(frozen=True, slots=True)
class PortDefinition:
    name: str
    data_type: PortDataType
    required: bool = True


@dataclass(frozen=True, slots=True)
class ConfigField:
    name: str
    value_type: ConfigValueType = ConfigValueType.STRING
    required: bool = False
    choices: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class NodeDefinition:
    type_id: str
    label: str
    effect: EffectKind
    input_ports: tuple[PortDefinition, ...] = ()
    output_ports: tuple[PortDefinition, ...] = ()
    config_fields: tuple[ConfigField, ...] = ()

    def input_port(self, name: str) -> PortDefinition | None:
        return next((port for port in self.input_ports if port.name == name), None)

    def output_port(self, name: str) -> PortDefinition | None:
        return next((port for port in self.output_ports if port.name == name), None)

    def config_field(self, name: str) -> ConfigField | None:
        return next((item for item in self.config_fields if item.name == name), None)


@dataclass(frozen=True, slots=True)
class WorkflowNode:
    id: str
    type_id: str
    config: Mapping[str, Any] = dataclass_field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class WorkflowEdge:
    source_node_id: str
    source_port: str
    target_node_id: str
    target_port: str
    id: str = ""


@dataclass(frozen=True, slots=True)
class WorkflowDefinition:
    nodes: tuple[WorkflowNode, ...]
    edges: tuple[WorkflowEdge, ...]


class WorkflowValidationCode(StrEnum):
    EMPTY_WORKFLOW = "empty_workflow"
    DUPLICATE_NODE_ID = "duplicate_node_id"
    DUPLICATE_EDGE_ID = "duplicate_edge_id"
    MANUAL_TRIGGER_COUNT = "manual_trigger_count"
    TRIGGER_HAS_INCOMING_EDGE = "trigger_has_incoming_edge"
    MISSING_TERMINAL = "missing_terminal"
    UNKNOWN_NODE_TYPE = "unknown_node_type"
    FORBIDDEN_NODE_TYPE = "forbidden_node_type"
    UNKNOWN_SOURCE_NODE = "unknown_source_node"
    UNKNOWN_TARGET_NODE = "unknown_target_node"
    UNKNOWN_SOURCE_PORT = "unknown_source_port"
    UNKNOWN_TARGET_PORT = "unknown_target_port"
    PORT_TYPE_MISMATCH = "port_type_mismatch"
    MISSING_REQUIRED_INPUT = "missing_required_input"
    MISSING_REQUIRED_CONFIG = "missing_required_config"
    UNEXPECTED_CONFIG = "unexpected_config"
    INVALID_CONFIG = "invalid_config"
    ORPHAN_NODE = "orphan_node"
    CYCLE_DETECTED = "cycle_detected"
    WRITE_REQUIRES_APPROVAL = "write_requires_approval"


@dataclass(frozen=True, slots=True)
class WorkflowValidationError:
    code: WorkflowValidationCode
    message: str
    node_id: str | None = None
    edge_id: str | None = None
    field: str | None = None
    details: Mapping[str, Any] = dataclass_field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "code": self.code.value,
            "message": self.message,
        }
        if self.node_id is not None:
            data["node_id"] = self.node_id
        if self.edge_id is not None:
            data["edge_id"] = self.edge_id
        if self.field is not None:
            data["field"] = self.field
        if self.details:
            data["details"] = dict(self.details)
        return data


@dataclass(frozen=True, slots=True)
class WorkflowValidationResult:
    errors: tuple[WorkflowValidationError, ...] = ()

    @property
    def valid(self) -> bool:
        return not self.errors

    def to_dict(self) -> dict[str, Any]:
        return {
            "valid": self.valid,
            "errors": [error.to_dict() for error in self.errors],
        }


def _port(name: str, data_type: PortDataType, *, required: bool = True) -> PortDefinition:
    return PortDefinition(name=name, data_type=data_type, required=required)


def _config(
    name: str,
    *,
    value_type: ConfigValueType = ConfigValueType.STRING,
    required: bool = False,
    choices: tuple[str, ...] = (),
) -> ConfigField:
    return ConfigField(
        name=name,
        value_type=value_type,
        required=required,
        choices=choices,
    )


_SAFE_NODE_DEFINITIONS = (
    NodeDefinition(
        type_id="trigger.manual",
        label="Manual trigger",
        effect=EffectKind.NONE,
        output_ports=(_port("out", PortDataType.PROMPT),),
        config_fields=(_config("quick_action"),),
    ),
    NodeDefinition(
        type_id="agent.plan",
        label="Agent plan",
        effect=EffectKind.ANALYSIS,
        input_ports=(_port("in", PortDataType.PROMPT),),
        output_ports=(_port("out", PortDataType.PLAN),),
        config_fields=(
            _config(
                "depth",
                required=True,
                choices=tuple(profile.value for profile in DepthProfile),
            ),
        ),
    ),
    NodeDefinition(
        type_id="source.search",
        label="Source search",
        effect=EffectKind.READ,
        input_ports=(_port("in", PortDataType.PLAN),),
        output_ports=(_port("out", PortDataType.SOURCES),),
        config_fields=(_config("query_template"),),
    ),
    NodeDefinition(
        type_id="source.read",
        label="Source read",
        effect=EffectKind.READ,
        input_ports=(_port("in", PortDataType.SOURCES),),
        output_ports=(_port("out", PortDataType.CONTEXT),),
        config_fields=(
            _config("max_documents", value_type=ConfigValueType.INTEGER),
        ),
    ),
    NodeDefinition(
        type_id="project.analyze",
        label="Project analyze",
        effect=EffectKind.ANALYSIS,
        input_ports=(_port("in", PortDataType.PROMPT),),
        output_ports=(_port("out", PortDataType.ANALYSIS),),
        config_fields=(
            _config(
                "analysis_kind",
                required=True,
                choices=("general", "architecture", "requirements", "sources"),
            ),
        ),
    ),
    NodeDefinition(
        type_id="llm.synthesize",
        label="LLM synthesize",
        effect=EffectKind.ANALYSIS,
        input_ports=(_port("in", PortDataType.ANALYSIS),),
        output_ports=(_port("out", PortDataType.RESULT),),
        config_fields=(
            _config("model_profile_id", required=True),
            _config("instruction"),
        ),
    ),
    NodeDefinition(
        type_id="llm.compare",
        label="LLM compare",
        effect=EffectKind.ANALYSIS,
        input_ports=(_port("in", PortDataType.CONTEXT),),
        output_ports=(_port("out", PortDataType.RESULT),),
        config_fields=(
            _config("left_model_profile_id", required=True),
            _config("right_model_profile_id", required=True),
            _config("instruction"),
        ),
    ),
    NodeDefinition(
        type_id="insight.assess",
        label="Insight assess",
        effect=EffectKind.ANALYSIS,
        input_ports=(_port("in", PortDataType.CONTEXT),),
        output_ports=(_port("out", PortDataType.INSIGHT),),
        config_fields=(
            _config(
                "perspective",
                required=True,
                choices=("knowledge", "architecture", "delivery"),
            ),
        ),
    ),
    NodeDefinition(
        type_id="learning.plan",
        label="Learning plan",
        effect=EffectKind.ANALYSIS,
        input_ports=(_port("in", PortDataType.INSIGHT),),
        output_ports=(_port("out", PortDataType.RESULT),),
        config_fields=(_config("objective"),),
    ),
    NodeDefinition(
        type_id="artifact.create",
        label="Artifact create",
        effect=EffectKind.ANALYSIS,
        input_ports=(_port("in", PortDataType.ANALYSIS),),
        output_ports=(_port("out", PortDataType.ARTIFACT),),
        config_fields=(
            _config("format", required=True, choices=("markdown", "json")),
            _config("title"),
        ),
    ),
    NodeDefinition(
        type_id="agent.respond",
        label="Agent response",
        effect=EffectKind.ANALYSIS,
        input_ports=(_port("in", PortDataType.ARTIFACT),),
        output_ports=(_port("out", PortDataType.RESULT),),
        config_fields=(
            _config("format", choices=("markdown", "text")),
            _config("message_type"),
        ),
    ),
    NodeDefinition(
        type_id="approval.request",
        label="Approval request",
        effect=EffectKind.NONE,
        input_ports=(_port("in", PortDataType.ARTIFACT),),
        output_ports=(_port("out", PortDataType.APPROVED_ARTIFACT),),
        config_fields=(_config("action_summary", required=True),),
    ),
    NodeDefinition(
        type_id="artifact.export",
        label="Artifact export",
        effect=EffectKind.PROJECT_WRITE,
        input_ports=(_port("in", PortDataType.APPROVED_ARTIFACT),),
        config_fields=(
            _config(
                "target",
                required=True,
                choices=("download", "project_exports"),
            ),
        ),
    ),
    NodeDefinition(
        type_id="obsidian.publish",
        label="Obsidian publish",
        effect=EffectKind.EXTERNAL_WRITE,
        input_ports=(_port("in", PortDataType.APPROVED_ARTIFACT),),
        config_fields=(_config("connection_id", required=True),),
    ),
    NodeDefinition(
        type_id="control.branch",
        label="Branch",
        effect=EffectKind.NONE,
        input_ports=(_port("in", PortDataType.ANY),),
        output_ports=(
            _port("true", PortDataType.ANY),
            _port("false", PortDataType.ANY),
        ),
        config_fields=(_config("condition", required=True),),
    ),
    NodeDefinition(
        type_id="control.join",
        label="Join",
        effect=EffectKind.NONE,
        input_ports=(_port("in", PortDataType.ANY),),
        output_ports=(_port("out", PortDataType.ANY),),
        config_fields=(
            _config("strategy", choices=("all", "any")),
        ),
    ),
)


SAFE_NODE_REGISTRY: Mapping[str, NodeDefinition] = MappingProxyType(
    {definition.type_id: definition for definition in _SAFE_NODE_DEFINITIONS}
)


_FORBIDDEN_NODE_TOKENS = frozenset(
    {"shell", "script", "http", "https", "mcp", "path", "filesystem", "fs"}
)


def list_safe_node_definitions() -> tuple[NodeDefinition, ...]:
    return _SAFE_NODE_DEFINITIONS


def get_node_definition(type_id: str) -> NodeDefinition | None:
    return SAFE_NODE_REGISTRY.get(type_id)


def validate_workflow(
    workflow: WorkflowDefinition,
    *,
    registry: Mapping[str, NodeDefinition] = SAFE_NODE_REGISTRY,
) -> WorkflowValidationResult:
    errors: list[WorkflowValidationError] = []
    if not workflow.nodes:
        return WorkflowValidationResult(
            errors=(
                WorkflowValidationError(
                    code=WorkflowValidationCode.EMPTY_WORKFLOW,
                    message="workflow must contain at least one node",
                ),
            )
        )

    nodes_by_id: dict[str, WorkflowNode] = {}
    for node in workflow.nodes:
        if node.id in nodes_by_id:
            errors.append(
                WorkflowValidationError(
                    code=WorkflowValidationCode.DUPLICATE_NODE_ID,
                    message=f"duplicate node id: {node.id}",
                    node_id=node.id,
                )
            )
            continue
        nodes_by_id[node.id] = node

    seen_edge_ids: set[str] = set()
    for edge in workflow.edges:
        if edge.id and edge.id in seen_edge_ids:
            errors.append(
                WorkflowValidationError(
                    code=WorkflowValidationCode.DUPLICATE_EDGE_ID,
                    message=f"duplicate edge id: {edge.id}",
                    edge_id=edge.id,
                )
            )
        if edge.id:
            seen_edge_ids.add(edge.id)

    definitions_by_node_id: dict[str, NodeDefinition] = {}
    for node in nodes_by_id.values():
        definition = registry.get(node.type_id)
        if definition is None:
            code = (
                WorkflowValidationCode.FORBIDDEN_NODE_TYPE
                if _is_forbidden_node_type(node.type_id)
                else WorkflowValidationCode.UNKNOWN_NODE_TYPE
            )
            errors.append(
                WorkflowValidationError(
                    code=code,
                    message=f"node type is not allowed: {node.type_id}",
                    node_id=node.id,
                    field="type_id",
                    details={"type_id": node.type_id},
                )
            )
            continue
        definitions_by_node_id[node.id] = definition
        _validate_node_config(node, definition, errors)

    trigger_ids = [
        node.id for node in nodes_by_id.values() if node.type_id == "trigger.manual"
    ]
    if len(trigger_ids) != 1:
        errors.append(
            WorkflowValidationError(
                code=WorkflowValidationCode.MANUAL_TRIGGER_COUNT,
                message="workflow must contain exactly one trigger.manual node",
                details={"count": len(trigger_ids)},
            )
        )

    successors = {node_id: set() for node_id in nodes_by_id}
    predecessors = {node_id: set() for node_id in nodes_by_id}
    incoming_ports: dict[tuple[str, str], int] = {}
    for edge in workflow.edges:
        source = nodes_by_id.get(edge.source_node_id)
        target = nodes_by_id.get(edge.target_node_id)
        if source is None:
            errors.append(
                WorkflowValidationError(
                    code=WorkflowValidationCode.UNKNOWN_SOURCE_NODE,
                    message=f"edge references unknown source node: {edge.source_node_id}",
                    edge_id=edge.id or None,
                    details={"source_node_id": edge.source_node_id},
                )
            )
        if target is None:
            errors.append(
                WorkflowValidationError(
                    code=WorkflowValidationCode.UNKNOWN_TARGET_NODE,
                    message=f"edge references unknown target node: {edge.target_node_id}",
                    edge_id=edge.id or None,
                    details={"target_node_id": edge.target_node_id},
                )
            )
        if source is None or target is None:
            continue

        successors[source.id].add(target.id)
        predecessors[target.id].add(source.id)
        incoming_ports[(target.id, edge.target_port)] = (
            incoming_ports.get((target.id, edge.target_port), 0) + 1
        )
        _validate_edge_ports(
            edge,
            definitions_by_node_id.get(source.id),
            definitions_by_node_id.get(target.id),
            errors,
        )

    for node_id, definition in definitions_by_node_id.items():
        for input_port in definition.input_ports:
            if input_port.required and incoming_ports.get((node_id, input_port.name), 0) == 0:
                errors.append(
                    WorkflowValidationError(
                        code=WorkflowValidationCode.MISSING_REQUIRED_INPUT,
                        message=f"required input is not connected: {input_port.name}",
                        node_id=node_id,
                        field=input_port.name,
                    )
                )

    if len(trigger_ids) == 1:
        trigger_id = trigger_ids[0]
        if predecessors[trigger_id]:
            errors.append(
                WorkflowValidationError(
                    code=WorkflowValidationCode.TRIGGER_HAS_INCOMING_EDGE,
                    message="trigger.manual cannot have incoming edges",
                    node_id=trigger_id,
                )
            )
        reachable = _reachable_from(trigger_id, successors)
        for node_id in nodes_by_id:
            if node_id not in reachable:
                errors.append(
                    WorkflowValidationError(
                        code=WorkflowValidationCode.ORPHAN_NODE,
                        message="node is not reachable from trigger.manual",
                        node_id=node_id,
                    )
                )

        terminal_ids = sorted(
            node_id
            for node_id in reachable
            if node_id != trigger_id
            and node_id in definitions_by_node_id
            and not successors[node_id]
        )
        if not terminal_ids:
            errors.append(
                WorkflowValidationError(
                    code=WorkflowValidationCode.MISSING_TERMINAL,
                    message="workflow must contain at least one reachable terminal node",
                )
            )
        _validate_write_dominance(
            trigger_id,
            reachable,
            predecessors,
            nodes_by_id,
            definitions_by_node_id,
            errors,
        )

    cycle_node_ids = _cycle_node_ids(successors, predecessors)
    if cycle_node_ids:
        errors.append(
            WorkflowValidationError(
                code=WorkflowValidationCode.CYCLE_DETECTED,
                message="workflow graph must be acyclic",
                details={"node_ids": cycle_node_ids},
            )
        )

    return WorkflowValidationResult(errors=tuple(errors))


def _is_forbidden_node_type(type_id: str) -> bool:
    normalized = type_id.lower().replace("-", ".").replace("_", ".")
    tokens = {token for token in normalized.split(".") if token}
    return bool(tokens & _FORBIDDEN_NODE_TOKENS)


def _validate_node_config(
    node: WorkflowNode,
    definition: NodeDefinition,
    errors: list[WorkflowValidationError],
) -> None:
    for name in node.config:
        if definition.config_field(name) is None:
            errors.append(
                WorkflowValidationError(
                    code=WorkflowValidationCode.UNEXPECTED_CONFIG,
                    message=f"config field is not allowed: {name}",
                    node_id=node.id,
                    field=name,
                )
            )

    for config_field in definition.config_fields:
        value = node.config.get(config_field.name)
        if config_field.required and _is_blank(value):
            errors.append(
                WorkflowValidationError(
                    code=WorkflowValidationCode.MISSING_REQUIRED_CONFIG,
                    message=f"required config is missing: {config_field.name}",
                    node_id=node.id,
                    field=config_field.name,
                )
            )
            continue
        if value is None:
            continue
        if not _config_type_matches(config_field.value_type, value):
            errors.append(
                WorkflowValidationError(
                    code=WorkflowValidationCode.INVALID_CONFIG,
                    message=f"config field has invalid type: {config_field.name}",
                    node_id=node.id,
                    field=config_field.name,
                    details={"expected_type": config_field.value_type.value},
                )
            )
            continue
        if config_field.choices and value not in config_field.choices:
            errors.append(
                WorkflowValidationError(
                    code=WorkflowValidationCode.INVALID_CONFIG,
                    message=f"config field has unsupported value: {config_field.name}",
                    node_id=node.id,
                    field=config_field.name,
                    details={"allowed_values": list(config_field.choices)},
                )
            )


def _is_blank(value: Any) -> bool:
    return value is None or (isinstance(value, str) and not value.strip())


def _config_type_matches(value_type: ConfigValueType, value: Any) -> bool:
    if value_type is ConfigValueType.STRING:
        return isinstance(value, str) and bool(value.strip())
    if value_type is ConfigValueType.INTEGER:
        return isinstance(value, int) and not isinstance(value, bool) and value >= 1
    if value_type is ConfigValueType.BOOLEAN:
        return isinstance(value, bool)
    return False


def _validate_edge_ports(
    edge: WorkflowEdge,
    source_definition: NodeDefinition | None,
    target_definition: NodeDefinition | None,
    errors: list[WorkflowValidationError],
) -> None:
    if source_definition is None or target_definition is None:
        return
    source_port = source_definition.output_port(edge.source_port)
    target_port = target_definition.input_port(edge.target_port)
    if source_port is None:
        errors.append(
            WorkflowValidationError(
                code=WorkflowValidationCode.UNKNOWN_SOURCE_PORT,
                message=f"unknown source port: {edge.source_port}",
                edge_id=edge.id or None,
                node_id=edge.source_node_id,
                field=edge.source_port,
            )
        )
    if target_port is None:
        errors.append(
            WorkflowValidationError(
                code=WorkflowValidationCode.UNKNOWN_TARGET_PORT,
                message=f"unknown target port: {edge.target_port}",
                edge_id=edge.id or None,
                node_id=edge.target_node_id,
                field=edge.target_port,
            )
        )
    if source_port is None or target_port is None:
        return
    if (
        source_port.data_type is not PortDataType.ANY
        and target_port.data_type is not PortDataType.ANY
        and source_port.data_type is not target_port.data_type
    ):
        errors.append(
            WorkflowValidationError(
                code=WorkflowValidationCode.PORT_TYPE_MISMATCH,
                message="edge ports have incompatible data types",
                edge_id=edge.id or None,
                details={
                    "source_type": source_port.data_type.value,
                    "target_type": target_port.data_type.value,
                },
            )
        )


def _reachable_from(start: str, successors: Mapping[str, set[str]]) -> set[str]:
    reachable: set[str] = set()
    pending = [start]
    while pending:
        node_id = pending.pop()
        if node_id in reachable:
            continue
        reachable.add(node_id)
        pending.extend(sorted(successors[node_id], reverse=True))
    return reachable


def _cycle_node_ids(
    successors: Mapping[str, set[str]],
    predecessors: Mapping[str, set[str]],
) -> list[str]:
    indegree = {node_id: len(predecessors[node_id]) for node_id in successors}
    ready = deque(sorted(node_id for node_id, count in indegree.items() if count == 0))
    processed: set[str] = set()
    while ready:
        node_id = ready.popleft()
        processed.add(node_id)
        for target_id in sorted(successors[node_id]):
            indegree[target_id] -= 1
            if indegree[target_id] == 0:
                ready.append(target_id)
    return sorted(set(successors) - processed)


def _validate_write_dominance(
    trigger_id: str,
    reachable: set[str],
    predecessors: Mapping[str, set[str]],
    nodes_by_id: Mapping[str, WorkflowNode],
    definitions_by_node_id: Mapping[str, NodeDefinition],
    errors: list[WorkflowValidationError],
) -> None:
    dominators: dict[str, set[str]] = {
        node_id: ({trigger_id} if node_id == trigger_id else set(reachable))
        for node_id in reachable
    }
    changed = True
    while changed:
        changed = False
        for node_id in sorted(reachable - {trigger_id}):
            node_predecessors = predecessors[node_id] & reachable
            if not node_predecessors:
                new_dominators = {node_id}
            else:
                predecessor_dominators = [dominators[item] for item in node_predecessors]
                new_dominators = set.intersection(*predecessor_dominators) | {node_id}
            if new_dominators != dominators[node_id]:
                dominators[node_id] = new_dominators
                changed = True

    approval_ids = {
        node_id
        for node_id, node in nodes_by_id.items()
        if node.type_id == "approval.request"
    }
    for node_id in sorted(reachable):
        definition = definitions_by_node_id.get(node_id)
        if definition is None or not definition.effect.requires_approval:
            continue
        dominating_approvals = approval_ids & dominators[node_id]
        if not dominating_approvals:
            errors.append(
                WorkflowValidationError(
                    code=WorkflowValidationCode.WRITE_REQUIRES_APPROVAL,
                    message=(
                        "every path to a project or external write node must pass "
                        "through approval.request"
                    ),
                    node_id=node_id,
                    details={"effect": definition.effect.value},
                )
            )
