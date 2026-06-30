from pathlib import Path


SCRIPT_DIR = Path("ops/scripts")


def _script(name: str) -> str:
    return (SCRIPT_DIR / name).read_text(encoding="utf-8")


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

    assert 'DB_PATH="${KI_DB_PATH:-$PROJECT_ROOT/runtime/webapp/knowledge_island.db}"' in script
    assert 'BACKUP_DIR="${KI_BACKUP_DIR:-$PROJECT_ROOT/runtime/backups}"' in script
    assert 'BACKUP_RETENTION="${KI_BACKUP_RETENTION:-7}"' in script
    assert "sqlite3" in script
    assert ".backup" in script
    assert "RAG_QDRANT_PATH" in script
    assert "KI_QDRANT_DIR" in script
    assert "tar -czf" in script
    assert "find \"$BACKUP_DIR\"" in script


def test_cleanup_runtime_script_keeps_persistent_data_safe():
    script = _script("cleanup_runtime.sh")

    assert 'RUNTIME_DIR="${KI_RUNTIME_DIR:-$PROJECT_ROOT/runtime}"' in script
    assert "knowledge_island.db" in script
    assert "RAG_QDRANT_PATH" in script
    assert "KI_QDRANT_DIR" in script
    assert "__pycache__" in script
    assert "*.pyc" in script
    assert "find \"$RUNTIME_DIR\"" in script
    assert 'rm -rf "$RUNTIME_DIR"' not in script
    assert "runtime/backups" in script


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
