from __future__ import annotations

from pathlib import Path
from typing import List, Optional

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QDialog, QDialogButtonBox, QFileDialog, QHBoxLayout,
    QLabel, QLineEdit, QListWidget, QListWidgetItem,
    QMessageBox, QPushButton, QVBoxLayout, QWidget,
)

from legacy.desktop.desktop.style import ACCENT, SUCCESS, WARNING, ERROR, TEXT_SECONDARY
from legacy.desktop.domain.models.workspace import Workspace


class WorkspaceView(QWidget):
    """项目空间管理面板：列表、新建、删除、快捷索引。"""

    # 发出信号通知 Controller
    create_requested  = Signal(str, str)    # (name, root_path)
    delete_requested  = Signal(str)         # workspace_id
    workspace_selected = Signal(object)     # Workspace 对象（不只是 ID）
    index_requested   = Signal(str)         # workspace_id → 触发索引

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._workspaces: List[Workspace] = []
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        title = QLabel("项目空间")
        title.setStyleSheet("font-size: 13px; font-weight: 600; padding: 4px 0;")
        layout.addWidget(title)

        self._list = QListWidget()
        self._list.setMaximumHeight(160)
        self._list.currentRowChanged.connect(self._on_selection_changed)
        layout.addWidget(self._list)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(4)

        self._btn_create = QPushButton("＋")
        self._btn_create.setToolTip("新建项目空间")
        self._btn_create.setFixedWidth(32)

        self._btn_index = QPushButton("▶")
        self._btn_index.setToolTip("索引当前项目空间")
        self._btn_index.setFixedWidth(32)
        self._btn_index.setEnabled(False)

        self._btn_delete = QPushButton("✕")
        self._btn_delete.setToolTip("删除项目空间")
        self._btn_delete.setFixedWidth(32)
        self._btn_delete.setEnabled(False)

        self._btn_create.clicked.connect(self._on_create_clicked)
        self._btn_index.clicked.connect(self._on_index_clicked)
        self._btn_delete.clicked.connect(self._on_delete_clicked)

        btn_row.addWidget(self._btn_create)
        btn_row.addWidget(self._btn_index)
        btn_row.addStretch()
        btn_row.addWidget(self._btn_delete)
        layout.addLayout(btn_row)

    # ── 数据绑定（由 Controller 调用） ───────────────────────────────────

    def load_workspaces(self, workspaces: List[Workspace]) -> None:
        self._workspaces = workspaces
        self._list.clear()
        for ws in workspaces:
            dot, tip = _status_display(ws)
            item = QListWidgetItem(f"{dot} {ws.name}")
            item.setToolTip(tip)
            item.setData(256, ws.id)   # UserRole = id
            self._list.addItem(item)

    def current_workspace(self) -> Optional[Workspace]:
        row = self._list.currentRow()
        if 0 <= row < len(self._workspaces):
            return self._workspaces[row]
        return None

    def current_workspace_id(self) -> Optional[str]:
        ws = self.current_workspace()
        return ws.id if ws else None

    def update_workspace_status(self, workspace_id: str) -> None:
        """索引完成后刷新对应列表项的状态指示符（由外部调用）。"""
        # 触发一次 reload 即可；此处仅标记，刷新由 Controller.load_all 负责
        pass

    # ── 内部槽 ────────────────────────────────────────────────────────────

    def _on_selection_changed(self, row: int) -> None:
        has = 0 <= row < len(self._workspaces)
        self._btn_delete.setEnabled(has)
        self._btn_index.setEnabled(has)
        if has:
            self.workspace_selected.emit(self._workspaces[row])

    def _on_create_clicked(self) -> None:
        dlg = _CreateWorkspaceDialog(self)
        if dlg.exec() == QDialog.Accepted:
            self.create_requested.emit(dlg.name(), dlg.root_path())

    def _on_index_clicked(self) -> None:
        ws = self.current_workspace()
        if ws:
            self.index_requested.emit(ws.id)

    def _on_delete_clicked(self) -> None:
        ws = self.current_workspace()
        if not ws:
            return
        reply = QMessageBox.question(
            self, "确认删除",
            f"删除项目空间「{ws.name}」将同时清除其所有文档、片段和对话历史，确定吗？",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            self.delete_requested.emit(ws.id)


# ── 状态指示 ──────────────────────────────────────────────────────────────────

def _status_display(ws: Workspace) -> tuple[str, str]:
    """返回 (状态符号, tooltip 文字)。"""
    if ws.last_index_status == "ok":
        return "●", f"已索引  {ws.supported_files} 个文件"
    elif ws.last_index_status == "error":
        return "⚠", "索引出错，请重新索引"
    else:
        return "○", "尚未建立索引"


# ── 新建项目空间对话框 ────────────────────────────────────────────────────────

class _CreateWorkspaceDialog(QDialog):

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("新建项目空间")
        self.setMinimumWidth(420)
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(8)

        # 目录选择（放在上面，因为选择后名称自动填写）
        layout.addWidget(QLabel("知识库目录："))
        path_row = QHBoxLayout()
        self._path_edit = QLineEdit()
        self._path_edit.setPlaceholderText("选择包含 .md / .txt 文件的目录")
        btn_browse = QPushButton("浏览…")
        btn_browse.clicked.connect(self._browse)
        path_row.addWidget(self._path_edit)
        path_row.addWidget(btn_browse)
        layout.addLayout(path_row)

        # 项目空间名称（选目录后自动填写，可修改）
        layout.addWidget(QLabel("项目空间名称："))
        self._name_edit = QLineEdit()
        self._name_edit.setPlaceholderText("例如：2024 求职（从目录名自动填写）")
        layout.addWidget(self._name_edit)

        hint = QLabel("💡 创建后将自动开始建立索引")
        hint.setStyleSheet(f"color: {ACCENT}; font-size: 12px; padding: 4px 0;")
        layout.addWidget(hint)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.button(QDialogButtonBox.Ok).setText("创建并索引")
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _browse(self) -> None:
        path = QFileDialog.getExistingDirectory(self, "选择知识库目录")
        if path:
            self._path_edit.setText(path)
            # 如果名称栏为空，自动填写目录名
            if not self._name_edit.text().strip():
                self._name_edit.setText(Path(path).name)

    def _on_accept(self) -> None:
        if not self._path_edit.text().strip():
            QMessageBox.warning(self, "提示", "请先选择知识库目录")
            return
        if not self._name_edit.text().strip():
            # 名称仍为空则用目录名兜底
            self._name_edit.setText(Path(self._path_edit.text()).name)
        self.accept()

    def name(self) -> str:
        return self._name_edit.text().strip()

    def root_path(self) -> str:
        return self._path_edit.text().strip()
