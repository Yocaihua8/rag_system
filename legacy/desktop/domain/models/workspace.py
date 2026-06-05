from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional
import uuid


@dataclass(frozen=True)
class Workspace:
    """用户创建的知识库工作区。"""
    id: str
    name: str
    root_path: str           # 文件系统路径字符串
    created_at: str          # ISO 8601

    # 索引状态（摄入完成后更新）
    last_indexed_at: str     # "" 表示从未索引
    last_index_status: str   # "" | "ok" | "error"
    total_files: int
    supported_files: int

    # ------------------------------------------------------------------ #
    # 工厂方法
    # ------------------------------------------------------------------ #

    @classmethod
    def create(cls, name: str, root_path: str) -> "Workspace":
        return cls(
            id=str(uuid.uuid4()),
            name=name,
            root_path=root_path,
            created_at=datetime.now(timezone.utc).isoformat(),
            last_indexed_at="",
            last_index_status="",
            total_files=0,
            supported_files=0,
        )

    def with_index_stats(
        self,
        status: str,
        total_files: int,
        supported_files: int,
    ) -> "Workspace":
        """返回更新了索引状态的新实例（frozen 不可原地修改）。"""
        return Workspace(
            id=self.id,
            name=self.name,
            root_path=self.root_path,
            created_at=self.created_at,
            last_indexed_at=datetime.now(timezone.utc).isoformat(),
            last_index_status=status,
            total_files=total_files,
            supported_files=supported_files,
        )

    # ------------------------------------------------------------------ #
    # 序列化
    # ------------------------------------------------------------------ #

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "root_path": self.root_path,
            "created_at": self.created_at,
            "last_indexed_at": self.last_indexed_at,
            "last_index_status": self.last_index_status,
            "total_files": self.total_files,
            "supported_files": self.supported_files,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Workspace":
        return cls(
            id=data["id"],
            name=data["name"],
            root_path=data["root_path"],
            created_at=data["created_at"],
            last_indexed_at=data.get("last_indexed_at", ""),
            last_index_status=data.get("last_index_status", ""),
            total_files=data.get("total_files", 0),
            supported_files=data.get("supported_files", 0),
        )
