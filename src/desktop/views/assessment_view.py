from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QLabel, QPushButton, QVBoxLayout, QWidget

from src.desktop.style import ACCENT, TEXT_SECONDARY


class AssessmentView(QWidget):
    """掌握评估页面占位。

    第一阶段只提供稳定页面骨架和文案。后续计划接入自动出题、
    回答评估和能力差距报告。
    """

    start_requested = Signal(str)  # workspace_id

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._workspace_id: str = ""
        self._build_ui()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 16)
        root.setSpacing(12)

        title = QLabel("掌握评估")
        title.setProperty("title", "true")
        root.addWidget(title)

        body = QWidget()
        body_layout = QVBoxLayout(body)
        body_layout.setAlignment(Qt.AlignCenter)
        body_layout.setSpacing(10)

        icon = QLabel("✓")
        icon.setAlignment(Qt.AlignCenter)
        icon.setStyleSheet(f"font-size: 42px; color: {ACCENT};")
        body_layout.addWidget(icon)

        headline = QLabel("掌握评估入口已就绪")
        headline.setAlignment(Qt.AlignCenter)
        headline.setStyleSheet("font-size: 16px; font-weight: 600;")
        body_layout.addWidget(headline)

        description = QLabel(
            "后续接入自动出题后，系统会围绕当前项目生成问题，并根据你的回答给出"
            "掌握情况、漏掉的关键点和建议阅读文件。"
        )
        description.setAlignment(Qt.AlignCenter)
        description.setWordWrap(True)
        description.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 13px;")
        body_layout.addWidget(description)

        self._btn_start = QPushButton("开始评估")
        self._btn_start.setProperty("primary", "true")
        self._btn_start.setEnabled(False)
        self._btn_start.clicked.connect(self._emit_start)
        body_layout.addWidget(self._btn_start, alignment=Qt.AlignCenter)

        root.addWidget(body, 1)

    def set_workspace(self, workspace_id: str) -> None:
        self._workspace_id = workspace_id
        self._btn_start.setEnabled(bool(workspace_id))

    def _emit_start(self) -> None:
        if self._workspace_id:
            self.start_requested.emit(self._workspace_id)
