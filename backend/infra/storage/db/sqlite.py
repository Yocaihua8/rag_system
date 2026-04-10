from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Set


PROJECT_ROOT = Path(__file__).resolve().parents[3]
RUNTIME_DIR = PROJECT_ROOT / "runtime"
RUNTIME_DB = RUNTIME_DIR / "app.db"


def get_connection() -> sqlite3.Connection:
    RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(RUNTIME_DB))
    conn.execute("PRAGMA journal_mode=WAL;")
    return conn


def init_runtime_db() -> None:
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS workspaces (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                root_path TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS tasks (
                id TEXT PRIMARY KEY,
                kind TEXT NOT NULL,
                status TEXT NOT NULL,
                progress INTEGER NOT NULL,
                message TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS conversations (
                id TEXT PRIMARY KEY,
                workspace_id TEXT NOT NULL,
                question TEXT NOT NULL,
                answer TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS app_settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
            """
        )
        _ensure_workspace_columns(conn)


def _ensure_workspace_columns(conn: sqlite3.Connection) -> None:
    cols = _table_columns(conn, "workspaces")
    if "last_indexed_at" not in cols:
        conn.execute("ALTER TABLE workspaces ADD COLUMN last_indexed_at TEXT DEFAULT ''")
    if "last_index_status" not in cols:
        conn.execute("ALTER TABLE workspaces ADD COLUMN last_index_status TEXT DEFAULT ''")
    if "total_files" not in cols:
        conn.execute("ALTER TABLE workspaces ADD COLUMN total_files INTEGER DEFAULT 0")
    if "supported_files" not in cols:
        conn.execute("ALTER TABLE workspaces ADD COLUMN supported_files INTEGER DEFAULT 0")


def _table_columns(conn: sqlite3.Connection, table: str) -> Set[str]:
    rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
    return {str(r[1]) for r in rows}

