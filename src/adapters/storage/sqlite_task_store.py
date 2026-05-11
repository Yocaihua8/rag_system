from __future__ import annotations

import sqlite3
from typing import List, Optional

from src.domain.models.task import Task, TaskKind, TaskStatus
from src.ports.task_store import ITaskStore


class SqliteTaskStore(ITaskStore):

    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def save(self, task: Task) -> Task:
        self._conn.execute(
            """
            INSERT INTO tasks (id, kind, status, progress, message, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                task.id, task.kind.value, task.status.value,
                task.progress, task.message, task.created_at,
            ),
        )
        self._conn.commit()
        return task

    def update(self, task: Task) -> None:
        self._conn.execute(
            "UPDATE tasks SET status = ?, progress = ?, message = ? WHERE id = ?",
            (task.status.value, task.progress, task.message, task.id),
        )
        self._conn.commit()

    def get(self, task_id: str) -> Optional[Task]:
        row = self._conn.execute(
            "SELECT * FROM tasks WHERE id = ?", (task_id,)
        ).fetchone()
        return _row_to_task(row) if row else None

    def list_recent(self, limit: int = 20) -> List[Task]:
        rows = self._conn.execute(
            "SELECT * FROM tasks ORDER BY created_at DESC LIMIT ?", (limit,)
        ).fetchall()
        return [_row_to_task(r) for r in rows]


def _row_to_task(row: sqlite3.Row) -> Task:
    return Task(
        id=row["id"],
        kind=TaskKind(row["kind"]),
        status=TaskStatus(row["status"]),
        progress=row["progress"],
        message=row["message"],
        created_at=row["created_at"],
    )
