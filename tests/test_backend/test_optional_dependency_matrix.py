from urllib.error import URLError


def test_optional_dependency_matrix_downgrades_without_optional_tools(capsys, monkeypatch, tmp_path):
    import sys

    from backend.config.reranker import RerankerSettings, build_reranker
    from backend.config.vector_store import VectorStoreSettings, build_vector_store
    from backend.providers.llm.ollama import OllamaLLM
    from webapp.document_processing import process_bytes

    monkeypatch.setitem(sys.modules, "pymupdf", None)
    pdf_result = process_bytes("manual.pdf", b"%PDF-1.4")

    vector_store = build_vector_store(
        VectorStoreSettings(
            enabled=True,
            provider="qdrant",
            path=tmp_path / "qdrant",
            collection="chunks",
            vector_size=4,
        ),
        dependency_available=lambda: False,
    )
    reranker = build_reranker(
        RerankerSettings(enabled=True),
        dependency_available=lambda: False,
    )
    ollama_available = OllamaLLM(
        host="http://ollama.local",
        opener=lambda request, timeout: (_ for _ in ()).throw(URLError("down")),
    ).is_available()

    stderr = capsys.readouterr().err
    assert pdf_result.skipped_reason == "pdf extraction requires optional parser"
    assert vector_store is None
    assert reranker is None
    assert ollama_available is False
    assert "WARNING: qdrant-client is not installed; Qdrant vector store disabled" in stderr
    assert "WARNING: sentence-transformers is not installed; reranker disabled" in stderr
    assert "WARNING: Ollama is not available at http://ollama.local" in stderr
