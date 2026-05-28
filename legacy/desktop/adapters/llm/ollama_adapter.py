"""
OllamaAdapter — ILLMClient 的 Ollama 实现。

依赖：ollama>=0.3.0（pip install ollama）
Ollama 服务必须在本地运行（默认 http://localhost:11434）。
"""
from __future__ import annotations

from typing import Iterator, List

import ollama

from legacy.desktop.ports.llm_client import ILLMClient, LLMRequest, LLMResponse


class OllamaAdapter(ILLMClient):

    def __init__(self, host: str = "http://localhost:11434") -> None:
        self._client = ollama.Client(host=host)
        self._host = host

    # ------------------------------------------------------------------ #
    # ILLMClient 实现
    # ------------------------------------------------------------------ #

    def generate(self, request: LLMRequest) -> LLMResponse:
        """阻塞调用，返回完整响应。须在 Worker 线程中调用，禁止在主线程使用。"""
        messages = self._build_messages(request)
        response = self._client.chat(
            model=request.model,
            messages=messages,
            options={
                "temperature": request.temperature,
                "num_predict": request.max_tokens,
            },
        )
        content = response["message"]["content"]
        return LLMResponse(content=content, model=request.model)

    def stream(self, request: LLMRequest) -> Iterator[str]:
        """
        流式调用，逐 token yield 内容片段。
        调用方（QueryWorker）负责在每次 yield 后发 Qt Signal。
        """
        messages = self._build_messages(request)
        stream = self._client.chat(
            model=request.model,
            messages=messages,
            stream=True,
            options={
                "temperature": request.temperature,
                "num_predict": request.max_tokens,
            },
        )
        for chunk in stream:
            token = chunk.get("message", {}).get("content", "")
            if token:
                yield token

    def is_available(self) -> bool:
        """检测 Ollama 是否可达，用于启动检查和降级判断。"""
        try:
            self._client.list()
            return True
        except Exception:
            return False

    def list_models(self) -> List[str]:
        """返回当前已拉取的模型名列表。"""
        try:
            result = self._client.list()
            return [m["name"] for m in result.get("models", [])]
        except Exception:
            return []

    # ------------------------------------------------------------------ #
    # 内部辅助
    # ------------------------------------------------------------------ #

    @staticmethod
    def _build_messages(request: LLMRequest) -> list:
        messages = []
        if request.system_prompt:
            messages.append({"role": "system", "content": request.system_prompt})
        messages.append({"role": "user", "content": request.prompt})
        return messages
