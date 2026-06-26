from __future__ import annotations

import json
from pathlib import Path
from urllib.error import URLError

from backend.config.paths import app_data_dir
from backend.providers.embedder.ollama import OllamaEmbedder
from backend.providers.llm.ollama import OllamaLLM


class _FakeResponse:
    def __init__(self, body: dict | None = None, lines: list[dict] | None = None) -> None:
        self._body = body or {}
        self._lines = lines or []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False

    def read(self) -> bytes:
        return json.dumps(self._body).encode("utf-8")

    def __iter__(self):
        for line in self._lines:
            yield (json.dumps(line) + "\n").encode("utf-8")


def _payload(request) -> dict:
    return json.loads((request.data or b"{}").decode("utf-8"))


def test_ollama_llm_generate_posts_chat_payload():
    calls: list[dict] = []

    def opener(request, timeout):
        calls.append({"url": request.full_url, "method": request.method, "payload": _payload(request), "timeout": timeout})
        return _FakeResponse({"message": {"content": "连接正常"}})

    client = OllamaLLM(host="http://ollama.local", model="qwen2.5:7b", opener=opener, timeout=3.0)

    result = client.generate("请测试", system_prompt="只回答测试", temperature=0.2, max_tokens=32)

    assert result.content == "连接正常"
    assert result.provider == "ollama"
    assert result.model == "qwen2.5:7b"
    assert calls == [
        {
            "url": "http://ollama.local/api/chat",
            "method": "POST",
            "payload": {
                "model": "qwen2.5:7b",
                "messages": [
                    {"role": "system", "content": "只回答测试"},
                    {"role": "user", "content": "请测试"},
                ],
                "stream": False,
                "options": {"temperature": 0.2, "num_predict": 32},
            },
            "timeout": 3.0,
        }
    ]


def test_ollama_llm_stream_yields_message_tokens():
    def opener(request, timeout):
        assert request.full_url == "http://ollama.local/api/chat"
        assert _payload(request)["stream"] is True
        return _FakeResponse(
            lines=[
                {"message": {"content": "连"}},
                {"message": {"content": "接"}},
                {"done": True},
            ]
        )

    client = OllamaLLM(host="http://ollama.local", model="qwen2.5:7b", opener=opener)

    assert list(client.stream("请测试")) == ["连", "接"]


def test_ollama_llm_availability_failure_warns_without_raising(capsys):
    def opener(request, timeout):
        raise URLError("connection refused")

    client = OllamaLLM(host="http://ollama.local", opener=opener)

    assert client.is_available() is False
    assert "WARNING: Ollama is not available at http://ollama.local" in capsys.readouterr().err


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


def test_app_data_dir_is_platform_aware():
    home = Path("/Users/tester")

    assert str(
        app_data_dir(
            system="Windows",
            environ={"APPDATA": r"C:\Users\tester\AppData\Roaming"},
            home=home,
        )
    ).endswith(r"C:\Users\tester\AppData\Roaming\KnowledgeIsland")
    assert app_data_dir(system="Windows", environ={}, home=home) == home / "AppData" / "Roaming" / "KnowledgeIsland"
    assert app_data_dir(system="Darwin", environ={}, home=home) == home / "Library" / "Application Support" / "KnowledgeIsland"
    assert app_data_dir(system="Linux", environ={"XDG_CONFIG_HOME": "/tmp/config"}, home=home) == Path(
        "/tmp/config"
    ) / "KnowledgeIsland"
    assert app_data_dir(system="Linux", environ={}, home=home) == home / ".config" / "KnowledgeIsland"
