from __future__ import annotations

from PySide6.QtCore import Signal

from src.application.query_usecases import QueryKnowledgeBaseUseCase, QueryRequest, QueryResponse
from src.desktop.workers.base_worker import BaseWorker


class QueryWorker(BaseWorker):
    """
    在独立线程中执行 RAG 问答，支持流式 token 输出。

    流式模式：每收到一个 LLM token，发出 token_received(str) 信号。
             UI 槽将 token 追加到答案文本框，形成打字机效果。
    result_ready 携带完整的 QueryResponse（含来源 chunks）。
    """

    # 流式 token 信号
    token_received = Signal(str)

    def __init__(
        self,
        use_case: QueryKnowledgeBaseUseCase,
        request: QueryRequest,
        streaming: bool = True,
    ) -> None:
        super().__init__()
        self._use_case = use_case
        self._request = request
        self._streaming = streaming

    def _execute(self) -> QueryResponse:
        if self._streaming:
            return self._use_case.execute_streaming(
                request=self._request,
                on_token=lambda t: self.token_received.emit(t),
            )
        return self._use_case.execute(self._request)
