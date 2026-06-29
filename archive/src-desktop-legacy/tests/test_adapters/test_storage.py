"""
test_storage.py — SQLite 存储适配器测试。

使用内存数据库（:memory:），零文件副作用。
验证全部 Store 的 CRUD 行为及级联删除。
"""
from __future__ import annotations

from pathlib import Path

import pytest

from src.adapters.storage.db import create_connection, init_schema
from src.adapters.storage.sqlite_workspace_store import SqliteWorkspaceStore
from src.adapters.storage.sqlite_document_store import SqliteDocumentStore
from src.adapters.storage.sqlite_chunk_store import SqliteChunkStore
from src.adapters.storage.sqlite_task_store import SqliteTaskStore
from src.adapters.storage.sqlite_conversation_store import SqliteConversationStore
from src.adapters.storage.sqlite_project_knowledge_store import SqliteProjectKnowledgeStore
from src.adapters.storage.sqlite_tag_store import SqliteTagStore, SqliteDocumentTagStore
from src.adapters.storage.sqlite_source_store import SqliteSourceStore
from src.adapters.storage.sqlite_knowledge_mastery_store import SqliteKnowledgeMasteryStore
from src.adapters.storage.sqlite_graph_store import SqliteGraphStore
from src.domain.models.chunk import Chunk
from src.domain.models.graph import GraphEdge, GraphNode
from src.domain.models.conversation import ConversationRecord
from src.domain.models.document import Document
from src.domain.models.source import Source
from src.domain.models.tag import DocumentTag, Tag
from src.domain.models.project_knowledge import (
    Evidence,
    KnowledgePoint,
    MasteryRecord,
    MasteryStatus,
    ProjectKnowledgePoint,
    SkillArea,
)
from src.domain.models.task import Task, TaskKind, TaskStatus
from src.domain.models.workspace import Workspace


@pytest.fixture
def conn():
    """每个测试独立的内存数据库连接。"""
    c = create_connection(Path(":memory:"))
    init_schema(c)
    yield c
    c.close()


@pytest.fixture
def stores(conn):
    return {
        "ws":    SqliteWorkspaceStore(conn),
        "doc":   SqliteDocumentStore(conn),
        "chunk": SqliteChunkStore(conn),
        "task":  SqliteTaskStore(conn),
        "conv":  SqliteConversationStore(conn),
        "pkp":   SqliteProjectKnowledgeStore(conn),
        "mastery": SqliteKnowledgeMasteryStore(conn),
        "tag":   SqliteTagStore(conn),
        "doc_tag": SqliteDocumentTagStore(conn),
        "source": SqliteSourceStore(conn),
        "graph": SqliteGraphStore(conn),
    }


# ── Schema ───────────────────────────────────────────────────────────────────

class TestKnowledgeIslandSchema:

    def test_core_model_tables_and_columns_exist(self, conn):
        tables = {
            row["name"]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            ).fetchall()
        }
        assert {"projects", "tags", "document_tags", "sources"}.issubset(tables)
        assert {
            "skill_areas",
            "knowledge_points",
            "evidences",
            "mastery_records",
        }.issubset(tables)
        assert {"graph_nodes", "graph_edges"}.issubset(tables)

        document_columns = {
            row["name"] for row in conn.execute("PRAGMA table_info(documents)")
        }
        assert {
            "project_id",
            "source_type",
            "raw_content",
            "normalized_markdown",
            "plain_text",
            "rendered_html",
            "updated_at",
        }.issubset(document_columns)

        chunk_columns = {
            row["name"] for row in conn.execute("PRAGMA table_info(chunks)")
        }
        assert {
            "project_id",
            "chunk_index",
            "heading_path",
            "chunk_markdown",
            "chunk_plain_text",
            "token_count",
            "embedding_id",
            "created_at",
            "updated_at",
        }.issubset(chunk_columns)

        conversation_columns = {
            row["name"]
            for row in conn.execute("PRAGMA table_info(conversations)").fetchall()
        }
        assert "session_id" in conversation_columns

        graph_node_columns = {
            row["name"] for row in conn.execute("PRAGMA table_info(graph_nodes)")
        }
        assert {
            "workspace_id",
            "label",
            "node_type",
            "source_ref",
            "confidence",
        }.issubset(graph_node_columns)

        graph_edge_columns = {
            row["name"] for row in conn.execute("PRAGMA table_info(graph_edges)")
        }
        assert {
            "workspace_id",
            "source_node_id",
            "target_node_id",
            "relationship",
            "confidence",
        }.issubset(graph_edge_columns)


# ── WorkspaceStore ────────────────────────────────────────────────────────────

class TestWorkspaceStore:

    def test_save_and_get(self, stores):
        ws_store = stores["ws"]
        ws = Workspace.create("求职 2024", "/kb/root")
        ws_store.save(ws)
        found = ws_store.get(ws.id)
        assert found is not None
        assert found.name == "求职 2024"
        assert found.root_path == "/kb/root"

    def test_get_nonexistent_returns_none(self, stores):
        assert stores["ws"].get("no-such-id") is None

    def test_list_all(self, stores):
        ws_store = stores["ws"]
        ws1 = Workspace.create("ws1", "/kb1")
        ws2 = Workspace.create("ws2", "/kb2")
        ws_store.save(ws1)
        ws_store.save(ws2)
        result = ws_store.list_all()
        ids = [w.id for w in result]
        assert ws1.id in ids
        assert ws2.id in ids

    def test_update(self, stores):
        ws_store = stores["ws"]
        ws = Workspace.create("ws", "/kb")
        ws_store.save(ws)
        updated = ws.with_index_stats("ok", 5, 3)
        ws_store.update(updated)
        found = ws_store.get(ws.id)
        assert found.last_index_status == "ok"
        assert found.total_files == 5

    def test_delete(self, stores):
        ws_store = stores["ws"]
        ws = Workspace.create("tmp", "/kb")
        ws_store.save(ws)
        ws_store.delete(ws.id)
        assert ws_store.get(ws.id) is None

    def test_upsert_semantics(self, stores):
        """save() 使用 INSERT OR REPLACE，重复 save 同一对象不报错且仅保留一条。"""
        ws_store = stores["ws"]
        ws = Workspace.create("ws", "/kb")
        ws_store.save(ws)
        ws_store.save(ws)   # 重复 save，不应报错
        assert len(ws_store.list_all()) == 1


# ── DocumentStore ─────────────────────────────────────────────────────────────

class TestDocumentStore:

    def _make_ws(self, stores) -> str:
        ws = Workspace.create("ws", "/kb")
        stores["ws"].save(ws)
        return ws.id

    def test_save_and_exists(self, stores):
        ws_id = self._make_ws(stores)
        doc = Document.create(ws_id, "resume", "/kb/resume.md", "content", "resume")
        stores["doc"].save_batch([doc])
        assert stores["doc"].exists(doc.id)

    def test_list_by_workspace(self, stores):
        ws_id = self._make_ws(stores)
        docs = [Document.create(ws_id, f"doc{i}", f"/kb/d{i}.md", "c", "general")
                for i in range(3)]
        stores["doc"].save_batch(docs)
        result = stores["doc"].list_by_workspace(ws_id)
        assert len(result) == 3

    def test_delete_by_workspace(self, stores):
        ws_id = self._make_ws(stores)
        docs = [Document.create(ws_id, f"d{i}", f"/p{i}", "c", "general") for i in range(2)]
        stores["doc"].save_batch(docs)
        stores["doc"].delete_by_workspace(ws_id)
        assert stores["doc"].list_by_workspace(ws_id) == []

    def test_save_and_get_knowledge_island_fields(self, stores):
        ws_id = self._make_ws(stores)
        doc = Document.create(
            workspace_id=ws_id,
            project_id=ws_id,
            title="README",
            source_type="markdown",
            source_path="/kb/README.md",
            raw_content="# 标题",
            normalized_markdown="# 标题",
            plain_text="标题",
            rendered_html="<h1>标题</h1>",
        )

        stores["doc"].save_batch([doc])
        found = stores["doc"].get(doc.id)

        assert found is not None
        assert found.project_id == ws_id
        assert found.source_type == "markdown"
        assert found.raw_content == "# 标题"
        assert found.normalized_markdown == "# 标题"
        assert found.plain_text == "标题"
        assert found.rendered_html == "<h1>标题</h1>"


# ── ChunkStore ────────────────────────────────────────────────────────────────

class TestChunkStore:

    def _setup(self, stores) -> tuple:
        ws = Workspace.create("ws", "/kb")
        stores["ws"].save(ws)
        doc = Document.create(ws.id, "doc", "/p", "content", "resume")
        stores["doc"].save_batch([doc])
        return ws.id, doc.id

    def test_save_and_count(self, stores):
        ws_id, doc_id = self._setup(stores)
        # Chunk.create(document_id, workspace_id, content, order, domain)
        chunks = [Chunk.create(doc_id, ws_id, f"text {i}", i, "resume") for i in range(5)]
        stores["chunk"].save_batch(chunks)
        assert stores["chunk"].count_by_workspace(ws_id) == 5

    def test_get(self, stores):
        ws_id, doc_id = self._setup(stores)
        chunk = Chunk.create(doc_id, ws_id, "Python RAG", 0, "resume")
        stores["chunk"].save_batch([chunk])
        found = stores["chunk"].get(chunk.id)
        assert found is not None
        assert found.content == "Python RAG"

    def test_list_by_workspace(self, stores):
        ws_id, doc_id = self._setup(stores)
        chunks = [Chunk.create(doc_id, ws_id, f"c{i}", i, "general") for i in range(4)]
        stores["chunk"].save_batch(chunks)
        result = stores["chunk"].list_by_workspace(ws_id)
        assert len(result) == 4

    def test_list_by_ids_preserves_input_order_and_ignores_missing_ids(self, stores):
        ws_id, doc_id = self._setup(stores)
        chunks = [Chunk.create(doc_id, ws_id, f"c{i}", i, "general") for i in range(3)]
        stores["chunk"].save_batch(chunks)

        result = stores["chunk"].list_by_ids([chunks[2].id, "missing-id", chunks[0].id])

        assert [chunk.id for chunk in result] == [chunks[2].id, chunks[0].id]
        assert stores["chunk"].list_by_ids([]) == []

    def test_delete_by_workspace(self, stores):
        ws_id, doc_id = self._setup(stores)
        chunks = [Chunk.create(doc_id, ws_id, "c", 0, "general")]
        stores["chunk"].save_batch(chunks)
        stores["chunk"].delete_by_workspace(ws_id)
        assert stores["chunk"].count_by_workspace(ws_id) == 0

    def test_delete_by_document(self, stores):
        ws_id, doc_id = self._setup(stores)
        other_doc = Document.create(ws_id, "other", "/p2", "other", "resume")
        stores["doc"].save_batch([other_doc])

        stores["chunk"].save_batch([
            Chunk.create(doc_id, ws_id, "doc1", 0, "general"),
            Chunk.create(doc_id, ws_id, "doc1-2", 1, "general"),
            Chunk.create(other_doc.id, ws_id, "doc2", 0, "general"),
        ])

        stores["chunk"].delete_by_document(doc_id)
        assert stores["chunk"].count_by_workspace(ws_id) == 1
        assert stores["chunk"].list_by_document(other_doc.id)
        assert stores["chunk"].list_by_document(doc_id) == []

    def test_save_and_get_knowledge_island_fields(self, stores):
        ws_id, doc_id = self._setup(stores)
        chunk = Chunk.create(
            document_id=doc_id,
            workspace_id=ws_id,
            project_id=ws_id,
            chunk_index=2,
            heading_path=["README", "导入"],
            chunk_markdown="## 导入\n\n内容",
            chunk_plain_text="导入\n\n内容",
            token_count=8,
            embedding_id="embedding-1",
        )

        stores["chunk"].save_batch([chunk])
        found = stores["chunk"].get(chunk.id)

        assert found is not None
        assert found.project_id == ws_id
        assert found.chunk_index == 2
        assert found.heading_path == ["README", "导入"]
        assert found.chunk_markdown == "## 导入\n\n内容"
        assert found.chunk_plain_text == "导入\n\n内容"
        assert found.token_count == 8
        assert found.embedding_id == "embedding-1"


# ── Tag / Source ─────────────────────────────────────────────────────────────


class TestTagStore:

    def test_save_get_delete_tag(self, stores):
        tag_store = stores["tag"]
        tag = Tag.create("RAG")
        tag_store.save(tag)
        found = tag_store.get(tag.id)
        assert found is not None
        assert found.name == "RAG"

        found_by_name = tag_store.get_by_name("RAG")
        assert found_by_name is not None
        assert found_by_name.id == tag.id

        all_tags = tag_store.list_all()
        assert len(all_tags) == 1
        assert all_tags[0].name == "RAG"

        tag_store.delete(tag.id)
        assert tag_store.get(tag.id) is None


class TestDocumentTagStore:

    def _make_doc(self, stores) -> tuple[Workspace, Document]:
        ws = Workspace.create("ws", "/kb")
        stores["ws"].save(ws)
        doc = Document.create(ws.id, "doc", "/p", "content", "general")
        stores["doc"].save_batch([doc])
        return ws, doc

    def test_bind_and_list(self, stores):
        doc_tag_store = stores["doc_tag"]
        tag_store = stores["tag"]

        ws, doc = self._make_doc(stores)
        tag = Tag.create("Python")
        tag_store.save(tag)
        doc_tag_store.save(DocumentTag.create(doc.id, tag.id))

        tag_ids = doc_tag_store.list_tag_ids_by_document(doc.id)
        assert tag_ids == [tag.id]

        doc_ids = doc_tag_store.list_documents_by_tag(tag.id)
        assert doc.id in doc_ids

        doc_tag_store.delete_by_document(doc.id)
        assert doc_tag_store.list_tag_ids_by_document(doc.id) == []


class TestSourceStore:

    def _make_doc(self, stores) -> tuple[Workspace, Document]:
        ws = Workspace.create("ws", "/kb")
        stores["ws"].save(ws)
        doc = Document.create(ws.id, "doc", "/p", "content", "general")
        stores["doc"].save_batch([doc])
        return ws, doc

    def test_save_and_checksum_lookup(self, stores):
        source_store = stores["source"]
        ws, doc = self._make_doc(stores)
        source = Source.create(
            document_id=doc.id,
            source_type="markdown",
            source_path="/p/readme.md",
            checksum="abc123",
        )
        source_store.save(source)

        latest = source_store.get_by_document(doc.id)
        assert latest is not None
        assert latest.checksum == "abc123"

        by_path = source_store.find_by_path("/p/readme.md")
        assert by_path is not None
        assert by_path.document_id == doc.id

        assert source_store.exists_same_checksum("/p/readme.md", "abc123") is True
        assert source_store.exists_same_checksum("/p/readme.md", "nope") is False


# ── TaskStore ─────────────────────────────────────────────────────────────────

class TestTaskStore:

    def test_save_and_get(self, stores):
        task = Task.create(TaskKind.INGEST, "开始摄入")
        stores["task"].save(task)
        found = stores["task"].get(task.id)
        assert found is not None
        assert found.kind == TaskKind.INGEST
        assert found.status == TaskStatus.PENDING

    def test_update_status(self, stores):
        task = Task.create(TaskKind.QUERY, "查询")
        stores["task"].save(task)
        done = task.update(TaskStatus.DONE, 100, "完成")
        stores["task"].update(done)
        found = stores["task"].get(task.id)
        assert found.status == TaskStatus.DONE
        assert found.progress == 100

    def test_list_recent(self, stores):
        tasks = [Task.create(TaskKind.INGEST, f"task-{i}") for i in range(5)]
        for t in tasks:
            stores["task"].save(t)
        recent = stores["task"].list_recent(limit=3)
        assert len(recent) <= 3


# ── ConversationStore ─────────────────────────────────────────────────────────

class TestConversationStore:

    def _make_ws(self, stores, name="ws") -> str:
        ws = Workspace.create(name, "/kb")
        stores["ws"].save(ws)
        return ws.id

    def test_save_and_list(self, stores):
        # ConversationRecord 有 FK 约束，必须先建 workspace
        ws_id = self._make_ws(stores, "ws-conv")
        records = [
            ConversationRecord.create(ws_id, f"问题{i}", f"答案{i}")
            for i in range(3)
        ]
        for r in records:
            stores["conv"].save(r)
        result = stores["conv"].list_recent(ws_id, limit=10)
        assert len(result) == 3

    def test_list_recent_limit(self, stores):
        ws_id = self._make_ws(stores, "ws-limit")
        for i in range(10):
            stores["conv"].save(
                ConversationRecord.create(ws_id, f"q{i}", f"a{i}")
            )
        result = stores["conv"].list_recent(ws_id, limit=5)
        assert len(result) == 5

    def test_list_recent_filters_by_session_id(self, stores):
        ws_id = self._make_ws(stores, "ws-sessions")
        default_record = ConversationRecord.create(ws_id, "默认问题", "默认答案")
        session_a = ConversationRecord.create(
            ws_id,
            "会话A问题",
            "会话A答案",
            session_id="session-a",
        )
        session_b = ConversationRecord.create(
            ws_id,
            "会话B问题",
            "会话B答案",
            session_id="session-b",
        )

        stores["conv"].save(default_record)
        stores["conv"].save(session_a)
        stores["conv"].save(session_b)

        default_history = stores["conv"].list_recent(ws_id, limit=10)
        session_a_history = stores["conv"].list_recent(
            ws_id,
            limit=10,
            session_id="session-a",
        )

        assert [record.question for record in default_history] == ["默认问题"]
        assert [record.question for record in session_a_history] == ["会话A问题"]

    def test_delete_by_workspace(self, stores):
        ws_id = self._make_ws(stores, "ws-del")
        for i in range(3):
            stores["conv"].save(ConversationRecord.create(ws_id, "q", "a"))
        stores["conv"].delete_by_workspace(ws_id)
        assert stores["conv"].list_recent(ws_id, limit=10) == []


# ── ProjectKnowledgeStore ─────────────────────────────────────────────────────

class TestProjectKnowledgeStore:

    def _make_ws(self, stores) -> str:
        ws = Workspace.create("project", "/repo")
        stores["ws"].save(ws)
        return ws.id

    def test_save_batch_and_list_by_workspace(self, stores):
        ws_id = self._make_ws(stores)
        points = [
            ProjectKnowledgePoint.create(
                workspace_id=ws_id,
                name="FastAPI",
                kind="tech_stack",
                summary="后端 API 技术栈。",
                source_path="/repo/README.md",
                evidence="FastAPI",
                confidence=0.8,
            ),
            ProjectKnowledgePoint.create(
                workspace_id=ws_id,
                name="tests",
                kind="test",
                summary="项目包含测试目录。",
                source_path="/repo/tests/test_app.py",
                evidence="tests/test_app.py",
                confidence=0.7,
            ),
        ]

        stores["pkp"].save_batch(points)
        result = stores["pkp"].list_by_workspace(ws_id)

        assert [p.name for p in result] == ["FastAPI", "tests"]
        assert result[0].kind == "tech_stack"
        assert result[0].summary == "后端 API 技术栈。"
        assert result[0].source_path == "/repo/README.md"
        assert result[0].evidence == "FastAPI"
        assert result[0].confidence == 0.8
        assert result[0].created_at
        assert stores["pkp"].count_by_workspace(ws_id) == 2

    def test_delete_by_workspace(self, stores):
        ws_id = self._make_ws(stores)
        point = ProjectKnowledgePoint.create(
            workspace_id=ws_id,
            name="README",
            kind="concept",
            summary="README 描述项目入口。",
            source_path="/repo/README.md",
            evidence="# Project",
            confidence=0.6,
        )
        stores["pkp"].save_batch([point])

        stores["pkp"].delete_by_workspace(ws_id)

        assert stores["pkp"].list_by_workspace(ws_id) == []
        assert stores["pkp"].count_by_workspace(ws_id) == 0


class TestKnowledgeMasteryStore:

    def _make_ws(self, stores) -> str:
        ws = Workspace.create("mastery", "/repo")
        stores["ws"].save(ws)
        return ws.id

    def _make_area(self, stores, ws_id: str) -> SkillArea:
        area = SkillArea.create(
            workspace_id=ws_id,
            name="后端开发",
            description="服务端基础。",
        )
        stores["mastery"].save_skill_area(area)
        return area

    def test_skill_area_roundtrip(self, stores):
        ws_id = self._make_ws(stores)
        area = self._make_area(stores, ws_id)
        found = stores["mastery"].get_skill_area(area.id)

        assert found is not None
        assert found.id == area.id
        assert found.workspace_id == ws_id
        assert found.name == "后端开发"
        assert len(stores["mastery"].list_skill_areas_by_workspace(ws_id)) == 1

    def test_knowledge_point_and_evidence_roundtrip(self, stores):
        ws_id = self._make_ws(stores)
        area = self._make_area(stores, ws_id)
        point = KnowledgePoint.create(
            workspace_id=ws_id,
            skill_area_id=area.id,
            name="RESTful API",
            summary="掌握 REST 接口设计与实现。",
            confidence=0.9,
        )
        stores["mastery"].save_knowledge_point(point)

        evidence = Evidence.create(
            workspace_id=ws_id,
            knowledge_point_id=point.id,
            source_path="/repo/docs/api.md",
            snippet="POST /users 用于创建用户。",
            confidence=0.88,
        )
        stores["mastery"].save_evidence(evidence)

        assert stores["mastery"].get_knowledge_point(point.id) is not None
        assert stores["mastery"].get_evidence(evidence.id) is not None

        evidences = stores["mastery"].list_evidences_by_knowledge_point(point.id)
        assert len(evidences) == 1
        assert evidences[0].id == evidence.id

        points = stores["mastery"].list_knowledge_points_by_workspace(ws_id)
        assert len(points) == 1
        assert points[0].skill_area_id == area.id

        points_by_area = stores["mastery"].list_knowledge_points_by_skill_area(area.id)
        assert len(points_by_area) == 1
        assert points_by_area[0].id == point.id

    def test_mastery_record_transitions(self, stores):
        ws_id = self._make_ws(stores)
        area = self._make_area(stores, ws_id)
        point = KnowledgePoint.create(
            workspace_id=ws_id,
            skill_area_id=area.id,
            name="AsyncIO",
            summary="并发模型。",
            confidence=0.8,
        )
        stores["mastery"].save_knowledge_point(point)

        record = MasteryRecord.create(
            workspace_id=ws_id,
            knowledge_point_id=point.id,
            confidence=0.4,
            note="初始认领。",
        )
        stores["mastery"].save_mastery_record(record)
        assert stores["mastery"].get_mastery_record(record.id) is not None

        evidence_found = record.mark_evidence_found("ev-1", "找到了文档片段。")
        stores["mastery"].save_mastery_record(evidence_found)

        verified = evidence_found.mark_verified("能解释示例代码。", 0.95)
        stores["mastery"].save_mastery_record(verified)

        records = stores["mastery"].list_mastery_records_by_knowledge_point(point.id)
        assert len(records) == 1
        assert records[0].status == MasteryStatus.VERIFIED
        assert records[0].confidence == 0.95


# ── 级联删除 ──────────────────────────────────────────────────────────────────

class TestCascadeDelete:
    """删除 Workspace 时应自动级联清理关联数据。"""

    def test_cascade_on_workspace_delete(self, stores):
        ws = Workspace.create("cascade-test", "/kb")
        stores["ws"].save(ws)

        doc = Document.create(ws.id, "doc", "/p", "content", "resume")
        stores["doc"].save_batch([doc])

        # Chunk.create(document_id, workspace_id, content, order, domain)
        chunk = Chunk.create(doc.id, ws.id, "text", 0, "resume")
        stores["chunk"].save_batch([chunk])

        stores["conv"].save(
            ConversationRecord.create(ws.id, "q", "a")
        )
        stores["pkp"].save_batch([
            ProjectKnowledgePoint.create(
                workspace_id=ws.id,
                name="FastAPI",
                kind="tech_stack",
                summary="后端 API 技术栈。",
                source_path="/p",
                evidence="FastAPI",
                confidence=0.8,
            )
        ])

        # 删除工作区
        stores["ws"].delete(ws.id)

        # 子数据应已级联删除
        assert stores["doc"].list_by_workspace(ws.id) == []
        assert stores["chunk"].count_by_workspace(ws.id) == 0
        assert stores["conv"].list_recent(ws.id, limit=10) == []
        assert stores["pkp"].count_by_workspace(ws.id) == 0

    def test_workspace_delete_cascades_to_mastery(self, stores):
        ws = Workspace.create("cascade-mastery", "/kb")
        stores["ws"].save(ws)

        area = SkillArea.create(
            workspace_id=ws.id,
            name="前端开发",
            description="UI 实现。",
        )
        stores["mastery"].save_skill_area(area)

        point = KnowledgePoint.create(
            workspace_id=ws.id,
            skill_area_id=area.id,
            name="React",
            summary="掌握组件渲染。",
            confidence=0.7,
        )
        stores["mastery"].save_knowledge_point(point)

        evidence = Evidence.create(
            workspace_id=ws.id,
            knowledge_point_id=point.id,
            source_path="/repo/docs/ui.md",
            snippet="组件化设计。",
            confidence=0.6,
        )
        stores["mastery"].save_evidence(evidence)

        record = MasteryRecord.create(
            workspace_id=ws.id,
            knowledge_point_id=point.id,
            evidence_id=evidence.id,
            status=MasteryStatus.EVIDENCE_FOUND,
            confidence=0.6,
        )
        stores["mastery"].save_mastery_record(record)

        stores["ws"].delete(ws.id)

        assert stores["mastery"].list_skill_areas_by_workspace(ws.id) == []
        assert stores["mastery"].list_knowledge_points_by_workspace(ws.id) == []
        assert stores["mastery"].list_mastery_records_by_workspace(ws.id) == []


class TestGraphStore:

    def _make_ws(self, stores) -> str:
        ws = Workspace.create("graph", "/repo")
        stores["ws"].save(ws)
        return ws.id

    def _make_node(self, stores, ws_id: str, name: str, node_type: str) -> GraphNode:
        node = GraphNode.create(
            workspace_id=ws_id,
            name=name,
            node_type=node_type,
            label=name,
            confidence=0.8,
        )
        stores["graph"].save_node(node)
        return node

    def test_node_crud_roundtrip(self, stores):
        ws_id = self._make_ws(stores)
        node = self._make_node(stores, ws_id, "概念A", "concept")

        found = stores["graph"].get_node(node.id)
        assert found is not None
        assert found.name == "概念A"
        assert found.node_type == "concept"
        assert stores["graph"].count_nodes_by_workspace(ws_id) == 1

        stores["graph"].delete_node(node.id)
        assert stores["graph"].get_node(node.id) is None
        assert stores["graph"].count_nodes_by_workspace(ws_id) == 0

    def test_edge_roundtrip_and_filter(self, stores):
        ws_id = self._make_ws(stores)
        source = self._make_node(stores, ws_id, "source", "artifact")
        target = self._make_node(stores, ws_id, "target", "concept")

        high = GraphEdge.create(
            workspace_id=ws_id,
            source_node_id=source.id,
            target_node_id=target.id,
            relationship="refs",
            confidence=0.95,
            source_snippet="snippet",
        )
        low = GraphEdge.create(
            workspace_id=ws_id,
            source_node_id=source.id,
            target_node_id=target.id,
            relationship="refs",
            confidence=0.6,
        )
        stores["graph"].save_edge(high)
        stores["graph"].save_edge(low)

        all_edges = stores["graph"].list_edges_by_node(ws_id, source.id)
        assert len(all_edges) == 2

        filtered = stores["graph"].list_edges_by_node(
            workspace_id=ws_id,
            source_node_id=source.id,
            min_confidence=0.7,
        )
        assert len(filtered) == 1
        assert filtered[0].id == high.id
        assert stores["graph"].count_edges_by_workspace(ws_id) == 2
