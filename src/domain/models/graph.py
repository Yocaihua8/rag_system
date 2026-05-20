from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import uuid


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _clamp_confidence(confidence: float) -> float:
    return max(0.0, min(1.0, confidence))


@dataclass(frozen=True)
class GraphNode:
    """轻量知识图谱节点。"""

    id: str
    workspace_id: str
    name: str
    label: str
    node_type: str
    source_ref: str
    confidence: float
    created_at: str
    updated_at: str

    @classmethod
    def create(
        cls,
        workspace_id: str,
        name: str,
        node_type: str = "concept",
        label: str = "",
        source_ref: str = "",
        confidence: float = 0.6,
    ) -> "GraphNode":
        now = _now()
        title = name.strip()
        node_type = node_type.strip() or "concept"
        return cls(
            id=str(uuid.uuid4()),
            workspace_id=workspace_id,
            name=title,
            label=label.strip() or title,
            node_type=node_type,
            source_ref=source_ref.strip(),
            confidence=_clamp_confidence(confidence),
            created_at=now,
            updated_at=now,
        )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "workspace_id": self.workspace_id,
            "name": self.name,
            "label": self.label,
            "node_type": self.node_type,
            "source_ref": self.source_ref,
            "confidence": self.confidence,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "GraphNode":
        return cls(
            id=data["id"],
            workspace_id=data["workspace_id"],
            name=data["name"],
            label=data.get("label", data.get("name", "")),
            node_type=data.get("node_type", data.get("type", "")) or "concept",
            source_ref=data.get("source_ref", ""),
            confidence=float(data.get("confidence", 0.6)),
            created_at=data["created_at"],
            updated_at=data.get("updated_at", data["created_at"]),
        )


@dataclass(frozen=True)
class GraphEdge:
    """轻量知识图谱边。"""

    id: str
    workspace_id: str
    source_node_id: str
    target_node_id: str
    relationship: str
    confidence: float
    source_path: str
    source_snippet: str
    created_at: str
    updated_at: str

    @classmethod
    def create(
        cls,
        workspace_id: str,
        source_node_id: str,
        target_node_id: str,
        relationship: str,
        source_path: str = "",
        source_snippet: str = "",
        confidence: float = 0.6,
    ) -> "GraphEdge":
        now = _now()
        return cls(
            id=str(uuid.uuid4()),
            workspace_id=workspace_id,
            source_node_id=source_node_id,
            target_node_id=target_node_id,
            relationship=relationship.strip() or "related_to",
            confidence=_clamp_confidence(confidence),
            source_path=source_path.strip(),
            source_snippet=source_snippet.strip(),
            created_at=now,
            updated_at=now,
        )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "workspace_id": self.workspace_id,
            "source_node_id": self.source_node_id,
            "target_node_id": self.target_node_id,
            "relationship": self.relationship,
            "confidence": self.confidence,
            "source_path": self.source_path,
            "source_snippet": self.source_snippet,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "GraphEdge":
        return cls(
            id=data["id"],
            workspace_id=data["workspace_id"],
            source_node_id=data["source_node_id"],
            target_node_id=data["target_node_id"],
            relationship=data["relationship"],
            confidence=float(data.get("confidence", 0.6)),
            source_path=data.get("source_path", ""),
            source_snippet=data.get("source_snippet", ""),
            created_at=data["created_at"],
            updated_at=data.get("updated_at", data["created_at"]),
        )
