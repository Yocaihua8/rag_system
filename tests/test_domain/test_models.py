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
from src.domain.models.project import Project
from src.domain.models.graph import GraphEdge, GraphNode
from src.domain.models.source import Source
from src.domain.models.tag import DocumentTag, Tag
from src.domain.models.workspace import Workspace
from src.domain.models.task import Task, TaskStatus, TaskKind
from src.domain.models.conversation import ConversationRecord
from src.domain.models.project_knowledge import (
    Evidence,
    KnowledgePoint,
    MasteryRecord,
    MasteryStatus,
    ProjectKnowledgePoint,
    SkillArea,
)
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

    def test_create_document_with_knowledge_island_formats(self):
        doc = Document.create(
            project_id="project-1",
            title="README",
            source_type="markdown",
            source_path="E:/Code/rag_system/README.md",
            raw_content="# 标题\n\n正文",
            normalized_markdown="# 标题\n\n正文",
            plain_text="标题\n\n正文",
            rendered_html="<h1>标题</h1><p>正文</p>",
        )

        assert doc.project_id == "project-1"
        assert doc.source_type == "markdown"
        assert doc.raw_content.startswith("# 标题")
        assert doc.normalized_markdown.startswith("# 标题")
        assert doc.plain_text == "标题\n\n正文"
        assert "<script" not in doc.rendered_html.lower()
        assert doc.updated_at


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

    def test_create_chunk_with_heading_path_and_plain_text(self):
        chunk = Chunk.create(
            document_id="doc-1",
            project_id="project-1",
            chunk_index=0,
            heading_path=["README", "架构"],
            chunk_markdown="## 架构\n\n内容",
            chunk_plain_text="架构\n\n内容",
            token_count=12,
            embedding_id="emb-1",
        )

        assert chunk.project_id == "project-1"
        assert chunk.chunk_index == 0
        assert chunk.heading_path == ["README", "架构"]
        assert chunk.chunk_markdown.startswith("## 架构")
        assert chunk.chunk_plain_text == "架构\n\n内容"
        assert chunk.token_count == 12
        assert chunk.embedding_id == "emb-1"


class TestGraphModels:

    def test_graph_node_roundtrip(self):
        node = GraphNode.create(
            workspace_id="ws-1",
            name="知识图谱",
            node_type="concept",
            label="知识",
            source_ref="/repo/notes.md",
            confidence=0.91,
        )

        restored = GraphNode.from_dict(node.to_dict())
        assert restored == node
        assert restored.node_type == "concept"
        assert restored.label == "知识"
        assert restored.source_ref == "/repo/notes.md"

    def test_graph_edge_roundtrip(self):
        edge = GraphEdge.create(
            workspace_id="ws-1",
            source_node_id="n1",
            target_node_id="n2",
            relationship="contains",
            confidence=1.2,
            source_path="/repo/a.md",
            source_snippet="示例片段",
        )

        restored = GraphEdge.from_dict(edge.to_dict())
        assert restored == edge
        assert restored.confidence == edge.confidence
        assert restored.relationship == "contains"
        assert restored.source_snippet == "示例片段"


# ── Project ──────────────────────────────────────────────────────────────────

class TestProject:

    def test_create_project_space(self):
        project = Project.create("知识岛", "个人第二大脑桌面端", "E:/Code/rag_system")

        assert project.name == "知识岛"
        assert project.description == "个人第二大脑桌面端"
        assert project.root_path == "E:/Code/rag_system"
        assert project.id
        assert project.created_at
        assert project.updated_at

    def test_roundtrip_serialization(self):
        project = Project.create("知识岛", "本地优先个人知识库", "E:/Code/rag_system")
        restored = Project.from_dict(project.to_dict())
        assert restored == project


# ── Tag / Source ─────────────────────────────────────────────────────────────

class TestTagAndSource:

    def test_create_tag_and_document_tag(self):
        tag = Tag.create("RAG", "#3366cc")
        link = DocumentTag.create("doc-1", tag.id)

        assert tag.name == "RAG"
        assert tag.color == "#3366cc"
        assert link.document_id == "doc-1"
        assert link.tag_id == tag.id

    def test_create_source_with_checksum(self):
        source = Source.create(
            document_id="doc-1",
            source_type="markdown",
            source_path="E:/Code/rag_system/README.md",
            checksum="abc123",
        )

        assert source.document_id == "doc-1"
        assert source.source_type == "markdown"
        assert source.source_path.endswith("README.md")
        assert source.checksum == "abc123"
        assert source.imported_at


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


class TestMasteryModels:

    def test_skill_area_create_and_roundtrip(self):
        area = SkillArea.create(
            workspace_id="ws-1",
            name="后端开发",
            description="掌握服务端设计与实现。"
        )
        restored = SkillArea.from_dict(area.to_dict())
        assert restored == area

    def test_knowledge_point_roundtrip_and_confidence_clamp(self):
        point = KnowledgePoint.create(
            workspace_id="ws-1",
            skill_area_id="area-1",
            name="REST 接口",
            summary="能够设计并实现 REST API。",
            confidence=1.8,
        )
        assert point.confidence == 1.0

        restored = KnowledgePoint.from_dict(point.to_dict())
        assert restored == point

    def test_evidence_roundtrip(self):
        evidence = Evidence.create(
            workspace_id="ws-1",
            knowledge_point_id="kp-1",
            source_path="/repo/docs/api.md",
            snippet="POST /users 用于创建用户。",
            confidence=0.9,
        )
        restored = Evidence.from_dict(evidence.to_dict())
        assert restored == evidence

    def test_mastery_status_and_transition(self):
        record = MasteryRecord.create(
            workspace_id="ws-1",
            knowledge_point_id="kp-1",
            status=MasteryStatus.CLAIMED,
        )
        assert record.status == MasteryStatus.CLAIMED

        with_evidence = record.mark_evidence_found(
            evidence_id="e-1",
            note="从文档找到实现说明。",
        )
        assert with_evidence.status == MasteryStatus.EVIDENCE_FOUND
        assert with_evidence.evidence_id == "e-1"

        verified = with_evidence.mark_verified(confidence=0.92)
        assert verified.status == MasteryStatus.VERIFIED
        assert verified.confidence == 0.92
