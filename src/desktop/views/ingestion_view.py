from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QHBoxLayout, QLabel, QProgressBar,
    QPushButton, QTextEdit, QVBoxLayout, QWidget,
)

from src.application.ingestion_usecases import IngestProgress


class IngestionView(QWidget):
    """知识库摄入面板：触发索引、显示进度日志。"""

    ingest_requested = Signal(str, bool)  # (workspace_id, force_reindex)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._workspace_id: str = ""
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)

        title = QLabel("知识库索引")
        title.setProperty("title", "true")
        layout.addWidget(title)

        self._info_label = QLabel("请先在左侧选择工作区")
        self._info_label.setProperty("secondary", "true")
        layout.addWidget(self._info_label)

        btn_row = QHBoxLayout()
        self._btn_ingest = QPushButton("▶ 开始索引")
        self._btn_reindex = QPushButton("↺ 重建索引")
        self._btn_ingest.setEnabled(False)
        self._btn_reindex.setEnabled(False)
        self._btn_ingest.clicked.connect(lambda: self.ingest_requested.emit(self._workspace_id, False))
        self._btn_reindex.clicked.connect(lambda: self.ingest_requested.emit(self._workspace_id, True))
        btn_row.addWidget(self._btn_ingest)
        btn_row.addWidget(self._btn_reindex)
        btn_row.addStretch()
        layout.addLayout(btn_row)

        self._progress = QProgressBar()
        self._progress.setVisible(False)
        layout.addWidget(self._progress)

        layout.addWidget(QLabel("处理日志："))
        self._log = QTextEdit()
        self._log.setReadOnly(True)
        self._log.setFont(self._log.font())
        layout.addWidget(self._log)

    # ── 由 Controller 信号驱动 ────────────────────────────────────────────

    def set_workspace(self, workspace_id: str, name: str) -> None:
        self._workspace_id = workspace_id
        self._info_label.setText(f"当前工作区：{name}")
        self._btn_ingest.setEnabled(True)
        self._btn_reindex.setEnabled(True)
        self._log.clear()

    def on_started(self) -> None:
        self._progress.setValue(0)
        self._progress.setVisible(True)
        self._btn_ingest.setEnabled(False)
        self._btn_reindex.setEnabled(False)
        self._log.clear()
        self._log.append("开始摄入...")

    def on_progress(self, percent: int, message: str) -> None:
        self._progress.setValue(percent)
        self._log.append(message)

    def on_finished(self, result: IngestProgress) -> None:
        self._progress.setValue(100)
        self._log.append(f"\n✅ {result.message}")
        self._btn_ingest.setEnabled(True)
        self._btn_reindex.setEnabled(True)

    def on_failed(self, error: str) -> None:
        self._progress.setVisible(False)
        self._log.append(f"\n❌ 错误：{error}")
        self._btn_ingest.setEnabled(True)
        self._btn_reindex.setEnabled(True)
