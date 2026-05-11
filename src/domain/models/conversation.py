from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import uuid


@dataclass(frozen=True)
class ConversationRecord:
    """一条问答历史记录。"""
    id: str
    workspace_id: str
    question: str
    answer: str
    created_at: str          # ISO 8601

    # ------------------------------------------------------------------ #
    # 工厂方法
    # ------------------------------------------------------------------ #

    @classmethod
    def create(
        cls,
        workspace_id: str,
        question: str,
        answer: str,
    ) -> "ConversationRecord":
        return cls(
            id=str(uuid.uuid4()),
            workspace_id=workspace_id,
            question=question,
            answer=answer,
            created_at=datetime.now(timezone.utc).isoformat(),
        )

    # ------------------------------------------------------------------ #
    # 序列化
    # ------------------------------------------------------------------ #

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "workspace_id": self.workspace_id,
            "question": self.question,
            "answer": self.answer,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ConversationRecord":
        return cls(
            id=data["id"],
            workspace_id=data["workspace_id"],
            question=data["question"],
            answer=data["answer"],
            created_at=data["created_at"],
        )
