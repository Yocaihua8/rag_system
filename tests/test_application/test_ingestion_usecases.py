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

from src.application import ingestion_usecases
from src.application.container import AppContainer
from src.application.ingestion_usecases import IngestWorkspaceUseCase, IngestProgress
from src.application.workspace_usecases import WorkspaceUseCases
from src.config.settings import load_settings
from src.domain.errors import NotFoundError
from src.ports.retriever import RetrievalResult


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

    def test_incremental_ingest_reindexes_only_changed_file(self, setup):
        container, ws_uc, ingest_uc, kb = setup
        ws = ws_uc.create("ws", str(kb))
        self._run(ingest_uc, ws.id)

        before_docs = {
            d.source_path: d.id
            for d in container.document_store.list_by_workspace(ws.id)
        }
        assert str(kb / "resume" / "profile.md") in before_docs
        assert str(kb / "resume" / "projects.md") in before_docs

        changed_path = kb / "resume" / "profile.md"
        unchanged_path = kb / "resume" / "projects.md"
        changed_path.write_text(
            "# 简历（更新）\n\n新增一段改动文本。",
            encoding="utf-8",
        )

        before_changed_id = before_docs[str(changed_path)]
        before_unchanged_id = before_docs[str(unchanged_path)]

        class TrackingRetriever:
            def __init__(self):
                self.clear_calls: list[str] = []
                self.remove_calls: list[str] = []
                self.index_calls: list[list] = []
                self.indexed_document_ids: set[str] = set()

            def search(self, _query):
                return RetrievalResult(chunks=[], scores=[])

            def index(self, chunks):
                self.index_calls.append(chunks)
                self.indexed_document_ids.update(c.document_id for c in chunks)

            def clear(self, workspace_id: str) -> None:
                self.clear_calls.append(workspace_id)

            def remove_by_document(self, document_id: str) -> None:
                self.remove_calls.append(document_id)

        tracking = TrackingRetriever()
        ingest_uc_tracking = IngestWorkspaceUseCase(
            workspace_store=container.workspace_store,
            document_store=container.document_store,
            chunk_store=container.chunk_store,
            task_store=container.task_store,
            retriever=tracking,
            settings=container.settings,
        )
        self._run(ingest_uc_tracking, ws.id)

        after_docs = {
            d.source_path: d.id
            for d in container.document_store.list_by_workspace(ws.id)
        }
        after_unchanged_id = after_docs[str(unchanged_path)]
        after_changed_id = after_docs[str(changed_path)]

        assert tracking.clear_calls == []
        assert tracking.remove_calls == [before_changed_id]
        assert after_unchanged_id == before_unchanged_id
        assert after_changed_id != before_changed_id
        assert len(tracking.index_calls) == 1
        assert tracking.indexed_document_ids == {after_changed_id}

    def test_incremental_ingest_without_changes_skips_index(self, setup):
        container, ws_uc, ingest_uc, kb = setup
        ws = ws_uc.create("ws", str(kb))
        self._run(ingest_uc, ws.id)

        class TrackingRetriever:
            def __init__(self):
                self.clear_calls: list[str] = []
                self.remove_calls: list[str] = []
                self.index_calls: list[list] = []

            def search(self, _query):
                return RetrievalResult(chunks=[], scores=[])

            def index(self, chunks):
                self.index_calls.append(chunks)

            def clear(self, workspace_id: str) -> None:
                self.clear_calls.append(workspace_id)

            def remove_by_document(self, document_id: str) -> None:
                self.remove_calls.append(document_id)

        tracking = TrackingRetriever()
        ingest_uc_tracking = IngestWorkspaceUseCase(
            workspace_store=container.workspace_store,
            document_store=container.document_store,
            chunk_store=container.chunk_store,
            task_store=container.task_store,
            retriever=tracking,
            settings=container.settings,
        )
        self._run(ingest_uc_tracking, ws.id)

        assert tracking.clear_calls == []
        assert tracking.remove_calls == []
        assert tracking.index_calls == []

    def test_incremental_ingest_removes_deleted_files(self, setup):
        container, ws_uc, ingest_uc, kb = setup
        ws = ws_uc.create("ws", str(kb))

        # 首次摄入：两个文件都在
        self._run(ingest_uc, ws.id)
        docs_before = container.document_store.list_by_workspace(ws.id)
        assert len(docs_before) >= 2

        delete_target = kb / "resume" / "projects.md"
        delete_target.unlink()
        deleted_doc_id = next(
            d.id for d in docs_before
            if d.source_path == str(delete_target)
        )

        self._run(ingest_uc, ws.id)
        docs_after = container.document_store.list_by_workspace(ws.id)
        assert all(d.source_path != str(delete_target) for d in docs_after)
        assert all(c.document_id != deleted_doc_id for c in container.chunk_store.list_by_workspace(ws.id))
        assert container.source_store.get_by_document(deleted_doc_id) is None

        from src.ports.retriever import RetrievalQuery
        result = container.retriever.search(
            RetrievalQuery(question="项目经历", workspace_id=ws.id, top_k=5)
        )
        assert result.is_empty()

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

    def test_markdown_content_is_normalized_and_rendered_safely(self, setup):
        container, ws_uc, ingest_uc, kb = setup
        unsafe = kb / "unsafe.md"
        unsafe.write_text(
            "# 标题\r\n\r\n"
            "安全正文  \r\n\r\n"
            "<script>alert('x')</script>\r\n"
            "<div onclick=\"alert(1)\">保留文本</div>",
            encoding="utf-8",
        )
        ws = ws_uc.create("ws", str(kb))
        self._run(ingest_uc, ws.id)

        docs = container.document_store.list_by_workspace(ws.id)
        doc = next(d for d in docs if d.source_path == str(unsafe))
        assert "<script" in doc.raw_content.lower()
        assert doc.normalized_markdown == "# 标题\n\n安全正文\n\n保留文本"
        assert doc.plain_text == "标题\n\n安全正文\n\n保留文本"
        assert "<h1>标题</h1>" in doc.rendered_html
        assert "<script" not in doc.rendered_html.lower()
        assert "onclick" not in doc.rendered_html.lower()
        assert "alert" not in doc.rendered_html.lower()

        chunks = container.chunk_store.list_by_document(doc.id)
        assert chunks
        assert chunks[0].chunk_markdown == doc.normalized_markdown
        assert chunks[0].chunk_plain_text == doc.plain_text

    def test_pdf_and_docx_can_be_ingested_when_extractors_available(self, setup, monkeypatch):
        container, ws_uc, ingest_uc, kb = setup
        (kb / "paper.pdf").write_bytes(b"%PDF-1.4")
        (kb / "notes.docx").write_bytes(b"PK\x03\x04")

        monkeypatch.setattr(
            ingestion_usecases,
            "_extract_pdf_text",
            lambda _path: "PDF 内容\n章节一",
        )
        monkeypatch.setattr(
            ingestion_usecases,
            "_extract_docx_text",
            lambda _path: "DOCX 内容\n要点列表",
        )

        ws = ws_uc.create("ws-docs", str(kb))
        self._run(ingest_uc, ws.id)

        source_types = {
            d.source_type for d in container.document_store.list_by_workspace(ws.id)
        }
        assert {"md", "pdf", "docx"}.issubset(source_types)

        doc_pdf = next(
            d for d in container.document_store.list_by_workspace(ws.id)
            if d.source_type == "pdf"
        )
        assert "PDF 内容" in doc_pdf.raw_content
        doc_docx = next(
            d for d in container.document_store.list_by_workspace(ws.id)
            if d.source_type == "docx"
        )
        assert "DOCX 内容" in doc_docx.raw_content

    def test_pdf_or_docx_without_extractor_is_skipped(self, setup, monkeypatch):
        container, ws_uc, ingest_uc, kb = setup
        (kb / "bad.pdf").write_bytes(b"%PDF-1.4")

        monkeypatch.setattr(
            ingestion_usecases,
            "_extract_pdf_text",
            lambda _path: (_ for _ in ()).throw(RuntimeError("缺少解析依赖")),
        )

        ws = ws_uc.create("ws-skip", str(kb))
        result = self._run(ingest_uc, ws.id)

        assert result.done is True
        source_types = {d.source_type for d in container.document_store.list_by_workspace(ws.id)}
        assert "pdf" not in source_types
        assert result.error is None

    def test_short_sections_are_merged_to_reduce_over_splitting(self, setup):
        container, ws_uc, ingest_uc, kb = setup
        short_sections_file = kb / "short_sections.md"
        short_sections_file.write_text(
            "## 一\n段落一：一句话说明。\n\n"
            "## 二\n段落二：补充一句简短描述。\n\n"
            "## 三\n段落三：仍然保持短小。\n\n"
            "## 四\n段落四：继续补充。\n\n"
            "## 五\n最后一段也保持短小。\n",
            encoding="utf-8",
        )

        ws = ws_uc.create("ws-short", str(kb))
        self._run(ingest_uc, ws.id)

        doc = next(d for d in container.document_store.list_by_workspace(ws.id)
                   if d.source_path == str(short_sections_file))
        chunks = container.chunk_store.list_by_document(doc.id)

        # 原先每个超短节都会单独入库，修复后应合并为更少切片。
        assert len(chunks) == 1
        assert chunks[0].chunk_markdown.count("## ") >= 5
