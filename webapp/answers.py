from __future__ import annotations

from typing import Protocol

from webapp.llm import get_default_llm_client
from webapp.models import AnswerResult, ChatMessage, PromptPreset, SearchHit


class LlmAnswerClient(Protocol):
    provider: str

    def generate_answer(
        self,
        question: str,
        hits: list[SearchHit],
        history_messages: list[ChatMessage] | None = None,
        prompt_preset: PromptPreset | None = None,
    ) -> str:
        ...


def compose_answer(
    question: str,
    hits: list[SearchHit],
    llm_client: LlmAnswerClient | None = None,
    history_messages: list[ChatMessage] | None = None,
    prompt_preset: PromptPreset | None = None,
) -> AnswerResult:
    useful_hits = [hit for hit in hits if hit.score > 0]
    if not useful_hits:
        return AnswerResult(
            answer=f"没有找到与“{question}”直接相关的资料。请先导入项目文档，或换一个更具体的问题。",
            mode="local",
            tool_suggestion=_build_source_search_suggestion(question),
        )

    client = llm_client if llm_client is not None else get_default_llm_client()
    if client is not None:
        provider = getattr(client, "provider", "api")
        try:
            if prompt_preset is not None:
                answer = client.generate_answer(
                    question,
                    useful_hits[:5],
                    history_messages or [],
                    prompt_preset=prompt_preset,
                )
            else:
                answer = client.generate_answer(question, useful_hits[:5], history_messages or [])
            if answer.strip():
                return AnswerResult(answer=answer.strip(), mode="api", provider=provider)
        except Exception as exc:
            local_answer = _compose_local_answer(question, useful_hits)
            return AnswerResult(
                answer=local_answer,
                mode="fallback",
                provider=provider,
                warning=str(exc),
            )

    return AnswerResult(answer=_compose_local_answer(question, useful_hits), mode="local")


def _compose_local_answer(question: str, useful_hits: list[SearchHit]) -> str:
    snippets = [hit.snippet for hit in useful_hits[:3] if hit.snippet]
    if not snippets:
        return "找到了相关资料，但片段为空。请检查导入文件内容。"
    return "根据已导入资料：\n\n" + "\n\n".join(f"- {snippet}" for snippet in snippets)


def _build_source_search_suggestion(question: str) -> dict[str, object]:
    return {
        "tool": "search_sources",
        "arguments": {"query": question.strip()},
        "reason": "当前回答没有可用来源，可先用只读来源检索工具扩大召回。",
    }
