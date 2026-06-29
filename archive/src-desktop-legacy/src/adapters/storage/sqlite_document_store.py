from __future__ import annotations

import json
import sqlite3
from typing import List, Optional

from src.domain.models.document import Document
from src.ports.document_store import IDocumentStore


class SqliteDocumentStore(IDocumentStore):

    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def save(self, document: Document) -> None:
        self._conn.execute(
            """
            INSERT OR REPLACE INTO documents
                (
                    id, workspace_id, project_id, title, source_type, source_path,
                    content, raw_content, normalized_markdown, plain_text,
                    rendered_html, domain, tags, created_at, updated_at
                )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                document.id, document.workspace_id, document.project_id,
                document.title, document.source_type, document.source_path,
                document.content, document.raw_content,
                document.normalized_markdown, document.plain_text,
                document.rendered_html, document.domain,
                json.dumps(document.tags, ensure_ascii=False),
                document.created_at, document.updated_at,
            ),
        )
        self._conn.commit()

    def save_batch(self, documents: List[Document]) -> None:
        self._conn.executemany(
            """
            INSERT OR REPLACE INTO documents
                (
                    id, workspace_id, project_id, title, source_type, source_path,
                    content, raw_content, normalized_markdown, plain_text,
                    rendered_html, domain, tags, created_at, updated_at
                )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    d.id, d.workspace_id, d.project_id, d.title,
                    d.source_type, d.source_path, d.content,
                    d.raw_content, d.normalized_markdown, d.plain_text,
                    d.rendered_html, d.domain,
                    json.dumps(d.tags, ensure_ascii=False),
                    d.created_at, d.updated_at,
                )
                for d in documents
            ],
        )
        self._conn.commit()

    def get(self, document_id: str) -> Optional[Document]:
        row = self._conn.execute(
            "SELECT * FROM documents WHERE id = ?", (document_id,)
        ).fetchone()
        return _row_to_document(row) if row else None

    def list_by_workspace(self, workspace_id: str) -> List[Document]:
        rows = self._conn.execute(
            "SELECT * FROM documents WHERE workspace_id = ? ORDER BY created_at ASC",
            (workspace_id,),
        ).fetchall()
        return [_row_to_document(r) for r in rows]

    def delete_by_workspace(self, workspace_id: str) -> None:
        self._conn.execute(
            "DELETE FROM documents WHERE workspace_id = ?", (workspace_id,)
        )
        self._conn.commit()

    def exists(self, document_id: str) -> bool:
        row = self._conn.execute(
            "SELECT 1 FROM documents WHERE id = ?", (document_id,)
        ).fetchone()
        return row is not None

    def delete(self, document_id: str) -> None:
        """删除单个文档（ON DELETE CASCADE 自动清理关联 chunks）。"""
        self._conn.execute(
            "DELETE FROM documents WHERE id = ?", (document_id,)
        )
        self._conn.commit()


def _row_to_document(row: sqlite3.Row) -> Document:
    return Document(
        id=row["id"],
        workspace_id=row["workspace_id"],
        title=row["title"],
        source_path=row["source_path"],
        content=row["content"],
        domain=row["domain"],
        tags=json.loads(row["tags"]),
        created_at=row["created_at"],
        project_id=row["project_id"],
        source_type=row["source_type"],
        raw_content=row["raw_content"],
        normalized_markdown=row["normalized_markdown"],
        plain_text=row["plain_text"],
        rendered_html=row["rendered_html"],
        updated_at=row["updated_at"],
    )
