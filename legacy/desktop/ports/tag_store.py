from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Optional

from legacy.desktop.domain.models.tag import Tag, DocumentTag


class ITagStore(ABC):

    @abstractmethod
    def save(self, tag: Tag) -> None:
        """新增或更新标签。"""
        ...

    @abstractmethod
    def get(self, tag_id: str) -> Optional[Tag]:
        ...

    @abstractmethod
    def get_by_name(self, name: str) -> Optional[Tag]:
        ...

    @abstractmethod
    def list_all(self) -> List[Tag]:
        ...

    @abstractmethod
    def delete(self, tag_id: str) -> None:
        ...


class IDocumentTagStore(ABC):

    @abstractmethod
    def save(self, link: DocumentTag) -> None:
        """绑定文档-标签关系（幂等）。"""
        ...

    @abstractmethod
    def delete_by_document(self, document_id: str) -> None:
        ...

    @abstractmethod
    def list_tag_ids_by_document(self, document_id: str) -> List[str]:
        """返回文档绑定的 tag_id 列表。"""
        ...

    @abstractmethod
    def list_documents_by_tag(self, tag_id: str) -> List[str]:
        """返回绑定某标签的文档 id 列表。"""
        ...
