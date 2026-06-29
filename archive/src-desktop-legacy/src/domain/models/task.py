from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
import uuid


class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    DONE = "done"
    FAILED = "failed"


class TaskKind(str, Enum):
    INGEST = "ingest"
    QUERY = "query"
    GENERATE_RESUME = "generate_resume"
    GENERATE_JD = "generate_jd"
    GENERATE_INTERVIEW = "generate_interview"


@dataclass(frozen=True)
class Task:
    """长时操作的跟踪记录。"""
    id: str
    kind: TaskKind
    status: TaskStatus
    progress: int            # 0-100
    message: str
    created_at: str          # ISO 8601

    # ------------------------------------------------------------------ #
    # 工厂方法
    # ------------------------------------------------------------------ #

    @classmethod
    def create(cls, kind: TaskKind, message: str = "") -> "Task":
        return cls(
            id=str(uuid.uuid4()),
            kind=kind,
            status=TaskStatus.PENDING,
            progress=0,
            message=message,
            created_at=datetime.now(timezone.utc).isoformat(),
        )

    def update(
        self,
        status: TaskStatus,
        progress: int,
        message: str,
    ) -> "Task":
        """返回更新了状态的新实例。"""
        return Task(
            id=self.id,
            kind=self.kind,
            status=status,
            progress=max(0, min(100, progress)),
            message=message,
            created_at=self.created_at,
        )

    # ------------------------------------------------------------------ #
    # 序列化
    # ------------------------------------------------------------------ #

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "kind": self.kind.value,
            "status": self.status.value,
            "progress": self.progress,
            "message": self.message,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Task":
        return cls(
            id=data["id"],
            kind=TaskKind(data["kind"]),
            status=TaskStatus(data["status"]),
            progress=data.get("progress", 0),
            message=data.get("message", ""),
            created_at=data["created_at"],
        )
