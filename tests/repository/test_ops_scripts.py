import os
import shutil
import sqlite3
import subprocess
from pathlib import Path

import pytest


SCRIPT_DIR = Path("ops/scripts")


def _script(name: str) -> str:
    return (SCRIPT_DIR / name).read_text(encoding="utf-8")


def _bash_executable() -> str | None:
    if os.name == "nt":
        program_files = Path(os.environ.get("ProgramFiles", r"C:\Program Files"))
        git_bash = program_files / "Git" / "bin" / "bash.exe"
        if git_bash.is_file():
            return str(git_bash)
    return shutil.which("bash")


def test_ops_scripts_exist_and_use_strict_bash():
    expected = {"backup_db.sh", "cleanup_runtime.sh", "rebuild_index.sh"}

    assert {path.name for path in SCRIPT_DIR.glob("*.sh")} == expected
    for name in expected:
        script = _script(name)
        assert script.startswith("#!/usr/bin/env bash")
        assert "set -euo pipefail" in script
        assert 'PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"' in script


def test_backup_db_script_uses_safe_defaults_and_backup_commands():
    script = _script("backup_db.sh")

    assert 'DB_PATH="${KI_DB_PATH:-$PROJECT_ROOT/runtime/v2/app.db}"' in script
    assert 'BACKUP_DIR="${KI_BACKUP_DIR:-$PROJECT_ROOT/runtime/v2/backups}"' in script
    assert 'BACKUP_RETENTION="${KI_BACKUP_RETENTION:-7}"' in script
    assert "sqlite3" in script
    assert ".backup" in script
    assert 'cygpath -m "$DB_BACKUP_PATH"' in script
    assert "RAG_QDRANT_PATH" in script
    assert "KI_QDRANT_DIR" in script
    assert "tar -czf" in script
    assert "find \"$BACKUP_DIR\"" in script


def test_backup_db_script_creates_restorable_v2_database(tmp_path):
    bash = _bash_executable()
    if bash is None:
        pytest.skip("bash is required to execute the operations backup script")

    project_root = tmp_path / "project"
    script_path = project_root / "ops" / "scripts" / "backup_db.sh"
    script_path.parent.mkdir(parents=True)
    shutil.copy2(SCRIPT_DIR / "backup_db.sh", script_path)

    database_path = project_root / "runtime" / "v2" / "app.db"
    database_path.parent.mkdir(parents=True)
    with sqlite3.connect(database_path) as connection:
        connection.execute(
            "CREATE TABLE app_metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL)"
        )
        connection.execute(
            "INSERT INTO app_metadata (key, value) VALUES (?, ?)",
            ("data_generation", "v2"),
        )
        connection.execute(
            "CREATE TABLE backup_verification "
            "(id INTEGER PRIMARY KEY, content TEXT NOT NULL)"
        )
        connection.execute(
            "INSERT INTO backup_verification (content) VALUES (?)",
            ("knowledge-island-v2",),
        )

    environment = os.environ.copy()
    for variable in (
        "KI_DB_PATH",
        "KI_BACKUP_DIR",
        "KI_QDRANT_DIR",
        "RAG_QDRANT_PATH",
    ):
        environment.pop(variable, None)
    environment["KI_BACKUP_RETENTION"] = "2"
    completed = subprocess.run(
        [bash, str(script_path)],
        cwd=project_root,
        env=environment,
        text=True,
        capture_output=True,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr
    if shutil.which("sqlite3") is not None:
        assert "falling back to file copy" not in completed.stderr
    backup_files = list(
        (project_root / "runtime" / "v2" / "backups").glob(
            "knowledge-island-v2-*.sqlite3"
        )
    )
    assert len(backup_files) == 1

    restored_database = tmp_path / "restored" / "app.db"
    restored_database.parent.mkdir()
    shutil.copy2(backup_files[0], restored_database)
    with sqlite3.connect(restored_database) as connection:
        assert connection.execute("PRAGMA integrity_check").fetchone() == ("ok",)
        assert connection.execute(
            "SELECT value FROM app_metadata WHERE key = 'data_generation'"
        ).fetchone() == ("v2",)
        assert connection.execute(
            "SELECT content FROM backup_verification"
        ).fetchall() == [("knowledge-island-v2",)]


def test_cleanup_runtime_script_keeps_persistent_data_safe():
    script = _script("cleanup_runtime.sh")

    assert 'RUNTIME_DIR="${KI_RUNTIME_DIR:-$PROJECT_ROOT/runtime/v2}"' in script
    assert "app.db" in script
    assert "RAG_QDRANT_PATH" in script
    assert "KI_QDRANT_DIR" in script
    assert "__pycache__" in script
    assert "*.pyc" in script
    assert "find \"$RUNTIME_DIR\"" in script
    assert 'rm -rf "$RUNTIME_DIR"' not in script
    assert "runtime/v2/backups" in script


def test_rebuild_index_script_calls_admin_endpoint_with_optional_auth():
    script = _script("rebuild_index.sh")

    assert 'BASE_URL="${KI_BASE_URL:-http://127.0.0.1:8765}"' in script
    assert "/api/admin/rebuild-index" in script
    assert "curl" in script
    assert "KI_PROJECT_ID" in script
    assert "KI_API_KEY" in script
    assert "X-API-Key:" in script
    assert "KI_BEARER_TOKEN" in script
    assert "Authorization: Bearer" in script
    assert "Content-Type: application/json" in script
