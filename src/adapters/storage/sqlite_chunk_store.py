from __future__ import annotations

import json
import sqlite3
from typing import List, Optional

from src.domain.models.chunk import Chunk
from src.ports.chunk_store import IChunkStore


class SqliteChunkStore(IChunkStore):

    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def save_batch(self, chunks: List[Chunk]) -> None:
        self._conn.executemany(
            """
            INSERT OR REPLACE INTO chunks
                (id, document_id, workspace_id, domain, tags, content, ord)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    c.id, c.document_id, c.workspace_id, c.domain,
                    json.dumps(c.tags, ensure_ascii=False),
                    c.content, c.order,
                )
                for c in chunks
            ],
        )
        self._conn.commit()

    def get(self, chunk_id: str) -> Optional[Chunk]:
        row = self._conn.execute(
            "SELECT * FROM chunks WHERE id = ?", (chunk_id,)
        ).fetchone()
        return _row_to_chunk(row) if row else None

    def list_by_workspace(self, workspace_id: str) -> List[Chunk]:
        rows = self._conn.execute(
            "SELECT * FROM chunks WHERE workspace_id = ? ORDER BY document_id, ord ASC",
            (workspace_id,),
        ).fetchall()
        return [_row_to_chunk(r) for r in rows]

    def list_by_document(self, document_id: str) -> List[Chunk]:
        rows = self._conn.execute(
            "SELECT * FROM chunks WHERE document_id = ? ORDER BY ord ASC",
            (document_id,),
        ).fetchall()
        return [_row_to_chunk(r) for r in rows]

    def delete_by_workspace(self, workspace_id: str) -> None:
        self._conn.execute(
            "DELETE FROM chunks WHERE workspace_id = ?", (workspace_id,)
        )
        self._conn.commit()

    def count_by_workspace(self, workspace_id: str) -> int:
        row = self._conn.execute(
            "SELECT COUNT(*) FROM chunks WHERE workspace_id = ?", (workspace_id,)
        ).fetchone()
        return row[0] if row else 0

    def list_by_ids(self, chunk_ids: list[str]) -> list[Chunk]:
        """批量按 ID 加载 Chunk。空列表返回空。最多 500 个以避免 SQL 过长。"""
        if not chunk_ids:
            return []
        # 限制批量大小
        ids = chunk_ids[:500]
        placeholders = ",".join("?" for _ in ids)
        rows = self._conn.execute(
            f"SELECT * FROM chunks WHERE id IN ({placeholders})",
            ids,
        ).fetchall()
        # 保持输入顺序
        row_map = {r["id"]: _row_to_chunk(r) for r in rows}
        return [row_map[cid] for cid in ids if cid in row_map]


def _row_to_chunk(row: sqlite3.Row) -> Chunk:
    return Chunk(
        id=row["id"],
        document_id=row["document_id"],
        workspace_id=row["workspace_id"],
        domain=row["domain"],
        tags=json.loads(row["tags"]),
        content=row["content"],
        order=row["ord"],
    )
