from __future__ import annotations

from typing import Optional

from PySide6.QtCore import QObject, Signal

from src.application.knowledge_mastery_usecases import (
    AssessmentQuestion,
    AssessmentSession,
    KnowledgeMasteryUseCase,
    AssessmentQuestionResult,
)
from src.domain.errors import NotFoundError, ValidationError


class AssessmentController(QObject):
    """掌握评估页面轻量编排。"""

    session_started = Signal(object)          # AssessmentSession
    question_loaded = Signal(object, int, int)  # question, index, total
    question_evaluated = Signal(object)       # AssessmentQuestionResult
    assessment_finished = Signal(object, int, int, int, object)
    assessment_failed = Signal(str)

    def __init__(self, use_case: KnowledgeMasteryUseCase, parent=None) -> None:
        super().__init__(parent)
        self._use_case = use_case
        self._session: Optional[AssessmentSession] = None
        self._pending_results: list[AssessmentQuestionResult] = []
        self._question_to_point: dict[str, str] = {}

    def start(
        self,
        workspace_id: str,
        question_count: int = 5,
        *,
        prioritize_missed: bool = False,
        focus_knowledge_point_ids: tuple[str, ...] | None = None,
    ) -> None:
        self._start_internal(
            workspace_id=workspace_id,
            question_count=question_count,
            prioritize_missed=prioritize_missed,
            focus_knowledge_point_ids=focus_knowledge_point_ids,
        )

    def start_follow_up(self, workspace_id: str, question_id: str) -> None:
        question = self._question_to_point.get(question_id)
        if not question:
            self.assessment_failed.emit("未找到可复测题目，请重新开始评估后选择题目")
            return
        self._start_internal(
            workspace_id=workspace_id,
            question_count=1,
            focus_knowledge_point_ids=(question,),
        )

    def retry_missed_questions(self, workspace_id: str, question_count: int = 5) -> None:
        self._start_internal(
            workspace_id=workspace_id,
            question_count=question_count,
            prioritize_missed=True,
        )

    def _start_internal(
        self,
        workspace_id: str,
        question_count: int,
        prioritize_missed: bool = False,
        focus_knowledge_point_ids: tuple[str, ...] | None = None,
    ) -> None:
        try:
            session = self._use_case.create_assessment_session(
                workspace_id=workspace_id,
                question_count=question_count,
                prioritize_missed=prioritize_missed,
                focus_knowledge_point_ids=focus_knowledge_point_ids,
            )
            self._session = session
            self._pending_results = []
            self._question_to_point = {q.id: q.knowledge_point_id for q in session.questions}
            self.session_started.emit(session)

            if not session.questions:
                self.assessment_failed.emit("未生成题目，请检查项目知识点是否已提取")
                return

            self.question_loaded.emit(session.questions[0], 0, len(session.questions))
        except (ValidationError, NotFoundError) as exc:
            self.assessment_failed.emit(str(exc))
            self._session = None
            self._pending_results = []
        except Exception as exc:  # 防御性兜底，避免 UI 异常静默
            self.assessment_failed.emit(f"启动评估失败：{exc}")
            self._session = None
            self._pending_results = []

    def submit_answer(self, workspace_id: str, question_id: str, answer: str) -> None:
        if not self._session or self._session.workspace_id != workspace_id:
            self.assessment_failed.emit("请先重新开始本次评估")
            return

        question = next((q for q in self._session.questions if q.id == question_id), None)
        if question is None:
            self.assessment_failed.emit("题目不存在，请重新开始评估")
            return

        try:
            result = self._use_case.evaluate_answer(
                workspace_id=workspace_id,
                question=question,
                answer=answer,
            )
        except (ValidationError, NotFoundError) as exc:
            self.assessment_failed.emit(str(exc))
            return

        self._use_case.record_assessment_attempt(
            workspace_id=workspace_id,
            session=self._session,
            question_id=question_id,
            answer=answer,
            result=result,
        )
        self._pending_results.append(result)
        self.question_evaluated.emit(result)

        answered = len(self._pending_results)
        if answered >= len(self._session.questions):
            mastered = len([r for r in self._pending_results if r.status == "已掌握"])
            basic = len([r for r in self._pending_results if r.status == "基本理解"])
            needs_help = len(
                [r for r in self._pending_results if r.status == "需要补充"]
            )
            report = self._use_case.generate_ability_gap_report(
                session=self._session,
                results=self._pending_results,
            )
            self.assessment_finished.emit(self._pending_results, mastered, basic, needs_help, report)
            self._session = None
            return

        next_question = self._session.questions[answered]
        self.question_loaded.emit(next_question, answered, len(self._session.questions))
