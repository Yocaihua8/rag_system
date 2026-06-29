from __future__ import annotations

from typing import List

from src.domain.errors import NotFoundError, ValidationError
from src.domain.models.workspace import Workspace
from src.ports.workspace_store import IWorkspaceStore


class WorkspaceUseCases:

    def __init__(self, store: IWorkspaceStore) -> None:
        self._store = store

    def create(self, name: str, root_path: str) -> Workspace:
        name = name.strip()
        if not name:
            raise ValidationError("工作区名称不能为空")
        if not root_path.strip():
            raise ValidationError("根目录路径不能为空")
        ws = Workspace.create(name=name, root_path=root_path.strip())
        return self._store.save(ws)

    def list_all(self) -> List[Workspace]:
        return self._store.list_all()

    def get(self, workspace_id: str) -> Workspace:
        ws = self._store.get(workspace_id)
        if ws is None:
            raise NotFoundError("Workspace", workspace_id)
        return ws

    def rename(self, workspace_id: str, new_name: str) -> Workspace:
        new_name = new_name.strip()
        if not new_name:
            raise ValidationError("工作区名称不能为空")
        ws = self.get(workspace_id)
        updated = Workspace(
            id=ws.id, name=new_name, root_path=ws.root_path,
            created_at=ws.created_at, last_indexed_at=ws.last_indexed_at,
            last_index_status=ws.last_index_status,
            total_files=ws.total_files, supported_files=ws.supported_files,
        )
        self._store.update(updated)
        return updated

    def set_root_path(self, workspace_id: str, path: str) -> Workspace:
        ws = self.get(workspace_id)
        updated = Workspace(
            id=ws.id, name=ws.name, root_path=path.strip(),
            created_at=ws.created_at, last_indexed_at=ws.last_indexed_at,
            last_index_status=ws.last_index_status,
            total_files=ws.total_files, supported_files=ws.supported_files,
        )
        self._store.update(updated)
        return updated

    def delete(self, workspace_id: str) -> None:
        self.get(workspace_id)  # 确认存在
        self._store.delete(workspace_id)
