"""
test_tag_source_usecases.py — Tag / Source 用例测试。

验证：
  - 标签绑定用例会归一化名称并去重
  - 绑定关系按文档清空与重建
  - checksum 可用于判断文件来源是否未变更
"""
from __future__ import annotations

from pathlib import Path

from legacy.desktop.adapters.storage.db import create_connection, init_schema
from legacy.desktop.adapters.storage.sqlite_document_store import SqliteDocumentStore
from legacy.desktop.adapters.storage.sqlite_tag_store import SqliteTagStore, SqliteDocumentTagStore
from legacy.desktop.adapters.storage.sqlite_source_store import SqliteSourceStore
from legacy.desktop.adapters.storage.sqlite_workspace_store import SqliteWorkspaceStore
from legacy.desktop.application.tag_source_usecases import DocumentTaggingUseCase, SourceUseCase
from legacy.desktop.domain.models.document import Document
from legacy.desktop.domain.models.workspace import Workspace


import pytest


@pytest.fixture
def conn():
    c = create_connection(Path(":memory:"))
    init_schema(c)
    yield c
    c.close()


@pytest.fixture
def stores(conn):
    return {
        "workspace": SqliteWorkspaceStore(conn),
        "document": SqliteDocumentStore(conn),
        "tag": SqliteTagStore(conn),
        "doc_tag": SqliteDocumentTagStore(conn),
        "source": SqliteSourceStore(conn),
    }


def _make_document(stores) -> Document:
    workspace = Workspace.create("ws", "/tmp")
    stores["workspace"].save(workspace)
    doc = Document.create(
        workspace_id=workspace.id,
        title="doc",
        source_path="/tmp/doc.md",
        content="content",
        domain="general",
    )
    stores["document"].save(doc)
    return doc


class TestDocumentTaggingUseCase:

    def test_set_and_clear_document_tags(self, conn, stores):
        doc = _make_document(stores)
        uc = DocumentTaggingUseCase(stores["tag"], stores["doc_tag"])

        tags = uc.set_document_tags(doc.id, ["RAG", "  AI  ", "RAG"])
        assert [t.name for t in tags] == ["RAG", "AI"]
        assert [t.name for t in uc.list_document_tags(doc.id)] == ["AI", "RAG"]

        uc.clear_document_tags(doc.id)
        assert uc.list_document_tags(doc.id) == []


class TestSourceUseCase:

    def test_upsert_and_unchanged(self, stores):
        doc = _make_document(stores)
        uc = SourceUseCase(stores["source"])
        source = uc.upsert_source(
            document_id=doc.id,
            source_type="markdown",
            source_path="/tmp/doc.md",
            checksum="abc",
        )

        assert source.id
        assert stores["source"].get_by_document(doc.id) is not None
        assert uc.is_unchanged("/tmp/doc.md", "abc") is True
        assert uc.is_unchanged("/tmp/doc.md", "diff") is False
