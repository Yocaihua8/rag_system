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

        CREATE TABLE IF NOT EXISTS projects (
            id              TEXT PRIMARY KEY,
            name            TEXT NOT NULL,
            description     TEXT NOT NULL DEFAULT '',
            root_path       TEXT NOT NULL DEFAULT '',
            created_at      TEXT NOT NULL,
            updated_at      TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS documents (
            id              TEXT PRIMARY KEY,
            workspace_id    TEXT NOT NULL,
            project_id      TEXT NOT NULL DEFAULT '',
            title           TEXT NOT NULL,
            source_type     TEXT NOT NULL DEFAULT '',
            source_path     TEXT NOT NULL,
            content         TEXT NOT NULL,
            raw_content     TEXT NOT NULL DEFAULT '',
            normalized_markdown TEXT NOT NULL DEFAULT '',
            plain_text      TEXT NOT NULL DEFAULT '',
            rendered_html   TEXT NOT NULL DEFAULT '',
            domain          TEXT NOT NULL DEFAULT 'general',
            tags            TEXT NOT NULL DEFAULT '[]',
            created_at      TEXT NOT NULL,
            updated_at      TEXT NOT NULL DEFAULT '',
            FOREIGN KEY (workspace_id) REFERENCES workspaces(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS chunks (
            id              TEXT PRIMARY KEY,
            document_id     TEXT NOT NULL,
            workspace_id    TEXT NOT NULL,
            project_id      TEXT NOT NULL DEFAULT '',
            domain          TEXT NOT NULL DEFAULT 'general',
            tags            TEXT NOT NULL DEFAULT '[]',
            content         TEXT NOT NULL,
            ord             INTEGER NOT NULL DEFAULT 0,
            chunk_index     INTEGER NOT NULL DEFAULT 0,
            heading_path    TEXT NOT NULL DEFAULT '[]',
            chunk_markdown  TEXT NOT NULL DEFAULT '',
            chunk_plain_text TEXT NOT NULL DEFAULT '',
            token_count     INTEGER NOT NULL DEFAULT 0,
            embedding_id    TEXT NOT NULL DEFAULT '',
            created_at      TEXT NOT NULL DEFAULT '',
            updated_at      TEXT NOT NULL DEFAULT '',
            FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE,
            FOREIGN KEY (workspace_id) REFERENCES workspaces(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS tags (
            id          TEXT PRIMARY KEY,
            name        TEXT NOT NULL,
            color       TEXT NOT NULL DEFAULT '',
            created_at  TEXT NOT NULL,
            updated_at  TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS document_tags (
            document_id TEXT NOT NULL,
            tag_id      TEXT NOT NULL,
            PRIMARY KEY (document_id, tag_id),
            FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE,
            FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS sources (
            id              TEXT PRIMARY KEY,
            document_id     TEXT NOT NULL,
            source_type     TEXT NOT NULL,
            source_path     TEXT NOT NULL,
            imported_at     TEXT NOT NULL,
            checksum        TEXT NOT NULL DEFAULT '',
            FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE
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

        CREATE TABLE IF NOT EXISTS skill_areas (
            id              TEXT PRIMARY KEY,
            workspace_id    TEXT NOT NULL,
            name            TEXT NOT NULL,
            description     TEXT NOT NULL,
            created_at      TEXT NOT NULL,
            updated_at      TEXT NOT NULL,
            FOREIGN KEY (workspace_id) REFERENCES workspaces(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS knowledge_points (
            id              TEXT PRIMARY KEY,
            workspace_id    TEXT NOT NULL,
            skill_area_id   TEXT NOT NULL,
            name            TEXT NOT NULL,
            summary         TEXT NOT NULL,
            confidence      REAL NOT NULL,
            created_at      TEXT NOT NULL,
            updated_at      TEXT NOT NULL,
            FOREIGN KEY (workspace_id) REFERENCES workspaces(id) ON DELETE CASCADE,
            FOREIGN KEY (skill_area_id) REFERENCES skill_areas(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS evidences (
            id                  TEXT PRIMARY KEY,
            workspace_id        TEXT NOT NULL,
            knowledge_point_id   TEXT NOT NULL,
            source_path         TEXT NOT NULL,
            snippet             TEXT NOT NULL,
            confidence          REAL NOT NULL,
            created_at          TEXT NOT NULL,
            FOREIGN KEY (workspace_id) REFERENCES workspaces(id) ON DELETE CASCADE,
            FOREIGN KEY (knowledge_point_id) REFERENCES knowledge_points(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS mastery_records (
            id                  TEXT PRIMARY KEY,
            workspace_id        TEXT NOT NULL,
            knowledge_point_id   TEXT NOT NULL,
            status              TEXT NOT NULL,
            evidence_id         TEXT NOT NULL DEFAULT '',
            confidence          REAL NOT NULL,
            note                TEXT NOT NULL DEFAULT '',
            created_at          TEXT NOT NULL,
            updated_at          TEXT NOT NULL,
            FOREIGN KEY (workspace_id) REFERENCES workspaces(id) ON DELETE CASCADE,
            FOREIGN KEY (knowledge_point_id) REFERENCES knowledge_points(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS graph_nodes (
            id              TEXT PRIMARY KEY,
            workspace_id    TEXT NOT NULL,
            name            TEXT NOT NULL,
            label           TEXT NOT NULL,
            node_type       TEXT NOT NULL,
            source_ref      TEXT NOT NULL DEFAULT '',
            confidence      REAL NOT NULL,
            created_at      TEXT NOT NULL,
            updated_at      TEXT NOT NULL,
            FOREIGN KEY (workspace_id) REFERENCES workspaces(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS graph_edges (
            id                  TEXT PRIMARY KEY,
            workspace_id        TEXT NOT NULL,
            source_node_id      TEXT NOT NULL,
            target_node_id      TEXT NOT NULL,
            relationship        TEXT NOT NULL,
            confidence          REAL NOT NULL,
            source_path         TEXT NOT NULL DEFAULT '',
            source_snippet      TEXT NOT NULL DEFAULT '',
            created_at          TEXT NOT NULL,
            updated_at          TEXT NOT NULL,
            FOREIGN KEY (workspace_id) REFERENCES workspaces(id) ON DELETE CASCADE,
            FOREIGN KEY (source_node_id) REFERENCES graph_nodes(id) ON DELETE CASCADE,
            FOREIGN KEY (target_node_id) REFERENCES graph_nodes(id) ON DELETE CASCADE
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
    _ensure_columns(conn)
    _ensure_indexes(conn)


def _ensure_columns(conn: sqlite3.Connection) -> None:
    """为已有本地数据库追加新列，避免破坏旧安装。"""
    _add_missing_columns(conn, "documents", {
        "project_id": "TEXT NOT NULL DEFAULT ''",
        "source_type": "TEXT NOT NULL DEFAULT ''",
        "raw_content": "TEXT NOT NULL DEFAULT ''",
        "normalized_markdown": "TEXT NOT NULL DEFAULT ''",
        "plain_text": "TEXT NOT NULL DEFAULT ''",
        "rendered_html": "TEXT NOT NULL DEFAULT ''",
        "updated_at": "TEXT NOT NULL DEFAULT ''",
    })
    _add_missing_columns(conn, "chunks", {
        "project_id": "TEXT NOT NULL DEFAULT ''",
        "chunk_index": "INTEGER NOT NULL DEFAULT 0",
        "heading_path": "TEXT NOT NULL DEFAULT '[]'",
        "chunk_markdown": "TEXT NOT NULL DEFAULT ''",
        "chunk_plain_text": "TEXT NOT NULL DEFAULT ''",
        "token_count": "INTEGER NOT NULL DEFAULT 0",
        "embedding_id": "TEXT NOT NULL DEFAULT ''",
        "created_at": "TEXT NOT NULL DEFAULT ''",
        "updated_at": "TEXT NOT NULL DEFAULT ''",
    })
    conn.commit()


def _add_missing_columns(
    conn: sqlite3.Connection,
    table_name: str,
    columns: dict[str, str],
) -> None:
    existing = {
        row["name"]
        for row in conn.execute(f"PRAGMA table_info({table_name})").fetchall()
    }
    for column, ddl in columns.items():
        if column not in existing:
            conn.execute(f"ALTER TABLE {table_name} ADD COLUMN {column} {ddl}")


def _ensure_indexes(conn: sqlite3.Connection) -> None:
    """创建查询常用索引（幂等）。"""
    conn.executescript("""
        CREATE INDEX IF NOT EXISTS idx_documents_workspace
            ON documents(workspace_id);
        CREATE INDEX IF NOT EXISTS idx_documents_project
            ON documents(project_id);
        CREATE INDEX IF NOT EXISTS idx_chunks_workspace
            ON chunks(workspace_id);
        CREATE INDEX IF NOT EXISTS idx_chunks_project
            ON chunks(project_id);
        CREATE INDEX IF NOT EXISTS idx_chunks_document
            ON chunks(document_id);
        CREATE INDEX IF NOT EXISTS idx_sources_document
            ON sources(document_id);
        CREATE INDEX IF NOT EXISTS idx_sources_checksum
            ON sources(checksum);
        CREATE INDEX IF NOT EXISTS idx_pkp_workspace
            ON project_knowledge_points(workspace_id);
        CREATE INDEX IF NOT EXISTS idx_pkp_workspace_kind
            ON project_knowledge_points(workspace_id, kind);
        CREATE INDEX IF NOT EXISTS idx_skill_areas_workspace
            ON skill_areas(workspace_id);
        CREATE INDEX IF NOT EXISTS idx_kp_workspace
            ON knowledge_points(workspace_id);
        CREATE INDEX IF NOT EXISTS idx_kp_skill_area
            ON knowledge_points(skill_area_id);
        CREATE INDEX IF NOT EXISTS idx_evidences_workspace
            ON evidences(workspace_id);
        CREATE INDEX IF NOT EXISTS idx_evidences_point
            ON evidences(knowledge_point_id);
        CREATE INDEX IF NOT EXISTS idx_mastery_workspace
            ON mastery_records(workspace_id);
        CREATE INDEX IF NOT EXISTS idx_mastery_point
            ON mastery_records(knowledge_point_id);
        CREATE INDEX IF NOT EXISTS idx_mastery_status
            ON mastery_records(status);
        CREATE INDEX IF NOT EXISTS idx_conversations_workspace
            ON conversations(workspace_id);
        CREATE INDEX IF NOT EXISTS idx_graph_nodes_workspace
            ON graph_nodes(workspace_id);
        CREATE INDEX IF NOT EXISTS idx_graph_nodes_type
            ON graph_nodes(workspace_id, node_type);
        CREATE INDEX IF NOT EXISTS idx_graph_edges_workspace
            ON graph_edges(workspace_id);
        CREATE INDEX IF NOT EXISTS idx_graph_edges_source
            ON graph_edges(source_node_id);
        CREATE INDEX IF NOT EXISTS idx_graph_edges_target
            ON graph_edges(target_node_id);
        CREATE INDEX IF NOT EXISTS idx_tasks_created
            ON tasks(created_at DESC);
    """)
    conn.commit()
