"""
SQLite 连接工厂与 Schema 初始化。
路径完全由 AppSettings.db_path 决定，无任何硬编码。
"""
from __future__ import annotations

import sqlite3
from pathlib import Path


def create_connection(db_path: Path) -> sqlite3.Connection:
    """
    创建并返回一个 SQLite 连接。
    - WAL 模式：提升并发读写性能
    - Row factory：允许按列名访问
    """
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path), check_same_thread=False)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA foreign_keys=ON;")
    conn.row_factory = sqlite3.Row
    return conn


def init_schema(conn: sqlite3.Connection) -> None:
    """创建所有表（幂等，若已存在则跳过）。"""
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS workspaces (
            id                  TEXT PRIMARY KEY,
            name                TEXT NOT NULL,
            root_path           TEXT NOT NULL,
            created_at          TEXT NOT NULL,
            last_indexed_at     TEXT NOT NULL DEFAULT '',
            last_index_status   TEXT NOT NULL DEFAULT '',
            total_files         INTEGER NOT NULL DEFAULT 0,
            supported_files     INTEGER NOT NULL DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS documents (
            id              TEXT PRIMARY KEY,
            workspace_id    TEXT NOT NULL,
            title           TEXT NOT NULL,
            source_path     TEXT NOT NULL,
            content         TEXT NOT NULL,
            domain          TEXT NOT NULL DEFAULT 'general',
            tags            TEXT NOT NULL DEFAULT '[]',
            created_at      TEXT NOT NULL,
            FOREIGN KEY (workspace_id) REFERENCES workspaces(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS chunks (
            id              TEXT PRIMARY KEY,
            document_id     TEXT NOT NULL,
            workspace_id    TEXT NOT NULL,
            domain          TEXT NOT NULL DEFAULT 'general',
            tags            TEXT NOT NULL DEFAULT '[]',
            content         TEXT NOT NULL,
            ord             INTEGER NOT NULL DEFAULT 0,
            FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE,
            FOREIGN KEY (workspace_id) REFERENCES workspaces(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS project_knowledge_points (
            id              TEXT PRIMARY KEY,
            workspace_id    TEXT NOT NULL,
            name            TEXT NOT NULL,
            kind            TEXT NOT NULL,
            summary         TEXT NOT NULL,
            source_path     TEXT NOT NULL,
            evidence        TEXT NOT NULL,
            confidence      REAL NOT NULL,
            created_at      TEXT NOT NULL,
            FOREIGN KEY (workspace_id) REFERENCES workspaces(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS tasks (
            id          TEXT PRIMARY KEY,
            kind        TEXT NOT NULL,
            status      TEXT NOT NULL,
            progress    INTEGER NOT NULL DEFAULT 0,
            message     TEXT NOT NULL DEFAULT '',
            created_at  TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS conversations (
            id              TEXT PRIMARY KEY,
            workspace_id    TEXT NOT NULL,
            question        TEXT NOT NULL,
            answer          TEXT NOT NULL,
            created_at      TEXT NOT NULL,
            FOREIGN KEY (workspace_id) REFERENCES workspaces(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS app_settings (
            key     TEXT PRIMARY KEY,
            value   TEXT NOT NULL
        );
    """)
    conn.commit()
    _ensure_indexes(conn)


def _ensure_indexes(conn: sqlite3.Connection) -> None:
    """创建查询常用索引（幂等）。"""
    conn.executescript("""
        CREATE INDEX IF NOT EXISTS idx_documents_workspace
            ON documents(workspace_id);
        CREATE INDEX IF NOT EXISTS idx_chunks_workspace
            ON chunks(workspace_id);
        CREATE INDEX IF NOT EXISTS idx_chunks_document
            ON chunks(document_id);
        CREATE INDEX IF NOT EXISTS idx_pkp_workspace
            ON project_knowledge_points(workspace_id);
        CREATE INDEX IF NOT EXISTS idx_pkp_workspace_kind
            ON project_knowledge_points(workspace_id, kind);
        CREATE INDEX IF NOT EXISTS idx_conversations_workspace
            ON conversations(workspace_id);
        CREATE INDEX IF NOT EXISTS idx_tasks_created
            ON tasks(created_at DESC);
    """)
    conn.commit()
