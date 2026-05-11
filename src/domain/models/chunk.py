from __future__ import annotations

from dataclasses import dataclass
from typing import List
import uuid


@dataclass(frozen=True)
class Chunk:
    """
    文档分块后的最小检索单元。

    frozen=True：不可变，可安全跨线程传递，也可作为 dict key。
    """
    id: str
    document_id: str
    workspace_id: str
    domain: str
    tags: List[str]
    content: str
    order: int               # 在原文档中的块序号（0-based）

    # ------------------------------------------------------------------ #
    # 工厂方法
    # ------------------------------------------------------------------ #

    @classmethod
    def create(
        cls,
        document_id: str,
        workspace_id: str,
        content: str,
        order: int,
        domain: str = "general",
        tags: List[str] = None,
    ) -> "Chunk":
        return cls(
            id=str(uuid.uuid4()),
            document_id=document_id,
            workspace_id=workspace_id,
            domain=domain,
            tags=tags or [],
            content=content,
            order=order,
        )

    # ------------------------------------------------------------------ #
    # 序列化
    # ------------------------------------------------------------------ #

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "document_id": self.document_id,
            "workspace_id": self.workspace_id,
            "domain": self.domain,
            "tags": self.tags,
            "content": self.content,
            "order": self.order,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Chunk":
        return cls(
            id=data["id"],
            document_id=data["document_id"],
            workspace_id=data["workspace_id"],
            domain=data.get("domain", "general"),
            tags=data.get("tags", []),
            content=data["content"],
            order=data.get("order", 0),
        )
