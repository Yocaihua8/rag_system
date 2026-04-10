import uuid
from datetime import datetime, timezone
from typing import List

from desktop.db.sqlite import get_connection
from desktop.settings import DB_PATH


def add_history(question: str, answer: str) -> str:
    record_id = str(uuid.uuid4())
    with get_connection(DB_PATH) as conn:
        conn.execute(
            "INSERT INTO chats (id, question, answer, created_at) VALUES (?, ?, ?, ?)",
            (record_id, question, answer, datetime.now(timezone.utc).isoformat()),
        )
    return record_id


def list_history(limit: int = 50) -> List[dict]:
    with get_connection(DB_PATH) as conn:
        cur = conn.execute(
            "SELECT id, question, answer, created_at FROM chats ORDER BY created_at DESC LIMIT ?",
            (limit,),
        )
        rows = cur.fetchall()
    return [
        {"id": r[0], "question": r[1], "answer": r[2], "created_at": r[3]} for r in rows
    ]
