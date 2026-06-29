"""
test_workspace_usecases.py — 工作区用例测试。
"""
from __future__ import annotations

import dataclasses
from pathlib import Path

import pytest

from src.application.container import AppContainer
from src.application.workspace_usecases import WorkspaceUseCases
from src.config.settings import load_settings
from src.domain.errors import NotFoundError


@pytest.fixture
def uc(tmp_path) -> WorkspaceUseCases:
    s = load_settings(override_env={
        "RAG_KB_ROOT": str(tmp_path / "kb"),
        "RAG_RUNTIME_DIR": str(tmp_path / "runtime"),
    })
    s = dataclasses.replace(s, db_path=Path(":memory:"))
    container = AppContainer.build_for_testing(s)
    return WorkspaceUseCases(container.workspace_store)


class TestWorkspaceUseCases:

    def test_create_and_list(self, uc):
        ws = uc.create("求职 2024", "/kb/root")
        assert ws.name == "求职 2024"
        workspaces = uc.list_all()
        assert any(w.id == ws.id for w in workspaces)

    def test_get(self, uc):
        ws = uc.create("test", "/kb")
        found = uc.get(ws.id)
        assert found.id == ws.id
        assert found.name == "test"

    def test_get_nonexistent_raises(self, uc):
        with pytest.raises(NotFoundError):
            uc.get("no-such-id")

    def test_delete(self, uc):
        ws = uc.create("to-delete", "/kb")
        uc.delete(ws.id)
        with pytest.raises(NotFoundError):
            uc.get(ws.id)

    def test_list_empty(self, uc):
        assert uc.list_all() == []

    def test_multiple_workspaces(self, uc):
        ws1 = uc.create("ws1", "/kb1")
        ws2 = uc.create("ws2", "/kb2")
        ws3 = uc.create("ws3", "/kb3")
        all_ws = uc.list_all()
        ids = {w.id for w in all_ws}
        assert {ws1.id, ws2.id, ws3.id} == ids
