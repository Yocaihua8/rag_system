from pathlib import Path

from backend.knowledge_island.search import search_documents
from backend.knowledge_island.storage import KnowledgeStore


def test_sparse_dense_vector_conversion_uses_fixed_96_dimensions():
    from backend.knowledge_island.vector_backend import dense_to_sparse, sparse_to_dense

    dense = sparse_to_dense({"0": 0.25, "95": 0.75, "120": 1.0})

    assert len(dense) == 96
    assert dense[0] == 0.25
    assert dense[95] == 0.75
    assert "120" not in dense_to_sparse(dense)
    assert dense_to_sparse(dense) == {"0": 0.25, "95": 0.75}


def test_sqlite_vector_backend_preserves_existing_similarity_order(tmp_path: Path):
    from backend.knowledge_island.vector_backend import SqliteVectorBackend
    from backend.knowledge_island.vector_index import text_vector

    store = KnowledgeStore(tmp_path / "app.db")
    project = store.create_project("Demo", tmp_path)
    store.upsert_document(project.id, tmp_path / "model.md", "model.md", "DeepSeek API Key")
    store.upsert_document(project.id, tmp_path / "docker.md", "docker.md", "Docker compose")

    backend = SqliteVectorBackend(store)
    hits = backend.search(project.id, text_vector("DeepSeek API Key"), top_k=1)
    chunks_by_id = {chunk.id: chunk for chunk in store.list_chunks(project.id)}

    assert len(hits) == 1
    assert chunks_by_id[hits[0][0]].document.relative_path == "model.md"
    assert hits[0][1] > 0
    assert backend.count(project.id) == store.count_chunk_vectors(project.id)


def test_search_documents_uses_injected_vector_backend_candidates(tmp_path: Path):
    store = KnowledgeStore(tmp_path / "app.db")
    project = store.create_project("Demo", tmp_path)
    store.upsert_document(project.id, tmp_path / "model.md", "model.md", "Model settings")
    store.upsert_document(project.id, tmp_path / "docker.md", "docker.md", "Docker compose")
    chunks = store.list_chunks(project.id)
    docker_chunk = next(chunk for chunk in chunks if chunk.document.relative_path == "docker.md")

    class FakeVectorBackend:
        def search(self, project_id, vector, top_k):
            return [(docker_chunk.id, 0.9)]

        def count(self, project_id):
            return 1

    hits = search_documents(
        store,
        project.id,
        "unmatched query",
        limit=1,
        use_keyword=False,
        use_vector=True,
        vector_backend=FakeVectorBackend(),
    )

    assert [hit.document.relative_path for hit in hits] == ["docker.md"]
    assert hits[0].vector_score == 0.9
