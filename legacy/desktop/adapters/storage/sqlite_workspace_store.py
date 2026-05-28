from __future__ import annotations

import sqlite3
from typing import List, Optional

from legacy.desktop.domain.models.workspace import Workspace
from legacy.desktop.ports.workspace_store import IWorkspaceStore


class SqliteWorkspaceStore(IWorkspaceStore):

    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def save(self, workspace: Workspace) -> Workspace:
        self._conn.execute(
            """
            INSERT OR REPLACE INTO workspaces
                (id, name, root_path, created_at,
                 last_indexed_at, last_index_status, total_files, supported_files)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                workspace.id, workspace.name, workspace.root_path,
                workspace.created_at, workspace.last_indexed_at,
                workspace.last_index_status, workspace.total_files,
                workspace.supported_files,
            ),
        )
        self._conn.commit()
        return workspace

    def get(self, workspace_id: str) -> Optional[Workspace]:
        row = self._conn.execute(
            "SELECT * FROM workspaces WHERE id = ?", (workspace_id,)
        ).fetchone()
        return _row_to_workspace(row) if row else None

    def list_all(self) -> List[Workspace]:
        rows = self._conn.execute(
            "SELECT * FROM workspaces ORDER BY created_at ASC"
        ).fetchall()
        return [_row_to_workspace(r) for r in rows]

    def update(self, workspace: Workspace) -> None:
        self._conn.execute(
            """
            UPDATE workspaces SET
                name = ?, root_path = ?,
                last_indexed_at = ?, last_index_status = ?,
                total_files = ?, supported_files = ?
            WHERE id = ?
            """,
            (
                workspace.name, workspace.root_path,
                workspace.last_indexed_at, workspace.last_index_status,
                workspace.total_files, workspace.supported_files,
                workspace.id,
            ),
        )
        self._conn.commit()

    def delete(self, workspace_id: str) -> None:
        self._conn.execute("DELETE FROM workspaces WHERE id = ?", (workspace_id,))
        self._conn.commit()


def _row_to_workspace(row: sqlite3.Row) -> Workspace:
    return Workspace(
        id=row["id"],
        name=row["name"],
        root_path=row["root_path"],
        created_at=row["created_at"],
        last_indexed_at=row["last_indexed_at"],
        last_index_status=row["last_index_status"],
        total_files=row["total_files"],
        supported_files=row["supported_files"],
    )
