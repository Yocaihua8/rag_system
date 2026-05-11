from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List

from src.domain.models.project_knowledge import ProjectKnowledgePoint


class IProjectKnowledgeStore(ABC):

    @abstractmethod
    def save_batch(self, points: List[ProjectKnowledgePoint]) -> None:
        raise NotImplementedError

    @abstractmethod
    def list_by_workspace(self, workspace_id: str) -> List[ProjectKnowledgePoint]:
        raise NotImplementedError

    @abstractmethod
    def delete_by_workspace(self, workspace_id: str) -> None:
        raise NotImplementedError

    @abstractmethod
    def count_by_workspace(self, workspace_id: str) -> int:
        raise NotImplementedError
