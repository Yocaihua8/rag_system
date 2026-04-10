import uuid
from datetime import datetime, timezone
from typing import Dict

from desktop.db.sqlite import get_connection
from desktop.settings import DB_PATH


class TaskManager:
    def __init__(self) -> None:
        self.db_path = DB_PATH

    def create(self, message: str = "") -> str:
        task_id = str(uuid.uuid4())
        with get_connection(self.db_path) as conn:
            conn.execute(
                "INSERT INTO tasks (id, status, progress, message, created_at) VALUES (?, ?, ?, ?, ?)",
                (task_id, "running", 0, message, datetime.now(timezone.utc).isoformat()),
            )
        return task_id

    def update(self, task_id: str, status: str, progress: int, message: str) -> None:
        with get_connection(self.db_path) as conn:
            conn.execute(
                "UPDATE tasks SET status=?, progress=?, message=? WHERE id=?",
                (status, progress, message, task_id),
            )

    def get(self, task_id: str) -> Dict:
        with get_connection(self.db_path) as conn:
            cur = conn.execute("SELECT id, status, progress, message FROM tasks WHERE id=?", (task_id,))
            row = cur.fetchone()
        if not row:
            return {"id": task_id, "status": "unknown", "progress": 0, "message": ""}
        return {"id": row[0], "status": row[1], "progress": row[2], "message": row[3]}
