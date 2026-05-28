from __future__ import annotations

from PySide6.QtCore import Signal

from legacy.desktop.application.ingestion_usecases import IngestProgress, IngestWorkspaceUseCase
from legacy.desktop.desktop.workers.base_worker import BaseWorker


class IngestWorker(BaseWorker):
    """
    在独立线程中执行知识库摄入。
    progress_updated 信号实时反映每个文件的处理进度 (percent, message)。
    progress_detailed 信号携带完整 IngestProgress（含 stage / elapsed_ms）。
    result_ready 携带最后一个 IngestProgress（包含完成统计）。
    """

    # 详细进度信号：(percent, message, stage, elapsed_ms)
    progress_detailed = Signal(int, str, str, int)

    def __init__(
        self,
        use_case: IngestWorkspaceUseCase,
        workspace_id: str,
        force_reindex: bool = False,
    ) -> None:
        super().__init__()
        self._use_case = use_case
        self._workspace_id = workspace_id
        self._force_reindex = force_reindex

    def _execute(self) -> IngestProgress:
        last: IngestProgress = None
        for progress in self._use_case.execute(self._workspace_id, self._force_reindex):
            self.progress_updated.emit(progress.percent, progress.message)
            self.progress_detailed.emit(
                progress.percent, progress.message,
                progress.stage, progress.elapsed_ms,
            )
            last = progress
            if progress.error:
                raise RuntimeError(progress.error)
        return last
