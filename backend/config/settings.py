from __future__ import annotations

import os
import platform
from dataclasses import dataclass
from pathlib import Path

from backend.config import defaults
from backend.config.paths import app_data_dir


API_KEY_ENV_NAMES = (
    "RAG_LLM_API_KEY",
    "deepseekapikey",
    "DEEPSEEK_API_KEY",
    "DEEPSEEK_APIKEY",
    "DeepSeekApiKey",
)


@dataclass(frozen=True)
class AppSettings:
    kb_root: Path
    runtime_dir: Path
    db_path: Path
    vector_dir: Path
    logs_dir: Path
    outputs_dir: Path
    app_data_dir: Path
    ollama_host: str
    ollama_model: str
    embedding_model: str
    embedding_dim: int
    retriever_kind: str
    chunk_size: int
    chunk_overlap: int
    retrieval_top_k: int
    llm_temperature: float
    llm_max_tokens: int
    llm_provider: str
    llm_api_base: str
    llm_api_key: str
    llm_api_model: str
    embed_provider: str
    embedding_api_base: str
    embedding_api_key: str
    embedding_api_model: str


def _project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _parse_env_file(path: Path) -> dict[str, str]:
    result: dict[str, str] = {}
    if not path.exists():
        return result
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        result[key.strip()] = value.strip().strip('"').strip("'")
    return result


def _resolve(env: dict[str, str], key: str, fallback: str) -> str:
    return env.get(key, fallback)


def _first_non_empty(env: dict[str, str], keys: tuple[str, ...]) -> str:
    for key in keys:
        value = env.get(key)
        if value:
            return value
    return ""


def get_api_key_env_name() -> str:
    for key in API_KEY_ENV_NAMES:
        if os.environ.get(key):
            return key
    for key in API_KEY_ENV_NAMES:
        if _persistent_env().get(key):
            return key
    return ""


def _apply_deepseek_env_alias(env: dict[str, str], source: dict[str, str]) -> None:
    deepseek_key = _first_non_empty(
        source,
        ("deepseekapikey", "DEEPSEEK_API_KEY", "DEEPSEEK_APIKEY", "DeepSeekApiKey"),
    )
    if not deepseek_key or source.get("RAG_LLM_API_KEY"):
        return

    env["RAG_LLM_API_KEY"] = deepseek_key
    if not source.get("RAG_LLM_PROVIDER"):
        env["RAG_LLM_PROVIDER"] = "api"
    if not source.get("RAG_LLM_API_BASE"):
        env["RAG_LLM_API_BASE"] = defaults.LLM_API_BASE
    if not source.get("RAG_LLM_API_MODEL"):
        env["RAG_LLM_API_MODEL"] = defaults.LLM_API_MODEL


def _persistent_env() -> dict[str, str]:
    if platform.system() != "Windows":
        return {}

    try:
        import winreg
    except ImportError:
        return {}

    keys = (
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
    result: dict[str, str] = {}
    locations = (
        (winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Control\Session Manager\Environment"),
        (winreg.HKEY_CURRENT_USER, "Environment"),
    )

    for root, path in locations:
        try:
            with winreg.OpenKey(root, path) as handle:
                for key in keys:
                    try:
                        value, _ = winreg.QueryValueEx(handle, key)
                    except OSError:
                        continue
                    if isinstance(value, str) and value:
                        result[key] = value
        except OSError:
            continue
    return result


def load_settings(override_env: dict[str, str] | None = None) -> AppSettings:
    app_data = app_data_dir()
    project_root = _project_root()

    env: dict[str, str] = {}
    env.update(_parse_env_file(project_root / ".env"))
    env.update(_parse_env_file(app_data / ".env"))

    persistent_env = _persistent_env()
    env.update(persistent_env)
    _apply_deepseek_env_alias(env, persistent_env)

    for key in (
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
    ):
        if key in os.environ:
            env[key] = os.environ[key]
    _apply_deepseek_env_alias(env, os.environ)

    if override_env:
        env.update(override_env)
        _apply_deepseek_env_alias(env, override_env)

    kb_root = Path(_resolve(env, "RAG_KB_ROOT", defaults.KB_ROOT)).expanduser().resolve()
    runtime_dir = Path(
        _resolve(env, "RAG_RUNTIME_DIR", str(project_root / "runtime"))
    ).expanduser().resolve()

    return AppSettings(
        kb_root=kb_root,
        runtime_dir=runtime_dir,
        db_path=runtime_dir / "app.db",
        vector_dir=runtime_dir / "vectors",
        logs_dir=runtime_dir / "logs",
        outputs_dir=runtime_dir / "outputs",
        app_data_dir=app_data,
        ollama_host=_resolve(env, "RAG_OLLAMA_HOST", defaults.OLLAMA_HOST),
        ollama_model=_resolve(env, "RAG_OLLAMA_MODEL", defaults.OLLAMA_MODEL),
        embedding_model=_resolve(env, "RAG_EMBEDDING_MODEL", defaults.EMBEDDING_MODEL),
        embedding_dim=int(_resolve(env, "RAG_EMBEDDING_DIM", defaults.EMBEDDING_DIM)),
        retriever_kind=_resolve(env, "RAG_RETRIEVER_KIND", defaults.RETRIEVER_KIND),
        chunk_size=int(_resolve(env, "RAG_CHUNK_SIZE", defaults.CHUNK_SIZE)),
        chunk_overlap=int(_resolve(env, "RAG_CHUNK_OVERLAP", defaults.CHUNK_OVERLAP)),
        retrieval_top_k=int(_resolve(env, "RAG_TOP_K", defaults.RETRIEVAL_TOP_K)),
        llm_temperature=float(_resolve(env, "RAG_LLM_TEMPERATURE", defaults.LLM_TEMPERATURE)),
        llm_max_tokens=int(_resolve(env, "RAG_LLM_MAX_TOKENS", defaults.LLM_MAX_TOKENS)),
        llm_provider=_resolve(env, "RAG_LLM_PROVIDER", defaults.LLM_PROVIDER),
        llm_api_base=_resolve(env, "RAG_LLM_API_BASE", defaults.LLM_API_BASE),
        llm_api_key=_resolve(env, "RAG_LLM_API_KEY", defaults.LLM_API_KEY),
        llm_api_model=_resolve(env, "RAG_LLM_API_MODEL", defaults.LLM_API_MODEL),
        embed_provider=_resolve(env, "RAG_EMBED_PROVIDER", defaults.EMBED_PROVIDER),
        embedding_api_base=_resolve(env, "RAG_EMBED_API_BASE", defaults.EMBED_API_BASE),
        embedding_api_key=_resolve(env, "RAG_EMBED_API_KEY", defaults.EMBED_API_KEY),
        embedding_api_model=_resolve(env, "RAG_EMBED_API_MODEL", defaults.EMBED_API_MODEL),
    )


def save_setting(key: str, value: str, settings: AppSettings) -> None:
    env_file = settings.app_data_dir / ".env"
    settings.app_data_dir.mkdir(parents=True, exist_ok=True)

    escaped_value = str(value).replace('"', '\\"')
    update_key = key.strip()
    updated_lines: list[str] = []
    found = False

    if env_file.exists():
        for raw_line in env_file.read_text(encoding="utf-8").splitlines():
            stripped = raw_line.strip()
            if stripped.startswith("#") or "=" not in raw_line or not stripped:
                updated_lines.append(raw_line)
                continue

            existing_key, _, _ = raw_line.partition("=")
            if existing_key.strip() == update_key:
                leading = raw_line[: len(raw_line) - len(raw_line.lstrip())]
                updated_lines.append(f'{leading}{update_key}="{escaped_value}"')
                found = True
            else:
                updated_lines.append(raw_line)

    if not found:
        updated_lines.append(f'{update_key}="{escaped_value}"')

    env_file.write_text("\n".join(updated_lines) + "\n", encoding="utf-8")


__all__ = [
    "API_KEY_ENV_NAMES",
    "AppSettings",
    "get_api_key_env_name",
    "load_settings",
    "save_setting",
]
