from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import src.config.settings as settings_module
from src.config.settings import load_settings
from src.desktop.controllers.settings_controller import SettingsController


def test_settings_controller_saves_string_and_numeric_fields(tmp_path, monkeypatch):
    appdata = tmp_path / "appdata"
    appdata.mkdir()
    monkeypatch.setattr(settings_module, "_app_data_dir", lambda: appdata)
    monkeypatch.setattr(settings_module, "_persistent_env", lambda: {})
    for key in [
        "RAG_KB_ROOT",
        "RAG_OLLAMA_MODEL",
        "RAG_LLM_TEMPERATURE",
        "RAG_LLM_MAX_TOKENS",
    ]:
        monkeypatch.delenv(key, raising=False)
    settings = load_settings(override_env={
        "RAG_RUNTIME_DIR": str(tmp_path / "runtime"),
        "RAG_KB_ROOT": str(tmp_path / "kb"),
    })
    controller = SettingsController(settings)
    saved_settings = []
    errors = []
    controller.settings_saved.connect(saved_settings.append)
    controller.error_occurred.connect(errors.append)

    controller.save({
        "kb_root": str(tmp_path / "new-kb"),
        "ollama_model": "qwen2.5:7b",
        "llm_temperature": 0.0,
        "llm_max_tokens": 256,
    })

    assert errors == []
    assert len(saved_settings) == 1
    saved = saved_settings[0]
    assert str(saved.kb_root) == str(tmp_path / "new-kb")
    assert saved.ollama_model == "qwen2.5:7b"
    assert saved.llm_temperature == 0.0
    assert saved.llm_max_tokens == 256


def test_main_window_delegates_settings_save_to_controller():
    source = (settings_module._project_root() / "src" / "desktop" / "views" / "main_window.py").read_text(
        encoding="utf-8"
    )

    assert "SettingsController" in source
    assert "SettingsUseCases" not in source
    assert "def _on_settings_save" not in source
