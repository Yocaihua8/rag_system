from __future__ import annotations

import sqlite3
from typing import List

from src.domain.models.project_knowledge import ProjectKnowledgePoint
from src.ports.project_knowledge_store import IProjectKnowledgeStore


class SqliteProjectKnowledgeStore(IProjectKnowledgeStore):

    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def save_batch(self, points: List[ProjectKnowledgePoint]) -> None:
        self._conn.executemany(
            """
            INSERT OR REPLACE INTO project_knowledge_points
                (id, workspace_id, name, kind, summary, source_path, evidence, confidence, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    p.id,
                    p.workspace_id,
                    p.name,
                    p.kind,
                    p.summary,
                    p.source_path,
                    p.evidence,
                    p.confidence,
                    p.created_at,
                )
                for p in points
            ],
        )
        self._conn.commit()

    def list_by_workspace(self, workspace_id: str) -> List[ProjectKnowledgePoint]:
        rows = self._conn.execute(
            """
            SELECT * FROM project_knowledge_points
            WHERE workspace_id = ?
            ORDER BY kind ASC, name ASC, created_at ASC
            """,
            (workspace_id,),
        ).fetchall()
        return [_row_to_point(row) for row in rows]

    def delete_by_workspace(self, workspace_id: str) -> None:
        self._conn.execute(
            "DELETE FROM project_knowledge_points WHERE workspace_id = ?",
            (workspace_id,),
        )
        self._conn.commit()

    def count_by_workspace(self, workspace_id: str) -> int:
        row = self._conn.execute(
            "SELECT COUNT(*) FROM project_knowledge_points WHERE workspace_id = ?",
            (workspace_id,),
        ).fetchone()
        return row[0] if row else 0


def _row_to_point(row: sqlite3.Row) -> ProjectKnowledgePoint:
    return ProjectKnowledgePoint(
        id=row["id"],
        workspace_id=row["workspace_id"],
        name=row["name"],
        kind=row["kind"],
        summary=row["summary"],
        source_path=row["source_path"],
        evidence=row["evidence"],
        confidence=row["confidence"],
        created_at=row["created_at"],
    )
