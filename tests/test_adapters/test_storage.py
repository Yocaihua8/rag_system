"""
test_storage.py — SQLite 存储适配器测试。

使用内存数据库（:memory:），零文件副作用。
验证全部 6 个 Store 的 CRUD 行为及级联删除。
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
from src.domain.models.chunk import Chunk
from src.domain.models.conversation import ConversationRecord
from src.domain.models.document import Document
from src.domain.models.project_knowledge import ProjectKnowledgePoint
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
    }


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

    def test_delete_by_workspace(self, stores):
        ws_id, doc_id = self._setup(stores)
        chunks = [Chunk.create(doc_id, ws_id, "c", 0, "general")]
        stores["chunk"].save_batch(chunks)
        stores["chunk"].delete_by_workspace(ws_id)
        assert stores["chunk"].count_by_workspace(ws_id) == 0


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
