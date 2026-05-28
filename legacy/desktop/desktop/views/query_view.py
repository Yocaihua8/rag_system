from __future__ import annotations

from typing import Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QLineEdit, QListWidget,
    QListWidgetItem, QPushButton, QSplitter,
    QStackedWidget, QTextEdit, QVBoxLayout, QWidget,
)

from legacy.desktop.application.query_usecases import QueryResponse
from legacy.desktop.desktop.style import (
    ACCENT, BTN_PRIMARY_BG, BTN_PRIMARY_HOVER, BTN_PRIMARY_PRESSED,
    TEXT_SECONDARY,
)
from legacy.desktop.domain.models.workspace import Workspace


class QueryView(QWidget):
    """RAG 问答面板：问题输入、流式答案显示、来源列表。

    三种显示状态：
      - empty     : 尚未选择任何项目空间（初始状态）
      - need_index: 已选项目空间但未建索引
      - ready     : 正常问答状态
    """

    query_submitted = Signal(str, str)    # (workspace_id, question)
    index_requested = Signal(str)         # workspace_id -> trigger indexing
    assessment_requested = Signal(str)    # workspace_id -> open assessment

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._workspace_id: str = ""
        self._build_ui()
        self._show_state("empty")

    # ── UI 构建 ───────────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 16)
        root.setSpacing(12)

        # 页面标题
        title = QLabel("项目问答")
        title.setProperty("title", "true")
        root.addWidget(title)

        # ── 状态层（用 QStackedWidget 切换空/未索引/就绪三种状态） ──
        self._state_stack = QStackedWidget()

        # 状态 0：没有项目空间
        self._state_stack.addWidget(self._make_empty_state())
        # 状态 1：有项目空间但未索引
        self._state_stack.addWidget(self._make_index_needed_state())
        # 状态 2：正常问答
        self._state_stack.addWidget(self._make_query_state())

        root.addWidget(self._state_stack, 1)

    def _make_empty_state(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setAlignment(Qt.AlignCenter)

        icon = QLabel("📂")
        icon.setStyleSheet("font-size: 48px;")
        icon.setAlignment(Qt.AlignCenter)
        lay.addWidget(icon)

        msg = QLabel("还没有项目空间\n\n在左侧点击 ＋ 创建项目空间，选择包含文档的目录\n创建后将自动建立索引，完成后即可提问")
        msg.setAlignment(Qt.AlignCenter)
        msg.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 14px; line-height: 1.6;")
        msg.setWordWrap(True)
        lay.addWidget(msg)

        return w

    def _make_index_needed_state(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setAlignment(Qt.AlignCenter)

        icon = QLabel("⚡")
        icon.setStyleSheet("font-size: 48px;")
        icon.setAlignment(Qt.AlignCenter)
        lay.addWidget(icon)

        self._index_needed_msg = QLabel("该项目空间尚未建立索引")
        self._index_needed_msg.setAlignment(Qt.AlignCenter)
        self._index_needed_msg.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 14px;")
        lay.addWidget(self._index_needed_msg)

        self._btn_start_index = QPushButton("▶  立即建立索引")
        self._btn_start_index.setFixedWidth(180)
        self._btn_start_index.setProperty("primary", "true")
        self._btn_start_index.style().unpolish(self._btn_start_index)
        self._btn_start_index.style().polish(self._btn_start_index)
        self._btn_start_index.clicked.connect(
            lambda: self.index_requested.emit(self._workspace_id)
        )
        lay.addSpacing(8)
        lay.addWidget(self._btn_start_index, alignment=Qt.AlignCenter)

        return w

    def _make_query_state(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(8)

        # 问题输入区
        input_row = QHBoxLayout()
        self._question_input = QLineEdit()
        self._question_input.setPlaceholderText("围绕当前项目提问，按 Enter 或点击发送...")
        self._question_input.returnPressed.connect(self._submit)
        self._btn_assessment = QPushButton("开始评估")
        self._btn_assessment.setToolTip("进入掌握评估，先自动生成题目再提交答案")
        self._btn_assessment.setEnabled(False)
        self._btn_assessment.clicked.connect(self._start_assessment)
        self._btn_send = QPushButton("发送")
        self._btn_send.clicked.connect(self._submit)
        input_row.addWidget(self._question_input)
        input_row.addWidget(self._btn_assessment)
        input_row.addWidget(self._btn_send)
        lay.addLayout(input_row)

        # 答案 + 来源 分栏
        splitter = QSplitter(Qt.Vertical)

        answer_widget = QWidget()
        answer_layout = QVBoxLayout(answer_widget)
        answer_layout.setContentsMargins(0, 0, 0, 0)
        answer_label = QLabel("答案")
        answer_label.setProperty("secondary", "true")
        answer_layout.addWidget(answer_label)
        self._answer_display = QTextEdit()
        self._answer_display.setReadOnly(True)
        self._answer_display.setPlaceholderText("答案将在此显示…")
        answer_layout.addWidget(self._answer_display)
        splitter.addWidget(answer_widget)

        sources_widget = QWidget()
        sources_layout = QVBoxLayout(sources_widget)
        sources_layout.setContentsMargins(0, 0, 0, 0)
        sources_label = QLabel("来源片段")
        sources_label.setProperty("secondary", "true")
        sources_layout.addWidget(sources_label)
        self._sources_list = QListWidget()
        sources_layout.addWidget(self._sources_list)
        splitter.addWidget(sources_widget)

        splitter.setSizes([360, 140])
        lay.addWidget(splitter, 1)

        return w

    # ── 状态切换 ─────────────────────────────────────────────────────────

    def _show_state(self, state: str) -> None:
        mapping = {"empty": 0, "need_index": 1, "ready": 2}
        self._state_stack.setCurrentIndex(mapping.get(state, 0))

    # ── 由 MainWindow / Controller 调用 ──────────────────────────────────

    def set_workspace(self, workspace: Optional[Workspace]) -> None:
        """切换项目空间，根据索引状态显示对应界面。"""
        if workspace is None:
            self._workspace_id = ""
            self._btn_assessment.setEnabled(False)
            self._show_state("empty")
            return

        self._workspace_id = workspace.id
        if workspace.last_index_status == "ok":
            self._btn_assessment.setEnabled(True)
            self._show_state("ready")
        else:
            self._btn_assessment.setEnabled(False)
            self._index_needed_msg.setText(
                f"项目空间「{workspace.name}」尚未建立索引"
            )
            self._show_state("need_index")

    def mark_indexed(self) -> None:
        """索引完成后由外部调用，切换到就绪状态。"""
        if self._workspace_id:
            self._btn_assessment.setEnabled(True)
            self._show_state("ready")

    # ── 问答事件（Controller 信号驱动） ──────────────────────────────────

    def on_query_started(self) -> None:
        self._answer_display.clear()
        self._sources_list.clear()
        self._btn_send.setEnabled(False)
        self._btn_assessment.setEnabled(False)
        self._question_input.setEnabled(False)

    def on_token_received(self, token: str) -> None:
        """流式追加 token 到答案框。"""
        cursor = self._answer_display.textCursor()
        cursor.movePosition(cursor.End)
        cursor.insertText(token)
        self._answer_display.setTextCursor(cursor)
        self._answer_display.ensureCursorVisible()

    def on_query_finished(self, response: QueryResponse) -> None:
        self._btn_send.setEnabled(True)
        self._btn_assessment.setEnabled(bool(self._workspace_id))
        self._question_input.setEnabled(True)
        self._question_input.clear()

        self._sources_list.clear()
        for i, (chunk, score) in enumerate(zip(response.sources, response.scores), 1):
            text = f"[{i}] {chunk.domain} | 相似度 {score:.2f} | {chunk.content[:80]}…"
            self._sources_list.addItem(QListWidgetItem(text))

    def on_query_failed(self, error: str) -> None:
        self._answer_display.setPlainText(f"❌ 错误：{error}")
        self._btn_send.setEnabled(True)
        self._btn_assessment.setEnabled(bool(self._workspace_id))
        self._question_input.setEnabled(True)

    def _submit(self) -> None:
        q = self._question_input.text().strip()
        if q and self._workspace_id:
            self.query_submitted.emit(self._workspace_id, q)

    def _start_assessment(self) -> None:
        if self._workspace_id:
            self.assessment_requested.emit(self._workspace_id)
