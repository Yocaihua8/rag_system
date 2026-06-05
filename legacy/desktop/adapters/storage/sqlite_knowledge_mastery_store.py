from __future__ import annotations

from typing import List, Optional
import sqlite3

from legacy.desktop.domain.models.project_knowledge import (
    Evidence,
    KnowledgePoint,
    MasteryRecord,
    MasteryStatus,
    SkillArea,
)
from legacy.desktop.ports.knowledge_mastery_store import IKnowledgeMasteryStore


class SqliteKnowledgeMasteryStore(IKnowledgeMasteryStore):

    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def save_skill_area(self, skill_area: SkillArea) -> None:
        self._conn.execute(
            """
            INSERT OR REPLACE INTO skill_areas
                (id, workspace_id, name, description, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                skill_area.id,
                skill_area.workspace_id,
                skill_area.name,
                skill_area.description,
                skill_area.created_at,
                skill_area.updated_at,
            ),
        )
        self._conn.commit()

    def get_skill_area(self, skill_area_id: str) -> Optional[SkillArea]:
        row = self._conn.execute(
            "SELECT * FROM skill_areas WHERE id = ?",
            (skill_area_id,),
        ).fetchone()
        return _row_to_skill_area(row) if row else None

    def list_skill_areas_by_workspace(self, workspace_id: str) -> List[SkillArea]:
        rows = self._conn.execute(
            "SELECT * FROM skill_areas WHERE workspace_id = ? ORDER BY created_at ASC",
            (workspace_id,),
        ).fetchall()
        return [_row_to_skill_area(r) for r in rows]

    def delete_skill_area(self, skill_area_id: str) -> None:
        self._conn.execute("DELETE FROM skill_areas WHERE id = ?", (skill_area_id,))
        self._conn.commit()

    def save_knowledge_point(self, point: KnowledgePoint) -> None:
        self._conn.execute(
            """
            INSERT OR REPLACE INTO knowledge_points
                (id, workspace_id, skill_area_id, name, summary, confidence, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                point.id,
                point.workspace_id,
                point.skill_area_id,
                point.name,
                point.summary,
                point.confidence,
                point.created_at,
                point.updated_at,
            ),
        )
        self._conn.commit()

    def get_knowledge_point(self, point_id: str) -> Optional[KnowledgePoint]:
        row = self._conn.execute(
            "SELECT * FROM knowledge_points WHERE id = ?",
            (point_id,),
        ).fetchone()
        return _row_to_knowledge_point(row) if row else None

    def list_knowledge_points_by_workspace(self, workspace_id: str) -> List[KnowledgePoint]:
        rows = self._conn.execute(
            """
            SELECT * FROM knowledge_points
            WHERE workspace_id = ?
            ORDER BY created_at ASC, name ASC
            """,
            (workspace_id,),
        ).fetchall()
        return [_row_to_knowledge_point(r) for r in rows]

    def list_knowledge_points_by_skill_area(self, skill_area_id: str) -> List[KnowledgePoint]:
        rows = self._conn.execute(
            """
            SELECT * FROM knowledge_points
            WHERE skill_area_id = ?
            ORDER BY created_at ASC, name ASC
            """,
            (skill_area_id,),
        ).fetchall()
        return [_row_to_knowledge_point(r) for r in rows]

    def delete_knowledge_point(self, point_id: str) -> None:
        self._conn.execute("DELETE FROM knowledge_points WHERE id = ?", (point_id,))
        self._conn.commit()

    def save_evidence(self, evidence: Evidence) -> None:
        self._conn.execute(
            """
            INSERT OR REPLACE INTO evidences
                (id, workspace_id, knowledge_point_id, source_path, snippet, confidence, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                evidence.id,
                evidence.workspace_id,
                evidence.knowledge_point_id,
                evidence.source_path,
                evidence.snippet,
                evidence.confidence,
                evidence.created_at,
            ),
        )
        self._conn.commit()

    def list_evidences_by_knowledge_point(self, knowledge_point_id: str) -> List[Evidence]:
        rows = self._conn.execute(
            """
            SELECT * FROM evidences
            WHERE knowledge_point_id = ?
            ORDER BY created_at ASC
            """,
            (knowledge_point_id,),
        ).fetchall()
        return [_row_to_evidence(r) for r in rows]

    def get_evidence(self, evidence_id: str) -> Optional[Evidence]:
        row = self._conn.execute(
            "SELECT * FROM evidences WHERE id = ?",
            (evidence_id,),
        ).fetchone()
        return _row_to_evidence(row) if row else None

    def save_mastery_record(self, record: MasteryRecord) -> None:
        self._conn.execute(
            """
            INSERT OR REPLACE INTO mastery_records
                (id, workspace_id, knowledge_point_id, status, evidence_id, confidence, note, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                record.id,
                record.workspace_id,
                record.knowledge_point_id,
                record.status.value,
                record.evidence_id,
                record.confidence,
                record.note,
                record.created_at,
                record.updated_at,
            ),
        )
        self._conn.commit()

    def get_mastery_record(self, record_id: str) -> Optional[MasteryRecord]:
        row = self._conn.execute(
            "SELECT * FROM mastery_records WHERE id = ?",
            (record_id,),
        ).fetchone()
        return _row_to_mastery_record(row) if row else None

    def list_mastery_records_by_workspace(self, workspace_id: str) -> List[MasteryRecord]:
        rows = self._conn.execute(
            """
            SELECT * FROM mastery_records
            WHERE workspace_id = ?
            ORDER BY created_at DESC
            """,
            (workspace_id,),
        ).fetchall()
        return [_row_to_mastery_record(r) for r in rows]

    def list_mastery_records_by_knowledge_point(self, knowledge_point_id: str) -> List[MasteryRecord]:
        rows = self._conn.execute(
            """
            SELECT * FROM mastery_records
            WHERE knowledge_point_id = ?
            ORDER BY created_at DESC
            """,
            (knowledge_point_id,),
        ).fetchall()
        return [_row_to_mastery_record(r) for r in rows]

    def delete_by_workspace(self, workspace_id: str) -> None:
        self._conn.execute("DELETE FROM skill_areas WHERE workspace_id = ?", (workspace_id,))
        self._conn.commit()


def _row_to_skill_area(row: sqlite3.Row) -> SkillArea:
    return SkillArea(
        id=row["id"],
        workspace_id=row["workspace_id"],
        name=row["name"],
        description=row["description"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _row_to_knowledge_point(row: sqlite3.Row) -> KnowledgePoint:
    return KnowledgePoint(
        id=row["id"],
        workspace_id=row["workspace_id"],
        skill_area_id=row["skill_area_id"],
        name=row["name"],
        summary=row["summary"],
        confidence=row["confidence"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _row_to_evidence(row: sqlite3.Row) -> Evidence:
    return Evidence(
        id=row["id"],
        workspace_id=row["workspace_id"],
        knowledge_point_id=row["knowledge_point_id"],
        source_path=row["source_path"],
        snippet=row["snippet"],
        confidence=row["confidence"],
        created_at=row["created_at"],
    )


def _row_to_mastery_record(row: sqlite3.Row) -> MasteryRecord:
    return MasteryRecord(
        id=row["id"],
        workspace_id=row["workspace_id"],
        knowledge_point_id=row["knowledge_point_id"],
        status=MasteryStatus(row["status"]),
        evidence_id=row["evidence_id"],
        confidence=row["confidence"],
        note=row["note"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )
