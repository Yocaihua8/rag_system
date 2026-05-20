from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
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


class MasteryStatus(str, Enum):
    CLAIMED = "claimed"
    EVIDENCE_FOUND = "evidence_found"
    VERIFIED = "verified"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _clamp_confidence(confidence: float) -> float:
    return max(0.0, min(1.0, confidence))


@dataclass(frozen=True)
class SkillArea:
    """掌握评估中的能力域/技能域。"""

    id: str
    workspace_id: str
    name: str
    description: str
    created_at: str
    updated_at: str

    @classmethod
    def create(
        cls,
        workspace_id: str,
        name: str,
        description: str = "",
    ) -> "SkillArea":
        now = _now()
        return cls(
            id=str(uuid.uuid4()),
            workspace_id=workspace_id,
            name=name.strip(),
            description=description.strip(),
            created_at=now,
            updated_at=now,
        )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "workspace_id": self.workspace_id,
            "name": self.name,
            "description": self.description,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "SkillArea":
        return cls(
            id=data["id"],
            workspace_id=data["workspace_id"],
            name=data["name"],
            description=data.get("description", ""),
            created_at=data["created_at"],
            updated_at=data.get("updated_at", data["created_at"]),
        )


@dataclass(frozen=True)
class KnowledgePoint:
    """学习掌握中的知识点。"""

    id: str
    workspace_id: str
    skill_area_id: str
    name: str
    summary: str
    confidence: float
    created_at: str
    updated_at: str

    @classmethod
    def create(
        cls,
        workspace_id: str,
        skill_area_id: str,
        name: str,
        summary: str,
        confidence: float = 0.6,
    ) -> "KnowledgePoint":
        now = _now()
        return cls(
            id=str(uuid.uuid4()),
            workspace_id=workspace_id,
            skill_area_id=skill_area_id,
            name=name.strip(),
            summary=summary.strip(),
            confidence=_clamp_confidence(confidence),
            created_at=now,
            updated_at=now,
        )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "workspace_id": self.workspace_id,
            "skill_area_id": self.skill_area_id,
            "name": self.name,
            "summary": self.summary,
            "confidence": self.confidence,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "KnowledgePoint":
        return cls(
            id=data["id"],
            workspace_id=data["workspace_id"],
            skill_area_id=data["skill_area_id"],
            name=data["name"],
            summary=data["summary"],
            confidence=float(data.get("confidence", 0.6)),
            created_at=data["created_at"],
            updated_at=data.get("updated_at", data["created_at"]),
        )


@dataclass(frozen=True)
class Evidence:
    """证明某个知识点掌握证据的来源片段。"""

    id: str
    workspace_id: str
    knowledge_point_id: str
    source_path: str
    snippet: str
    confidence: float
    created_at: str

    @classmethod
    def create(
        cls,
        workspace_id: str,
        knowledge_point_id: str,
        source_path: str,
        snippet: str,
        confidence: float = 0.6,
    ) -> "Evidence":
        return cls(
            id=str(uuid.uuid4()),
            workspace_id=workspace_id,
            knowledge_point_id=knowledge_point_id,
            source_path=source_path,
            snippet=snippet.strip(),
            confidence=_clamp_confidence(confidence),
            created_at=_now(),
        )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "workspace_id": self.workspace_id,
            "knowledge_point_id": self.knowledge_point_id,
            "source_path": self.source_path,
            "snippet": self.snippet,
            "confidence": self.confidence,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Evidence":
        return cls(
            id=data["id"],
            workspace_id=data["workspace_id"],
            knowledge_point_id=data["knowledge_point_id"],
            source_path=data["source_path"],
            snippet=data["snippet"],
            confidence=float(data.get("confidence", 0.6)),
            created_at=data["created_at"],
        )


@dataclass(frozen=True)
class MasteryRecord:
    """用户对单个知识点的掌握轨迹记录。"""

    id: str
    workspace_id: str
    knowledge_point_id: str
    status: MasteryStatus
    evidence_id: str
    confidence: float
    note: str
    created_at: str
    updated_at: str

    @classmethod
    def create(
        cls,
        workspace_id: str,
        knowledge_point_id: str,
        evidence_id: str = "",
        status: MasteryStatus = MasteryStatus.CLAIMED,
        confidence: float = 0.6,
        note: str = "",
    ) -> "MasteryRecord":
        now = _now()
        return cls(
            id=str(uuid.uuid4()),
            workspace_id=workspace_id,
            knowledge_point_id=knowledge_point_id,
            status=status,
            evidence_id=evidence_id,
            confidence=_clamp_confidence(confidence),
            note=note.strip(),
            created_at=now,
            updated_at=now,
        )

    def mark_evidence_found(self, evidence_id: str, note: str = "") -> "MasteryRecord":
        return MasteryRecord(
            id=self.id,
            workspace_id=self.workspace_id,
            knowledge_point_id=self.knowledge_point_id,
            status=MasteryStatus.EVIDENCE_FOUND,
            evidence_id=evidence_id,
            confidence=self.confidence,
            note=note.strip() or self.note,
            created_at=self.created_at,
            updated_at=_now(),
        )

    def mark_verified(self, note: str = "", confidence: float | None = None) -> "MasteryRecord":
        return MasteryRecord(
            id=self.id,
            workspace_id=self.workspace_id,
            knowledge_point_id=self.knowledge_point_id,
            status=MasteryStatus.VERIFIED,
            evidence_id=self.evidence_id,
            confidence=_clamp_confidence(confidence)
            if confidence is not None
            else self.confidence,
            note=note.strip() or self.note,
            created_at=self.created_at,
            updated_at=_now(),
        )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "workspace_id": self.workspace_id,
            "knowledge_point_id": self.knowledge_point_id,
            "status": self.status.value,
            "evidence_id": self.evidence_id,
            "confidence": self.confidence,
            "note": self.note,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "MasteryRecord":
        return cls(
            id=data["id"],
            workspace_id=data["workspace_id"],
            knowledge_point_id=data["knowledge_point_id"],
            status=MasteryStatus(data.get("status", MasteryStatus.CLAIMED.value)),
            evidence_id=data.get("evidence_id", ""),
            confidence=float(data.get("confidence", 0.6)),
            note=data.get("note", ""),
            created_at=data["created_at"],
            updated_at=data.get("updated_at", data["created_at"]),
        )
