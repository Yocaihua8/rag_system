from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Optional

from src.domain.models.chunk import Chunk


class IChunkStore(ABC):

    @abstractmethod
    def save_batch(self, chunks: List[Chunk]) -> None: ...

    @abstractmethod
    def get(self, chunk_id: str) -> Optional[Chunk]: ...

    @abstractmethod
    def list_by_workspace(self, workspace_id: str) -> List[Chunk]: ...

    @abstractmethod
    def list_by_document(self, document_id: str) -> List[Chunk]: ...

    @abstractmethod
    def delete_by_workspace(self, workspace_id: str) -> None: ...

    @abstractmethod
    def count_by_workspace(self, workspace_id: str) -> int: ...

    @abstractmethod
    def list_by_ids(self, chunk_ids: list[str]) -> list[Chunk]:
        """批量按 ID 加载 Chunk，用于避免 N+1 查询。保持输入顺序。"""
        ...
