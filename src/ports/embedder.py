from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List


@dataclass(frozen=True)
class EmbeddingResult:
    vector: List[float]
    model: str


class IEmbedder(ABC):
    """文本嵌入接口。实现必须保证同一模型对相同输入返回相同向量。"""

    @abstractmethod
    def embed(self, text: str) -> EmbeddingResult:
        """将单条文本转换为稠密向量。"""
        ...

    @abstractmethod
    def embed_batch(self, texts: List[str]) -> List[EmbeddingResult]:
        """批量嵌入，减少网络往返。返回列表与输入等长且顺序对应。"""
        ...

    @property
    @abstractmethod
    def dimension(self) -> int:
        """向量维度（如 nomic-embed-text = 768）。"""
        ...
