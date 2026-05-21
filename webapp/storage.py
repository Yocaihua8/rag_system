from __future__ import annotations

import hashlib
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path

from webapp.chunking import count_tokens, split_into_chunks
from webapp.models import Document, DocumentChunk, Project


class DocumentWriteResult:
    def __init__(self, document: Document, action: str):
        self.document = document
        self.action = action


class KnowledgeStore:
    def __init__(self, db_path: Path):
        self.db_path = Path(db_path)
        if str(self.db_path) != ":memory:":
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def create_project(self, name: str, root_path: Path) -> Project:
        project = Project(
            id=str(uuid.uuid4()),
            name=name.strip() or Path(root_path).name,
            root_path=Path(root_path),
            created_at=_now(),
        )
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO projects (id, name, root_path, created_at) VALUES (?, ?, ?, ?)",
                (project.id, project.name, str(project.root_path), project.created_at),
            )
        return project

    def list_projects(self) -> list[Project]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT id, name, root_path, created_at FROM projects ORDER BY created_at DESC"
            ).fetchall()
        return [_project_from_row(row) for row in rows]

    def get_project(self, project_id: str) -> Project | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT id, name, root_path, created_at FROM projects WHERE id = ?",
                (project_id,),
            ).fetchone()
        return _project_from_row(row) if row else None

    def rename_project(self, project_id: str, name: str) -> Project | None:
        clean_name = name.strip()
        with self._connect() as conn:
            result = conn.execute(
                "UPDATE projects SET name = ? WHERE id = ?",
                (clean_name, project_id),
            )
        if result.rowcount == 0:
            return None
        return self.get_project(project_id)

    def delete_project(self, project_id: str) -> bool:
        with self._connect() as conn:
            result = conn.execute("DELETE FROM projects WHERE id = ?", (project_id,))
        return result.rowcount > 0

    def upsert_document(
        self,
        project_id: str,
        source_path: Path,
        relative_path: str,
        content: str,
    ) -> DocumentWriteResult:
        checksum = hashlib.sha256(content.encode("utf-8")).hexdigest()
        now = _now()
        document_id = str(uuid.uuid4())
        action = "created"
        with self._connect() as conn:
            existing = conn.execute(
                "SELECT id, checksum FROM documents WHERE project_id = ? AND relative_path = ?",
                (project_id, relative_path),
            ).fetchone()
            if existing:
                document_id = existing["id"]
                action = "unchanged" if existing["checksum"] == checksum else "updated"
            document = Document(
                document_id,
                project_id,
                source_path,
                relative_path,
                content,
                checksum,
                now,
            )
            conn.execute(
                """
                INSERT INTO documents
                    (id, project_id, source_path, relative_path, content, checksum, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(project_id, relative_path) DO UPDATE SET
                    source_path = excluded.source_path,
                    content = excluded.content,
                    checksum = excluded.checksum,
                    updated_at = excluded.updated_at
                """,
                (
                    document_id,
                    project_id,
                    str(source_path),
                    relative_path,
                    content,
                    checksum,
                    now,
                ),
            )
            self._replace_document_chunks(conn, document)
        return DocumentWriteResult(document=document, action=action)

    def list_documents(self, project_id: str) -> list[Document]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT id, project_id, source_path, relative_path, content, checksum, updated_at
                FROM documents
                WHERE project_id = ?
                ORDER BY relative_path ASC
                """,
                (project_id,),
            ).fetchall()
        return [_document_from_row(row) for row in rows]

    def list_chunks(self, project_id: str) -> list[DocumentChunk]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT
                    c.id AS chunk_id,
                    c.chunk_index,
                    c.content AS chunk_content,
                    c.token_count,
                    c.created_at AS chunk_created_at,
                    d.id,
                    d.project_id,
                    d.source_path,
                    d.relative_path,
                    d.content,
                    d.checksum,
                    d.updated_at
                FROM document_chunks c
                JOIN documents d ON d.id = c.document_id
                WHERE c.project_id = ?
                ORDER BY d.relative_path ASC, c.chunk_index ASC
                """,
                (project_id,),
            ).fetchall()
        return [_chunk_from_row(row) for row in rows]

    def get_document(self, document_id: str) -> Document | None:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT id, project_id, source_path, relative_path, content, checksum, updated_at
                FROM documents
                WHERE id = ?
                """,
                (document_id,),
            ).fetchone()
        return _document_from_row(row) if row else None

    def delete_document(self, document_id: str) -> Document | None:
        document = self.get_document(document_id)
        if not document:
            return None
        with self._connect() as conn:
            conn.execute("DELETE FROM documents WHERE id = ?", (document_id,))
        return document

    def delete_documents_not_in(self, project_id: str, relative_paths: set[str]) -> int:
        existing_paths = {doc.relative_path for doc in self.list_documents(project_id)}
        stale_paths = sorted(existing_paths - relative_paths)
        if not stale_paths:
            return 0
        with self._connect() as conn:
            conn.executemany(
                "DELETE FROM documents WHERE project_id = ? AND relative_path = ?",
                [(project_id, relative_path) for relative_path in stale_paths],
            )
        return len(stale_paths)

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def _init_schema(self) -> None:
        with self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS projects (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    root_path TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS documents (
                    id TEXT PRIMARY KEY,
                    project_id TEXT NOT NULL,
                    source_path TEXT NOT NULL,
                    relative_path TEXT NOT NULL,
                    content TEXT NOT NULL,
                    checksum TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    UNIQUE(project_id, relative_path),
                    FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE CASCADE
                );

                CREATE INDEX IF NOT EXISTS idx_documents_project
                    ON documents(project_id);

                CREATE TABLE IF NOT EXISTS document_chunks (
                    id TEXT PRIMARY KEY,
                    document_id TEXT NOT NULL,
                    project_id TEXT NOT NULL,
                    chunk_index INTEGER NOT NULL,
                    content TEXT NOT NULL,
                    token_count INTEGER NOT NULL,
                    created_at TEXT NOT NULL,
                    UNIQUE(document_id, chunk_index),
                    FOREIGN KEY(document_id) REFERENCES documents(id) ON DELETE CASCADE
                );

                CREATE INDEX IF NOT EXISTS idx_document_chunks_project
                    ON document_chunks(project_id);
                """
            )
            self._backfill_document_chunks(conn)

    def _replace_document_chunks(self, conn: sqlite3.Connection, document: Document) -> None:
        conn.execute("DELETE FROM document_chunks WHERE document_id = ?", (document.id,))
        rows = []
        now = _now()
        for index, chunk in enumerate(split_into_chunks(document.content)):
            rows.append(
                (
                    str(uuid.uuid4()),
                    document.id,
                    document.project_id,
                    index,
                    chunk,
                    count_tokens(chunk),
                    now,
                )
            )
        conn.executemany(
            """
            INSERT INTO document_chunks
                (id, document_id, project_id, chunk_index, content, token_count, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            rows,
        )

    def _backfill_document_chunks(self, conn: sqlite3.Connection) -> None:
        rows = conn.execute(
            """
            SELECT
                d.id,
                d.project_id,
                d.source_path,
                d.relative_path,
                d.content,
                d.checksum,
                d.updated_at
            FROM documents d
            LEFT JOIN document_chunks c ON c.document_id = d.id
            WHERE c.id IS NULL
            """
        ).fetchall()
        for row in rows:
            self._replace_document_chunks(conn, _document_from_row(row))


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _project_from_row(row: sqlite3.Row) -> Project:
    return Project(row["id"], row["name"], Path(row["root_path"]), row["created_at"])


def _document_from_row(row: sqlite3.Row) -> Document:
    return Document(
        row["id"],
        row["project_id"],
        Path(row["source_path"]),
        row["relative_path"],
        row["content"],
        row["checksum"],
        row["updated_at"],
    )


def _chunk_from_row(row: sqlite3.Row) -> DocumentChunk:
    document = Document(
        row["id"],
        row["project_id"],
        Path(row["source_path"]),
        row["relative_path"],
        row["content"],
        row["checksum"],
        row["updated_at"],
    )
    return DocumentChunk(
        id=row["chunk_id"],
        document=document,
        chunk_index=row["chunk_index"],
        content=row["chunk_content"],
        token_count=row["token_count"],
        created_at=row["chunk_created_at"],
    )
