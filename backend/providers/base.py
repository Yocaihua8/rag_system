from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterator, Sequence
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


__all__ = [
    "BaseEmbedder",
    "BaseLLM",
    "LLMMessage",
    "LLMResult",
]
