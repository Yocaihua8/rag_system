"""
openai_compat_adapter.py — OpenAI 兼容 API 适配器。

支持所有兼容 OpenAI Chat Completions 接口的提供商：
  - DeepSeek     https://api.deepseek.com/v1
  - OpenAI       https://api.openai.com/v1
  - 通义千问      https://dashscope.aliyuncs.com/compatible-mode/v1
  - Moonshot/Kimi https://api.moonshot.cn/v1
  - 本地 vLLM / LM Studio 等

API Key 读取优先级（由 load_settings() 保证）：
  OS 环境变量 RAG_LLM_API_KEY > appdata/.env > 项目 .env > 空串
"""
from __future__ import annotations

from typing import Iterator

from src.ports.llm_client import ILLMClient, LLMRequest, LLMResponse


class OpenAICompatAdapter(ILLMClient):
    """
    基于 openai SDK 的 OpenAI 兼容适配器。
    通过 base_url 参数支持任意兼容接口。
    """

    def __init__(
        self,
        api_key: str,
        base_url: str,
        model: str,
        timeout: float = 60.0,
    ) -> None:
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._model = model
        self._timeout = timeout
        self._client = None   # 延迟初始化，避免导入时报错

    def _get_client(self):
        """懒加载 openai 客户端，避免在 openai 未安装时崩溃。"""
        if self._client is None:
            try:
                from openai import OpenAI
            except ImportError as e:
                raise ImportError(
                    "使用云端 API 需要安装 openai 包：pip install openai"
                ) from e
            self._client = OpenAI(
                api_key=self._api_key,
                base_url=self._base_url,
                timeout=self._timeout,
            )
        return self._client

    # ── ILLMClient 实现 ──────────────────────────────────────────────────────

    def generate(self, request: LLMRequest) -> LLMResponse:
        client = self._get_client()
        messages = self._build_messages(request)
        response = client.chat.completions.create(
            model=self._model,
            messages=messages,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            stream=False,
        )
        content = response.choices[0].message.content or ""
        return LLMResponse(content=content, model=self._model)

    def stream(self, request: LLMRequest) -> Iterator[str]:
        client = self._get_client()
        messages = self._build_messages(request)
        stream = client.chat.completions.create(
            model=self._model,
            messages=messages,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            stream=True,
        )
        for chunk in stream:
            delta = chunk.choices[0].delta
            if delta and delta.content:
                yield delta.content

    def is_available(self) -> bool:
        """API Key 非空即视为可用（不发送实际请求，避免启动时延迟）。"""
        return bool(self._api_key and self._api_key.strip())

    def list_models(self) -> list[str]:
        return [self._model]

    # ── 内部辅助 ─────────────────────────────────────────────────────────────

    @staticmethod
    def _build_messages(request: LLMRequest) -> list[dict]:
        messages = []
        if request.system_prompt:
            messages.append({"role": "system", "content": request.system_prompt})
        messages.append({"role": "user", "content": request.prompt})
        return messages
