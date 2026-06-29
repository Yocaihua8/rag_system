from __future__ import annotations

import dataclasses
from pathlib import Path

import pytest

from src.application.container import AppContainer
from src.application.project_analysis_usecases import ProjectAnalysisUseCase
from src.application.workspace_usecases import WorkspaceUseCases
from src.config.settings import load_settings
from src.domain.errors import NotFoundError
from src.domain.models.document import Document


def _build_container(tmp_path) -> AppContainer:
    settings = load_settings(override_env={
        "RAG_KB_ROOT": str(tmp_path / "kb"),
        "RAG_RUNTIME_DIR": str(tmp_path / "runtime"),
        "RAG_RETRIEVER_KIND": "keyword",
        "RAG_EMBED_PROVIDER": "none",
    })
    settings = dataclasses.replace(settings, db_path=Path(":memory:"))
    return AppContainer.build_for_testing(settings)


def test_container_exposes_project_knowledge_store(tmp_path):
    container = _build_container(tmp_path)

    assert container.project_knowledge_store is not None


class TestProjectAnalysisUseCase:

    def test_extracts_knowledge_points_from_project_documents(self, tmp_path):
        container = _build_container(tmp_path)
        workspace = WorkspaceUseCases(container.workspace_store).create(
            "project", str(tmp_path / "repo")
        )
        docs = [
            Document.create(
                workspace_id=workspace.id,
                title="README",
                source_path=str(tmp_path / "repo" / "README.md"),
                content="# RAG 系统\n\n使用 FastAPI、SQLite 和 PySide6 构建项目知识库。\n\n## 索引流程\n扫描文件后分块并建立索引。",
                domain="general",
                tags=["Python"],
            ),
            Document.create(
                workspace_id=workspace.id,
                title="pyproject",
                source_path=str(tmp_path / "repo" / "pyproject.toml"),
                content="[project]\ndependencies = ['pytest']",
                domain="general",
                tags=[],
            ),
            Document.create(
                workspace_id=workspace.id,
                title="test_app",
                source_path=str(tmp_path / "repo" / "tests" / "test_app.py"),
                content="def test_app():\n    assert True",
                domain="general",
                tags=[],
            ),
        ]
        container.document_store.save_batch(docs)

        result = ProjectAnalysisUseCase(
            workspace_store=container.workspace_store,
            document_store=container.document_store,
            project_knowledge_store=container.project_knowledge_store,
        ).analyze(workspace.id)

        names = {point.name for point in result.points}
        kinds = {point.kind for point in result.points}

        assert result.total_documents == 3
        assert result.total_points == len(result.points)
        assert "FastAPI" in names
        assert "SQLite" in names
        assert "PySide6" in names
        assert "索引流程" in names
        assert "测试目录" in names
        assert "tech_stack" in kinds
        assert "flow" in kinds
        assert "test" in kinds
        assert all(point.source_path for point in result.points)
        assert (
            container.project_knowledge_store.count_by_workspace(workspace.id)
            == len(result.points)
        )

    def test_analyze_replaces_old_points_for_workspace(self, tmp_path):
        container = _build_container(tmp_path)
        workspace = WorkspaceUseCases(container.workspace_store).create(
            "project", str(tmp_path / "repo")
        )
        first_doc = Document.create(
            workspace_id=workspace.id,
            title="README",
            source_path=str(tmp_path / "repo" / "README.md"),
            content="FastAPI",
            domain="general",
            tags=[],
        )
        container.document_store.save_batch([first_doc])
        usecase = ProjectAnalysisUseCase(
            workspace_store=container.workspace_store,
            document_store=container.document_store,
            project_knowledge_store=container.project_knowledge_store,
        )
        usecase.analyze(workspace.id)
        first_count = container.project_knowledge_store.count_by_workspace(workspace.id)

        container.document_store.delete(first_doc.id)
        second_doc = Document.create(
            workspace_id=workspace.id,
            title="README",
            source_path=str(tmp_path / "repo" / "README.md"),
            content="SQLite",
            domain="general",
            tags=[],
        )
        container.document_store.save_batch([second_doc])
        result = usecase.analyze(workspace.id)

        assert first_count > 0
        assert {point.name for point in result.points} == {"SQLite"}
        assert container.project_knowledge_store.count_by_workspace(workspace.id) == 1

    def test_empty_workspace_returns_empty_result(self, tmp_path):
        container = _build_container(tmp_path)
        workspace = WorkspaceUseCases(container.workspace_store).create(
            "empty", str(tmp_path / "empty")
        )

        result = ProjectAnalysisUseCase(
            workspace_store=container.workspace_store,
            document_store=container.document_store,
            project_knowledge_store=container.project_knowledge_store,
        ).analyze(workspace.id)

        assert result.total_documents == 0
        assert result.total_points == 0
        assert result.points == []

    def test_windows_tests_path_is_detected(self, tmp_path):
        container = _build_container(tmp_path)
        workspace = WorkspaceUseCases(container.workspace_store).create(
            "project", str(tmp_path / "repo")
        )
        doc = Document.create(
            workspace_id=workspace.id,
            title="test_helper",
            source_path=r"E:\repo\tests\test_helper.py",
            content="def test_helper():\n    assert True",
            domain="general",
            tags=[],
        )
        container.document_store.save_batch([doc])

        result = ProjectAnalysisUseCase(
            workspace_store=container.workspace_store,
            document_store=container.document_store,
            project_knowledge_store=container.project_knowledge_store,
        ).analyze(workspace.id)

        assert "测试目录" in {point.name for point in result.points}

    def test_nonexistent_workspace_raises(self, tmp_path):
        container = _build_container(tmp_path)

        with pytest.raises(NotFoundError):
            ProjectAnalysisUseCase(
                workspace_store=container.workspace_store,
                document_store=container.document_store,
                project_knowledge_store=container.project_knowledge_store,
            ).analyze("no-such-workspace")
