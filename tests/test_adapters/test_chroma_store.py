from pathlib import Path

from legacy.desktop.adapters.vector_store import chroma_store
from legacy.desktop.adapters.vector_store.chroma_store import ChromaVectorStore


def test_chroma_vector_store_uses_configured_persist_dir(
    tmp_path: Path,
    monkeypatch,
) -> None:
    captured: dict[str, object] = {}

    class FakePersistentClient:
        def __init__(self, path: str, settings: object) -> None:
            captured["path"] = path
            captured["settings"] = settings

    monkeypatch.setattr(
        chroma_store.chromadb,
        "PersistentClient",
        FakePersistentClient,
    )

    persist_dir = tmp_path / "runtime" / "vectors"

    ChromaVectorStore(persist_dir=persist_dir)

    assert persist_dir.is_dir()
    assert captured["path"] == str(persist_dir)
