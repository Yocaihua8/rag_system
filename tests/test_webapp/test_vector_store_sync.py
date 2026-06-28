from __future__ import annotations

from pathlib import Path

from webapp.storage import KnowledgeStore


def test_upsert_document_syncs_chunk_vectors_to_vector_store(tmp_path: Path):
    vector_store = RecordingVectorStore()
    embedding_client = FakeEmbeddingClient()
    store = KnowledgeStore(
        tmp_path / "app.db",
        embedding_client=embedding_client,
        vector_store=vector_store,
    )
    project = store.create_project("Demo", tmp_path)

    result = store.upsert_document(
        project.id,
        tmp_path / "guide.md",
        "guide.md",
        "模型设置：填写 DeepSeek API Key。\n\n导入说明：选择文件夹导入。",
    )

    chunks = store.list_chunks(project.id)
    assert result.action == "created"
    assert store.count_chunk_vectors(project.id) == len(chunks)
    assert len(vector_store.upserts) == 1
    records = vector_store.upserts[0]
    assert [record.chunk_id for record in records] == [chunk.id for chunk in chunks]
    assert {record.project_id for record in records} == {project.id}
    assert {record.document_id for record in records} == {result.document.id}
    assert [record.chunk_index for record in records] == [chunk.chunk_index for chunk in chunks]
    assert [record.path for record in records] == ["guide.md", "guide.md"]
    assert {record.provider for record in records} == {"api"}
    assert {record.model for record in records} == {"fake-embedding"}
    assert records[0].vector == {"deepseek": 1.0, "api": 1.0, "key": 1.0}


def test_update_and_delete_remove_stale_vectors_from_vector_store(tmp_path: Path):
    vector_store = RecordingVectorStore()
    store = KnowledgeStore(
        tmp_path / "app.db",
        embedding_client=FakeEmbeddingClient(),
        vector_store=vector_store,
    )
    project = store.create_project("Demo", tmp_path)

    first = store.upsert_document(
        project.id,
        tmp_path / "guide.md",
        "guide.md",
        "DeepSeek API Key setup",
    )
    first_chunk_ids = [record.chunk_id for record in vector_store.upserts[-1]]

    store.upsert_document(
        project.id,
        tmp_path / "guide.md",
        "guide.md",
        "Docker startup guide",
    )
    second_chunk_ids = [record.chunk_id for record in vector_store.upserts[-1]]
    deleted_document = store.delete_document(first.document.id)

    assert first_chunk_ids != second_chunk_ids
    assert vector_store.deletes[0] == {
        "project_id": project.id,
        "chunk_ids": first_chunk_ids,
    }
    assert deleted_document is not None
    assert vector_store.deletes[1] == {
        "project_id": project.id,
        "chunk_ids": second_chunk_ids,
    }


def test_delete_documents_not_in_removes_stale_vectors_from_vector_store(tmp_path: Path):
    vector_store = RecordingVectorStore()
    store = KnowledgeStore(
        tmp_path / "app.db",
        embedding_client=FakeEmbeddingClient(),
        vector_store=vector_store,
    )
    project = store.create_project("Demo", tmp_path)
    store.upsert_document(project.id, tmp_path / "keep.md", "keep.md", "Keep DeepSeek API notes")
    drop = store.upsert_document(project.id, tmp_path / "drop.md", "drop.md", "Drop Docker notes")
    drop_chunk_ids = [chunk.id for chunk in store.list_chunks(project.id) if chunk.document.id == drop.document.id]

    deleted = store.delete_documents_not_in(project.id, {"keep.md"})

    assert deleted == 1
    assert vector_store.deletes[-1] == {
        "project_id": project.id,
        "chunk_ids": drop_chunk_ids,
    }


def test_vector_store_failure_does_not_break_sqlite_write(tmp_path: Path, capsys):
    store = KnowledgeStore(
        tmp_path / "app.db",
        embedding_client=FakeEmbeddingClient(),
        vector_store=FailingVectorStore(),
    )
    project = store.create_project("Demo", tmp_path)

    result = store.upsert_document(
        project.id,
        tmp_path / "guide.md",
        "guide.md",
        "DeepSeek API Key setup",
    )

    assert result.action == "created"
    assert len(store.list_chunks(project.id)) == 1
    assert store.count_chunk_vectors(project.id) == 1
    assert "WARNING: vector store upsert failed" in capsys.readouterr().err


class FakeEmbeddingClient:
    provider = "api"
    model = "fake-embedding"

    def embed_texts(self, texts):
        vectors = []
        for text in texts:
            lowered = text.lower()
            vectors.append({
                "deepseek": 1.0 if "deepseek" in lowered else 0.0,
                "api": 1.0 if "api" in lowered else 0.0,
                "key": 1.0 if "key" in lowered else 0.0,
            })
        return vectors


class RecordingVectorStore:
    def __init__(self):
        self.upserts = []
        self.deletes = []

    def search(self, project_id, query_vector, limit):
        return []

    def upsert(self, records):
        self.upserts.append(list(records))

    def delete(self, project_id, chunk_ids=None):
        self.deletes.append({
            "project_id": project_id,
            "chunk_ids": list(chunk_ids or []),
        })

    def is_available(self):
        return True


class FailingVectorStore(RecordingVectorStore):
    def upsert(self, records):
        raise RuntimeError("qdrant write failed")
