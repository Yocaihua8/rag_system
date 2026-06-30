from __future__ import annotations

import json
from urllib.error import URLError

from backend.providers.base import LLMMessage
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


class _RawResponse:
    def __init__(self, body: str, lines: list[str] | None = None) -> None:
        self._body = body
        self._lines = lines or []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False

    def read(self) -> bytes:
        return self._body.encode("utf-8")

    def __iter__(self):
        for line in self._lines:
            yield (line + "\n").encode("utf-8")


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


def test_ollama_llm_generate_includes_history_and_model_override():
    calls: list[dict] = []

    def opener(request, timeout):
        calls.append(_payload(request))
        return _FakeResponse({"message": {"content": "继续回答"}})

    client = OllamaLLM(host="http://ollama.local", model="default-model", opener=opener)

    result = client.generate(
        "继续",
        history=[
            LLMMessage(role="user", content="上一问"),
            LLMMessage(role="assistant", content="   "),
            LLMMessage(role="assistant", content="上一答"),
        ],
        model="override-model",
    )

    assert result.content == "继续回答"
    assert result.model == "override-model"
    assert calls[0]["model"] == "override-model"
    assert calls[0]["messages"] == [
        {"role": "user", "content": "上一问"},
        {"role": "assistant", "content": "上一答"},
        {"role": "user", "content": "继续"},
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


def test_ollama_llm_stream_ignores_invalid_json_and_empty_tokens():
    def opener(request, timeout):
        assert _payload(request)["stream"] is True
        return _RawResponse(
            "",
            lines=[
                "not-json",
                json.dumps({"message": {"content": ""}}),
                json.dumps({"message": {"content": "有效"}}),
                json.dumps({"done": True}),
                json.dumps({"message": {"content": "ignored-after-done"}}),
            ],
        )

    client = OllamaLLM(host="http://ollama.local", opener=opener)

    assert list(client.stream("请测试")) == ["有效"]


def test_ollama_llm_availability_failure_warns_without_raising(capsys):
    def opener(request, timeout):
        raise URLError("connection refused")

    client = OllamaLLM(host="http://ollama.local", opener=opener)

    assert client.is_available() is False
    assert "WARNING: Ollama is not available at http://ollama.local" in capsys.readouterr().err


def test_ollama_llm_list_models_reads_tags_and_hides_failures():
    tag_calls = 0

    def opener(request, timeout):
        nonlocal tag_calls
        tag_calls += 1
        assert request.full_url == "http://ollama.local/api/tags"
        assert request.method == "GET"
        return _FakeResponse({"models": [{"name": "qwen2.5:7b"}, {"name": ""}, {"other": "ignored"}]})

    client = OllamaLLM(host="http://ollama.local", opener=opener)

    assert client.list_models() == ["qwen2.5:7b"]
    assert tag_calls == 1

    failing = OllamaLLM(host="http://ollama.local", opener=lambda request, timeout: (_ for _ in ()).throw(URLError("down")))
    assert failing.list_models() == []


def test_ollama_llm_generate_reports_invalid_or_missing_response():
    invalid_json = OllamaLLM(host="http://ollama.local", opener=lambda request, timeout: _RawResponse("{"))
    missing_content = OllamaLLM(host="http://ollama.local", opener=lambda request, timeout: _FakeResponse({"message": {}}))

    try:
        invalid_json.generate("请测试")
    except RuntimeError as exc:
        assert str(exc) == "Ollama response is not valid JSON"
    else:
        raise AssertionError("invalid JSON should fail")

    try:
        missing_content.generate("请测试")
    except RuntimeError as exc:
        assert str(exc) == "Ollama response missing message.content"
    else:
        raise AssertionError("missing content should fail")


def test_ollama_llm_pull_model_streams_status_and_wraps_url_errors():
    def opener(request, timeout):
        assert request.full_url == "http://ollama.local/api/pull"
        assert _payload(request) == {"model": "qwen2.5:7b", "stream": True}
        return _RawResponse(
            "",
            lines=[
                json.dumps({"status": "pulling manifest"}),
                "not-json",
                json.dumps(["not-a-dict"]),
                json.dumps({"status": "success"}),
            ],
        )

    client = OllamaLLM(host="http://ollama.local", opener=opener)

    assert list(client.pull_model("qwen2.5:7b")) == [
        {"status": "pulling manifest"},
        {"status": "success"},
    ]

    failing = OllamaLLM(host="http://ollama.local", opener=lambda request, timeout: (_ for _ in ()).throw(URLError("down")))
    try:
        list(failing.pull_model("qwen2.5:7b"))
    except RuntimeError as exc:
        assert str(exc) == "down"
    else:
        raise AssertionError("pull URL error should be wrapped")
