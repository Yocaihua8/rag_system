"""
从 AppSettings 派生的路径辅助函数。
调用方直接传入 AppSettings 实例，不持有全局状态。
"""
from __future__ import annotations

from pathlib import Path

from src.config.settings import AppSettings


def kb_raw_dir(s: AppSettings) -> Path:
    """知识库原始文件根目录。"""
    return s.kb_root / "raw"


def kb_domain_dir(s: AppSettings, domain: str) -> Path:
    """按领域分类的原始文件目录，如 raw/resume、raw/jds。"""
    return kb_raw_dir(s) / domain


def ensure_runtime_dirs(s: AppSettings) -> None:
    """创建所有运行时目录（首次启动 / 测试 setup 时调用）。"""
    for path in (
        s.runtime_dir,
        s.vector_dir,
        s.logs_dir,
        s.outputs_dir,
        s.app_data_dir,
    ):
        path.mkdir(parents=True, exist_ok=True)


def ensure_kb_dirs(s: AppSettings) -> None:
    """创建知识库目录结构（首次运行向导完成后调用）。"""
    for domain in ("resume", "jds", "notes", "paper", "prompts"):
        kb_domain_dir(s, domain).mkdir(parents=True, exist_ok=True)
