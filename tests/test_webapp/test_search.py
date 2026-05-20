from pathlib import Path

from webapp.import_rules import MAX_TEXT_FILE_BYTES
from webapp.ingestion import import_directory
from webapp.search import search_documents
from webapp.storage import KnowledgeStore


def test_import_directory_indexes_supported_text_files(tmp_path: Path):
    project_dir = tmp_path / "demo"
    project_dir.mkdir()
    (project_dir / "README.md").write_text("# Demo\n\nPython SQLite local-first app", encoding="utf-8")
    (project_dir / "image.png").write_bytes(b"not text")

    store = KnowledgeStore(tmp_path / "app.db")
    project = store.create_project("Demo", project_dir)

    result = import_directory(store, project.id, project_dir)

    assert result.imported == 1
    assert result.skipped == 0
    documents = store.list_documents(project.id)
    assert [doc.relative_path for doc in documents] == ["README.md"]


def test_import_directory_reports_reimport_changes_and_removes_missing_files(tmp_path: Path):
    project_dir = tmp_path / "demo"
    project_dir.mkdir()
    (project_dir / "a.md").write_text("Alpha", encoding="utf-8")
    (project_dir / "b.md").write_text("Beta", encoding="utf-8")
    store = KnowledgeStore(tmp_path / "app.db")
    project = store.create_project("Demo", project_dir)

    first = import_directory(store, project.id, project_dir)
    (project_dir / "a.md").write_text("Alpha changed", encoding="utf-8")
    (project_dir / "b.md").unlink()
    (project_dir / "c.md").write_text("Gamma", encoding="utf-8")

    second = import_directory(store, project.id, project_dir)

    assert first.created == 2
    assert second.imported == 2
    assert second.created == 1
    assert second.updated == 1
    assert second.deleted == 1
    assert second.unchanged == 0
    assert [doc.relative_path for doc in store.list_documents(project.id)] == ["a.md", "c.md"]


def test_import_directory_skips_dependency_cache_and_vcs_directories(tmp_path: Path):
    project_dir = tmp_path / "demo"
    project_dir.mkdir()
    (project_dir / "docs").mkdir()
    (project_dir / "docs" / "keep.md").write_text("Keep this", encoding="utf-8")

    for ignored_dir in [
        ".agents",
        ".claude",
        ".codex",
        ".git",
        ".idea",
        ".venv",
        ".vscode",
        "node_modules",
        "__pycache__",
    ]:
        nested = project_dir / ignored_dir
        nested.mkdir()
        (nested / "ignored.md").write_text("Do not import", encoding="utf-8")

    store = KnowledgeStore(tmp_path / "app.db")
    project = store.create_project("Demo", project_dir)

    result = import_directory(store, project.id, project_dir)

    assert result.imported == 1
    assert result.skipped == 0
    assert [doc.relative_path for doc in store.list_documents(project.id)] == ["docs/keep.md"]


def test_import_directory_skips_text_files_over_size_limit(tmp_path: Path):
    project_dir = tmp_path / "demo"
    project_dir.mkdir()
    (project_dir / "small.md").write_text("Small content", encoding="utf-8")
    (project_dir / "huge.md").write_text("x" * (MAX_TEXT_FILE_BYTES + 1), encoding="utf-8")
    store = KnowledgeStore(tmp_path / "app.db")
    project = store.create_project("Demo", project_dir)

    result = import_directory(store, project.id, project_dir)

    assert result.imported == 1
    assert result.skipped == 1
    assert result.skipped_details == [{"path": "huge.md", "reason": "file too large"}]
    assert [doc.relative_path for doc in store.list_documents(project.id)] == ["small.md"]


def test_search_documents_ranks_matching_documents_first(tmp_path: Path):
    store = KnowledgeStore(tmp_path / "app.db")
    project = store.create_project("Demo", tmp_path)
    store.upsert_document(project.id, tmp_path / "api.md", "api.md", "FastAPI route and request handler")
    store.upsert_document(project.id, tmp_path / "ui.md", "ui.md", "PySide desktop widget")

    hits = search_documents(store, project.id, "request api", limit=3)

    assert hits[0].document.relative_path == "api.md"
    assert hits[0].score > hits[-1].score
    assert "request handler" in hits[0].snippet
