"""
test_ingestion_usecases.py — 摄入用例测试。

验证：
  - 正常摄入流程（扫描 → 分块 → 存储 → 索引）
  - 空目录处理
  - 重建索引（force_reindex=True）
  - 不存在的工作区抛 NotFoundError
"""
from __future__ import annotations

import dataclasses
from pathlib import Path

import pytest

from src.application.container import AppContainer
from src.application.ingestion_usecases import IngestWorkspaceUseCase, IngestProgress
from src.application.workspace_usecases import WorkspaceUseCases
from src.config.settings import load_settings
from src.domain.errors import NotFoundError


@pytest.fixture
def setup(tmp_path):
    """返回 (container, ws_usecases, ingest_uc, kb_dir)。"""
    kb = tmp_path / "kb"
    (kb / "resume").mkdir(parents=True)
    (kb / "resume" / "profile.md").write_text(
        "# 简历\n\nPython FastAPI RAG 向量检索 微服务",
        encoding="utf-8"
    )
    (kb / "resume" / "projects.md").write_text(
        "# 项目经历\n\n## RAG 系统\n搭建了完整的 RAG 流程。",
        encoding="utf-8"
    )

    s = load_settings(override_env={
        "RAG_KB_ROOT": str(kb),
        "RAG_RUNTIME_DIR": str(tmp_path / "runtime"),
        "RAG_RETRIEVER_KIND": "keyword",
        "RAG_EMBED_PROVIDER": "none",
    })
    s = dataclasses.replace(s, db_path=Path(":memory:"))
    container = AppContainer.build_for_testing(s)

    ws_uc = WorkspaceUseCases(container.workspace_store)
    ingest_uc = IngestWorkspaceUseCase(
        workspace_store=container.workspace_store,
        document_store=container.document_store,
        chunk_store=container.chunk_store,
        task_store=container.task_store,
        retriever=container.retriever,
        settings=container.settings,
    )
    return container, ws_uc, ingest_uc, kb


class TestIngestWorkspaceUseCase:

    def _run(self, ingest_uc, ws_id, force=False) -> IngestProgress:
        """驱动生成器，返回最后一个 IngestProgress。"""
        last = None
        for progress in ingest_uc.execute(ws_id, force_reindex=force):
            last = progress
        return last

    def test_basic_ingest(self, setup):
        container, ws_uc, ingest_uc, kb = setup
        ws = ws_uc.create("测试工作区", str(kb))
        result = self._run(ingest_uc, ws.id)

        assert result.done is True
        assert result.error is None
        assert result.total >= 2          # 至少扫到 2 个文件
        assert container.chunk_store.count_by_workspace(ws.id) > 0

    def test_chunks_are_retrievable(self, setup):
        container, ws_uc, ingest_uc, kb = setup
        ws = ws_uc.create("ws", str(kb))
        self._run(ingest_uc, ws.id)

        # KeywordRetriever 索引已建立，应能搜到 chunk
        from src.ports.retriever import RetrievalQuery
        result = container.retriever.search(
            RetrievalQuery(question="Python RAG", workspace_id=ws.id)
        )
        assert len(result.chunks) > 0

    def test_workspace_status_updated(self, setup):
        container, ws_uc, ingest_uc, kb = setup
        ws = ws_uc.create("ws", str(kb))
        self._run(ingest_uc, ws.id)

        ws_updated = container.workspace_store.get(ws.id)
        assert ws_updated.last_index_status == "ok"
        assert ws_updated.supported_files >= 1

    def test_force_reindex_clears_old_chunks(self, setup):
        container, ws_uc, ingest_uc, kb = setup
        ws = ws_uc.create("ws", str(kb))

        # 第一次摄入
        self._run(ingest_uc, ws.id)
        count_1 = container.chunk_store.count_by_workspace(ws.id)
        assert count_1 > 0

        # 强制重建
        self._run(ingest_uc, ws.id, force=True)
        count_2 = container.chunk_store.count_by_workspace(ws.id)
        assert count_2 == count_1   # 重建后数量应相同

    def test_empty_directory(self, tmp_path):
        empty_kb = tmp_path / "empty_kb"
        empty_kb.mkdir()

        s = load_settings(override_env={
            "RAG_KB_ROOT": str(empty_kb),
            "RAG_RUNTIME_DIR": str(tmp_path / "runtime"),
            "RAG_RETRIEVER_KIND": "keyword",
            "RAG_EMBED_PROVIDER": "none",
        })
        s = dataclasses.replace(s, db_path=Path(":memory:"))
        container = AppContainer.build_for_testing(s)
        ws_uc = WorkspaceUseCases(container.workspace_store)
        ingest_uc = IngestWorkspaceUseCase(
            container.workspace_store, container.document_store,
            container.chunk_store, container.task_store,
            container.retriever, container.settings,
        )
        ws = ws_uc.create("empty", str(empty_kb))
        result = self._run(ingest_uc, ws.id)

        assert result.done is True
        assert result.error is None
        assert container.chunk_store.count_by_workspace(ws.id) == 0

    def test_nonexistent_workspace_raises(self, setup):
        _, _, ingest_uc, _ = setup
        with pytest.raises(NotFoundError):
            list(ingest_uc.execute("no-such-ws"))

    def test_progress_yields_messages(self, setup):
        container, ws_uc, ingest_uc, kb = setup
        ws = ws_uc.create("ws", str(kb))

        progresses = list(ingest_uc.execute(ws.id))
        assert len(progresses) > 1   # 至少有「扫描」+「完成」两条
        assert all(isinstance(p, IngestProgress) for p in progresses)
