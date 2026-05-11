from __future__ import annotations

import sqlite3
from typing import List

from src.domain.models.conversation import ConversationRecord
from src.ports.conversation_store import IConversationStore


class SqliteConversationStore(IConversationStore):

    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def save(self, record: ConversationRecord) -> ConversationRecord:
        self._conn.execute(
            """
            INSERT INTO conversations (id, workspace_id, question, answer, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (record.id, record.workspace_id, record.question,
             record.answer, record.created_at),
        )
        self._conn.commit()
        return record

    def list_recent(self, workspace_id: str, limit: int = 20) -> List[ConversationRecord]:
        rows = self._conn.execute(
            """
            SELECT * FROM conversations
            WHERE workspace_id = ?
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (workspace_id, limit),
        ).fetchall()
        return [_row_to_record(r) for r in rows]

    def delete_by_workspace(self, workspace_id: str) -> None:
        self._conn.execute(
            "DELETE FROM conversations WHERE workspace_id = ?", (workspace_id,)
        )
        self._conn.commit()


def _row_to_record(row: sqlite3.Row) -> ConversationRecord:
    return ConversationRecord(
        id=row["id"],
        workspace_id=row["workspace_id"],
        question=row["question"],
        answer=row["answer"],
        created_at=row["created_at"],
    )
