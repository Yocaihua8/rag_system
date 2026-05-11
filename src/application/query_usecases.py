"""
QueryKnowledgeBaseUseCase — 检索 + LLM 问答。

流程：
  embed(question) → vector search → load chunks → build prompt → LLM generate → save history
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Iterator, List, Optional

from src.domain.models.chunk import Chunk
from src.domain.models.conversation import ConversationRecord
from src.ports.conversation_store import IConversationStore
from src.ports.llm_client import ILLMClient, LLMRequest
from src.ports.retriever import IRetriever, RetrievalQuery


SYSTEM_PROMPT = """你是一位专业的职业发展助手。
请基于用户提供的知识库内容，准确、简洁地回答问题。
如果知识库中没有相关信息，请明确说明，不要编造内容。
回答时请引用具体内容，保持专业性。"""


@dataclass(frozen=True)
class QueryRequest:
    workspace_id: str
    question: str
    domains: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    top_k: int = 8


@dataclass(frozen=True)
class QueryResponse:
    answer: str
    sources: List[Chunk]
    scores: List[float]
    model_used: str


class QueryKnowledgeBaseUseCase:

    def __init__(
        self,
        retriever: IRetriever,
        llm_client: ILLMClient,
        conversation_store: IConversationStore,
        model: str = "qwen2.5:7b",
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> None:
        self._retriever = retriever
        self._llm = llm_client
        self._conv_store = conversation_store
        self._model = model
        self._temperature = temperature
        self._max_tokens = max_tokens

    def execute(self, request: QueryRequest) -> QueryResponse:
        """阻塞调用，返回完整响应。在 Worker 线程中调用。"""
        retrieval = self._retriever.search(
            RetrievalQuery(
                question=request.question,
                workspace_id=request.workspace_id,
                domains=request.domains,
                tags=request.tags,
                top_k=request.top_k,
            )
        )

        prompt = self._build_prompt(request.question, retrieval.chunks)
        llm_req = LLMRequest(
            prompt=prompt,
            model=self._model,
            system_prompt=SYSTEM_PROMPT,
            temperature=self._temperature,
            max_tokens=self._max_tokens,
        )
        response = self._llm.generate(llm_req)

        self._conv_store.save(
            ConversationRecord.create(
                workspace_id=request.workspace_id,
                question=request.question,
                answer=response.content,
            )
        )

        return QueryResponse(
            answer=response.content,
            sources=retrieval.chunks,
            scores=retrieval.scores,
            model_used=response.model,
        )

    def execute_streaming(
        self,
        request: QueryRequest,
        on_token: Callable[[str], None],
    ) -> QueryResponse:
        """
        流式调用。每收到一个 token 片段，调用 on_token(token)。
        在 Worker 线程中调用；on_token 内部发 Qt Signal。
        """
        retrieval = self._retriever.search(
            RetrievalQuery(
                question=request.question,
                workspace_id=request.workspace_id,
                domains=request.domains,
                tags=request.tags,
                top_k=request.top_k,
            )
        )

        prompt = self._build_prompt(request.question, retrieval.chunks)
        llm_req = LLMRequest(
            prompt=prompt,
            model=self._model,
            system_prompt=SYSTEM_PROMPT,
            temperature=self._temperature,
            max_tokens=self._max_tokens,
        )

        full_answer_parts = []
        for token in self._llm.stream(llm_req):
            on_token(token)
            full_answer_parts.append(token)
        full_answer = "".join(full_answer_parts)

        self._conv_store.save(
            ConversationRecord.create(
                workspace_id=request.workspace_id,
                question=request.question,
                answer=full_answer,
            )
        )

        return QueryResponse(
            answer=full_answer,
            sources=retrieval.chunks,
            scores=retrieval.scores,
            model_used=self._model,
        )

    def get_history(
        self,
        workspace_id: str,
        limit: int = 20,
    ) -> List[ConversationRecord]:
        return self._conv_store.list_recent(workspace_id, limit)

    # ── 内部 ──────────────────────────────────────────────────────────────

    @staticmethod
    def _build_prompt(question: str, chunks: List[Chunk]) -> str:
        if not chunks:
            return f"知识库中暂无相关内容。\n\n问题：{question}"

        context_parts = []
        for i, chunk in enumerate(chunks, 1):
            tags_str = "、".join(chunk.tags) if chunk.tags else "—"
            context_parts.append(
                f"[来源 {i}] 领域：{chunk.domain} | 标签：{tags_str}\n{chunk.content}"
            )
        context = "\n\n---\n\n".join(context_parts)
        return f"参考资料：\n\n{context}\n\n问题：{question}"
