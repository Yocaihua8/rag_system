from __future__ import annotations

import dataclasses
import pytest
from pathlib import Path

from legacy.desktop.application.container import AppContainer
from legacy.desktop.application.graph_usecases import GraphUseCase
from legacy.desktop.application.workspace_usecases import WorkspaceUseCases
from legacy.desktop.config.settings import load_settings
from legacy.desktop.domain.errors import NotFoundError, ValidationError


def _build_container(tmp_path) -> AppContainer:
    settings = load_settings(override_env={
        "RAG_KB_ROOT": str(tmp_path / "kb"),
        "RAG_RUNTIME_DIR": str(tmp_path / "runtime"),
        "RAG_RETRIEVER_KIND": "keyword",
        "RAG_EMBED_PROVIDER": "none",
    })
    settings = dataclasses.replace(settings, db_path=Path(":memory:"))
    return AppContainer.build_for_testing(settings)


class TestGraphUseCase:

    def test_create_node_and_edge_and_neighbors(self, tmp_path):
        container = _build_container(tmp_path)
        ws = WorkspaceUseCases(container.workspace_store).create("ws", str(tmp_path / "repo"))
        uc = GraphUseCase(container.workspace_store, container.graph_store)

        concept = uc.create_node(
            workspace_id=ws.id,
            name="知识图谱",
            node_type="concept",
            confidence=0.9,
        )
        file_node = uc.create_node(
            workspace_id=ws.id,
            name="README",
            node_type="artifact",
            confidence=0.8,
        )

        edge = uc.create_edge(
            workspace_id=ws.id,
            source_node_id=concept.id,
            target_node_id=file_node.id,
            relationship="defined_in",
            source_path="README.md",
            confidence=0.88,
        )

        neighbors = uc.list_neighbors(ws.id, concept.id, min_confidence=0.5)
        assert neighbors == [file_node]

        edges = uc.list_edges(ws.id, concept.id, min_confidence=0.85)
        assert edges == [edge]

    def test_create_edge_requires_existing_nodes(self, tmp_path):
        container = _build_container(tmp_path)
        ws = WorkspaceUseCases(container.workspace_store).create("ws", str(tmp_path / "repo"))
        uc = GraphUseCase(container.workspace_store, container.graph_store)
        node = uc.create_node(ws.id, "node-a")

        with pytest.raises(NotFoundError):
            uc.create_edge(
                workspace_id=ws.id,
                source_node_id=node.id,
                target_node_id="missing-node",
                relationship="related_to",
            )

    def test_validation_errors(self, tmp_path):
        container = _build_container(tmp_path)
        ws = WorkspaceUseCases(container.workspace_store).create("ws", str(tmp_path / "repo"))
        uc = GraphUseCase(container.workspace_store, container.graph_store)

        with pytest.raises(ValidationError):
            uc.create_node(ws.id, "   ")
        with pytest.raises(ValidationError):
            uc.create_node(ws.id, "node", confidence=-0.1)
        with pytest.raises(NotFoundError):
            uc.list_neighbors(ws.id, "missing-node")
