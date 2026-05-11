from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, List, Tuple


@dataclass(frozen=True)
class VectorSearchResult:
    chunk_id: str
    score: float             # 余弦相似度，范围 [0, 1]，越大越相似


class IVectorStore(ABC):
    """向量索引的读写接口。实现负责持久化策略（内存/文件/数据库）。"""

    @abstractmethod
    def upsert(
        self,
        chunk_id: str,
        vector: List[float],
        metadata: Dict[str, str],
    ) -> None:
        """插入或更新单个向量。metadata 用于过滤（workspace_id / domain / tags）。"""
        ...

    @abstractmethod
    def upsert_batch(
        self,
        items: List[Tuple[str, List[float], Dict[str, str]]],
    ) -> None:
        """批量插入/更新。items 中每项为 (chunk_id, vector, metadata)。"""
        ...

    @abstractmethod
    def search(
        self,
        query_vector: List[float],
        top_k: int,
        workspace_id: str,
        domain: str = "",
    ) -> List[VectorSearchResult]:
        """
        在指定工作区内执行最近邻搜索。
        若 domain 非空，则仅在该领域内搜索。
        返回列表按 score 降序排列，最多 top_k 条。
        """
        ...

    @abstractmethod
    def delete_by_workspace(self, workspace_id: str) -> None:
        """删除指定工作区的全部向量（重建索引前调用）。"""
        ...

    @abstractmethod
    def count(self, workspace_id: str) -> int:
        """返回指定工作区的向量数量。"""
        ...
