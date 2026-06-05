from __future__ import annotations

from pathlib import Path

from legacy.desktop.config.settings import AppSettings, get_api_key_env_name, load_settings, save_setting
from backend.knowledge_island.llm import OpenAICompatibleChatClient, load_llm_config
from backend.knowledge_island.models import Document, SearchHit


def get_llm_settings_body(settings: AppSettings | None = None) -> dict:
    current = settings or load_settings()
    return {"settings": _settings_payload(current)}


def save_llm_settings(payload: dict) -> dict:
    current = load_settings()
    provider = _clean_choice(str(payload.get("provider", "")), {"api", "ollama"}, "api")
    api_base = str(payload.get("api_base", "")).strip() or current.llm_api_base
    model = str(payload.get("model", "")).strip() or current.llm_api_model
    api_key = str(payload.get("api_key", "")).strip()

    for key, value in (
        ("RAG_LLM_PROVIDER", provider),
        ("RAG_LLM_API_BASE", api_base),
        ("RAG_LLM_API_MODEL", model),
    ):
        save_setting(key, value, current)
    if api_key:
        save_setting("RAG_LLM_API_KEY", api_key, current)

    return get_llm_settings_body(load_settings())


def test_llm_settings() -> dict:
    client = OpenAICompatibleChatClient(load_llm_config(), timeout=20.0)
    if not client.is_configured():
        raise RuntimeError("LLM provider is not configured")
    document = Document(
        id="settings-test",
        project_id="settings",
        source_path=Path("settings-test.md"),
        relative_path="settings-test.md",
        content="知识岛模型连接测试。",
        checksum="settings-test",
        updated_at="",
    )
    hit = SearchHit(document=document, score=1.0, snippet="知识岛模型连接测试。")
    answer = client.generate_answer("请回复：连接正常。", [hit])
    return {"ok": True, "provider": client.provider, "message": answer[:200]}


def _settings_payload(settings: AppSettings) -> dict:
    env_key_name = get_api_key_env_name()
    return {
        "provider": settings.llm_provider,
        "api_base": settings.llm_api_base,
        "model": settings.llm_api_model,
        "has_api_key": bool(settings.llm_api_key.strip()),
        "api_key_source": "environment" if env_key_name else ("saved" if settings.llm_api_key else ""),
    }


def _clean_choice(value: str, allowed: set[str], fallback: str) -> str:
    clean = value.strip().lower()
    return clean if clean in allowed else fallback
