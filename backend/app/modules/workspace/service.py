from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from backend.infra.storage.db.sqlite import get_connection


@dataclass
class Workspace:
    id: str
    name: str
    root_path: str
    created_at: str
    last_indexed_at: str = ""
    last_index_status: str = ""
    total_files: int = 0
    supported_files: int = 0


class WorkspaceService:
    def create(self, name: str, root_path: str) -> Workspace:
        ws_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        with get_connection() as conn:
            conn.execute(
                "INSERT INTO workspaces (id, name, root_path, created_at, last_indexed_at, last_index_status, total_files, supported_files) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (ws_id, name, str(Path(root_path)), now, "", "", 0, 0),
            )
        return Workspace(id=ws_id, name=name, root_path=root_path, created_at=now)

    def list_all(self) -> List[Workspace]:
        with get_connection() as conn:
            rows = conn.execute(
                "SELECT id, name, root_path, created_at, last_indexed_at, last_index_status, total_files, supported_files "
                "FROM workspaces ORDER BY created_at DESC"
            ).fetchall()
        return [
            Workspace(
                id=r[0],
                name=r[1],
                root_path=r[2],
                created_at=r[3],
                last_indexed_at=r[4] or "",
                last_index_status=r[5] or "",
                total_files=int(r[6] or 0),
                supported_files=int(r[7] or 0),
            )
            for r in rows
        ]

    def update_root_path(self, workspace_id: str, root_path: str) -> None:
        with get_connection() as conn:
            conn.execute(
                "UPDATE workspaces SET root_path=? WHERE id=?",
                (str(Path(root_path)), workspace_id),
            )

    def get(self, workspace_id: str) -> Optional[Workspace]:
        with get_connection() as conn:
            row = conn.execute(
                "SELECT id, name, root_path, created_at, last_indexed_at, last_index_status, total_files, supported_files "
                "FROM workspaces WHERE id=?",
                (workspace_id,),
            ).fetchone()
        if not row:
            return None
        return Workspace(
            id=row[0],
            name=row[1],
            root_path=row[2],
            created_at=row[3],
            last_indexed_at=row[4] or "",
            last_index_status=row[5] or "",
            total_files=int(row[6] or 0),
            supported_files=int(row[7] or 0),
        )

    def find_by_name(self, name: str) -> Optional[Workspace]:
        with get_connection() as conn:
            row = conn.execute(
                "SELECT id, name, root_path, created_at, last_indexed_at, last_index_status, total_files, supported_files "
                "FROM workspaces WHERE name=?",
                (name,),
            ).fetchone()
        if not row:
            return None
        return Workspace(
            id=row[0],
            name=row[1],
            root_path=row[2],
            created_at=row[3],
            last_indexed_at=row[4] or "",
            last_index_status=row[5] or "",
            total_files=int(row[6] or 0),
            supported_files=int(row[7] or 0),
        )

    def delete(self, workspace_id: str) -> None:
        with get_connection() as conn:
            conn.execute("DELETE FROM conversations WHERE workspace_id=?", (workspace_id,))
            conn.execute("DELETE FROM workspaces WHERE id=?", (workspace_id,))

    def update_index_stats(self, workspace_id: str, status: str, total_files: int, supported_files: int) -> None:
        now = datetime.now(timezone.utc).isoformat()
        with get_connection() as conn:
            conn.execute(
                "UPDATE workspaces SET last_indexed_at=?, last_index_status=?, total_files=?, supported_files=? WHERE id=?",
                (now, status, total_files, supported_files, workspace_id),
            )

