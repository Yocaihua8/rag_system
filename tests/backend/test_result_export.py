from pathlib import Path

from backend.domain.result_export import result_output_dir


def test_result_output_dir_defaults_to_configured_v2_runtime(
    monkeypatch,
    tmp_path,
):
    runtime_dir = tmp_path / "runtime" / "v2"
    monkeypatch.delenv("KI_OUTPUT_DIR", raising=False)
    monkeypatch.delenv("RAG_OUTPUT_DIR", raising=False)
    monkeypatch.setenv("RAG_RUNTIME_DIR", str(runtime_dir))

    assert result_output_dir() == runtime_dir.resolve() / "outputs"


def test_result_output_dir_preserves_explicit_override_priority(
    monkeypatch,
    tmp_path,
):
    ki_output_dir = tmp_path / "ki-outputs"
    rag_output_dir = tmp_path / "rag-outputs"
    monkeypatch.setenv("KI_OUTPUT_DIR", str(ki_output_dir))
    monkeypatch.setenv("RAG_OUTPUT_DIR", str(rag_output_dir))

    assert result_output_dir() == Path(ki_output_dir)

    monkeypatch.delenv("KI_OUTPUT_DIR")

    assert result_output_dir() == Path(rag_output_dir)
