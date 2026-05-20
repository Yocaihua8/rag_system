from __future__ import annotations

from typing import Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from src.desktop.style import TEXT_SECONDARY
from src.application.knowledge_mastery_usecases import (
    AbilityGapReport,
    AssessmentQuestion,
    AssessmentQuestionResult,
)


class AssessmentView(QWidget):
    """掌握评估主流程页面（最小闭环）。"""

    start_requested = Signal(str)  # workspace_id
    answer_submitted = Signal(str, str, str)  # workspace_id, question_id, answer
    follow_up_requested = Signal(str, str)  # workspace_id, question_id
    retry_missed_requested = Signal(str)  # workspace_id

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._workspace_id: str = ""
        self._question_total = 0
        self._current_question_id: Optional[str] = None
        self._follow_up_question_ids: tuple[str, ...] = ()
        self._build_ui()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 16)
        root.setSpacing(12)

        title = QLabel("掌握评估")
        title.setProperty("title", "true")
        root.addWidget(title)

        self._intro = QLabel("围绕当前项目已提炼知识点，自动生成评估题并给出理解反馈。")
        self._intro.setWordWrap(True)
        self._intro.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 13px;")
        root.addWidget(self._intro)

        self._btn_start = QPushButton("开始评估")
        self._btn_start.setProperty("primary", "true")
        self._btn_start.setEnabled(False)
        self._btn_start.clicked.connect(self._on_start)
        root.addWidget(self._btn_start, alignment=Qt.AlignLeft)

        self._progress = QLabel("未开始")
        self._progress.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 12px;")
        root.addWidget(self._progress)

        self._question_prompt = QLabel("题目待生成")
        self._question_prompt.setWordWrap(True)
        self._question_prompt.setProperty("secondary", "true")
        self._question_prompt.setStyleSheet("font-weight: 600;")
        root.addWidget(self._question_prompt)

        self._source_hint = QLabel("")
        self._source_hint.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 12px;")
        self._source_hint.setWordWrap(True)
        root.addWidget(self._source_hint)

        self._answer_input = QTextEdit()
        self._answer_input.setPlaceholderText("在这里回答问题，提交后生成反馈…")
        self._answer_input.setFixedHeight(120)
        root.addWidget(self._answer_input)

        submit_row = QHBoxLayout()
        submit_row.addStretch(1)
        self._btn_submit = QPushButton("提交")
        self._btn_submit.setEnabled(False)
        self._btn_submit.clicked.connect(self._on_submit)
        submit_row.addWidget(self._btn_submit)
        self._btn_follow_up = QPushButton("继续追问")
        self._btn_follow_up.setEnabled(False)
        self._btn_follow_up.clicked.connect(self._on_follow_up)
        submit_row.addWidget(self._btn_follow_up)
        self._btn_retry_missed = QPushButton("错题复测")
        self._btn_retry_missed.setEnabled(False)
        self._btn_retry_missed.clicked.connect(self._on_retry_missed)
        submit_row.addWidget(self._btn_retry_missed)
        root.addLayout(submit_row)

        self._result_output = QTextEdit()
        self._result_output.setReadOnly(True)
        self._result_output.setPlaceholderText("评估反馈将在这里显示…")
        root.addWidget(self._result_output, 1)

    def set_workspace(self, workspace_id: str | None) -> None:
        self._workspace_id = workspace_id or ""
        self._btn_start.setEnabled(bool(workspace_id))
        self._btn_submit.setEnabled(False)
        self._answer_input.clear()
        self._progress.setText("未开始" if workspace_id else "请先选择项目空间")

    def set_session(self, question_total: int) -> None:
        self._question_total = question_total
        self._result_output.clear()
        self._follow_up_question_ids = ()
        self._btn_follow_up.setEnabled(False)
        self._btn_retry_missed.setEnabled(False)
        self._progress.setText(f"共 {question_total} 题")

    # ── controller callbacks ────────────────────────────────────────────────

    def show_question(self, question: AssessmentQuestion, index: int, total: int) -> None:
        self._question_total = total
        self._current_question_id = question.id
        self._question_prompt.setText(f"第 {index + 1} 题：{question.prompt}")
        self._source_hint.setText(f"来源：{question.source_path}")
        self._progress.setText(f"进度：{index + 1}/{total}")
        self._btn_submit.setEnabled(True)
        self._answer_input.setEnabled(True)
        self._answer_input.clear()
        self._answer_input.setFocus()

    def show_question_feedback(self, result: AssessmentQuestionResult) -> None:
        self._result_output.append(
            f"问题结果：{result.status}（匹配得分：{result.score:.0%}）"
        )
        self._result_output.append(f"  - 命中：{_join_or_na(result.matched_points)}")
        self._result_output.append(f"  - 遗漏：{_join_or_na(result.missing_points)}")
        self._result_output.append(f"  - 反馈：{result.feedback}")
        self._result_output.append("")

    def show_summary(
        self,
        mastered: int,
        basic: int,
        needs_help: int,
        total: int,
    ) -> None:
        self._btn_submit.setEnabled(False)
        self._answer_input.setEnabled(False)
        self._progress.setText("评估完成")
        self._result_output.append("====== 评估汇总 ======")
        self._result_output.append(f"已掌握：{mastered}，基本理解：{basic}，需要补充：{needs_help}（共 {total} 题）")
        self._result_output.append("可继续围绕遗漏点回看对应来源文件。")
        self._btn_start.setText("重新开始")
        self._btn_start.setEnabled(True)

    def show_gap_report(self, report: AbilityGapReport) -> None:
        self._result_output.append("====== 能力差距报告 ======")
        self._result_output.append(report.overview)
        self._result_output.append(f"已掌握知识点：{_join_or_na(report.mastered_knowledge_points)}")
        self._result_output.append(f"薄弱知识点：{_join_or_na(report.weak_knowledge_points)}")
        self._result_output.append(
            f"建议阅读文件：{_join_or_na(report.suggested_reading_files)}"
        )
        self._result_output.append(
            f"建议追问：{_join_or_na(report.suggested_follow_up_questions)}"
        )
        self._result_output.append(f"下一步学习顺序：{_join_or_na(report.next_learning_order)}")
        self._follow_up_question_ids = report.follow_up_question_ids
        has_follow_up = bool(self._follow_up_question_ids)
        self._btn_follow_up.setEnabled(has_follow_up and bool(self._workspace_id))
        self._btn_retry_missed.setEnabled(has_follow_up and bool(self._workspace_id))

    def show_error(self, message: str) -> None:
        self._progress.setText("评估异常")
        self._result_output.append(f"⚠️ {message}")
        self._btn_submit.setEnabled(False)

    def reset(self) -> None:
        self._progress.setText("未开始")
        self._btn_start.setText("开始评估")
        self._btn_start.setEnabled(bool(self._workspace_id))
        self._btn_submit.setEnabled(False)
        self._answer_input.clear()
        self._answer_input.setEnabled(True)
        self._question_prompt.setText("题目待生成")
        self._source_hint.setText("")
        self._result_output.clear()
        self._follow_up_question_ids = ()
        self._btn_follow_up.setEnabled(False)
        self._btn_retry_missed.setEnabled(False)

    # ── event handlers ──────────────────────────────────────────────────

    def _on_start(self) -> None:
        if not self._workspace_id:
            return
        self._btn_start.setEnabled(False)
        self._btn_submit.setEnabled(False)
        self._answer_input.setReadOnly(False)
        self._answer_input.setEnabled(True)
        self.start_requested.emit(self._workspace_id)

    def _on_submit(self) -> None:
        if not self._current_question_id or not self._workspace_id:
            return

        answer = self._answer_input.toPlainText().strip()
        if not answer:
            return

        self._btn_submit.setEnabled(False)
        self.answer_submitted.emit(self._workspace_id, self._current_question_id, answer)

    def _on_follow_up(self) -> None:
        if not self._follow_up_question_ids or not self._workspace_id:
            return
        self.follow_up_requested.emit(self._workspace_id, self._follow_up_question_ids[0])
        self._btn_follow_up.setEnabled(False)

    def _on_retry_missed(self) -> None:
        if not self._workspace_id:
            return
        self.retry_missed_requested.emit(self._workspace_id)
        self._btn_retry_missed.setEnabled(False)


def _join_or_na(values: tuple[str, ...]) -> str:
    return "、".join(values) if values else "无"
