from __future__ import annotations

import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from webapp.models import ImportResult
from webapp.routes import imports as import_routes
from webapp.routes.imports import handle_imports_route
from webapp.storage import KnowledgeStore


def _empty_import_result() -> ImportResult:
    return ImportResult(
        imported=0,
        skipped=0,
        errors=[],
        skipped_details=[],
        created=0,
        updated=0,
        unchanged=0,
        deleted=0,
    )


def test_directory_import_serializes_same_project_requests(tmp_path, monkeypatch):
    store = KnowledgeStore(tmp_path / "app.db")
    project_root = tmp_path / "project"
    project_root.mkdir()
    project = store.create_project("知识岛", project_root)
    first_entered = threading.Event()
    release_first = threading.Event()
    active_lock = threading.Lock()
    active_count = 0
    max_active_count = 0

    def slow_import(store, project_id, root_path):
        nonlocal active_count, max_active_count
        with active_lock:
            active_count += 1
            max_active_count = max(max_active_count, active_count)
        if not first_entered.is_set():
            first_entered.set()
            release_first.wait(timeout=2)
        time.sleep(0.02)
        with active_lock:
            active_count -= 1
        return _empty_import_result()

    monkeypatch.setattr(import_routes, "import_directory", slow_import)

    with ThreadPoolExecutor(max_workers=2) as executor:
        first = executor.submit(handle_imports_route, store, "POST", "/api/import", {}, {"project_id": project.id})
        assert first_entered.wait(timeout=1)
        second = executor.submit(handle_imports_route, store, "POST", "/api/import", {}, {"project_id": project.id})
        time.sleep(0.08)
        release_first.set()

        assert first.result(timeout=2).status == 200
        assert second.result(timeout=2).status == 200

    assert max_active_count == 1


def test_directory_import_allows_different_projects_to_overlap(tmp_path, monkeypatch):
    store = KnowledgeStore(tmp_path / "app.db")
    first_root = tmp_path / "first"
    second_root = tmp_path / "second"
    first_root.mkdir()
    second_root.mkdir()
    first_project = store.create_project("知识岛 A", first_root)
    second_project = store.create_project("知识岛 B", second_root)
    release_imports = threading.Event()
    entered_projects: set[str] = set()
    active_lock = threading.Lock()
    active_count = 0
    max_active_count = 0

    def slow_import(store, project_id, root_path):
        nonlocal active_count, max_active_count
        with active_lock:
            active_count += 1
            max_active_count = max(max_active_count, active_count)
            entered_projects.add(project_id)
        release_imports.wait(timeout=2)
        with active_lock:
            active_count -= 1
        return _empty_import_result()

    monkeypatch.setattr(import_routes, "import_directory", slow_import)

    with ThreadPoolExecutor(max_workers=2) as executor:
        first = executor.submit(handle_imports_route, store, "POST", "/api/import", {}, {"project_id": first_project.id})
        second = executor.submit(handle_imports_route, store, "POST", "/api/import", {}, {"project_id": second_project.id})
        deadline = time.monotonic() + 1
        while time.monotonic() < deadline and len(entered_projects) < 2:
            time.sleep(0.01)
        release_imports.set()

        assert first.result(timeout=2).status == 200
        assert second.result(timeout=2).status == 200

    assert entered_projects == {first_project.id, second_project.id}
    assert max_active_count == 2


def test_project_indexing_coordinator_serializes_per_project():
    from webapp.indexing import ProjectIndexingCoordinator

    coordinator = ProjectIndexingCoordinator()
    first_entered = threading.Event()
    release_first = threading.Event()
    second_entered = threading.Event()

    def first_scope():
        with coordinator.project_scope("project-a"):
            first_entered.set()
            release_first.wait(timeout=2)

    def second_scope():
        with coordinator.project_scope("project-a"):
            second_entered.set()

    with ThreadPoolExecutor(max_workers=2) as executor:
        first = executor.submit(first_scope)
        assert first_entered.wait(timeout=1)
        second = executor.submit(second_scope)
        assert not second_entered.wait(timeout=0.08)
        release_first.set()

        first.result(timeout=2)
        second.result(timeout=2)

    assert second_entered.is_set()
