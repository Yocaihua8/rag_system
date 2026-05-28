from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import uuid


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True)
class Tag:
    """个人知识资产的标签。"""

    id: str
    name: str
    color: str
    created_at: str
    updated_at: str

    @classmethod
    def create(cls, name: str, color: str = "") -> "Tag":
        now = _now()
        return cls(
            id=str(uuid.uuid4()),
            name=name.strip(),
            color=color.strip(),
            created_at=now,
            updated_at=now,
        )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "color": self.color,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Tag":
        return cls(
            id=data["id"],
            name=data["name"],
            color=data.get("color", ""),
            created_at=data["created_at"],
            updated_at=data.get("updated_at", data["created_at"]),
        )


@dataclass(frozen=True)
class DocumentTag:
    """Document 与 Tag 的多对多关联。"""

    document_id: str
    tag_id: str

    @classmethod
    def create(cls, document_id: str, tag_id: str) -> "DocumentTag":
        return cls(document_id=document_id, tag_id=tag_id)

    def to_dict(self) -> dict:
        return {
            "document_id": self.document_id,
            "tag_id": self.tag_id,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "DocumentTag":
        return cls(document_id=data["document_id"], tag_id=data["tag_id"])
