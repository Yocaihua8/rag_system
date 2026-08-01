from pathlib import Path

from backend.domain.models import Document, SearchHit


def test_search_hit_serializes_rerank_score():
    document = Document(
        id="doc-1",
        project_id="project-1",
        source_path=Path("guide.md"),
        relative_path="guide.md",
        content="Reranker test",
        checksum="checksum",
        updated_at="2026-06-26T00:00:00Z",
    )

    hit = SearchHit(document=document, score=0.2, snippet="Reranker test", rerank_score=0.95)

    assert hit.to_dict()["rerank_score"] == 0.95
