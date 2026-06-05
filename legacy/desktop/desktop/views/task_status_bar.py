from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHBoxLayout, QLabel, QProgressBar, QStatusBar, QWidget


class TaskStatusBar(QStatusBar):
    """底部状态栏：显示当前任务进度和消息。"""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._label = QLabel("就绪")
        self._bar = QProgressBar()
        self._bar.setFixedWidth(200)
        self._bar.setRange(0, 100)
        self._bar.setVisible(False)

        self.addPermanentWidget(self._label)
        self.addPermanentWidget(self._bar)

    def show_progress(self, percent: int, message: str) -> None:
        self._label.setText(message)
        self._bar.setValue(percent)
        self._bar.setVisible(True)

    def show_message(self, message: str) -> None:
        self._label.setText(message)
        self._bar.setVisible(False)

    def reset(self) -> None:
        self._label.setText("就绪")
        self._bar.setValue(0)
        self._bar.setVisible(False)
