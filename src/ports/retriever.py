from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List

from src.domain.models.chunk import Chunk


@dataclass(frozen=True)
class RetrievalQuery:
    question: str
    workspace_id: str
    domains: List[str] = field(default_factory=list)   # 空 = 不限领域
    tags: List[str] = field(default_factory=list)       # 空 = 不限标签
    top_k: int = 8


@dataclass(frozen=True)
class RetrievalResult:
    chunks: List[Chunk]
    scores: List[float]      # 与 chunks 等长，相似度降序

    def is_empty(self) -> bool:
        return len(self.chunks) == 0

    def top_chunk(self) -> Chunk:
        if self.is_empty():
            raise ValueError("RetrievalResult is empty")
        return self.chunks[0]


class IRetriever(ABC):
    """检索接口。支持向量检索和关键词检索两种实现。"""

    @abstractmethod
    def search(self, query: RetrievalQuery) -> RetrievalResult:
        """执行检索，返回相关 Chunk 及其分数。"""
        ...

    @abstractmethod
    def index(self, chunks: List[Chunk]) -> None:
        """
        将 Chunk 列表加入索引。
        VectorRetriever：调用 IEmbedder 生成向量后写入 IVectorStore。
        KeywordRetriever：更新内存 token 索引。
        由 IngestWorkspaceUseCase 在摄入完成后调用。
        """
        ...

    @abstractmethod
    def clear(self, workspace_id: str) -> None:
        """清除指定工作区的全部索引数据（重建索引前调用）。"""
        ...
