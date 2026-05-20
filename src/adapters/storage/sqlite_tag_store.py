from __future__ import annotations

from typing import List
import sqlite3

from src.domain.models.tag import Tag, DocumentTag
from src.ports.tag_store import ITagStore, IDocumentTagStore


class SqliteTagStore(ITagStore):

    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def save(self, tag: Tag) -> None:
        self._conn.execute(
            """
            INSERT OR REPLACE INTO tags (id, name, color, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (tag.id, tag.name, tag.color, tag.created_at, tag.updated_at),
        )
        self._conn.commit()

    def get(self, tag_id: str) -> Tag | None:
        row = self._conn.execute(
            "SELECT * FROM tags WHERE id = ?", (tag_id,)
        ).fetchone()
        return _row_to_tag(row) if row else None

    def get_by_name(self, name: str) -> Tag | None:
        row = self._conn.execute(
            "SELECT * FROM tags WHERE name = ? LIMIT 1",
            (name,),
        ).fetchone()
        return _row_to_tag(row) if row else None

    def list_all(self) -> List[Tag]:
        rows = self._conn.execute(
            "SELECT * FROM tags ORDER BY name ASC"
        ).fetchall()
        return [_row_to_tag(r) for r in rows]

    def delete(self, tag_id: str) -> None:
        self._conn.execute("DELETE FROM tags WHERE id = ?", (tag_id,))
        self._conn.commit()


class SqliteDocumentTagStore(IDocumentTagStore):

    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def save(self, link: DocumentTag) -> None:
        self._conn.execute(
            """
            INSERT OR IGNORE INTO document_tags (document_id, tag_id)
            VALUES (?, ?)
            """,
            (link.document_id, link.tag_id),
        )
        self._conn.commit()

    def delete_by_document(self, document_id: str) -> None:
        self._conn.execute(
            "DELETE FROM document_tags WHERE document_id = ?",
            (document_id,),
        )
        self._conn.commit()

    def list_tag_ids_by_document(self, document_id: str) -> List[str]:
        rows = self._conn.execute(
            "SELECT tag_id FROM document_tags WHERE document_id = ? ORDER BY tag_id ASC",
            (document_id,),
        ).fetchall()
        return [r[0] for r in rows]

    def list_documents_by_tag(self, tag_id: str) -> List[str]:
        rows = self._conn.execute(
            "SELECT document_id FROM document_tags WHERE tag_id = ? ORDER BY document_id ASC",
            (tag_id,),
       ).fetchall()
        return [r[0] for r in rows]


def _row_to_tag(row: sqlite3.Row) -> Tag:
    return Tag(
        id=row["id"],
        name=row["name"],
        color=row["color"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )
