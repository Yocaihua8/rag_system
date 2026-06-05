from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

from legacy.desktop.domain.models.source import Source


class ISourceStore(ABC):

    @abstractmethod
    def save(self, source: Source) -> None:
        ...

    @abstractmethod
    def get_by_document(self, document_id: str) -> Optional[Source]:
        """返回文档最近一次来源记录。"""
        ...

    @abstractmethod
    def find_by_path(self, source_path: str) -> Optional[Source]:
        """按源路径获取最近一次来源记录。"""
        ...

    @abstractmethod
    def exists_same_checksum(self, source_path: str, checksum: str) -> bool:
        ...

    @abstractmethod
    def delete_by_document(self, document_id: str) -> None:
        ...
