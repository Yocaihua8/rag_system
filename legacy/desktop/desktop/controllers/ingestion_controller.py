from __future__ import annotations

from typing import Optional

from PySide6.QtCore import QObject, Signal

from legacy.desktop.application.ingestion_usecases import IngestProgress, IngestWorkspaceUseCase
from legacy.desktop.desktop.workers.base_worker import WorkerResult
from legacy.desktop.desktop.workers.ingest_worker import IngestWorker


class IngestionController(QObject):
    ingest_started = Signal()
    ingest_progress = Signal(int, str)     # (percent, message)
    ingest_finished = Signal(object)       # IngestProgress
    ingest_failed = Signal(str)

    def __init__(self, use_case: IngestWorkspaceUseCase, parent=None) -> None:
        super().__init__(parent)
        self._use_case = use_case
        self._worker: Optional[IngestWorker] = None

    def start(self, workspace_id: str, force: bool = False) -> None:
        if self._worker and self._worker.isRunning():
            return  # 防止重复触发
        self._worker = IngestWorker(self._use_case, workspace_id, force)
        self._worker.progress_updated.connect(self.ingest_progress)
        self._worker.result_ready.connect(self._on_result)
        self._worker.finished.connect(self._worker.deleteLater)
        self.ingest_started.emit()
        self._worker.start()

    def _on_result(self, result: WorkerResult) -> None:
        if result.success:
            self.ingest_finished.emit(result.data)
        else:
            self.ingest_failed.emit(result.error or "未知错误")
