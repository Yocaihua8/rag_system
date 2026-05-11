from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Optional

from src.domain.models.document import Document


class IDocumentStore(ABC):

    @abstractmethod
    def save(self, document: Document) -> None: ...

    @abstractmethod
    def save_batch(self, documents: List[Document]) -> None: ...

    @abstractmethod
    def get(self, document_id: str) -> Optional[Document]: ...

    @abstractmethod
    def list_by_workspace(self, workspace_id: str) -> List[Document]: ...

    @abstractmethod
    def delete_by_workspace(self, workspace_id: str) -> None: ...

    @abstractmethod
    def exists(self, document_id: str) -> bool: ...

    @abstractmethod
    def delete(self, document_id: str) -> None:
        """删除单个文档（级联删除关联的 chunks）。"""
        ...
