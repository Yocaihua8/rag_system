from __future__ import annotations

from typing import Union

from src.application.generation_usecases import (
    GenerationResult,
    GenerateInterviewScriptUseCase,
    GenerateResumeUseCase,
    InterviewRequest,
    JDMatchRequest,
    MatchJDUseCase,
    ResumeRequest,
)
from src.desktop.workers.base_worker import BaseWorker

# 所有生成用例的联合类型
_AnyUseCase = Union[GenerateResumeUseCase, MatchJDUseCase, GenerateInterviewScriptUseCase]
_AnyRequest = Union[ResumeRequest, JDMatchRequest, InterviewRequest]


class GenerateWorker(BaseWorker):
    """
    在独立线程中执行生成类用例（简历 / JD 匹配 / 面试脚本）。
    progress_updated 发送 50% 的单次脉冲（生成前后各一次）。
    result_ready 携带 GenerationResult。
    """

    def __init__(self, use_case: _AnyUseCase, request: _AnyRequest) -> None:
        super().__init__()
        self._use_case = use_case
        self._request = request

    def _execute(self) -> GenerationResult:
        self.progress_updated.emit(10, "检索相关内容中...")
        result = self._use_case.execute(self._request)
        self.progress_updated.emit(100, "生成完成")
        return result
