from __future__ import annotations

from dataclasses import dataclass
from typing import List

from src.domain.errors import NotFoundError, ValidationError
from src.domain.models.graph import GraphEdge, GraphNode
from src.ports.graph_store import IGraphStore
from src.ports.workspace_store import IWorkspaceStore


class GraphUseCase:
    """轻量知识图谱用例：提供节点/关系创建与邻接查询。"""

    def __init__(self, workspace_store: IWorkspaceStore, graph_store: IGraphStore) -> None:
        self._workspace_store = workspace_store
        self._graph_store = graph_store

    def create_node(
        self,
        workspace_id: str,
        name: str,
        node_type: str = "concept",
        label: str = "",
        source_ref: str = "",
        confidence: float = 0.6,
    ) -> GraphNode:
        self._require_workspace(workspace_id)
        name = (name or "").strip()
        if not name:
            raise ValidationError("图谱节点名称不能为空")
        if not (0.0 <= confidence <= 1.0):
            raise ValidationError("置信度范围需在 0.0-1.0")
        node = GraphNode.create(
            workspace_id=workspace_id,
            name=name,
            node_type=(node_type or "concept").strip() or "concept",
            label=label,
            source_ref=source_ref,
            confidence=confidence,
        )
        self._graph_store.save_node(node)
        return node

    def create_edge(
        self,
        workspace_id: str,
        source_node_id: str,
        target_node_id: str,
        relationship: str,
        source_path: str = "",
        source_snippet: str = "",
        confidence: float = 0.6,
    ) -> GraphEdge:
        self._require_workspace(workspace_id)
        if source_node_id == target_node_id:
            raise ValidationError("不能创建指向自身的关系")

        source = self._get_node(workspace_id, source_node_id)
        target = self._get_node(workspace_id, target_node_id)
        if source is None or target is None:
            raise NotFoundError("GraphNode", source_node_id if source is None else target_node_id)

        if not (relationship or "").strip():
            raise ValidationError("关系类型不能为空")
        if not (0.0 <= confidence <= 1.0):
            raise ValidationError("置信度范围需在 0.0-1.0")

        edge = GraphEdge.create(
            workspace_id=workspace_id,
            source_node_id=source.id,
            target_node_id=target.id,
            relationship=relationship,
            source_path=source_path,
            source_snippet=source_snippet,
            confidence=confidence,
        )
        self._graph_store.save_edge(edge)
        return edge

    def list_edges(
        self,
        workspace_id: str,
        node_id: str,
        min_confidence: float = 0.0,
    ) -> List[GraphEdge]:
        self._require_workspace(workspace_id)
        self._ensure_node_exists(workspace_id, node_id)
        threshold = self._normalize_confidence(min_confidence)
        return self._graph_store.list_edges_by_node(workspace_id, node_id, threshold)

    def list_neighbors(
        self,
        workspace_id: str,
        node_id: str,
        min_confidence: float = 0.0,
    ) -> List[GraphNode]:
        edges = self.list_edges(workspace_id, node_id, min_confidence)
        target_ids = [edge.target_node_id for edge in edges]
        neighbors: List[GraphNode] = []
        seen = set()
        for target_id in target_ids:
            if target_id in seen:
                continue
            node = self._get_node(workspace_id, target_id)
            if node is not None:
                neighbors.append(node)
                seen.add(target_id)
        return neighbors

    def list_nodes_by_type(self, workspace_id: str, node_type: str) -> List[GraphNode]:
        self._require_workspace(workspace_id)
        return self._graph_store.list_nodes_by_type(
            workspace_id=workspace_id,
            node_type=(node_type or "concept").strip() or "concept",
        )

    def _ensure_node_exists(self, workspace_id: str, node_id: str) -> None:
        node = self._get_node(workspace_id, node_id)
        if node is None:
            raise NotFoundError("GraphNode", node_id)

    def _get_node(self, workspace_id: str, node_id: str) -> GraphNode | None:
        node = self._graph_store.get_node(node_id)
        if node is None or node.workspace_id != workspace_id:
            return None
        return node

    def _require_workspace(self, workspace_id: str) -> None:
        workspace = self._workspace_store.get(workspace_id)
        if workspace is None:
            raise NotFoundError("Workspace", workspace_id)

    def _normalize_confidence(self, value: float) -> float:
        if value < 0:
            return 0.0
        if value > 1:
            return 1.0
        return value
