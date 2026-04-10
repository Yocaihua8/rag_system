from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import List, Optional

from backend.infra.storage.db.sqlite import get_connection


@dataclass
class TaskRecord:
    id: str
    kind: str
    status: str
    progress: int
    message: str
    created_at: str


class TaskService:
    def create(self, kind: str, message: str = "") -> TaskRecord:
        task_id = str(uuid.uuid4())
        created_at = datetime.now(timezone.utc).isoformat()
        with get_connection() as conn:
            conn.execute(
                "INSERT INTO tasks (id, kind, status, progress, message, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                (task_id, kind, "running", 0, message, created_at),
            )
        return TaskRecord(id=task_id, kind=kind, status="running", progress=0, message=message, created_at=created_at)

    def update(self, task_id: str, status: str, progress: int, message: str) -> None:
        with get_connection() as conn:
            conn.execute(
                "UPDATE tasks SET status=?, progress=?, message=? WHERE id=?",
                (status, progress, message, task_id),
            )

    def get(self, task_id: str) -> Optional[TaskRecord]:
        with get_connection() as conn:
            row = conn.execute(
                "SELECT id, kind, status, progress, message, created_at FROM tasks WHERE id=?",
                (task_id,),
            ).fetchone()
        if not row:
            return None
        return TaskRecord(id=row[0], kind=row[1], status=row[2], progress=row[3], message=row[4], created_at=row[5])

    def list_recent(self, limit: int = 20) -> List[TaskRecord]:
        with get_connection() as conn:
            rows = conn.execute(
                "SELECT id, kind, status, progress, message, created_at FROM tasks ORDER BY created_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [TaskRecord(id=r[0], kind=r[1], status=r[2], progress=r[3], message=r[4], created_at=r[5]) for r in rows]

