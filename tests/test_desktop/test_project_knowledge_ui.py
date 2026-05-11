from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QLabel, QLineEdit, QPushButton

from src.desktop.views.assessment_view import AssessmentView
from src.desktop.views.guide_view import GuideView
from src.desktop.views.main_window import MainWindow
from src.desktop.views.query_view import QueryView
from src.domain.models.workspace import Workspace


def _app() -> QApplication:
    return QApplication.instance() or QApplication([])


def _label_texts(widget) -> list[str]:
    return [label.text() for label in widget.findChildren(QLabel)]


def _button_texts(widget) -> list[str]:
    return [button.text() for button in widget.findChildren(QPushButton)]


def _input_placeholders(widget) -> list[str]:
    return [line_edit.placeholderText() for line_edit in widget.findChildren(QLineEdit)]


def _button_by_text(widget, text: str) -> QPushButton:
    for button in widget.findChildren(QPushButton):
        if button.text() == text:
            return button
    raise AssertionError(f"button not found: {text}")


def test_query_view_uses_project_qa_language():
    _app()
    view = QueryView()

    labels = "\n".join(_label_texts(view))
    buttons = "\n".join(_button_texts(view))
    placeholders = "\n".join(_input_placeholders(view))

    assert "项目问答" in labels
    assert "开始评估" in buttons
    assert "围绕当前项目提问，按 Enter 或点击发送..." in placeholders
    assert "知识库问答" not in labels


def test_query_view_assessment_requires_workspace():
    _app()
    view = QueryView()
    emitted: list[str] = []
    view.assessment_requested.connect(emitted.append)

    assessment_button = _button_by_text(view, "开始评估")
    assert not assessment_button.isEnabled()

    view._start_assessment()
    assert emitted == []

    view.set_workspace(
        Workspace(
            id="workspace-1",
            name="项目",
            root_path=".",
            created_at="2026-05-11T00:00:00+00:00",
            last_indexed_at="2026-05-11T00:00:00+00:00",
            last_index_status="ok",
            total_files=1,
            supported_files=1,
        )
    )
    assert assessment_button.isEnabled()

    assessment_button.click()
    assert emitted == ["workspace-1"]

    view.set_workspace(None)
    assert not assessment_button.isEnabled()


def test_guide_view_uses_three_project_steps():
    _app()
    view = GuideView()
    labels = "\n".join(_label_texts(view))

    assert "欢迎使用项目知识库" in labels
    assert "导入项目" in labels
    assert "建立索引" in labels
    assert "开始使用" in labels
    assert "简历" not in labels


def test_assessment_view_placeholder_language():
    _app()
    view = AssessmentView()
    labels = "\n".join(_label_texts(view))

    assert "掌握评估" in labels
    assert "后续接入自动出题后，系统会围绕当前项目生成问题" in labels
    assert "第二大脑" not in labels


def test_main_window_uses_project_knowledge_navigation(container):
    _app()
    (container.settings.runtime_dir / ".guide_shown").parent.mkdir(parents=True, exist_ok=True)
    (container.settings.runtime_dir / ".guide_shown").touch()

    window = MainWindow(container)
    try:
        nav_buttons = [
            button.text().strip()
            for button in window._nav_buttons
            if button.property("nav") == "true"
        ]

        assert window.windowTitle() == "项目知识库助手"
        assert nav_buttons == [
            "🔍  项目问答",
            "📁  我的项目",
            "📚  知识库",
            "✓  掌握评估",
            "⚙️  设置",
        ]
        assert window._stack.count() == 5
        assert isinstance(window._assessment_view, AssessmentView)

        window._open_assessment("workspace-1")
        assert window._stack.currentIndex() == 3
        assert window._assessment_view._workspace_id == "workspace-1"
    finally:
        window.close()
