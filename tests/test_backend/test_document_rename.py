from pathlib import Path

import pytest

from backend.domain.project_analysis import analyze_project
from backend.storage import KnowledgeStore


class RecordingVectorStore:
    def __init__(self) -> None:
        self.upserts = []
        self.deletes = []

    def search(self, project_id, query_vector, limit):
        return []

    def upsert(self, records) -> None:
        self.upserts.append(list(records))

    def delete(self, project_id, chunk_ids=None) -> None:
        self.deletes.append((project_id, list(chunk_ids) if chunk_ids is not None else None))

    def is_available(self) -> bool:
        return True


def test_document_rename_preserves_identity_chunks_and_vector_metadata(tmp_path: Path):
    vector_store = RecordingVectorStore()
    store = KnowledgeStore(tmp_path / "app.db", vector_store=vector_store)
    root = tmp_path / "project"
    root.mkdir()
    project = store.create_project("Demo", root)
    original = store.upsert_document(
        project.id,
        root / "old.md",
        "notes/old.md",
        "# Local bridge\n\nObsidian events keep stable document identity.",
    ).document
    original_chunk_ids = [chunk.id for chunk in store.list_chunks(project.id)]
    analysis = analyze_project(store, project.id)
    vector_store.upserts.clear()

    renamed = store.rename_document_preserving_identity(
        project.id,
        "notes/old.md",
        "notes/new.md",
        root / "new.md",
    )

    assert renamed is not None
    assert renamed.id == original.id
    assert renamed.relative_path == "notes/new.md"
    assert renamed.source_path == root / "new.md"
    assert renamed.content == original.content
    assert renamed.checksum == original.checksum
    chunks = store.list_chunks(project.id)
    assert [chunk.id for chunk in chunks] == original_chunk_ids
    assert all(chunk.document.id == original.id for chunk in chunks)
    assert all(chunk.document.relative_path == "notes/new.md" for chunk in chunks)
    assert len(vector_store.upserts) == 1
    assert [record.chunk_id for record in vector_store.upserts[0]] == original_chunk_ids
    assert all(record.document_id == original.id for record in vector_store.upserts[0])
    assert all(record.path == "notes/new.md" for record in vector_store.upserts[0])
    assert store.get_latest_coach_analysis_run(project.id).status == "stale"
    sources = store.list_coach_knowledge_points(project.id, run_id=analysis["id"])[0].sources
    assert any(source.document_id == original.id for source in sources)


def test_document_rename_rejects_target_collision_before_marking_analysis_stale(
    tmp_path: Path,
):
    store = KnowledgeStore(tmp_path / "app.db", vector_store=None)
    root = tmp_path / "project"
    root.mkdir()
    project = store.create_project("Demo", root)
    first = store.upsert_document(
        project.id,
        root / "first.md",
        "first.md",
        "# First\n\nFirst source.",
    ).document
    second = store.upsert_document(
        project.id,
        root / "second.md",
        "second.md",
        "# Second\n\nSecond source.",
    ).document
    analyze_project(store, project.id)

    with pytest.raises(ValueError, match="target path already exists"):
        store.rename_document_preserving_identity(
            project.id,
            "first.md",
            "second.md",
        )

    assert store.get_latest_coach_analysis_run(project.id).status == "completed"
    assert store.get_document(first.id).relative_path == "first.md"
    assert store.get_document(second.id).relative_path == "second.md"


def test_document_rename_returns_none_when_source_path_is_unknown(tmp_path: Path):
    store = KnowledgeStore(tmp_path / "app.db", vector_store=None)
    project = store.create_project("Demo", tmp_path / "project")

    renamed = store.rename_document_preserving_identity(
        project.id,
        "missing.md",
        "renamed.md",
    )

    assert renamed is None
