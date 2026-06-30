from __future__ import annotations

from pathlib import Path

from backend.config.settings import API_KEY_ENV_NAMES, AppSettings


def _clear_settings_env(monkeypatch) -> None:
    keys = (
        "RAG_KB_ROOT",
        "RAG_RUNTIME_DIR",
        "RAG_OLLAMA_HOST",
        "RAG_OLLAMA_MODEL",
        "RAG_EMBEDDING_MODEL",
        "RAG_EMBEDDING_DIM",
        "RAG_RETRIEVER_KIND",
        "RAG_CHUNK_SIZE",
        "RAG_CHUNK_OVERLAP",
        "RAG_TOP_K",
        "RAG_LLM_TEMPERATURE",
        "RAG_LLM_MAX_TOKENS",
        "RAG_LLM_PROVIDER",
        "RAG_LLM_API_BASE",
        "RAG_LLM_API_KEY",
        "RAG_LLM_API_MODEL",
        "RAG_EMBED_PROVIDER",
        "RAG_EMBED_API_BASE",
        "RAG_EMBED_API_KEY",
        "RAG_EMBED_API_MODEL",
        *API_KEY_ENV_NAMES,
    )
    for key in keys:
        monkeypatch.delenv(key, raising=False)


def _isolate_settings(monkeypatch, tmp_path):
    import backend.config.settings as settings_module

    project_root = tmp_path / "project"
    app_data = tmp_path / "appdata"
    project_root.mkdir()
    app_data.mkdir()
    monkeypatch.setattr(settings_module, "_project_root", lambda: project_root)
    monkeypatch.setattr(settings_module, "app_data_dir", lambda: app_data)
    monkeypatch.setattr(settings_module, "_persistent_env", lambda: {})
    _clear_settings_env(monkeypatch)
    return settings_module, project_root, app_data


def test_load_settings_uses_defaults_and_derived_paths(monkeypatch, tmp_path):
    settings_module, _, app_data = _isolate_settings(monkeypatch, tmp_path)

    settings = settings_module.load_settings({})

    assert settings.kb_root == Path("~/KnowledgeIslandKB").expanduser().resolve()
    assert settings.runtime_dir == (tmp_path / "project" / "runtime").resolve()
    assert settings.db_path == settings.runtime_dir / "app.db"
    assert settings.vector_dir == settings.runtime_dir / "vectors"
    assert settings.logs_dir == settings.runtime_dir / "logs"
    assert settings.outputs_dir == settings.runtime_dir / "outputs"
    assert settings.app_data_dir == app_data
    assert settings.ollama_host == "http://localhost:11434"
    assert settings.ollama_model == "qwen2.5:7b"
    assert settings.embedding_dim == 768
    assert settings.llm_provider == "ollama"
    assert settings.llm_api_key == ""


def test_load_settings_applies_file_env_os_env_and_override_precedence(monkeypatch, tmp_path):
    settings_module, project_root, app_data = _isolate_settings(monkeypatch, tmp_path)
    (project_root / ".env").write_text(
        "\n".join(
            [
                "RAG_KB_ROOT='relative-kb'",
                "RAG_LLM_PROVIDER=ollama",
                "RAG_LLM_API_MODEL=project-model",
                "RAG_EMBEDDING_DIM=384",
            ]
        ),
        encoding="utf-8",
    )
    (app_data / ".env").write_text('RAG_LLM_API_MODEL="appdata-model"\n', encoding="utf-8")
    monkeypatch.setenv("RAG_LLM_PROVIDER", "api")

    settings = settings_module.load_settings(
        {
            "RAG_RUNTIME_DIR": str(tmp_path / "runtime-override"),
            "RAG_TOP_K": "12",
            "RAG_LLM_API_MODEL": "override-model",
        }
    )

    assert settings.kb_root == Path("relative-kb").resolve()
    assert settings.runtime_dir == (tmp_path / "runtime-override").resolve()
    assert settings.retrieval_top_k == 12
    assert settings.llm_provider == "api"
    assert settings.llm_api_model == "override-model"
    assert settings.embedding_dim == 384


def test_deepseek_alias_sets_api_provider_when_no_primary_key(monkeypatch, tmp_path):
    settings_module, _, _ = _isolate_settings(monkeypatch, tmp_path)
    monkeypatch.setenv("DEEPSEEK_API_KEY", "secret-from-os")

    settings = settings_module.load_settings({})

    assert settings.llm_provider == "api"
    assert settings.llm_api_base == "https://api.deepseek.com/v1"
    assert settings.llm_api_model == "deepseek-chat"
    assert settings.llm_api_key == "secret-from-os"


def test_deepseek_alias_does_not_replace_primary_api_key(monkeypatch, tmp_path):
    settings_module, _, _ = _isolate_settings(monkeypatch, tmp_path)
    monkeypatch.setenv("RAG_LLM_API_KEY", "primary-secret")
    monkeypatch.setenv("DEEPSEEK_API_KEY", "deepseek-secret")

    settings = settings_module.load_settings({})

    assert settings.llm_provider == "ollama"
    assert settings.llm_api_key == "primary-secret"


def test_get_api_key_env_name_prefers_process_env_then_persistent_env(monkeypatch, tmp_path):
    settings_module, _, _ = _isolate_settings(monkeypatch, tmp_path)
    monkeypatch.setenv("DEEPSEEK_APIKEY", "process-secret")
    monkeypatch.setattr(settings_module, "_persistent_env", lambda: {"RAG_LLM_API_KEY": "persistent-secret"})

    assert settings_module.get_api_key_env_name() == "DEEPSEEK_APIKEY"

    monkeypatch.delenv("DEEPSEEK_APIKEY")

    assert settings_module.get_api_key_env_name() == "RAG_LLM_API_KEY"


def test_save_setting_updates_or_appends_quoted_values(tmp_path):
    from backend.config.settings import save_setting

    settings = AppSettings(
        kb_root=tmp_path / "kb",
        runtime_dir=tmp_path / "runtime",
        db_path=tmp_path / "runtime" / "app.db",
        vector_dir=tmp_path / "runtime" / "vectors",
        logs_dir=tmp_path / "runtime" / "logs",
        outputs_dir=tmp_path / "runtime" / "outputs",
        app_data_dir=tmp_path / "appdata",
        ollama_host="",
        ollama_model="",
        embedding_model="",
        embedding_dim=768,
        retriever_kind="",
        chunk_size=512,
        chunk_overlap=64,
        retrieval_top_k=8,
        llm_temperature=0.7,
        llm_max_tokens=2048,
        llm_provider="",
        llm_api_base="",
        llm_api_key="",
        llm_api_model="",
        embed_provider="",
        embedding_api_base="",
        embedding_api_key="",
        embedding_api_model="",
    )
    settings.app_data_dir.mkdir()
    env_file = settings.app_data_dir / ".env"
    env_file.write_text("# keep comment\nRAG_LLM_PROVIDER=\"ollama\"\n", encoding="utf-8")

    save_setting("RAG_LLM_PROVIDER", 'api"value', settings)
    save_setting("RAG_LLM_API_MODEL", "deepseek-chat", settings)

    assert env_file.read_text(encoding="utf-8") == (
        '# keep comment\nRAG_LLM_PROVIDER="api\\"value"\nRAG_LLM_API_MODEL="deepseek-chat"\n'
    )
