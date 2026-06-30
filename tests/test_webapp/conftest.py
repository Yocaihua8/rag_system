import pytest

import backend.config.settings as settings_module


@pytest.fixture(autouse=True)
def _clear_web_llm_env(monkeypatch, tmp_path):
    for key in (
        "RAG_LLM_PROVIDER",
        "RAG_LLM_API_BASE",
        "RAG_LLM_API_KEY",
        "RAG_LLM_API_MODEL",
        "RAG_LLM_TEMPERATURE",
        "RAG_LLM_MAX_TOKENS",
        "DEEPSEEK_API_KEY",
        "DEEPSEEK_APIKEY",
        "DeepSeekApiKey",
        "deepseekapikey",
        "RAG_RERANKER_ENABLED",
        "RAG_RERANKER_MODEL",
    ):
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setenv("APPDATA", str(tmp_path / "appdata"))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "xdg-config"))
    monkeypatch.setattr(settings_module, "_project_root", lambda: tmp_path)
    monkeypatch.setattr(settings_module, "_persistent_env", lambda: {})
