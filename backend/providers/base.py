from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterator, Mapping, Sequence
from dataclasses import dataclass


@dataclass(frozen=True)
class LLMMessage:
    role: str
    content: str


@dataclass(frozen=True)
class LLMResult:
    content: str
    model: str
    provider: str


@dataclass(frozen=True)
class VectorSearchHit:
    chunk_id: str
    score: float
    provider: str = "local"
    model: str = "hashing-96"


@dataclass(frozen=True)
class VectorUpsertRecord:
    project_id: str
    document_id: str
    chunk_id: str
    chunk_index: int
    path: str
    content: str
    vector: Mapping[str, float]
    provider: str
    model: str


class BaseLLM(ABC):
    @property
    @abstractmethod
    def provider(self) -> str:
        """Provider identifier returned to API clients and observability."""

    @abstractmethod
    def generate(
        self,
        prompt: str,
        *,
        system_prompt: str = "",
        history: Sequence[LLMMessage] | None = None,
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> LLMResult:
        """Return a complete answer for a prompt."""

    @abstractmethod
    def stream(
        self,
        prompt: str,
        *,
        system_prompt: str = "",
        history: Sequence[LLMMessage] | None = None,
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> Iterator[str]:
        """Yield answer text chunks for a prompt."""

    @abstractmethod
    def is_available(self) -> bool:
        """Return whether the provider can be reached without blocking app startup."""


class BaseEmbedder(ABC):
    @property
    @abstractmethod
    def provider(self) -> str:
        """Provider identifier stored with generated vectors."""

    @property
    @abstractmethod
    def model(self) -> str:
        """Embedding model identifier stored with generated vectors."""

    @property
    @abstractmethod
    def dimension(self) -> int:
        """Expected vector dimension for this embedder."""

    @abstractmethod
    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        """Return one vector per input text, preserving input order."""

    @abstractmethod
    def is_available(self) -> bool:
        """Return whether the provider can be reached without blocking app startup."""


class BaseReranker(ABC):
    @abstractmethod
    def rerank(
        self,
        query: str,
        candidates: Sequence[object],
        top_n: int | None = None,
    ) -> list[object]:
        """Return candidates ordered by descending relevance to the query."""


class BaseVectorStore(ABC):
    @abstractmethod
    def search(
        self,
        project_id: str,
        query_vector: Mapping[str, float],
        limit: int,
    ) -> list[VectorSearchHit]:
        """Return vector hits ordered by descending similarity for a project."""

    @abstractmethod
    def upsert(self, records: Sequence[VectorUpsertRecord]) -> None:
        """Insert or update chunk vectors."""

    @abstractmethod
    def delete(self, project_id: str, chunk_ids: Sequence[str] | None = None) -> None:
        """Delete vectors for selected chunks, or the whole project when omitted."""

    @abstractmethod
    def is_available(self) -> bool:
        """Return whether the vector store can be used without blocking startup."""


__all__ = [
    "BaseEmbedder",
    "BaseLLM",
    "BaseReranker",
    "BaseVectorStore",
    "LLMMessage",
    "LLMResult",
    "VectorSearchHit",
    "VectorUpsertRecord",
]
