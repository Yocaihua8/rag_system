from __future__ import annotations

from typing import Callable

from PySide6.QtCore import QObject, Signal

from src.application.settings_usecases import SettingsUseCases
from src.config.settings import AppSettings


class SettingsController(QObject):
    settings_saved = Signal(object)
    error_occurred = Signal(str)

    def __init__(
        self,
        settings: AppSettings,
        parent=None,
        use_case_factory: Callable[[AppSettings], SettingsUseCases] = SettingsUseCases,
    ) -> None:
        super().__init__(parent)
        self._settings = settings
        self._use_case_factory = use_case_factory

    def save(self, data: dict) -> None:
        try:
            uc = self._use_case_factory(self._settings)
            save_map = {
                "kb_root": uc.save_kb_root,
                "ollama_host": uc.save_ollama_host,
                "ollama_model": uc.save_ollama_model,
                "embedding_model": uc.save_embedding_model,
                "llm_provider": uc.save_llm_provider,
                "llm_api_base": uc.save_llm_api_base,
                "llm_api_key": uc.save_llm_api_key,
                "llm_api_model": uc.save_llm_api_model,
                "embed_provider": uc.save_embed_provider,
            }
            latest_settings = self._settings
            for field, save_fn in save_map.items():
                if data.get(field):
                    latest_settings = save_fn(data[field])
            if "llm_temperature" in data:
                latest_settings = uc.save_llm_temperature(data["llm_temperature"])
            if "llm_max_tokens" in data:
                latest_settings = uc.save_llm_max_tokens(data["llm_max_tokens"])
            self._settings = latest_settings
            self.settings_saved.emit(latest_settings)
        except Exception as exc:
            self.error_occurred.emit(str(exc))
