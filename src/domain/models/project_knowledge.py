from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import uuid


@dataclass(frozen=True)
class ProjectKnowledgePoint:
    """从项目文档和代码中提炼出的可追溯知识点。"""

    id: str
    workspace_id: str
    name: str
    kind: str
    summary: str
    source_path: str
    evidence: str
    confidence: float
    created_at: str

    @classmethod
    def create(
        cls,
        workspace_id: str,
        name: str,
        kind: str,
        summary: str,
        source_path: str,
        evidence: str,
        confidence: float = 0.6,
    ) -> "ProjectKnowledgePoint":
        return cls(
            id=str(uuid.uuid4()),
            workspace_id=workspace_id,
            name=name.strip(),
            kind=kind.strip(),
            summary=summary.strip(),
            source_path=source_path,
            evidence=evidence.strip(),
            confidence=max(0.0, min(1.0, confidence)),
            created_at=datetime.now(timezone.utc).isoformat(),
        )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "workspace_id": self.workspace_id,
            "name": self.name,
            "kind": self.kind,
            "summary": self.summary,
            "source_path": self.source_path,
            "evidence": self.evidence,
            "confidence": self.confidence,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ProjectKnowledgePoint":
        return cls(
            id=data["id"],
            workspace_id=data["workspace_id"],
            name=data["name"],
            kind=data["kind"],
            summary=data["summary"],
            source_path=data["source_path"],
            evidence=data["evidence"],
            confidence=float(data.get("confidence", 0.6)),
            created_at=data["created_at"],
        )
