from __future__ import annotations

from typing import List, Optional

from PySide6.QtCore import QObject, Signal

from src.application.workspace_usecases import WorkspaceUseCases
from src.domain.models.workspace import Workspace


class WorkspaceController(QObject):
    workspaces_loaded = Signal(list)       # List[Workspace]
    workspace_created = Signal(object)     # Workspace
    workspace_deleted = Signal(str)        # workspace_id
    error_occurred = Signal(str)

    def __init__(self, use_cases: WorkspaceUseCases, parent=None) -> None:
        super().__init__(parent)
        self._uc = use_cases

    def load_all(self) -> None:
        try:
            ws_list = self._uc.list_all()
            self.workspaces_loaded.emit(ws_list)
        except Exception as e:
            self.error_occurred.emit(str(e))

    def create(self, name: str, root_path: str) -> None:
        try:
            ws = self._uc.create(name, root_path)
            self.workspace_created.emit(ws)
        except Exception as e:
            self.error_occurred.emit(str(e))

    def delete(self, workspace_id: str) -> None:
        try:
            self._uc.delete(workspace_id)
            self.workspace_deleted.emit(workspace_id)
        except Exception as e:
            self.error_occurred.emit(str(e))
