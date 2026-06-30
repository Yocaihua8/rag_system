from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from backend.config.paths import app_data_dir, app_env_file, ensure_kb_dirs, ensure_runtime_dirs, kb_domain_dir, kb_raw_dir


def test_app_data_dir_is_platform_aware():
    home = Path("/Users/tester")

    assert str(
        app_data_dir(
            system="Windows",
            environ={"APPDATA": r"C:\Users\tester\AppData\Roaming"},
            home=home,
        )
    ).endswith(r"C:\Users\tester\AppData\Roaming\KnowledgeIsland")
    assert app_data_dir(system="Windows", environ={}, home=home) == home / "AppData" / "Roaming" / "KnowledgeIsland"
    assert app_data_dir(system="Darwin", environ={}, home=home) == home / "Library" / "Application Support" / "KnowledgeIsland"
    assert app_data_dir(system="Linux", environ={"XDG_CONFIG_HOME": "/tmp/config"}, home=home) == Path(
        "/tmp/config"
    ) / "KnowledgeIsland"
    assert app_data_dir(system="Linux", environ={}, home=home) == home / ".config" / "KnowledgeIsland"


def test_app_env_file_uses_app_data_dir():
    assert app_env_file("CustomApp") == app_data_dir("CustomApp") / ".env"


def test_ensure_runtime_dirs_creates_all_runtime_locations(tmp_path):
    settings = SimpleNamespace(
        runtime_dir=tmp_path / "runtime",
        vector_dir=tmp_path / "runtime" / "vectors",
        logs_dir=tmp_path / "runtime" / "logs",
        outputs_dir=tmp_path / "runtime" / "outputs",
        app_data_dir=tmp_path / "appdata",
    )

    ensure_runtime_dirs(settings)

    assert settings.runtime_dir.is_dir()
    assert settings.vector_dir.is_dir()
    assert settings.logs_dir.is_dir()
    assert settings.outputs_dir.is_dir()
    assert settings.app_data_dir.is_dir()


def test_kb_paths_and_ensure_kb_dirs_create_expected_domains(tmp_path):
    settings = SimpleNamespace(kb_root=tmp_path / "kb")

    assert kb_raw_dir(settings) == tmp_path / "kb" / "raw"
    assert kb_domain_dir(settings, "notes") == tmp_path / "kb" / "raw" / "notes"

    ensure_kb_dirs(settings)

    for domain in ("resume", "jds", "notes", "paper", "prompts"):
        assert (tmp_path / "kb" / "raw" / domain).is_dir()
