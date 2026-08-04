from __future__ import annotations

from pathlib import Path

import pytest

import backend.config.v3 as v3_config


def _isolate(monkeypatch, tmp_path: Path) -> Path:
    project_root = tmp_path / "project"
    project_root.mkdir()
    monkeypatch.setattr(v3_config, "_project_root", lambda: project_root)
    monkeypatch.setattr(v3_config, "load_backend_env", lambda: {})
    for key in (
        "KI_DATA_ROOT",
        "KI_V3_DB_PATH",
        "KI_AGENT_MAX_CONCURRENCY",
        "KI_AGENT_LEASE_SECONDS",
        "KI_AGENT_POLL_INTERVAL_MS",
        "KI_V3_BACKUP_RETENTION",
        "RAG_RUNTIME_DIR",
    ):
        monkeypatch.delenv(key, raising=False)
    return project_root


def test_v3_settings_use_isolated_default_generation_root(monkeypatch, tmp_path):
    project_root = _isolate(monkeypatch, tmp_path)
    monkeypatch.setenv("RAG_RUNTIME_DIR", str(tmp_path / "legacy-v2"))

    settings = v3_config.load_v3_settings()

    assert settings.data_root == (project_root / "runtime" / "v3").resolve()
    assert settings.db_path == settings.data_root / "app.db"
    assert settings.vector_dir == settings.data_root / "vectors"
    assert settings.artifacts_dir == settings.data_root / "artifacts"
    assert settings.logs_dir == settings.data_root / "logs"
    assert settings.backups_dir == settings.data_root / "backups"
    assert settings.max_concurrency == 2
    assert settings.lease_seconds == 30
    assert settings.poll_interval_ms == 100
    assert settings.backup_retention == 7


def test_v3_settings_apply_explicit_paths_and_bounded_executor_values(
    monkeypatch, tmp_path
):
    _isolate(monkeypatch, tmp_path)
    data_root = tmp_path / "agent-data"
    db_path = tmp_path / "database" / "agent.db"

    settings = v3_config.load_v3_settings(
        {
            "KI_DATA_ROOT": str(data_root),
            "KI_V3_DB_PATH": str(db_path),
            "KI_AGENT_MAX_CONCURRENCY": "1",
            "KI_AGENT_LEASE_SECONDS": "90",
            "KI_AGENT_POLL_INTERVAL_MS": "250",
            "KI_V3_BACKUP_RETENTION": "5",
        }
    )

    assert settings.data_root == data_root.resolve()
    assert settings.db_path == db_path.resolve()
    assert settings.max_concurrency == 1
    assert settings.lease_seconds == 90
    assert settings.poll_interval_ms == 250
    assert settings.backup_retention == 5


@pytest.mark.parametrize(
    ("key", "value"),
    [
        ("KI_AGENT_MAX_CONCURRENCY", "3"),
        ("KI_AGENT_LEASE_SECONDS", "4"),
        ("KI_AGENT_POLL_INTERVAL_MS", "0"),
        ("KI_AGENT_POLL_INTERVAL_MS", "not-an-int"),
        ("KI_V3_BACKUP_RETENTION", "0"),
        ("KI_V3_BACKUP_RETENTION", "101"),
    ],
)
def test_v3_settings_reject_invalid_executor_limits(monkeypatch, tmp_path, key, value):
    _isolate(monkeypatch, tmp_path)

    with pytest.raises(ValueError, match=key):
        v3_config.load_v3_settings({key: value})


def test_ensure_v3_runtime_dirs_creates_only_declared_v3_locations(
    monkeypatch, tmp_path
):
    _isolate(monkeypatch, tmp_path)
    settings = v3_config.load_v3_settings(
        {"KI_DATA_ROOT": str(tmp_path / "runtime" / "v3")}
    )

    v3_config.ensure_v3_runtime_dirs(settings)

    for path in (
        settings.data_root,
        settings.db_path.parent,
        settings.vector_dir,
        settings.artifacts_dir,
        settings.logs_dir,
        settings.backups_dir,
    ):
        assert path.is_dir()
    assert not (tmp_path / "runtime" / "v2").exists()
