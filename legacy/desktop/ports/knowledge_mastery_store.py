from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Optional

from legacy.desktop.domain.models.project_knowledge import (
    Evidence,
    KnowledgePoint,
    MasteryRecord,
    SkillArea,
)


class IKnowledgeMasteryStore(ABC):

    @abstractmethod
    def save_skill_area(self, skill_area: SkillArea) -> None:
        ...

    @abstractmethod
    def get_skill_area(self, skill_area_id: str) -> Optional[SkillArea]:
        ...

    @abstractmethod
    def list_skill_areas_by_workspace(self, workspace_id: str) -> List[SkillArea]:
        ...

    @abstractmethod
    def delete_skill_area(self, skill_area_id: str) -> None:
        ...

    @abstractmethod
    def save_knowledge_point(self, point: KnowledgePoint) -> None:
        ...

    @abstractmethod
    def get_knowledge_point(self, point_id: str) -> Optional[KnowledgePoint]:
        ...

    @abstractmethod
    def list_knowledge_points_by_workspace(
        self,
        workspace_id: str,
    ) -> List[KnowledgePoint]:
        ...

    @abstractmethod
    def list_knowledge_points_by_skill_area(
        self,
        skill_area_id: str,
    ) -> List[KnowledgePoint]:
        ...

    @abstractmethod
    def delete_knowledge_point(self, point_id: str) -> None:
        ...

    @abstractmethod
    def save_evidence(self, evidence: Evidence) -> None:
        ...

    @abstractmethod
    def list_evidences_by_knowledge_point(
        self,
        knowledge_point_id: str,
    ) -> List[Evidence]:
        ...

    @abstractmethod
    def get_evidence(self, evidence_id: str) -> Optional[Evidence]:
        ...

    @abstractmethod
    def save_mastery_record(self, record: MasteryRecord) -> None:
        ...

    @abstractmethod
    def get_mastery_record(self, record_id: str) -> Optional[MasteryRecord]:
        ...

    @abstractmethod
    def list_mastery_records_by_workspace(self, workspace_id: str) -> List[MasteryRecord]:
        ...

    @abstractmethod
    def list_mastery_records_by_knowledge_point(
        self,
        knowledge_point_id: str,
    ) -> List[MasteryRecord]:
        ...

    @abstractmethod
    def delete_by_workspace(self, workspace_id: str) -> None:
        ...
