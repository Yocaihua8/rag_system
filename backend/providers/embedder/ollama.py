from __future__ import annotations

import json
import sys
from collections.abc import Callable, Sequence
from urllib.error import URLError
from urllib.request import Request, urlopen

from backend.providers.base import BaseEmbedder

DEFAULT_OLLAMA_EMBED_MODEL = "nomic-embed-text"
DEFAULT_OLLAMA_EMBED_DIMENSION = 768
DEFAULT_OLLAMA_HOST = "http://localhost:11434"


class OllamaEmbedder(BaseEmbedder):
    def __init__(
        self,
        host: str = DEFAULT_OLLAMA_HOST,
        model: str = DEFAULT_OLLAMA_EMBED_MODEL,
        dimension: int = DEFAULT_OLLAMA_EMBED_DIMENSION,
        opener: Callable | None = None,
        timeout: float = 60.0,
    ) -> None:
        self._host = host.rstrip("/")
        self._model = model
        self._dimension = dimension
        self._opener = opener or urlopen
        self._timeout = timeout

    @property
    def provider(self) -> str:
        return "ollama"

    @property
    def model(self) -> str:
        return self._model

    @property
    def dimension(self) -> int:
        return self._dimension

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        if not texts:
            return []
        return [self._embed_one(text) for text in texts]

    def is_available(self) -> bool:
        try:
            self._request_json("/api/tags", None, method="GET")
            return True
        except Exception as exc:
            print(f"WARNING: Ollama embeddings are not available at {self._host}: {exc}", file=sys.stderr)
            return False

    def _embed_one(self, text: str) -> list[float]:
        data = self._request_json(
            "/api/embeddings",
            {"model": self._model, "prompt": text},
        )
        vector = data.get("embedding")
        if not isinstance(vector, list):
            raise RuntimeError("Ollama embedding response missing embedding")
        return [float(value) for value in vector]

    def _request_json(self, path: str, payload: dict | None, method: str = "POST") -> dict:
        data = None
        headers = {"Content-Type": "application/json"}
        if payload is not None:
            data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        request = Request(f"{self._host}{path}", data=data, headers=headers, method=method)
        try:
            with self._opener(request, timeout=self._timeout) as response:
                raw_body = response.read().decode("utf-8")
        except URLError as exc:
            raise RuntimeError(str(exc.reason)) from exc
        try:
            return json.loads(raw_body or "{}")
        except json.JSONDecodeError as exc:
            raise RuntimeError("Ollama embedding response is not valid JSON") from exc


__all__ = [
    "DEFAULT_OLLAMA_EMBED_DIMENSION",
    "DEFAULT_OLLAMA_EMBED_MODEL",
    "DEFAULT_OLLAMA_HOST",
    "OllamaEmbedder",
]
