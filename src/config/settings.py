"""
配置层入口。

加载优先级（高 → 低）：
  1. OS 环境变量
  2. {app_data_dir}/.env   （用户通过 Settings UI 写入的运行时配置）
  3. {project_root}/.env   （开发者本地覆盖，gitignore）
  4. src/config/defaults.py（兜底，无硬编码路径）

唯一依赖：stdlib。不引入任何第三方库。
"""
from __future__ import annotations

import os
import platform
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from src.config import defaults


# ---------------------------------------------------------------------------
# AppSettings
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class AppSettings:
    # 知识库根目录（用户可配置）
    kb_root: Path

    # 运行时目录（均相对项目根，除非用户显式覆盖）
    runtime_dir: Path
    db_path: Path           # runtime_dir / app.db
    vector_dir: Path        # runtime_dir / vectors
    logs_dir: Path          # runtime_dir / logs
    outputs_dir: Path       # runtime_dir / outputs

    # 用户配置持久化目录（平台相关）
    app_data_dir: Path

    # Ollama
    ollama_host: str
    ollama_model: str
    embedding_model: str
    embedding_dim: int

    # 检索
    retriever_kind: str     # "vector" | "keyword"
    chunk_size: int
    chunk_overlap: int
    retrieval_top_k: int

    # LLM 生成
    llm_temperature: float
    llm_max_tokens: int

    # LLM 提供商
    llm_provider: str       # "ollama" | "api"
    llm_api_base: str       # OpenAI 兼容接口地址
    llm_api_key: str        # API Key（优先从 OS 环境变量读取）
    llm_api_model: str      # 云端模型名

    # Embedding 提供商
    embed_provider: str     # "ollama" | "none"


# ---------------------------------------------------------------------------
# 内部辅助
# ---------------------------------------------------------------------------

def _app_data_dir() -> Path:
    """返回平台对应的应用数据目录。"""
    system = platform.system()
    if system == "Windows":
        base = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
    elif system == "Darwin":
        base = Path.home() / "Library" / "Application Support"
    else:
        base = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
    return base / "CareerAssistant"


def _project_root() -> Path:
    """推断项目根目录（src/ 的上一层）。"""
    return Path(__file__).resolve().parents[2]


def _parse_env_file(path: Path) -> dict[str, str]:
    """
    解析 .env 文件，返回 key→value 字典。
    支持：
      - KEY=VALUE
      - KEY="VALUE"（去除引号）
      - # 注释行
      - 空行忽略
    """
    result: dict[str, str] = {}
    if not path.exists():
        return result
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        result[key] = value
    return result


def _resolve(env: dict[str, str], key: str, fallback: str) -> str:
    """从合并后的环境字典中取值，缺失时用 fallback。"""
    return env.get(key, fallback)


# ---------------------------------------------------------------------------
# 公开 API
# ---------------------------------------------------------------------------

def load_settings(override_env: Optional[dict[str, str]] = None) -> AppSettings:
    """
    按优先级合并配置并返回冻结的 AppSettings 实例。

    Parameters
    ----------
    override_env : dict, optional
        测试时可传入，直接覆盖所有来源（最高优先级）。
    """
    app_data = _app_data_dir()
    project_root = _project_root()

    # 从低到高叠加，后者覆盖前者
    env: dict[str, str] = {}

    # 层 4：项目根 .env（开发者本地）
    env.update(_parse_env_file(project_root / ".env"))

    # 层 3：appdata/.env（用户运行时设置）
    env.update(_parse_env_file(app_data / ".env"))

    # 层 2：OS 环境变量
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
        # LLM 提供商（API Key 优先从 OS 环境变量读取，不写文件）
        "RAG_LLM_PROVIDER",
        "RAG_LLM_API_BASE",
        "RAG_LLM_API_KEY",
        "RAG_LLM_API_MODEL",
        "RAG_EMBED_PROVIDER",
    ):
        if key in os.environ:
            env[key] = os.environ[key]

    # 层 1：测试覆盖（最高优先级）
    if override_env:
        env.update(override_env)

    # --- 解析各字段 ---

    kb_root = Path(
        _resolve(env, "RAG_KB_ROOT", defaults.KB_ROOT)
    ).expanduser().resolve()

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
        llm_temperature=float(
            _resolve(env, "RAG_LLM_TEMPERATURE", defaults.LLM_TEMPERATURE)
        ),
        llm_max_tokens=int(
            _resolve(env, "RAG_LLM_MAX_TOKENS", defaults.LLM_MAX_TOKENS)
        ),
        llm_provider=_resolve(env, "RAG_LLM_PROVIDER", defaults.LLM_PROVIDER),
        llm_api_base=_resolve(env, "RAG_LLM_API_BASE", defaults.LLM_API_BASE),
        llm_api_key=_resolve(env, "RAG_LLM_API_KEY", defaults.LLM_API_KEY),
        llm_api_model=_resolve(env, "RAG_LLM_API_MODEL", defaults.LLM_API_MODEL),
        embed_provider=_resolve(env, "RAG_EMBED_PROVIDER", defaults.EMBED_PROVIDER),
    )


def save_setting(key: str, value: str, settings: AppSettings) -> None:
    """
    将单个配置项持久化到 app_data_dir/.env。
    由 SettingsUseCases 调用，不直接暴露给 UI。
    """
    env_file = settings.app_data_dir / ".env"
    settings.app_data_dir.mkdir(parents=True, exist_ok=True)

    # 读取现有内容
    existing = _parse_env_file(env_file)
    existing[key] = value

    # 回写
    lines = [f'{k}="{v}"' for k, v in sorted(existing.items())]
    env_file.write_text("\n".join(lines) + "\n", encoding="utf-8")
