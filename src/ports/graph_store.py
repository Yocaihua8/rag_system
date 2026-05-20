from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List

from src.domain.models.graph import GraphEdge, GraphNode


class IGraphStore(ABC):

    @abstractmethod
    def save_node(self, node: GraphNode) -> None:
        raise NotImplementedError

    @abstractmethod
    def save_edge(self, edge: GraphEdge) -> None:
        raise NotImplementedError

    @abstractmethod
    def get_node(self, node_id: str) -> GraphNode | None:
        raise NotImplementedError

    @abstractmethod
    def get_edge(self, edge_id: str) -> GraphEdge | None:
        raise NotImplementedError

    @abstractmethod
    def list_nodes_by_workspace(self, workspace_id: str) -> List[GraphNode]:
        raise NotImplementedError

    @abstractmethod
    def list_edges_by_workspace(self, workspace_id: str) -> List[GraphEdge]:
        raise NotImplementedError

    @abstractmethod
    def list_nodes_by_type(
        self,
        workspace_id: str,
        node_type: str,
    ) -> List[GraphNode]:
        raise NotImplementedError

    @abstractmethod
    def list_edges_by_node(
        self,
        workspace_id: str,
        source_node_id: str,
        min_confidence: float | None = None,
    ) -> List[GraphEdge]:
        raise NotImplementedError

    @abstractmethod
    def delete_node(self, node_id: str) -> None:
        raise NotImplementedError

    @abstractmethod
    def delete_edge(self, edge_id: str) -> None:
        raise NotImplementedError

    @abstractmethod
    def delete_by_workspace(self, workspace_id: str) -> None:
        raise NotImplementedError

    @abstractmethod
    def count_nodes_by_workspace(self, workspace_id: str) -> int:
        raise NotImplementedError

    @abstractmethod
    def count_edges_by_workspace(self, workspace_id: str) -> int:
        raise NotImplementedError
