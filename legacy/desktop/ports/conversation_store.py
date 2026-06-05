from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List

from legacy.desktop.domain.models.conversation import ConversationRecord


class IConversationStore(ABC):

    @abstractmethod
    def save(self, record: ConversationRecord) -> ConversationRecord: ...

    @abstractmethod
    def list_recent(
        self,
        workspace_id: str,
        limit: int = 20,
        session_id: str = "",
    ) -> List[ConversationRecord]: ...

    @abstractmethod
    def delete_by_workspace(self, workspace_id: str) -> None: ...
