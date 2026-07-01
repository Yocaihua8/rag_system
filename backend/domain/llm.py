from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Callable, Iterator
from urllib.request import Request, urlopen

from backend.providers.llm.ollama import DEFAULT_OLLAMA_HOST, DEFAULT_OLLAMA_MODEL, OllamaLLM
from backend.config.settings import AppSettings, load_settings
from backend.domain.models import ChatMessage, PromptPreset, SearchHit


@dataclass(frozen=True)
class LlmConfig:
    provider: str
    api_base: str
    api_key: str
    model: str
    temperature: float
    max_tokens: int


class OpenAICompatibleChatClient:
    def __init__(
        self,
        config: LlmConfig,
        opener: Callable | None = None,
        timeout: float = 60.0,
    ) -> None:
        self._config = config
        self._opener = opener or urlopen
        self._timeout = timeout

    @property
    def provider(self) -> str:
        if "deepseek" in self._config.api_base.lower():
            return "deepseek"
        return self._config.provider or "api"

    def is_configured(self) -> bool:
        return (
            self._config.provider == "api"
            and bool(self._config.api_key.strip())
            and bool(self._config.api_base.strip())
            and bool(self._config.model.strip())
        )

    def generate_answer(
        self,
        question: str,
        hits: list[SearchHit],
        history_messages: list[ChatMessage] | None = None,
        prompt_preset: PromptPreset | None = None,
    ) -> str:
        if not self.is_configured():
            raise RuntimeError("LLM provider is not configured")

        payload = {
            "model": self._config.model,
            "messages": [
                {
                    "role": "system",
                    "content": _build_system_prompt(prompt_preset),
                },
                {
                    "role": "user",
                    "content": _build_user_prompt(question, hits, history_messages or [], prompt_preset),
                },
            ],
            "temperature": self._config.temperature,
            "max_tokens": self._config.max_tokens,
            "stream": False,
        }
        request = Request(
            _chat_completions_url(self._config.api_base),
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
            content = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise RuntimeError("LLM response missing choices[0].message.content") from exc
        return str(content or "").strip()

    def stream_answer(
        self,
        question: str,
        hits: list[SearchHit],
        history_messages: list[ChatMessage] | None = None,
        prompt_preset: PromptPreset | None = None,
    ) -> Iterator[str]:
        if not self.is_configured():
            raise RuntimeError("LLM provider is not configured")

        payload = {
            "model": self._config.model,
            "messages": [
                {
                    "role": "system",
                    "content": _build_system_prompt(prompt_preset),
                },
                {
                    "role": "user",
                    "content": _build_user_prompt(question, hits, history_messages or [], prompt_preset),
                },
            ],
            "temperature": self._config.temperature,
            "max_tokens": self._config.max_tokens,
            "stream": True,
        }
        request = Request(
            _chat_completions_url(self._config.api_base),
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self._config.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )

        with self._opener(request, timeout=self._timeout) as response:
            for raw_line in response:
                line = raw_line.decode("utf-8").strip()
                if not line.startswith("data:"):
                    continue
                payload_text = line.removeprefix("data:").strip()
                if payload_text == "[DONE]":
                    break
                try:
                    data = json.loads(payload_text)
                    content = data["choices"][0].get("delta", {}).get("content", "")
                except (json.JSONDecodeError, KeyError, IndexError, TypeError):
                    continue
                if content:
                    yield str(content)


class OllamaAnswerClient:
    def __init__(
        self,
        config: LlmConfig,
        client: OllamaLLM | None = None,
        timeout: float = 60.0,
    ) -> None:
        self._config = config
        self._client = client or OllamaLLM(
            host=config.api_base or DEFAULT_OLLAMA_HOST,
            model=config.model or DEFAULT_OLLAMA_MODEL,
            timeout=timeout,
        )

    @property
    def provider(self) -> str:
        return "ollama"

    def is_configured(self) -> bool:
        if self._config.provider != "ollama" or not (self._config.model or DEFAULT_OLLAMA_MODEL).strip():
            return False
        return self._client.is_available()

    def generate_answer(
        self,
        question: str,
        hits: list[SearchHit],
        history_messages: list[ChatMessage] | None = None,
        prompt_preset: PromptPreset | None = None,
    ) -> str:
        if not self.is_configured():
            raise RuntimeError("LLM provider is not configured")
        result = self._client.generate(
            _build_user_prompt(question, hits, history_messages or [], prompt_preset),
            system_prompt=_build_system_prompt(prompt_preset),
            model=self._config.model or DEFAULT_OLLAMA_MODEL,
            temperature=self._config.temperature,
            max_tokens=self._config.max_tokens,
        )
        return result.content

    def stream_answer(
        self,
        question: str,
        hits: list[SearchHit],
        history_messages: list[ChatMessage] | None = None,
        prompt_preset: PromptPreset | None = None,
    ) -> Iterator[str]:
        if not self.is_configured():
            raise RuntimeError("LLM provider is not configured")
        return self._client.stream(
            _build_user_prompt(question, hits, history_messages or [], prompt_preset),
            system_prompt=_build_system_prompt(prompt_preset),
            model=self._config.model or DEFAULT_OLLAMA_MODEL,
            temperature=self._config.temperature,
            max_tokens=self._config.max_tokens,
        )


def load_llm_config(settings: AppSettings | None = None) -> LlmConfig:
    current = settings or load_settings()
    if current.llm_provider == "ollama":
        return LlmConfig(
            provider=current.llm_provider,
            api_base=current.ollama_host,
            api_key="",
            model=current.ollama_model,
            temperature=current.llm_temperature,
            max_tokens=current.llm_max_tokens,
        )
    return LlmConfig(
        provider=current.llm_provider,
        api_base=current.llm_api_base,
        api_key=current.llm_api_key,
        model=current.llm_api_model,
        temperature=current.llm_temperature,
        max_tokens=current.llm_max_tokens,
    )


def build_llm_client(config: LlmConfig, timeout: float = 60.0) -> OpenAICompatibleChatClient | OllamaAnswerClient:
    if config.provider == "ollama":
        return OllamaAnswerClient(config, timeout=timeout)
    return OpenAICompatibleChatClient(config, timeout=timeout)


def get_default_llm_client() -> OpenAICompatibleChatClient | OllamaAnswerClient | None:
    client = build_llm_client(load_llm_config())
    return client if client.is_configured() else None


def _chat_completions_url(api_base: str) -> str:
    return f"{api_base.rstrip('/')}/chat/completions"


def _build_system_prompt(prompt_preset: PromptPreset | None = None) -> str:
    fixed_boundary = (
        "你是知识岛的本地项目资料助手。只基于用户提供的来源片段回答；"
        "如果来源不足，要明确说明缺口，不要编造。"
    )
    if not prompt_preset:
        return fixed_boundary
    return (
        fixed_boundary
        + "\n\n当前项目 Prompt 预设：\n"
        + prompt_preset.system_prompt.strip()
    )


def _build_user_prompt(
    question: str,
    hits: list[SearchHit],
    history_messages: list[ChatMessage] | None = None,
    prompt_preset: PromptPreset | None = None,
) -> str:
    history_messages = history_messages or []
    history_lines = []
    for message in history_messages[-3:]:
        history_lines.append(
            f"用户：{message.question.strip()}\n"
            f"助手：{message.answer.strip()[:500]}"
        )
    sources = []
    for index, hit in enumerate(hits[:5], start=1):
        sources.append(
            f"[{index}] {hit.document.relative_path}\n"
            f"{hit.snippet or hit.document.content[:500]}"
        )
    history_section = ""
    if history_lines:
        history_section = "最近对话：\n" + "\n\n".join(history_lines) + "\n\n"
    answer_format_section = ""
    if prompt_preset and prompt_preset.answer_format.strip():
        answer_format_section = f"\n\n回答格式要求：\n{prompt_preset.answer_format.strip()}"
    return (
        history_section
        + "当前问题：\n"
        f"{question.strip()}\n\n"
        "来源片段：\n"
        + "\n\n".join(sources)
        + answer_format_section
        + "\n\n请用中文回答，并在答案里点明依据来自哪些文件。"
    )
