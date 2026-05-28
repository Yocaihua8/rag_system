from pathlib import Path

from src.application.container import AppContainer
from src.config.settings import load_settings
from src.ports.vector_store import VectorSearchResult


def test_container_build_uses_settings_vector_dir_for_chroma(
    tmp_path: Path,
    monkeypatch,
) -> None:
    captured: dict[str, Path] = {}

    class FakeChromaVectorStore:
        def __init__(self, persist_dir: Path) -> None:
            captured["persist_dir"] = persist_dir

        def upsert(self, chunk_id, vector, metadata):
            raise AssertionError("not used")

        def upsert_batch(self, items):
            raise AssertionError("not used")

        def search(
            self,
            query_vector,
            top_k,
            workspace_id,
            domain="",
        ) -> list[VectorSearchResult]:
            raise AssertionError("not used")

        def delete_by_workspace(self, workspace_id):
            raise AssertionError("not used")

        def delete_by_document(self, document_id):
            raise AssertionError("not used")

        def count(self, workspace_id):
            raise AssertionError("not used")

    monkeypatch.setattr(
        "src.adapters.vector_store.chroma_store.ChromaVectorStore",
        FakeChromaVectorStore,
    )

    settings = load_settings(
        override_env={
            "RAG_KB_ROOT": str(tmp_path / "kb"),
            "RAG_RUNTIME_DIR": str(tmp_path / "runtime"),
            "RAG_DB_PATH": str(tmp_path / "app.db"),
            "RAG_EMBED_PROVIDER": "ollama",
            "RAG_RETRIEVER_KIND": "vector",
        }
    )

    AppContainer.build(settings)

    assert captured["persist_dir"] == settings.vector_dir
    assert settings.vector_dir == settings.runtime_dir / "vectors"
    assert settings.vector_dir.is_dir()
