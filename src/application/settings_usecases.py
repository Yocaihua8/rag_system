from __future__ import annotations

from src.config.settings import AppSettings, load_settings, save_setting


class SettingsUseCases:

    def __init__(self, settings: AppSettings) -> None:
        self._settings = settings

    def get_current(self) -> AppSettings:
        return self._settings

    def save_kb_root(self, path: str) -> AppSettings:
        save_setting("RAG_KB_ROOT", path, self._settings)
        self._settings = load_settings()
        return self._settings

    def save_ollama_host(self, host: str) -> AppSettings:
        save_setting("RAG_OLLAMA_HOST", host, self._settings)
        self._settings = load_settings()
        return self._settings

    def save_ollama_model(self, model: str) -> AppSettings:
        save_setting("RAG_OLLAMA_MODEL", model, self._settings)
        self._settings = load_settings()
        return self._settings

    def save_embedding_model(self, model: str) -> AppSettings:
        save_setting("RAG_EMBEDDING_MODEL", model, self._settings)
        self._settings = load_settings()
        return self._settings

    def save_llm_provider(self, provider: str) -> AppSettings:
        save_setting("RAG_LLM_PROVIDER", provider, self._settings)
        self._settings = load_settings()
        return self._settings

    def save_llm_api_base(self, base_url: str) -> AppSettings:
        save_setting("RAG_LLM_API_BASE", base_url, self._settings)
        self._settings = load_settings()
        return self._settings

    def save_llm_api_key(self, api_key: str) -> AppSettings:
        """
        将 API Key 写入 appdata/.env。
        若用户已通过 OS 环境变量设置，则此方法不应被调用（UI 层会禁用）。
        """
        save_setting("RAG_LLM_API_KEY", api_key, self._settings)
        self._settings = load_settings()
        return self._settings

    def save_llm_api_model(self, model: str) -> AppSettings:
        save_setting("RAG_LLM_API_MODEL", model, self._settings)
        self._settings = load_settings()
        return self._settings

    def save_embed_provider(self, provider: str) -> AppSettings:
        save_setting("RAG_EMBED_PROVIDER", provider, self._settings)
        self._settings = load_settings()
        return self._settings

    def save_llm_temperature(self, temperature: float) -> AppSettings:
        save_setting("RAG_LLM_TEMPERATURE", str(temperature), self._settings)
        self._settings = load_settings()
        return self._settings

    def save_llm_max_tokens(self, max_tokens: int) -> AppSettings:
        save_setting("RAG_LLM_MAX_TOKENS", str(max_tokens), self._settings)
        self._settings = load_settings()
        return self._settings
