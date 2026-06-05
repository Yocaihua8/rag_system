from __future__ import annotations

from typing import Optional

from PySide6.QtCore import QObject, Signal

from legacy.desktop.application.generation_usecases import (
    GenerationResult,
    GenerateInterviewScriptUseCase,
    GenerateResumeUseCase,
    InterviewRequest,
    JDMatchRequest,
    MatchJDUseCase,
    ResumeRequest,
)
from legacy.desktop.desktop.workers.base_worker import WorkerResult
from legacy.desktop.desktop.workers.generate_worker import GenerateWorker


class GenerationController(QObject):
    generation_started = Signal()
    generation_progress = Signal(int, str)
    generation_finished = Signal(object)   # GenerationResult
    generation_failed = Signal(str)

    def __init__(
        self,
        resume_uc: GenerateResumeUseCase,
        jd_uc: MatchJDUseCase,
        interview_uc: GenerateInterviewScriptUseCase,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self._resume_uc = resume_uc
        self._jd_uc = jd_uc
        self._interview_uc = interview_uc
        self._worker: Optional[GenerateWorker] = None

    def _start(self, use_case, request) -> None:
        if self._worker and self._worker.isRunning():
            return
        self._worker = GenerateWorker(use_case, request)
        self._worker.progress_updated.connect(self.generation_progress)
        self._worker.result_ready.connect(self._on_result)
        self._worker.finished.connect(self._worker.deleteLater)
        self.generation_started.emit()
        self._worker.start()

    def generate_resume(self, workspace_id: str, keywords: list, project_name: str) -> None:
        self._start(self._resume_uc, ResumeRequest(workspace_id, keywords, project_name))

    def match_jd(self, workspace_id: str, job_name: str, keywords: list) -> None:
        self._start(self._jd_uc, JDMatchRequest(workspace_id, job_name, keywords))

    def generate_interview(self, workspace_id: str, keywords: list, project_name: str) -> None:
        self._start(self._interview_uc, InterviewRequest(workspace_id, keywords, project_name))

    def _on_result(self, result: WorkerResult) -> None:
        if result.success:
            self.generation_finished.emit(result.data)
        else:
            self.generation_failed.emit(result.error or "未知错误")
