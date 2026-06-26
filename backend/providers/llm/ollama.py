from __future__ import annotations

import json
import sys
from collections.abc import Callable, Iterator, Sequence
from urllib.error import URLError
from urllib.request import Request, urlopen

from backend.providers.base import BaseLLM, LLMMessage, LLMResult

DEFAULT_OLLAMA_HOST = "http://localhost:11434"
DEFAULT_OLLAMA_MODEL = "qwen2.5:7b"


class OllamaLLM(BaseLLM):
    def __init__(
        self,
        host: str = DEFAULT_OLLAMA_HOST,
        model: str = DEFAULT_OLLAMA_MODEL,
        opener: Callable | None = None,
        timeout: float = 60.0,
    ) -> None:
        self._host = host.rstrip("/")
        self._model = model
        self._opener = opener or urlopen
        self._timeout = timeout

    @property
    def provider(self) -> str:
        return "ollama"

    @property
    def model(self) -> str:
        return self._model

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
        payload = self._chat_payload(
            prompt,
            system_prompt=system_prompt,
            history=history,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=False,
        )
        data = self._post_json("/api/chat", payload)
        try:
            content = data["message"]["content"]
        except (KeyError, TypeError) as exc:
            raise RuntimeError("Ollama response missing message.content") from exc
        return LLMResult(content=str(content or "").strip(), model=str(payload["model"]), provider=self.provider)

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
        payload = self._chat_payload(
            prompt,
            system_prompt=system_prompt,
            history=history,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True,
        )
        request = self._request("/api/chat", payload)
        with self._opener(request, timeout=self._timeout) as response:
            for raw_line in response:
                line = raw_line.decode("utf-8").strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if data.get("done"):
                    break
                token = data.get("message", {}).get("content", "")
                if token:
                    yield str(token)

    def is_available(self) -> bool:
        try:
            self._post_json("/api/tags", None, method="GET")
            return True
        except Exception as exc:
            print(f"WARNING: Ollama is not available at {self._host}: {exc}", file=sys.stderr)
            return False

    def list_models(self) -> list[str]:
        try:
            data = self._post_json("/api/tags", None, method="GET")
        except Exception:
            return []
        models = data.get("models", [])
        return [str(item.get("name", "")) for item in models if item.get("name")]

    def _chat_payload(
        self,
        prompt: str,
        *,
        system_prompt: str,
        history: Sequence[LLMMessage] | None,
        model: str | None,
        temperature: float,
        max_tokens: int,
        stream: bool,
    ) -> dict:
        messages: list[dict[str, str]] = []
        if system_prompt.strip():
            messages.append({"role": "system", "content": system_prompt.strip()})
        for item in history or []:
            if item.content.strip():
                messages.append({"role": item.role, "content": item.content})
        messages.append({"role": "user", "content": prompt})
        return {
            "model": model or self._model,
            "messages": messages,
            "stream": stream,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }

    def _post_json(self, path: str, payload: dict | None, method: str = "POST") -> dict:
        request = self._request(path, payload, method=method)
        try:
            with self._opener(request, timeout=self._timeout) as response:
                raw_body = response.read().decode("utf-8")
        except URLError as exc:
            raise RuntimeError(str(exc.reason)) from exc
        try:
            return json.loads(raw_body or "{}")
        except json.JSONDecodeError as exc:
            raise RuntimeError("Ollama response is not valid JSON") from exc

    def _request(self, path: str, payload: dict | None, method: str = "POST") -> Request:
        data = None
        headers = {"Content-Type": "application/json"}
        if payload is not None:
            data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        return Request(f"{self._host}{path}", data=data, headers=headers, method=method)


__all__ = ["DEFAULT_OLLAMA_HOST", "DEFAULT_OLLAMA_MODEL", "OllamaLLM"]
