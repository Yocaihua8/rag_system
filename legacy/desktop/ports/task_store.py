from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Optional

from legacy.desktop.domain.models.task import Task


class ITaskStore(ABC):

    @abstractmethod
    def save(self, task: Task) -> Task: ...

    @abstractmethod
    def update(self, task: Task) -> None: ...

    @abstractmethod
    def get(self, task_id: str) -> Optional[Task]: ...

    @abstractmethod
    def list_recent(self, limit: int = 20) -> List[Task]: ...
