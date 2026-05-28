from __future__ import annotations

from dataclasses import dataclass
from typing import List
from datetime import datetime, timezone
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
    project_id: str = ""
    chunk_index: int = 0
    heading_path: List[str] = None
    chunk_markdown: str = ""
    chunk_plain_text: str = ""
    token_count: int = 0
    embedding_id: str = ""
    created_at: str = ""
    updated_at: str = ""

    def __post_init__(self) -> None:
        if self.heading_path is None:
            object.__setattr__(self, "heading_path", [])
        if not self.project_id:
            object.__setattr__(self, "project_id", self.workspace_id)
        if self.chunk_index == 0 and self.order != 0:
            object.__setattr__(self, "chunk_index", self.order)
        if not self.chunk_markdown:
            object.__setattr__(self, "chunk_markdown", self.content)
        if not self.chunk_plain_text:
            object.__setattr__(self, "chunk_plain_text", self.chunk_markdown)
        now = datetime.now(timezone.utc).isoformat()
        if not self.created_at:
            object.__setattr__(self, "created_at", now)
        if not self.updated_at:
            object.__setattr__(self, "updated_at", self.created_at)

    # ------------------------------------------------------------------ #
    # 工厂方法
    # ------------------------------------------------------------------ #

    @classmethod
    def create(
        cls,
        document_id: str = "",
        workspace_id: str = "",
        content: str = "",
        order: int = 0,
        domain: str = "general",
        tags: List[str] = None,
        *,
        project_id: str = "",
        chunk_index: int = None,
        heading_path: List[str] = None,
        chunk_markdown: str = "",
        chunk_plain_text: str = "",
        token_count: int = 0,
        embedding_id: str = "",
    ) -> "Chunk":
        effective_markdown = chunk_markdown if chunk_markdown else content
        effective_plain = chunk_plain_text if chunk_plain_text else effective_markdown
        now = datetime.now(timezone.utc).isoformat()
        return cls(
            id=str(uuid.uuid4()),
            document_id=document_id,
            workspace_id=workspace_id,
            domain=domain,
            tags=tags or [],
            content=effective_markdown,
            order=order,
            project_id=project_id or workspace_id,
            chunk_index=order if chunk_index is None else chunk_index,
            heading_path=heading_path or [],
            chunk_markdown=effective_markdown,
            chunk_plain_text=effective_plain,
            token_count=token_count,
            embedding_id=embedding_id,
            created_at=now,
            updated_at=now,
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
            "project_id": self.project_id,
            "chunk_index": self.chunk_index,
            "heading_path": self.heading_path,
            "chunk_markdown": self.chunk_markdown,
            "chunk_plain_text": self.chunk_plain_text,
            "token_count": self.token_count,
            "embedding_id": self.embedding_id,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
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
            project_id=data.get("project_id", data.get("workspace_id", "")),
            chunk_index=data.get("chunk_index", data.get("order", 0)),
            heading_path=data.get("heading_path", []),
            chunk_markdown=data.get("chunk_markdown", data.get("content", "")),
            chunk_plain_text=data.get("chunk_plain_text", data.get("content", "")),
            token_count=data.get("token_count", 0),
            embedding_id=data.get("embedding_id", ""),
            created_at=data.get("created_at", ""),
            updated_at=data.get("updated_at", ""),
        )
