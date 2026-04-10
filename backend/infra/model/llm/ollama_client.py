from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import ollama


@dataclass
class OllamaResult:
    content: str
    model: str


class OllamaClient:
    def __init__(self, host: Optional[str] = None) -> None:
        self._host = host

    def generate(self, model: str, prompt: str) -> OllamaResult:
        kwargs = {"model": model, "prompt": prompt}
        if self._host:
            kwargs["host"] = self._host
        resp = ollama.generate(**kwargs)
        content = resp.get("response", "") if isinstance(resp, dict) else ""
        return OllamaResult(content=content, model=model)

