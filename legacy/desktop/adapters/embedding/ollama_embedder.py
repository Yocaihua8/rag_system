"""
OllamaEmbedder — IEmbedder 的 Ollama 实现。

使用 nomic-embed-text（768 维，支持中英文，完全本地运行）。
拉取命令：ollama pull nomic-embed-text
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List

import ollama

from legacy.desktop.ports.embedder import IEmbedder, EmbeddingResult

# 默认并行线程数（Ollama 嵌入是 I/O + CPU 混合，通常 2-4 最优）
_DEFAULT_MAX_WORKERS = 3


class OllamaEmbedder(IEmbedder):

    def __init__(
        self,
        host: str = "http://localhost:11434",
        model: str = "nomic-embed-text",
        dimension: int = 768,
        max_workers: int = _DEFAULT_MAX_WORKERS,
    ) -> None:
        self._host = host
        self._model = model
        self._dimension = dimension
        self._max_workers = max_workers
        # 主客户端保留给单条 embed 和健康检查
        self._client = ollama.Client(host=host)

    # ------------------------------------------------------------------ #
    # IEmbedder 实现
    # ------------------------------------------------------------------ #

    def embed(self, text: str) -> EmbeddingResult:
        """将单条文本转换为稠密向量。须在 Worker 线程中调用。"""
        response = self._client.embeddings(model=self._model, prompt=text)
        vector = response["embedding"]
        return EmbeddingResult(vector=vector, model=self._model)

    def embed_batch(self, texts: List[str]) -> List[EmbeddingResult]:
        """
        批量嵌入，使用线程池并发请求 Ollama 服务。
        每个线程创建独立的 Ollama Client（避免 httpx 连接池冲突）。

        若批量很小（≤2 条）或并行数=1，回退为串行调用。
        """
        if not texts:
            return []
        if len(texts) <= 2 or self._max_workers <= 1:
            return [self.embed(t) for t in texts]

        # 使用 dict 保持结果顺序 {index: EmbeddingResult}
        results: dict[int, EmbeddingResult] = {}
        workers = min(self._max_workers, len(texts))

        def _embed_one(idx: int, text: str) -> tuple[int, EmbeddingResult]:
            client = ollama.Client(host=self._host)
            response = client.embeddings(model=self._model, prompt=text)
            vector = response["embedding"]
            return idx, EmbeddingResult(vector=vector, model=self._model)

        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures = {
                executor.submit(_embed_one, i, t): i
                for i, t in enumerate(texts)
            }
            for future in as_completed(futures):
                idx, result = future.result()
                results[idx] = result

        return [results[i] for i in range(len(texts))]

    @property
    def dimension(self) -> int:
        return self._dimension


class DummyEmbedder(IEmbedder):
    """
    零依赖的测试用 Embedder。
    返回全零向量，不调用任何网络服务。
    仅用于单元测试，禁止在生产环境使用。
    """

    def __init__(self, dimension: int = 768) -> None:
        self._dimension = dimension

    def embed(self, text: str) -> EmbeddingResult:
        return EmbeddingResult(vector=[0.0] * self._dimension, model="dummy")

    def embed_batch(self, texts: List[str]) -> List[EmbeddingResult]:
        return [self.embed(t) for t in texts]

    @property
    def dimension(self) -> int:
        return self._dimension
