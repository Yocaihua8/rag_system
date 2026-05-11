"""
test_models.py — 领域模型层测试。

验证：
  - frozen=True（不可变，线程安全）
  - 工厂方法（.create()）生成合法实例
  - 更新方法（.update() / .with_index_stats()）返回新实例，不修改原值
  - 序列化（.to_dict() / .from_dict()）往返一致
  - 枚举类型值正确
"""
from __future__ import annotations

import dataclasses
import pytest

from src.domain.models.document import Document
from src.domain.models.chunk import Chunk
from src.domain.models.workspace import Workspace
from src.domain.models.task import Task, TaskStatus, TaskKind
from src.domain.models.conversation import ConversationRecord
from src.domain.models.project_knowledge import ProjectKnowledgePoint
from src.domain.errors import (
    DomainError, NotFoundError, ValidationError,
    ConfigurationError, IndexNotReadyError,
)


# ── Document ─────────────────────────────────────────────────────────────────

class TestDocument:

    def test_create_returns_valid_instance(self):
        doc = Document.create(
            workspace_id="ws-1",
            title="简历",
            source_path="/kb/resume.md",
            content="Python RAG 工程师",
            domain="resume",
            tags=["python", "rag"],
        )
        assert doc.workspace_id == "ws-1"
        assert doc.title == "简历"
        assert doc.domain == "resume"
        assert "python" in doc.tags
        assert doc.id  # uuid4 非空

    def test_frozen(self):
        doc = Document.create("ws", "title", "/path", "content", "general")
        with pytest.raises(dataclasses.FrozenInstanceError):
            doc.title = "new"  # type: ignore

    def test_roundtrip_serialization(self):
        doc = Document.create("ws", "t", "/p", "c", "resume", ["a", "b"])
        restored = Document.from_dict(doc.to_dict())
        assert restored == doc


# ── Chunk ────────────────────────────────────────────────────────────────────

class TestChunk:

    def test_create(self):
        # Chunk.create(document_id, workspace_id, content, order, domain, tags)
        chunk = Chunk.create(
            document_id="doc-1",
            workspace_id="ws-1",
            content="Python 技能",
            order=0,
            domain="resume",
        )
        assert chunk.order == 0
        assert chunk.domain == "resume"
        assert chunk.id

    def test_frozen(self):
        chunk = Chunk.create("doc", "ws", "content", 0, "general")
        with pytest.raises(dataclasses.FrozenInstanceError):
            chunk.content = "x"  # type: ignore

    def test_roundtrip_serialization(self):
        chunk = Chunk.create("doc", "ws", "内容", 2, "jds", tags=["python"])
        restored = Chunk.from_dict(chunk.to_dict())
        assert restored == chunk


# ── Workspace ────────────────────────────────────────────────────────────────

class TestWorkspace:

    def test_create(self):
        ws = Workspace.create("求职 2024", "/kb/root")
        assert ws.name == "求职 2024"
        assert ws.root_path == "/kb/root"
        assert ws.id

    def test_with_index_stats_returns_new_instance(self):
        ws = Workspace.create("ws", "/kb")
        updated = ws.with_index_stats("ok", 10, 5)
        assert updated is not ws
        assert updated.last_index_status == "ok"
        assert updated.total_files == 10
        assert updated.supported_files == 5   # 字段名是 supported_files
        # 原实例不变
        assert ws.last_index_status != "ok"

    def test_frozen(self):
        ws = Workspace.create("ws", "/kb")
        with pytest.raises(dataclasses.FrozenInstanceError):
            ws.name = "x"  # type: ignore


# ── Task ─────────────────────────────────────────────────────────────────────

class TestTask:

    def test_create(self):
        task = Task.create(TaskKind.INGEST, "开始摄入")
        assert task.kind == TaskKind.INGEST
        assert task.status == TaskStatus.PENDING
        assert task.id

    def test_update_returns_new_instance(self):
        task = Task.create(TaskKind.QUERY, "查询")
        done = task.update(TaskStatus.DONE, 100, "完成")
        assert done is not task
        assert done.status == TaskStatus.DONE
        assert done.progress == 100
        assert task.status == TaskStatus.PENDING  # 原实例不变

    def test_enum_values(self):
        assert TaskStatus.DONE.value == "done"
        assert TaskStatus.FAILED.value == "failed"
        assert TaskKind.INGEST.value == "ingest"
        assert TaskKind.QUERY.value == "query"

    def test_frozen(self):
        task = Task.create(TaskKind.INGEST, "msg")
        with pytest.raises(dataclasses.FrozenInstanceError):
            task.status = TaskStatus.DONE  # type: ignore


# ── ConversationRecord ────────────────────────────────────────────────────────

class TestConversationRecord:

    def test_create(self):
        # ConversationRecord.create(workspace_id, question, answer)
        rec = ConversationRecord.create(
            workspace_id="ws-1",
            question="什么是 RAG？",
            answer="检索增强生成。",
        )
        assert rec.workspace_id == "ws-1"
        assert rec.question == "什么是 RAG？"
        assert rec.answer == "检索增强生成。"
        assert rec.id

    def test_frozen(self):
        rec = ConversationRecord.create("ws", "q", "a")
        with pytest.raises(dataclasses.FrozenInstanceError):
            rec.answer = "x"  # type: ignore

    def test_roundtrip_serialization(self):
        rec = ConversationRecord.create("ws-2", "问题", "答案")
        restored = ConversationRecord.from_dict(rec.to_dict())
        assert restored == rec


# ── Errors ───────────────────────────────────────────────────────────────────

class TestErrors:

    def test_not_found_error_is_domain_error(self):
        err = NotFoundError("Workspace", "ws-999")
        assert isinstance(err, DomainError)
        assert "ws-999" in str(err)

    def test_validation_error(self):
        err = ValidationError("name", "不能为空")
        assert isinstance(err, DomainError)

    def test_configuration_error(self):
        err = ConfigurationError("ollama_host", "无效地址")
        assert isinstance(err, DomainError)

    def test_index_not_ready_error(self):
        err = IndexNotReadyError("ws-1")
        assert isinstance(err, DomainError)

    def test_error_hierarchy(self):
        for cls in (NotFoundError, ValidationError, ConfigurationError, IndexNotReadyError):
            assert issubclass(cls, DomainError)
            assert issubclass(cls, Exception)

class TestProjectKnowledgePoint:

    def test_create_defaults(self):
        point = ProjectKnowledgePoint.create(
            workspace_id="ws-1",
            name="FastAPI",
            kind="tech_stack",
            summary="项目使用 FastAPI 提供后端接口。",
            source_path="/repo/README.md",
            evidence="后端采用 FastAPI 构建 API",
            confidence=0.8,
        )

        assert point.workspace_id == "ws-1"
        assert point.name == "FastAPI"
        assert point.kind == "tech_stack"
        assert point.source_path == "/repo/README.md"
        assert point.confidence == 0.8
        assert point.id
        assert point.created_at

    def test_to_dict_and_from_dict_roundtrip(self):
        point = ProjectKnowledgePoint.create(
            workspace_id="ws-1",
            name="索引流程",
            kind="flow",
            summary="项目包含扫描、分块、索引流程。",
            source_path="/repo/docs/rag.md",
            evidence="扫描文件 -> 分块 -> 建立索引",
            confidence=0.7,
        )

        restored = ProjectKnowledgePoint.from_dict(point.to_dict())

        assert restored == point

    def test_frozen(self):
        point = ProjectKnowledgePoint.create(
            workspace_id="ws-1",
            name="FastAPI",
            kind="tech_stack",
            summary="项目使用 FastAPI。",
            source_path="/repo/README.md",
            evidence="FastAPI",
        )

        with pytest.raises(dataclasses.FrozenInstanceError):
            point.name = "SQLite"  # type: ignore

    def test_confidence_is_clamped(self):
        low = ProjectKnowledgePoint.create(
            workspace_id="ws-1",
            name="low",
            kind="concept",
            summary="summary",
            source_path="/repo/README.md",
            evidence="evidence",
            confidence=-1,
        )
        high = ProjectKnowledgePoint.create(
            workspace_id="ws-1",
            name="high",
            kind="concept",
            summary="summary",
            source_path="/repo/README.md",
            evidence="evidence",
            confidence=2,
        )

        assert low.confidence == 0.0
        assert high.confidence == 1.0
