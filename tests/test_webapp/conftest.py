import pytest


@pytest.fixture(autouse=True)
def _clear_web_llm_env(monkeypatch):
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
    ):
        monkeypatch.delenv(key, raising=False)
