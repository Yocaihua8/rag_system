from __future__ import annotations

from typing import Optional

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QApplication, QHBoxLayout, QLabel, QLineEdit,
    QMessageBox, QPushButton, QTabWidget, QTextEdit,
    QVBoxLayout, QWidget,
)

from src.application.generation_usecases import GenerationResult


class GenerationView(QWidget):
    """生成面板：简历 / JD 匹配 / 面试脚本三标签页。"""

    resume_requested = Signal(str, list, str)       # (workspace_id, keywords, project_name)
    jd_match_requested = Signal(str, str, list)     # (workspace_id, job_name, keywords)
    interview_requested = Signal(str, list, str)    # (workspace_id, keywords, project_name)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._workspace_id: str = ""
        # P2: 追踪当前活跃的输出框，避免扫描三个框的脆弱逻辑
        self._active_output: Optional[QTextEdit] = None
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)

        title = QLabel("内容生成")
        title.setProperty("title", "true")
        layout.addWidget(title)

        tabs = QTabWidget()
        tabs.addTab(self._build_resume_tab(), "📄 简历生成")
        tabs.addTab(self._build_jd_tab(), "🎯 JD 匹配")
        tabs.addTab(self._build_interview_tab(), "🎤 面试脚本")
        layout.addWidget(tabs)

    # ── 简历 Tab ──────────────────────────────────────────────────────────

    def _build_resume_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)

        layout.addWidget(QLabel("项目名称："))
        self._resume_project = QLineEdit()
        self._resume_project.setPlaceholderText("例如：电商后台系统")
        layout.addWidget(self._resume_project)

        layout.addWidget(QLabel("目标关键词（逗号分隔）："))
        self._resume_keywords = QLineEdit()
        self._resume_keywords.setPlaceholderText("Python, 微服务, 性能优化")
        layout.addWidget(self._resume_keywords)

        self._btn_resume = QPushButton("▶ 生成简历子弹点")
        self._btn_resume.setEnabled(False)
        self._btn_resume.clicked.connect(self._on_resume_clicked)
        layout.addWidget(self._btn_resume)

        self._resume_output, copy_btn = self._make_output_area()
        layout.addWidget(self._resume_output)
        layout.addWidget(copy_btn)
        return w

    # ── JD Tab ────────────────────────────────────────────────────────────

    def _build_jd_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)

        layout.addWidget(QLabel("岗位名称："))
        self._jd_job_name = QLineEdit()
        self._jd_job_name.setPlaceholderText("例如：后端工程师")
        layout.addWidget(self._jd_job_name)

        layout.addWidget(QLabel("JD 关键词（逗号分隔）："))
        self._jd_keywords = QLineEdit()
        self._jd_keywords.setPlaceholderText("Python, Docker, FastAPI, 高并发")
        layout.addWidget(self._jd_keywords)

        self._btn_jd = QPushButton("▶ 分析匹配度")
        self._btn_jd.setEnabled(False)
        self._btn_jd.clicked.connect(self._on_jd_clicked)
        layout.addWidget(self._btn_jd)

        self._jd_output, copy_btn = self._make_output_area()
        layout.addWidget(self._jd_output)
        layout.addWidget(copy_btn)
        return w

    # ── 面试 Tab ──────────────────────────────────────────────────────────

    def _build_interview_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)

        layout.addWidget(QLabel("项目名称："))
        self._interview_project = QLineEdit()
        self._interview_project.setPlaceholderText("例如：电商后台系统")
        layout.addWidget(self._interview_project)

        layout.addWidget(QLabel("岗位关键词（逗号分隔）："))
        self._interview_keywords = QLineEdit()
        self._interview_keywords.setPlaceholderText("Python, 架构, 团队协作")
        layout.addWidget(self._interview_keywords)

        self._btn_interview = QPushButton("▶ 生成面试脚本")
        self._btn_interview.setEnabled(False)
        self._btn_interview.clicked.connect(self._on_interview_clicked)
        layout.addWidget(self._btn_interview)

        self._interview_output, copy_btn = self._make_output_area()
        layout.addWidget(self._interview_output)
        layout.addWidget(copy_btn)
        return w

    # ── 由 Controller 信号驱动 ────────────────────────────────────────────

    def set_workspace(self, workspace_id: str) -> None:
        self._workspace_id = workspace_id
        for btn in (self._btn_resume, self._btn_jd, self._btn_interview):
            btn.setEnabled(True)

    def on_started(self) -> None:
        for btn in (self._btn_resume, self._btn_jd, self._btn_interview):
            btn.setEnabled(False)

    def on_finished(self, result: GenerationResult) -> None:
        # P2: 直接写入追踪的活跃输出框，无需遍历三个框
        if self._active_output is not None:
            self._active_output.setPlainText(result.markdown)
            self._active_output = None
        for btn in (self._btn_resume, self._btn_jd, self._btn_interview):
            btn.setEnabled(True)

    def on_progress(self, percent: int, message: str) -> None:
        if self._active_output is not None:
            self._active_output.setPlainText(f"⏳ {message}")

    def on_failed(self, error: str) -> None:
        # P1: 将错误信息显示在活跃输出框中，而不是静默地只恢复按钮
        if self._active_output is not None:
            self._active_output.setPlainText(f"❌ 生成失败：{error}")
            self._active_output = None
        for btn in (self._btn_resume, self._btn_jd, self._btn_interview):
            btn.setEnabled(True)

    # ── 内部槽 ────────────────────────────────────────────────────────────

    def _on_resume_clicked(self) -> None:
        # P4: 校验必填项
        kws = [k.strip() for k in self._resume_keywords.text().split(",") if k.strip()]
        if not kws:
            QMessageBox.warning(self, "缺少关键词", "请输入至少一个目标关键词。")
            return
        if not self._resume_project.text().strip():
            QMessageBox.warning(self, "缺少项目名称", "请输入项目名称。")
            return
        self._active_output = self._resume_output          # P2: 记录活跃输出框
        self._resume_output.setPlainText("⏳ 生成中...")
        self.resume_requested.emit(self._workspace_id, kws, self._resume_project.text().strip())

    def _on_jd_clicked(self) -> None:
        # P4: 校验必填项
        kws = [k.strip() for k in self._jd_keywords.text().split(",") if k.strip()]
        if not kws:
            QMessageBox.warning(self, "缺少关键词", "请输入至少一个 JD 关键词。")
            return
        if not self._jd_job_name.text().strip():
            QMessageBox.warning(self, "缺少岗位名称", "请输入岗位名称。")
            return
        self._active_output = self._jd_output              # P2: 记录活跃输出框
        self._jd_output.setPlainText("⏳ 分析中...")
        self.jd_match_requested.emit(self._workspace_id, self._jd_job_name.text().strip(), kws)

    def _on_interview_clicked(self) -> None:
        # P4: 校验必填项
        kws = [k.strip() for k in self._interview_keywords.text().split(",") if k.strip()]
        if not kws:
            QMessageBox.warning(self, "缺少关键词", "请输入至少一个岗位关键词。")
            return
        if not self._interview_project.text().strip():
            QMessageBox.warning(self, "缺少项目名称", "请输入项目名称。")
            return
        self._active_output = self._interview_output       # P2: 记录活跃输出框
        self._interview_output.setPlainText("⏳ 生成中...")
        self.interview_requested.emit(
            self._workspace_id, kws, self._interview_project.text().strip()
        )

    @staticmethod
    def _make_output_area():
        output = QTextEdit()
        output.setReadOnly(True)
        output.setPlaceholderText("生成结果将在此显示…")
        copy_btn = QPushButton("📋 复制到剪贴板")
        copy_btn.clicked.connect(lambda: QApplication.clipboard().setText(output.toPlainText()))
        return output, copy_btn
