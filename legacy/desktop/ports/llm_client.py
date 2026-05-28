from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Iterator, List, Optional


@dataclass(frozen=True)
class LLMRequest:
    prompt: str
    model: str
    system_prompt: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 2048


@dataclass(frozen=True)
class LLMResponse:
    content: str
    model: str


class ILLMClient(ABC):
    """LLM 推理接口。实现屏蔽底层服务差异（Ollama / OpenAI / 本地模型）。"""

    @abstractmethod
    def generate(self, request: LLMRequest) -> LLMResponse:
        """阻塞式调用，返回完整响应。在 Worker 线程中调用。"""
        ...

    @abstractmethod
    def stream(self, request: LLMRequest) -> Iterator[str]:
        """
        流式调用，逐 token yield 内容片段。
        Worker 线程迭代并通过 Signal 推送到 UI。
        """
        ...

    @abstractmethod
    def is_available(self) -> bool:
        """检测 LLM 后端是否可达（用于启动检查和降级判断）。"""
        ...

    @abstractmethod
    def list_models(self) -> List[str]:
        """返回当前后端已拉取的模型名列表。"""
        ...
