"""
conftest.py — pytest 共用 fixtures。

所有测试：
  - 零网络依赖（DummyEmbedder + KeywordRetriever + FakeLLM）
  - 零文件副作用（内存 SQLite + 临时目录）
  - 通过 AppContainer.build_for_testing() 组装
"""
from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from legacy.desktop.config.settings import AppSettings, load_settings
from legacy.desktop.application.container import AppContainer


# ── 测试专用 AppSettings ─────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def tmp_root(tmp_path_factory):
    """会话级临时根目录，session 结束后自动清理。"""
    return tmp_path_factory.mktemp("rag_test")


@pytest.fixture
def test_settings(tmp_path) -> AppSettings:
    """每个测试独立的临时配置，使用内存 SQLite（:memory:）。"""
    return load_settings(override_env={
        "RAG_KB_ROOT":       str(tmp_path / "kb"),
        "RAG_RUNTIME_DIR":   str(tmp_path / "runtime"),
        "RAG_RETRIEVER_KIND": "keyword",
        "RAG_EMBED_PROVIDER": "none",
        "RAG_LLM_PROVIDER":   "ollama",   # build_for_testing 会用 FakeLLM 覆盖
    })


@pytest.fixture
def container(test_settings) -> AppContainer:
    """每个测试独立的 AppContainer（内存 SQLite，无外部服务）。"""
    # build_for_testing 使用 :memory: SQLite，不写磁盘
    s = load_settings(override_env={
        "RAG_KB_ROOT":       str(test_settings.kb_root),
        "RAG_RUNTIME_DIR":   str(test_settings.runtime_dir),
        "RAG_RETRIEVER_KIND": "keyword",
        "RAG_EMBED_PROVIDER": "none",
    })
    # 将 db_path 覆盖为 :memory:，彻底隔离
    import dataclasses
    s_mem = dataclasses.replace(s, db_path=Path(":memory:"))
    return AppContainer.build_for_testing(s_mem)


@pytest.fixture
def kb_dir(tmp_path) -> Path:
    """临时知识库目录，预置几个 .md 文件。"""
    kb = tmp_path / "kb"
    (kb / "resume").mkdir(parents=True)
    (kb / "jds").mkdir(parents=True)
    (kb / "resume" / "profile.md").write_text(
        "# 个人简介\n\n## 技能\nPython FastAPI RAG 向量检索\n\n## 经历\n参与过多个 RAG 系统搭建。",
        encoding="utf-8",
    )
    (kb / "jds" / "jd_001.md").write_text(
        "# JD-001 后端工程师\n\n要求：Python FastAPI 高并发 微服务",
        encoding="utf-8",
    )
    return kb
