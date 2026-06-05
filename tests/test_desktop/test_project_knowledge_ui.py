from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QLabel, QLineEdit, QPushButton

from legacy.desktop.desktop.views.assessment_view import AssessmentView
from legacy.desktop.desktop.views.guide_view import GuideView
from legacy.desktop.desktop.views.ingestion_view import IngestionView
from legacy.desktop.desktop.views.main_window import MainWindow
from legacy.desktop.desktop.views.query_view import QueryView
from legacy.desktop.desktop.views.workspace_view import WorkspaceView, _CreateWorkspaceDialog
from legacy.desktop.application.knowledge_mastery_usecases import AbilityGapReport
from legacy.desktop.domain.models.workspace import Workspace


def _app() -> QApplication:
    return QApplication.instance() or QApplication([])


def _label_texts(widget) -> list[str]:
    return [label.text() for label in widget.findChildren(QLabel)]


def _button_texts(widget) -> list[str]:
    return [button.text() for button in widget.findChildren(QPushButton)]


def _input_placeholders(widget) -> list[str]:
    return [line_edit.placeholderText() for line_edit in widget.findChildren(QLineEdit)]


def _button_tooltips(widget) -> list[str]:
    return [button.toolTip() for button in widget.findChildren(QPushButton)]


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


def test_user_visible_workspace_language_moves_to_project_space():
    _app()
    widgets = [
        QueryView(),
        WorkspaceView(),
        IngestionView(),
        _CreateWorkspaceDialog(),
    ]
    try:
        visible_text = "\n".join(
            text
            for widget in widgets
            for text in (
                _label_texts(widget)
                + _button_texts(widget)
                + _button_tooltips(widget)
                + _input_placeholders(widget)
                + [widget.windowTitle()]
            )
            if text
        )

        assert "项目空间" in visible_text
        assert "工作区" not in visible_text
    finally:
        for widget in widgets:
            widget.close()


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


def test_assessment_view_assessment_flow_language():
    _app()
    view = AssessmentView()
    labels = "\n".join(_label_texts(view))

    assert "掌握评估" in labels
    assert "围绕当前项目已提炼知识点，自动生成评估题" in labels
    assert "第 1 题" not in labels
    assert "第二大脑" not in labels


def test_assessment_view_gap_report_render():
    _app()
    view = AssessmentView()

    view.show_gap_report(
        AbilityGapReport(
            workspace_id="ws",
            total_questions=2,
            mastered_count=1,
            basic_count=0,
            needs_improvement_count=1,
            mastered_knowledge_points=("FastAPI 路由",),
            weak_knowledge_points=("数据库流程",),
            suggested_reading_files=("/tmp/main.py",),
            suggested_follow_up_questions=("补充数据库流程中的校验与持久化",),
            next_learning_order=("数据库流程",),
            overview="共 2 题，1 项已掌握，0 项基本理解，1 项建议补充。",
        )
    )

    content = view._result_output.toPlainText()
    assert "能力差距报告" in content
    assert "数据库流程" in content
    assert "/tmp/main.py" in content


def test_assessment_view_follow_up_controls():
    _app()
    view = AssessmentView()
    calls: list[tuple[str, str]] = []
    retry_calls: list[str] = []
    view.follow_up_requested.connect(lambda ws, q: calls.append((ws, q)))
    view.retry_missed_requested.connect(lambda ws: retry_calls.append(ws))

    view.set_workspace("ws-1")
    view.show_gap_report(
        AbilityGapReport(
            workspace_id="ws-1",
            total_questions=2,
            mastered_count=0,
            basic_count=0,
            needs_improvement_count=1,
            mastered_knowledge_points=(),
            weak_knowledge_points=("数据库流程",),
            suggested_reading_files=("/tmp/flow.md",),
            suggested_follow_up_questions=("补充数据库流程中的校验与持久化",),
            follow_up_question_ids=("q-1", "q-2"),
            next_learning_order=("数据库流程",),
            overview="共 2 题，0 项已掌握，0 项基本理解，1 项建议补充。",
        )
    )

    _button_by_text(view, "继续追问").click()
    _button_by_text(view, "错题复测").click()

    assert calls == [("ws-1", "q-1")]
    assert retry_calls == ["ws-1"]


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

        assert window.windowTitle() == "知识岛"
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
