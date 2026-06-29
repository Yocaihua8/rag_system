from __future__ import annotations

from typing import List
import sqlite3

from src.domain.models.graph import GraphEdge, GraphNode
from src.ports.graph_store import IGraphStore


class SqliteGraphStore(IGraphStore):

    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def save_node(self, node: GraphNode) -> None:
        self._conn.execute(
            """
            INSERT OR REPLACE INTO graph_nodes
                (id, workspace_id, name, label, node_type, source_ref, confidence, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                node.id,
                node.workspace_id,
                node.name,
                node.label,
                node.node_type,
                node.source_ref,
                node.confidence,
                node.created_at,
                node.updated_at,
            ),
        )
        self._conn.commit()

    def save_edge(self, edge: GraphEdge) -> None:
        self._conn.execute(
            """
            INSERT OR REPLACE INTO graph_edges
                (id, workspace_id, source_node_id, target_node_id, relationship, confidence, source_path, source_snippet, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                edge.id,
                edge.workspace_id,
                edge.source_node_id,
                edge.target_node_id,
                edge.relationship,
                edge.confidence,
                edge.source_path,
                edge.source_snippet,
                edge.created_at,
                edge.updated_at,
            ),
        )
        self._conn.commit()

    def get_node(self, node_id: str) -> GraphNode | None:
        row = self._conn.execute(
            "SELECT * FROM graph_nodes WHERE id = ?",
            (node_id,),
        ).fetchone()
        return _row_to_node(row) if row else None

    def get_edge(self, edge_id: str) -> GraphEdge | None:
        row = self._conn.execute(
            "SELECT * FROM graph_edges WHERE id = ?",
            (edge_id,),
        ).fetchone()
        return _row_to_edge(row) if row else None

    def list_nodes_by_workspace(self, workspace_id: str) -> List[GraphNode]:
        rows = self._conn.execute(
            """
            SELECT * FROM graph_nodes
            WHERE workspace_id = ?
            ORDER BY updated_at ASC, name ASC
            """,
            (workspace_id,),
        ).fetchall()
        return [_row_to_node(r) for r in rows]

    def list_edges_by_workspace(self, workspace_id: str) -> List[GraphEdge]:
        rows = self._conn.execute(
            """
            SELECT * FROM graph_edges
            WHERE workspace_id = ?
            ORDER BY updated_at ASC
            """,
            (workspace_id,),
        ).fetchall()
        return [_row_to_edge(r) for r in rows]

    def list_nodes_by_type(self, workspace_id: str, node_type: str) -> List[GraphNode]:
        rows = self._conn.execute(
            """
            SELECT * FROM graph_nodes
            WHERE workspace_id = ? AND node_type = ?
            ORDER BY updated_at ASC, name ASC
            """,
            (workspace_id, node_type),
        ).fetchall()
        return [_row_to_node(r) for r in rows]

    def list_edges_by_node(
        self,
        workspace_id: str,
        source_node_id: str,
        min_confidence: float | None = None,
    ) -> List[GraphEdge]:
        query = """
            SELECT * FROM graph_edges
            WHERE workspace_id = ? AND source_node_id = ?
        """
        params = [workspace_id, source_node_id]
        if min_confidence is not None:
            query += " AND confidence >= ?"
            params.append(min_confidence)
        query += " ORDER BY confidence DESC, updated_at ASC"
        rows = self._conn.execute(query, tuple(params)).fetchall()
        return [_row_to_edge(r) for r in rows]

    def delete_node(self, node_id: str) -> None:
        self._conn.execute(
            "DELETE FROM graph_nodes WHERE id = ?",
            (node_id,),
        )
        self._conn.commit()

    def delete_edge(self, edge_id: str) -> None:
        self._conn.execute(
            "DELETE FROM graph_edges WHERE id = ?",
            (edge_id,),
        )
        self._conn.commit()

    def delete_by_workspace(self, workspace_id: str) -> None:
        self._conn.execute(
            "DELETE FROM graph_edges WHERE workspace_id = ?",
            (workspace_id,),
        )
        self._conn.execute(
            "DELETE FROM graph_nodes WHERE workspace_id = ?",
            (workspace_id,),
        )
        self._conn.commit()

    def count_nodes_by_workspace(self, workspace_id: str) -> int:
        row = self._conn.execute(
            "SELECT COUNT(*) FROM graph_nodes WHERE workspace_id = ?",
            (workspace_id,),
        ).fetchone()
        return row[0] if row else 0

    def count_edges_by_workspace(self, workspace_id: str) -> int:
        row = self._conn.execute(
            "SELECT COUNT(*) FROM graph_edges WHERE workspace_id = ?",
            (workspace_id,),
        ).fetchone()
        return row[0] if row else 0


def _row_to_node(row: sqlite3.Row) -> GraphNode:
    return GraphNode(
        id=row["id"],
        workspace_id=row["workspace_id"],
        name=row["name"],
        label=row["label"],
        node_type=row["node_type"],
        source_ref=row["source_ref"],
        confidence=row["confidence"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _row_to_edge(row: sqlite3.Row) -> GraphEdge:
    return GraphEdge(
        id=row["id"],
        workspace_id=row["workspace_id"],
        source_node_id=row["source_node_id"],
        target_node_id=row["target_node_id"],
        relationship=row["relationship"],
        confidence=row["confidence"],
        source_path=row["source_path"],
        source_snippet=row["source_snippet"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )
