from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List
import uuid


@dataclass(frozen=True)
class Document:
    """
    知识库中的一个原始文档。

    frozen=True：不可变，可安全跨线程传递。
    """
    id: str
    workspace_id: str
    title: str               # 通常为文件名（无扩展名）
    source_path: str         # 原始文件的绝对路径字符串
    content: str             # 原始文本内容
    domain: str              # 推断的领域，如 resume / jd / notes
    tags: List[str]          # 技术标签列表
    created_at: str          # ISO 8601 字符串

    # ------------------------------------------------------------------ #
    # 工厂方法
    # ------------------------------------------------------------------ #

    @classmethod
    def create(
        cls,
        workspace_id: str,
        title: str,
        source_path: str,
        content: str,
        domain: str = "general",
        tags: List[str] = None,
    ) -> "Document":
        return cls(
            id=str(uuid.uuid4()),
            workspace_id=workspace_id,
            title=title,
            source_path=source_path,
            content=content,
            domain=domain,
            tags=tags or [],
            created_at=datetime.now(timezone.utc).isoformat(),
        )

    # ------------------------------------------------------------------ #
    # 序列化
    # ------------------------------------------------------------------ #

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "workspace_id": self.workspace_id,
            "title": self.title,
            "source_path": self.source_path,
            "content": self.content,
            "domain": self.domain,
            "tags": self.tags,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Document":
        return cls(
            id=data["id"],
            workspace_id=data["workspace_id"],
            title=data["title"],
            source_path=data["source_path"],
            content=data["content"],
            domain=data.get("domain", "general"),
            tags=data.get("tags", []),
            created_at=data["created_at"],
        )
