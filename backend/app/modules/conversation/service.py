from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import List

from backend.infra.storage.db.sqlite import get_connection


@dataclass
class ConversationRecord:
    id: str
    workspace_id: str
    question: str
    answer: str
    created_at: str


class ConversationService:
    def add(self, workspace_id: str, question: str, answer: str) -> ConversationRecord:
        record_id = str(uuid.uuid4())
        created_at = datetime.now(timezone.utc).isoformat()
        with get_connection() as conn:
            conn.execute(
                "INSERT INTO conversations (id, workspace_id, question, answer, created_at) VALUES (?, ?, ?, ?, ?)",
                (record_id, workspace_id, question, answer, created_at),
            )
        return ConversationRecord(
            id=record_id,
            workspace_id=workspace_id,
            question=question,
            answer=answer,
            created_at=created_at,
        )

    def list_recent(self, workspace_id: str, limit: int = 10) -> List[ConversationRecord]:
        with get_connection() as conn:
            rows = conn.execute(
                "SELECT id, workspace_id, question, answer, created_at FROM conversations "
                "WHERE workspace_id=? ORDER BY created_at DESC LIMIT ?",
                (workspace_id, limit),
            ).fetchall()
        return [
            ConversationRecord(id=r[0], workspace_id=r[1], question=r[2], answer=r[3], created_at=r[4]) for r in rows
        ]

