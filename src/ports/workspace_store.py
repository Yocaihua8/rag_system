from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Optional

from src.domain.models.workspace import Workspace


class IWorkspaceStore(ABC):

    @abstractmethod
    def save(self, workspace: Workspace) -> Workspace: ...

    @abstractmethod
    def get(self, workspace_id: str) -> Optional[Workspace]: ...

    @abstractmethod
    def list_all(self) -> List[Workspace]: ...

    @abstractmethod
    def update(self, workspace: Workspace) -> None: ...

    @abstractmethod
    def delete(self, workspace_id: str) -> None: ...
