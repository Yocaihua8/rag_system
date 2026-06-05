"""
test_settings_usecases.py — SettingsUseCases 读写往返测试。

覆盖：
  - get_current 返回当前 AppSettings
  - 各 save_* 方法将值持久化后 load_settings 可读回
  - save_llm_temperature / save_llm_max_tokens (P5 新增)
  - 多字段连续保存互不干扰

关键点：
  save_setting() 写入 settings.app_data_dir/.env，
  load_settings() 通过 _app_data_dir() 决定读哪个目录。
  需 monkeypatch _app_data_dir 使两者指向同一个临时目录，
  否则会读到测试机上的真实用户配置，断言失败。
"""
from __future__ import annotations

import pytest

import legacy.desktop.config.settings as settings_module
from legacy.desktop.application.settings_usecases import SettingsUseCases
from legacy.desktop.config.settings import AppSettings, load_settings


@pytest.fixture(autouse=True)
def _clear_llm_env(monkeypatch):
    for key in (
        "RAG_LLM_PROVIDER",
        "RAG_LLM_API_BASE",
        "RAG_LLM_API_KEY",
        "RAG_LLM_API_MODEL",
        "DEEPSEEK_API_KEY",
        "DEEPSEEK_APIKEY",
        "DeepSeekApiKey",
        "deepseekapikey",
    ):
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setattr(settings_module, "_persistent_env", lambda: {})


# ── Fixture ───────────────────────────────────────────────────────────────────

@pytest.fixture
def uc(tmp_path, monkeypatch) -> SettingsUseCases:
    """
    将 _app_data_dir 重定向到 tmp_path/appdata，
    使 save_setting 与 load_settings 读写同一临时目录。
    """
    appdata = tmp_path / "appdata"
    appdata.mkdir(parents=True)
    monkeypatch.setattr(settings_module, "_app_data_dir", lambda: appdata)

    settings = load_settings(override_env={
        "RAG_RUNTIME_DIR": str(tmp_path / "runtime"),
        "RAG_KB_ROOT":     str(tmp_path / "kb"),
    })
    return SettingsUseCases(settings)


# ── 基础 ──────────────────────────────────────────────────────────────────────

class TestGetCurrent:

    def test_returns_app_settings(self, uc):
        s = uc.get_current()
        assert isinstance(s, AppSettings)

    def test_default_paths_use_knowledge_island_names(self, tmp_path, monkeypatch):
        appdata_base = tmp_path / "roaming"
        monkeypatch.setenv("APPDATA", str(appdata_base))
        monkeypatch.delenv("RAG_KB_ROOT", raising=False)
        monkeypatch.delenv("RAG_RUNTIME_DIR", raising=False)
        monkeypatch.setattr(settings_module, "_project_root", lambda: tmp_path / "repo")

        s = load_settings()

        assert s.kb_root.name == "KnowledgeIslandKB"
        assert s.app_data_dir.name == "KnowledgeIsland"


# ── 各字段保存 ────────────────────────────────────────────────────────────────

class TestSaveKbRoot:

    def test_save_and_load(self, uc, tmp_path):
        new_path = str(tmp_path / "new_kb")
        s = uc.save_kb_root(new_path)
        assert str(s.kb_root) == new_path


class TestSaveOllamaHost:

    def test_save_and_load(self, uc):
        s = uc.save_ollama_host("http://127.0.0.1:11434")
        assert s.ollama_host == "http://127.0.0.1:11434"


class TestSaveOllamaModel:

    def test_save_and_load(self, uc):
        s = uc.save_ollama_model("llama3:8b")
        assert s.ollama_model == "llama3:8b"


class TestSaveLLMProvider:

    def test_save_api_provider(self, uc):
        s = uc.save_llm_provider("api")
        assert s.llm_provider == "api"

    def test_save_ollama_provider(self, uc):
        s = uc.save_llm_provider("ollama")
        assert s.llm_provider == "ollama"


class TestSaveLLMApiBase:

    def test_save_and_load(self, uc):
        url = "https://api.deepseek.com/v1"
        s = uc.save_llm_api_base(url)
        assert s.llm_api_base == url


class TestSaveLLMApiModel:

    def test_save_and_load(self, uc):
        s = uc.save_llm_api_model("deepseek-chat")
        assert s.llm_api_model == "deepseek-chat"


class TestDeepSeekEnvAlias:

    def test_deepseek_api_key_env_enables_api_provider(self, tmp_path, monkeypatch):
        monkeypatch.setattr(settings_module, "_app_data_dir", lambda: tmp_path / "appdata")
        monkeypatch.setattr(settings_module, "_project_root", lambda: tmp_path / "repo")
        monkeypatch.setenv("DEEPSEEK_API_KEY", "sk-deepseek")

        s = load_settings(override_env={
            "RAG_RUNTIME_DIR": str(tmp_path / "runtime"),
            "RAG_KB_ROOT": str(tmp_path / "kb"),
        })

        assert s.llm_provider == "api"
        assert s.llm_api_key == "sk-deepseek"
        assert s.llm_api_base == "https://api.deepseek.com/v1"
        assert s.llm_api_model == "deepseek-chat"

    def test_deepseekapikey_override_env_alias(self, tmp_path, monkeypatch):
        monkeypatch.setattr(settings_module, "_app_data_dir", lambda: tmp_path / "appdata")
        monkeypatch.setattr(settings_module, "_project_root", lambda: tmp_path / "repo")

        s = load_settings(override_env={
            "RAG_RUNTIME_DIR": str(tmp_path / "runtime"),
            "RAG_KB_ROOT": str(tmp_path / "kb"),
            "deepseekapikey": "sk-local",
        })

        assert s.llm_provider == "api"
        assert s.llm_api_key == "sk-local"

    def test_windows_persistent_user_env_alias_is_read_when_process_env_is_missing(self, tmp_path, monkeypatch):
        monkeypatch.setattr(settings_module, "_app_data_dir", lambda: tmp_path / "appdata")
        monkeypatch.setattr(settings_module, "_project_root", lambda: tmp_path / "repo")
        monkeypatch.setattr(
            settings_module,
            "_persistent_env",
            lambda: {"DEEPSEEK_API_KEY": "sk-user-env"},
            raising=False,
        )

        s = load_settings(override_env={
            "RAG_RUNTIME_DIR": str(tmp_path / "runtime"),
            "RAG_KB_ROOT": str(tmp_path / "kb"),
        })

        assert s.llm_provider == "api"
        assert s.llm_api_key == "sk-user-env"

    def test_explicit_provider_env_can_keep_ollama(self, tmp_path, monkeypatch):
        monkeypatch.setattr(settings_module, "_app_data_dir", lambda: tmp_path / "appdata")
        monkeypatch.setattr(settings_module, "_project_root", lambda: tmp_path / "repo")
        monkeypatch.setenv("DEEPSEEK_API_KEY", "sk-deepseek")
        monkeypatch.setenv("RAG_LLM_PROVIDER", "ollama")

        s = load_settings(override_env={
            "RAG_RUNTIME_DIR": str(tmp_path / "runtime"),
            "RAG_KB_ROOT": str(tmp_path / "kb"),
        })

        assert s.llm_provider == "ollama"
        assert s.llm_api_key == "sk-deepseek"


class TestSaveEmbedProvider:

    def test_save_none(self, uc):
        s = uc.save_embed_provider("none")
        assert s.embed_provider == "none"

    def test_save_ollama(self, uc):
        s = uc.save_embed_provider("ollama")
        assert s.embed_provider == "ollama"


# ── P5 新增：temperature / max_tokens ─────────────────────────────────────────

class TestSaveLLMTemperature:

    def test_save_typical_value(self, uc):
        s = uc.save_llm_temperature(0.7)
        assert abs(s.llm_temperature - 0.7) < 1e-9

    def test_save_zero(self, uc):
        s = uc.save_llm_temperature(0.0)
        assert s.llm_temperature == 0.0

    def test_save_max_value(self, uc):
        s = uc.save_llm_temperature(2.0)
        assert abs(s.llm_temperature - 2.0) < 1e-9


class TestSaveLLMMaxTokens:

    def test_save_and_load(self, uc):
        s = uc.save_llm_max_tokens(2048)
        assert s.llm_max_tokens == 2048

    def test_save_min_value(self, uc):
        s = uc.save_llm_max_tokens(256)
        assert s.llm_max_tokens == 256

    def test_save_large_value(self, uc):
        s = uc.save_llm_max_tokens(8192)
        assert s.llm_max_tokens == 8192


# ── 多字段连续保存互不干扰 ────────────────────────────────────────────────────

class TestMultiFieldSave:

    def test_sequential_saves_do_not_override(self, uc):
        uc.save_ollama_model("qwen2.5:7b")
        uc.save_llm_temperature(0.5)
        s = uc.save_llm_max_tokens(1024)
        # 三个字段都应正确保存
        assert s.ollama_model == "qwen2.5:7b"
        assert abs(s.llm_temperature - 0.5) < 1e-9
        assert s.llm_max_tokens == 1024


class TestEnvFilePreserveFormatting:

    def test_save_preserves_comments_and_blank_lines(self, uc):
        env_file = uc._settings.app_data_dir / ".env"
        env_file.write_text(
            "# 运行时配置\n"
            "RAG_KB_ROOT=\"old/path\"\n"
            "\n"
            "# 模型参数\n"
            "RAG_OLLAMA_HOST=http://127.0.0.1:11434\n"
            "RAG_LLM_TEMPERATURE=\"0.5\"\n"
            "\n",
            encoding="utf-8",
        )

        uc.save_ollama_host("http://localhost:11434")

        lines = env_file.read_text(encoding="utf-8").splitlines()
        assert lines[0] == "# 运行时配置"
        assert lines[1] == "RAG_KB_ROOT=\"old/path\""
        assert lines[2] == ""
        assert lines[3] == "# 模型参数"
        assert lines[4] == "RAG_OLLAMA_HOST=\"http://localhost:11434\""
        assert lines[5] == "RAG_LLM_TEMPERATURE=\"0.5\""
