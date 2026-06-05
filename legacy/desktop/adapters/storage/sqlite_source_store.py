from __future__ import annotations

import sqlite3

from legacy.desktop.domain.models.source import Source
from legacy.desktop.ports.source_store import ISourceStore


class SqliteSourceStore(ISourceStore):

    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def save(self, source: Source) -> None:
        self._conn.execute(
            """
            INSERT OR REPLACE INTO sources
                (id, document_id, source_type, source_path, imported_at, checksum)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                source.id, source.document_id, source.source_type,
                source.source_path, source.imported_at, source.checksum,
            ),
        )
        self._conn.commit()

    def get_by_document(self, document_id: str) -> Source | None:
        row = self._conn.execute(
            """
            SELECT * FROM sources
            WHERE document_id = ?
            ORDER BY imported_at DESC
            LIMIT 1
            """,
            (document_id,),
        ).fetchone()
        return _row_to_source(row) if row else None

    def find_by_path(self, source_path: str) -> Source | None:
        row = self._conn.execute(
            """
            SELECT * FROM sources
            WHERE source_path = ?
            ORDER BY imported_at DESC
            LIMIT 1
            """,
            (source_path,),
        ).fetchone()
        return _row_to_source(row) if row else None

    def exists_same_checksum(self, source_path: str, checksum: str) -> bool:
        row = self._conn.execute(
            """
            SELECT 1 FROM sources
            WHERE source_path = ?
            AND checksum = ?
            LIMIT 1
            """,
            (source_path, checksum),
        ).fetchone()
        return row is not None

    def delete_by_document(self, document_id: str) -> None:
        self._conn.execute(
            "DELETE FROM sources WHERE document_id = ?",
            (document_id,),
        )
        self._conn.commit()


def _row_to_source(row: sqlite3.Row) -> Source:
    return Source(
        id=row["id"],
        document_id=row["document_id"],
        source_type=row["source_type"],
        source_path=row["source_path"],
        imported_at=row["imported_at"],
        checksum=row["checksum"],
    )
