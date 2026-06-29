from __future__ import annotations

from typing import Optional

from PySide6.QtCore import QObject, Signal

from src.application.query_usecases import QueryKnowledgeBaseUseCase, QueryRequest, QueryResponse
from src.desktop.workers.base_worker import WorkerResult
from src.desktop.workers.query_worker import QueryWorker


class QueryController(QObject):
    query_started = Signal()
    token_received = Signal(str)           # 流式 token
    query_finished = Signal(object)        # QueryResponse
    query_failed = Signal(str)

    def __init__(self, use_case: QueryKnowledgeBaseUseCase, parent=None) -> None:
        super().__init__(parent)
        self._use_case = use_case
        self._worker: Optional[QueryWorker] = None

    def submit(
        self,
        workspace_id: str,
        question: str,
        domains: list = None,
        top_k: int = 8,
        streaming: bool = True,
    ) -> None:
        if self._worker and self._worker.isRunning():
            return
        request = QueryRequest(
            workspace_id=workspace_id,
            question=question,
            domains=domains or [],
            top_k=top_k,
        )
        self._worker = QueryWorker(self._use_case, request, streaming)
        self._worker.token_received.connect(self.token_received)
        self._worker.progress_updated.connect(lambda p, m: None)  # 查询无进度条
        self._worker.result_ready.connect(self._on_result)
        self._worker.finished.connect(self._worker.deleteLater)
        self.query_started.emit()
        self._worker.start()

    def _on_result(self, result: WorkerResult) -> None:
        if result.success:
            self.query_finished.emit(result.data)
        else:
            self.query_failed.emit(result.error or "未知错误")
