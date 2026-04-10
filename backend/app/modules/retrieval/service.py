from __future__ import annotations

from dataclasses import dataclass


@dataclass
class RetrievalAnswer:
    answer: str
    sources: list[str]


class RetrievalService:
    def ask(self, question: str, corpus: list[str]) -> RetrievalAnswer:
        if not question.strip():
            return RetrievalAnswer(answer="", sources=[])
        hits = [c for c in corpus if question.lower() in c.lower()]
        if not hits:
            return RetrievalAnswer(answer="未命中相关上下文，请先扩充工作区资料。", sources=[])
        return RetrievalAnswer(answer=hits[0][:300], sources=hits[:3])
