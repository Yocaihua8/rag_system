from __future__ import annotations

import json
from urllib.error import URLError

import pytest

from backend.providers.embedder.ollama import OllamaEmbedder


class _FakeResponse:
    def __init__(self, body: dict | str) -> None:
        self._body = body

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False

    def read(self) -> bytes:
        if isinstance(self._body, str):
            return self._body.encode("utf-8")
        return json.dumps(self._body).encode("utf-8")


def _payload(request) -> dict:
    return json.loads((request.data or b"{}").decode("utf-8"))


def test_ollama_embedder_preserves_input_order():
    vectors = {
        "第一段": [1.0, 0.0],
        "第二段": [0.0, 1.0],
    }
    prompts: list[str] = []

    def opener(request, timeout):
        payload = _payload(request)
        prompts.append(payload["prompt"])
        return _FakeResponse({"embedding": vectors[payload["prompt"]]})

    embedder = OllamaEmbedder(host="http://ollama.local", model="nomic-embed-text", dimension=2, opener=opener)

    assert embedder.embed(["第一段", "第二段"]) == [[1.0, 0.0], [0.0, 1.0]]
    assert prompts == ["第一段", "第二段"]
    assert embedder.provider == "ollama"
    assert embedder.model == "nomic-embed-text"
    assert embedder.dimension == 2


def test_ollama_embedder_empty_input_skips_network_call():
    def opener(request, timeout):
        raise AssertionError("empty embedding input should not call Ollama")

    embedder = OllamaEmbedder(host="http://ollama.local", opener=opener)

    assert embedder.embed([]) == []


def test_ollama_embedder_posts_expected_embedding_payload():
    calls: list[dict] = []

    def opener(request, timeout):
        calls.append({"url": request.full_url, "method": request.method, "payload": _payload(request), "timeout": timeout})
        return _FakeResponse({"embedding": ["1", 2, 3.5]})

    embedder = OllamaEmbedder(host="http://ollama.local/", model="embed-model", dimension=3, opener=opener, timeout=2.5)

    assert embedder.embed(["片段"]) == [[1.0, 2.0, 3.5]]
    assert calls == [
        {
            "url": "http://ollama.local/api/embeddings",
            "method": "POST",
            "payload": {"model": "embed-model", "prompt": "片段"},
            "timeout": 2.5,
        }
    ]


def test_ollama_embedder_availability_failure_warns_without_raising(capsys):
    def opener(request, timeout):
        raise URLError("connection refused")

    embedder = OllamaEmbedder(host="http://ollama.local", opener=opener)

    assert embedder.is_available() is False
    assert "WARNING: Ollama embeddings are not available at http://ollama.local" in capsys.readouterr().err


def test_ollama_embedder_rejects_invalid_embedding_response():
    missing_embedding = OllamaEmbedder(
        host="http://ollama.local",
        opener=lambda request, timeout: _FakeResponse({"not_embedding": []}),
    )
    invalid_json = OllamaEmbedder(
        host="http://ollama.local",
        opener=lambda request, timeout: _FakeResponse("{"),
    )

    with pytest.raises(RuntimeError, match="Ollama embedding response missing embedding"):
        missing_embedding.embed(["片段"])

    with pytest.raises(RuntimeError, match="Ollama embedding response is not valid JSON"):
        invalid_json.embed(["片段"])
