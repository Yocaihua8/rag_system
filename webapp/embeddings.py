from __future__ import annotations

import json
import math
from dataclasses import dataclass
from typing import Callable, Protocol
from urllib.request import Request, urlopen

from backend.config.settings import AppSettings, load_settings
from webapp.vector_index import text_vector


@dataclass(frozen=True)
class EmbeddingConfig:
    provider: str
    api_base: str
    api_key: str
    model: str


class EmbeddingClient(Protocol):
    provider: str
    model: str

    def embed_texts(self, texts: list[str]) -> list[dict[str, float]]:
        ...


class LocalHashEmbeddingClient:
    provider = "local"
    model = "hashing-96"

    def embed_texts(self, texts: list[str]) -> list[dict[str, float]]:
        return [text_vector(text) for text in texts]


class OpenAICompatibleEmbeddingClient:
    def __init__(
        self,
        config: EmbeddingConfig,
        opener: Callable | None = None,
        timeout: float = 60.0,
    ) -> None:
        self._config = config
        self._opener = opener or urlopen
        self._timeout = timeout

    @property
    def provider(self) -> str:
        return self._config.provider or "api"

    @property
    def model(self) -> str:
        return self._config.model

    def is_configured(self) -> bool:
        return (
            self._config.provider == "api"
            and bool(self._config.api_base.strip())
            and bool(self._config.api_key.strip())
            and bool(self._config.model.strip())
        )

    def embed_texts(self, texts: list[str]) -> list[dict[str, float]]:
        if not self.is_configured():
            raise RuntimeError("Embedding provider is not configured")
        payload = {
            "model": self._config.model,
            "input": texts,
        }
        request = Request(
            _embeddings_url(self._config.api_base),
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self._config.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        with self._opener(request, timeout=self._timeout) as response:
            data = json.loads(response.read().decode("utf-8"))
        try:
            embeddings = [item["embedding"] for item in data["data"]]
        except (KeyError, TypeError) as exc:
            raise RuntimeError("Embedding response missing data[].embedding") from exc
        if len(embeddings) != len(texts):
            raise RuntimeError("Embedding response length mismatch")
        return [_normalize_embedding(embedding) for embedding in embeddings]


def load_embedding_config(settings: AppSettings | None = None) -> EmbeddingConfig:
    current = settings or load_settings()
    return EmbeddingConfig(
        provider=current.embed_provider,
        api_base=current.embedding_api_base,
        api_key=current.embedding_api_key,
        model=current.embedding_api_model,
    )


def get_default_embedding_client() -> EmbeddingClient:
    config = load_embedding_config()
    api_client = OpenAICompatibleEmbeddingClient(config)
    if api_client.is_configured():
        return api_client
    return LocalHashEmbeddingClient()


def embed_with_fallback(
    client: EmbeddingClient,
    texts: list[str],
) -> tuple[list[dict[str, float]], str, str]:
    if not texts:
        return [], client.provider, client.model
    try:
        return client.embed_texts(texts), client.provider, client.model
    except Exception:
        fallback = LocalHashEmbeddingClient()
        return fallback.embed_texts(texts), fallback.provider, fallback.model


def _embeddings_url(api_base: str) -> str:
    return f"{api_base.rstrip('/')}/embeddings"


def _normalize_embedding(embedding) -> dict[str, float]:
    if not isinstance(embedding, list):
        raise RuntimeError("Embedding item is not a list")
    values = [float(value) for value in embedding]
    norm = math.sqrt(sum(value * value for value in values))
    if norm == 0:
        return {}
    return {
        str(index): value / norm
        for index, value in enumerate(values)
        if value != 0
    }
