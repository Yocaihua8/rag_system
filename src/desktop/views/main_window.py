"""
MainWindow — 应用主窗口。

布局：左侧 Sidebar（固定 220px）+ 右侧 QStackedWidget（内容区）+ 底部 TaskStatusBar。

简化后的导航（5 项）：项目问答 | 我的项目 | 知识库 | 掌握评估 | 设置
  - 默认落地页：项目问答（而非知识库索引）
  - 创建工作区后自动触发索引，无需手动跳转
  - 使用指引改为侧边栏底部的 ？帮助按钮
"""
from __future__ import annotations

from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog, QDialogButtonBox, QHBoxLayout, QLabel, QPushButton,
    QStackedWidget, QVBoxLayout, QWidget, QMainWindow, QFrame,
)

from src.application.container import AppContainer
from src.application.ingestion_usecases import IngestWorkspaceUseCase
from src.application.query_usecases import QueryKnowledgeBaseUseCase
from src.application.workspace_usecases import WorkspaceUseCases
from src.application.settings_usecases import SettingsUseCases
from src.desktop.controllers.ingestion_controller import IngestionController
from src.desktop.controllers.query_controller import QueryController
from src.desktop.controllers.workspace_controller import WorkspaceController
from src.desktop.style import (
    BG_PRIMARY, BG_SECONDARY, BORDER, TEXT_PRIMARY, TEXT_SECONDARY, ACCENT,
    get_stylesheet,
)
from src.desktop.views.assessment_view import AssessmentView
from src.desktop.views.guide_view import GuideView
from src.desktop.views.ingestion_view import IngestionView
from src.desktop.views.query_view import QueryView
from src.desktop.views.settings_view import SettingsView
from src.desktop.views.task_status_bar import TaskStatusBar
from src.desktop.views.workspace_view import WorkspaceView
from src.domain.models.workspace import Workspace


_NAV_ITEMS = [
    ("🔍", "项目问答"),
    ("📁", "我的项目"),
    ("📚", "知识库"),
    ("✓", "掌握评估"),
    ("⚙️", "设置"),
]

_FIRST_RUN_FLAG = ".guide_shown"


class MainWindow(QMainWindow):

    def __init__(self, container: AppContainer) -> None:
        super().__init__()
        self._container = container
        self._current_workspace: Optional[Workspace] = None
        self.setWindowTitle("项目知识库助手")
        self.resize(1200, 760)

        self.setStyleSheet(get_stylesheet())

        self._build_ui()
        self._wire_controllers()

        # 初始加载工作区列表
        self._ws_controller.load_all()

        # 首次启动弹出使用指引（弹窗，不切换页面）
        if self._is_first_run():
            self._mark_first_run_done()
            self._show_guide_dialog()

    # ── 首次运行检测 ──────────────────────────────────────────────────────

    def _is_first_run(self) -> bool:
        flag = self._container.settings.runtime_dir / _FIRST_RUN_FLAG
        return not flag.exists()

    def _mark_first_run_done(self) -> None:
        try:
            flag = self._container.settings.runtime_dir / _FIRST_RUN_FLAG
            flag.touch()
        except Exception:
            pass

    def _show_guide_dialog(self) -> None:
        """以弹窗形式展示使用指引，不切换主页面。"""
        dlg = QDialog(self)
        dlg.setWindowTitle("使用指引")
        dlg.resize(740, 620)
        dlg.setStyleSheet(get_stylesheet())

        layout = QVBoxLayout(dlg)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        guide = GuideView()
        layout.addWidget(guide, 1)

        btn_box = QDialogButtonBox(QDialogButtonBox.Close)
        btn_box.button(QDialogButtonBox.Close).setText("关闭，开始使用")
        btn_box.rejected.connect(dlg.accept)
        btn_row = QWidget()
        btn_row_lay = QHBoxLayout(btn_row)
        btn_row_lay.setContentsMargins(16, 8, 16, 12)
        btn_row_lay.addStretch()
        btn_row_lay.addWidget(btn_box)
        layout.addWidget(btn_row)

        dlg.exec()

    # ── UI 构建 ───────────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        central = QWidget()
        central.setObjectName("content")
        self.setCentralWidget(central)
        root_layout = QHBoxLayout(central)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # ── 左侧 Sidebar ──────────────────────────────────────────────────
        sidebar = QWidget()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(220)
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(12, 16, 12, 12)
        sidebar_layout.setSpacing(2)

        app_title = QLabel("项目知识库")
        app_title.setStyleSheet(f"""
            font-size: 14px; font-weight: 700;
            color: {TEXT_PRIMARY};
            padding: 4px 4px 12px 4px;
            background: transparent;
        """)
        sidebar_layout.addWidget(app_title)

        # 工作区面板
        self._ws_view = WorkspaceView()
        sidebar_layout.addWidget(self._ws_view)

        # 分割线
        divider = QFrame()
        divider.setFrameShape(QFrame.HLine)
        divider.setStyleSheet(
            f"background-color: {BORDER}; max-height: 1px; border: none; margin: 8px 0;"
        )
        sidebar_layout.addWidget(divider)

        # 导航按钮
        self._nav_buttons: list[QPushButton] = []
        for icon, label in _NAV_ITEMS:
            btn = QPushButton(f"{icon}  {label}")
            btn.setCheckable(True)
            btn.setProperty("nav", "true")
            btn.style().unpolish(btn)
            btn.style().polish(btn)
            self._nav_buttons.append(btn)
            sidebar_layout.addWidget(btn)

        sidebar_layout.addStretch()

        # 底部：版本号 + 帮助按钮
        bottom_row = QHBoxLayout()
        version_label = QLabel("v2.0  ·  本地 RAG")
        version_label.setStyleSheet(f"""
            font-size: 11px; color: {TEXT_SECONDARY};
            padding: 4px; background: transparent;
        """)
        btn_help = QPushButton("？")
        btn_help.setToolTip("使用指引")
        btn_help.setFixedSize(24, 24)
        btn_help.setStyleSheet(f"""
            QPushButton {{
                color: {TEXT_SECONDARY}; border: 1px solid {BORDER};
                border-radius: 12px; font-size: 12px; background: transparent;
            }}
            QPushButton:hover {{ color: {TEXT_PRIMARY}; border-color: {ACCENT}; }}
        """)
        btn_help.clicked.connect(self._show_guide_dialog)
        bottom_row.addWidget(version_label)
        bottom_row.addStretch()
        bottom_row.addWidget(btn_help)
        sidebar_layout.addLayout(bottom_row)

        root_layout.addWidget(sidebar)

        # ── 右侧内容区 ────────────────────────────────────────────────────
        content_area = QWidget()
        content_area.setObjectName("content")
        content_layout = QVBoxLayout(content_area)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        self._stack = QStackedWidget()
        self._query_view = QueryView()
        self._project_view = IngestionView()
        self._knowledge_view = IngestionView()
        self._ingest_view = self._knowledge_view
        self._assessment_view = AssessmentView()
        self._settings_view = SettingsView()

        self._stack.addWidget(self._query_view)       # 0 项目问答
        self._stack.addWidget(self._project_view)     # 1 我的项目，占位复用索引页
        self._stack.addWidget(self._knowledge_view)   # 2 知识库
        self._stack.addWidget(self._assessment_view)  # 3 掌握评估
        self._stack.addWidget(self._settings_view)    # 4 设置

        content_layout.addWidget(self._stack)
        root_layout.addWidget(content_area, 1)

        # 状态栏
        self._status_bar = TaskStatusBar()
        self.setStatusBar(self._status_bar)

        # 加载设置到设置页
        self._settings_view.load_settings(self._container.settings)

        # 导航按钮逻辑
        for i, btn in enumerate(self._nav_buttons):
            btn.clicked.connect(lambda _, idx=i: self._switch_page(idx))
        self._switch_page(0)   # 默认：问答页

    def _switch_page(self, index: int) -> None:
        self._stack.setCurrentIndex(index)
        for i, btn in enumerate(self._nav_buttons):
            btn.setChecked(i == index)

    def _open_assessment(self, workspace_id: str) -> None:
        self._assessment_view.set_workspace(workspace_id)
        self._switch_page(3)

    # ── 控制器组装 ────────────────────────────────────────────────────────

    def _wire_controllers(self) -> None:
        c = self._container
        s = c.settings

        # WorkspaceController
        self._ws_controller = WorkspaceController(WorkspaceUseCases(c.workspace_store), self)
        self._ws_view.create_requested.connect(self._ws_controller.create)
        self._ws_view.delete_requested.connect(self._ws_controller.delete)
        self._ws_view.workspace_selected.connect(self._on_workspace_selected)
        self._ws_controller.workspaces_loaded.connect(self._ws_view.load_workspaces)
        self._ws_controller.workspace_deleted.connect(lambda _: self._ws_controller.load_all())
        self._ws_controller.error_occurred.connect(
            lambda e: self._status_bar.show_message(f"⚠️ {e}")
        )
        # 创建工作区后：刷新列表，然后自动触发索引
        self._ws_controller.workspace_created.connect(self._on_workspace_created)

        # IngestionController
        ingest_uc = IngestWorkspaceUseCase(
            c.workspace_store, c.document_store, c.chunk_store,
            c.task_store, c.retriever, s,
        )
        self._ingest_ctrl = IngestionController(ingest_uc, self)
        self._project_view.ingest_requested.connect(self._ingest_ctrl.start)
        self._ingest_view.ingest_requested.connect(self._ingest_ctrl.start)
        # 工作区面板上的「▶ 索引」按钮也触发索引
        self._ws_view.index_requested.connect(
            lambda ws_id: self._ingest_ctrl.start(ws_id, False)
        )
        # 问答页「立即建立索引」按钮
        self._query_view.index_requested.connect(
            lambda ws_id: self._ingest_ctrl.start(ws_id, False)
        )
        self._query_view.assessment_requested.connect(
            lambda ws_id: self._open_assessment(ws_id)
        )
        self._ingest_ctrl.ingest_started.connect(self._project_view.on_started)
        self._ingest_ctrl.ingest_started.connect(self._ingest_view.on_started)
        self._ingest_ctrl.ingest_started.connect(
            lambda: self._status_bar.show_progress(0, "索引中…")
        )
        self._ingest_ctrl.ingest_progress.connect(self._project_view.on_progress)
        self._ingest_ctrl.ingest_progress.connect(self._ingest_view.on_progress)
        self._ingest_ctrl.ingest_progress.connect(self._status_bar.show_progress)
        self._ingest_ctrl.ingest_finished.connect(self._project_view.on_finished)
        self._ingest_ctrl.ingest_finished.connect(self._ingest_view.on_finished)
        self._ingest_ctrl.ingest_finished.connect(self._on_ingest_finished)
        self._ingest_ctrl.ingest_failed.connect(self._project_view.on_failed)
        self._ingest_ctrl.ingest_failed.connect(self._ingest_view.on_failed)
        self._ingest_ctrl.ingest_failed.connect(
            lambda e: self._status_bar.show_message(f"❌ {e}")
        )

        # QueryController
        query_uc = QueryKnowledgeBaseUseCase(
            c.retriever, c.llm_client, c.conversation_store,
            model=s.ollama_model, temperature=s.llm_temperature,
        )
        self._query_ctrl = QueryController(query_uc, self)
        self._query_view.query_submitted.connect(
            lambda ws_id, q: self._query_ctrl.submit(ws_id, q, streaming=True)
        )
        self._query_ctrl.query_started.connect(self._query_view.on_query_started)
        self._query_ctrl.query_started.connect(
            lambda: self._status_bar.show_progress(0, "查询中…")
        )
        self._query_ctrl.token_received.connect(self._query_view.on_token_received)
        self._query_ctrl.query_finished.connect(self._query_view.on_query_finished)
        self._query_ctrl.query_finished.connect(
            lambda _: self._status_bar.show_message("✅ 查询完成")
        )
        self._query_ctrl.query_failed.connect(self._query_view.on_query_failed)
        self._query_ctrl.query_failed.connect(
            lambda e: self._status_bar.show_message(f"❌ {e}")
        )

        # AssessmentView
        self._assessment_view.start_requested.connect(
            lambda _: self._status_bar.show_message("掌握评估功能将在后续版本接入自动出题")
        )

        # SettingsView
        self._settings_view.save_requested.connect(self._on_settings_save)

    # ── 工作区事件 ────────────────────────────────────────────────────────

    def _on_workspace_created(self, ws: Workspace) -> None:
        """工作区创建后：刷新列表 + 自动触发索引。"""
        self._ws_controller.load_all()
        # 自动开始索引——用户不需要手动跳转到知识库页
        self._ingest_ctrl.start(ws.id, False)
        self._status_bar.show_message(f"⚡ 正在为「{ws.name}」建立索引…")

    def _on_workspace_selected(self, workspace: Workspace) -> None:
        """切换工作区，同步给各个功能页。"""
        self._current_workspace = workspace
        self._query_view.set_workspace(workspace)
        self._project_view.set_workspace(workspace.id, workspace.name)
        self._ingest_view.set_workspace(workspace.id, workspace.name)
        self._assessment_view.set_workspace(workspace.id)
        self._status_bar.show_message(f"已切换到工作区：{workspace.name}")

    def _on_ingest_finished(self, result) -> None:
        """索引完成后：刷新工作区列表状态，并通知问答页可以使用了。"""
        self._ws_controller.load_all()
        # 如果当前问答页正显示「未索引」状态，切换为就绪
        self._query_view.mark_indexed()
        self._status_bar.show_message(f"✅ {result.message}")

    # ── 设置保存 ──────────────────────────────────────────────────────────

    def _on_settings_save(self, data: dict) -> None:
        uc = SettingsUseCases(self._container.settings)
        _save_map = {
            "kb_root":         uc.save_kb_root,
            "ollama_host":     uc.save_ollama_host,
            "ollama_model":    uc.save_ollama_model,
            "embedding_model": uc.save_embedding_model,
            "llm_provider":    uc.save_llm_provider,
            "llm_api_base":    uc.save_llm_api_base,
            "llm_api_key":     uc.save_llm_api_key,
            "llm_api_model":   uc.save_llm_api_model,
            "embed_provider":  uc.save_embed_provider,
        }
        for field, save_fn in _save_map.items():
            if data.get(field):
                save_fn(data[field])
        # P5: 数值型字段需单独处理（0.0 也是有效值，不能用 if data.get() 判断）
        if "llm_temperature" in data:
            uc.save_llm_temperature(data["llm_temperature"])
        if "llm_max_tokens" in data:
            uc.save_llm_max_tokens(data["llm_max_tokens"])
        self._status_bar.show_message("✅ 设置已保存（部分设置重启后生效）")
