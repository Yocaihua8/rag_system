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
    project_id: str = ""
    source_type: str = ""
    raw_content: str = ""
    normalized_markdown: str = ""
    plain_text: str = ""
    rendered_html: str = ""
    updated_at: str = ""

    def __post_init__(self) -> None:
        if not self.project_id:
            object.__setattr__(self, "project_id", self.workspace_id)
        if not self.raw_content:
            object.__setattr__(self, "raw_content", self.content)
        if not self.normalized_markdown:
            object.__setattr__(self, "normalized_markdown", self.raw_content)
        if not self.plain_text:
            object.__setattr__(self, "plain_text", self.normalized_markdown)
        if not self.updated_at:
            object.__setattr__(self, "updated_at", self.created_at)

    # ------------------------------------------------------------------ #
    # 工厂方法
    # ------------------------------------------------------------------ #

    @classmethod
    def create(
        cls,
        workspace_id: str = "",
        title: str = "",
        source_path: str = "",
        content: str = "",
        domain: str = "general",
        tags: List[str] = None,
        *,
        project_id: str = "",
        source_type: str = "",
        raw_content: str = "",
        normalized_markdown: str = "",
        plain_text: str = "",
        rendered_html: str = "",
    ) -> "Document":
        now = datetime.now(timezone.utc).isoformat()
        effective_raw = raw_content if raw_content else content
        effective_markdown = normalized_markdown if normalized_markdown else effective_raw
        effective_plain = plain_text if plain_text else effective_markdown
        return cls(
            id=str(uuid.uuid4()),
            workspace_id=workspace_id,
            title=title,
            source_path=source_path,
            content=effective_raw,
            domain=domain,
            tags=tags or [],
            created_at=now,
            project_id=project_id or workspace_id,
            source_type=source_type,
            raw_content=effective_raw,
            normalized_markdown=effective_markdown,
            plain_text=effective_plain,
            rendered_html=rendered_html,
            updated_at=now,
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
            "project_id": self.project_id,
            "source_type": self.source_type,
            "raw_content": self.raw_content,
            "normalized_markdown": self.normalized_markdown,
            "plain_text": self.plain_text,
            "rendered_html": self.rendered_html,
            "updated_at": self.updated_at,
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
            project_id=data.get("project_id", data.get("workspace_id", "")),
            source_type=data.get("source_type", ""),
            raw_content=data.get("raw_content", data.get("content", "")),
            normalized_markdown=data.get("normalized_markdown", data.get("content", "")),
            plain_text=data.get("plain_text", data.get("content", "")),
            rendered_html=data.get("rendered_html", ""),
            updated_at=data.get("updated_at", data["created_at"]),
        )
