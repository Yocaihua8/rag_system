from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import uuid


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True)
class Project:
    """Knowledge Island 中的项目空间。"""

    id: str
    name: str
    description: str
    root_path: str
    created_at: str
    updated_at: str

    @classmethod
    def create(
        cls,
        name: str,
        description: str = "",
        root_path: str = "",
    ) -> "Project":
        now = _now()
        return cls(
            id=str(uuid.uuid4()),
            name=name.strip(),
            description=description.strip(),
            root_path=root_path,
            created_at=now,
            updated_at=now,
        )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "root_path": self.root_path,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Project":
        return cls(
            id=data["id"],
            name=data["name"],
            description=data.get("description", ""),
            root_path=data.get("root_path", ""),
            created_at=data["created_at"],
            updated_at=data.get("updated_at", data["created_at"]),
        )
