from backend.domain.source_fact_reports import build_source_fact_report


def test_source_fact_report_is_deterministic_and_keeps_evidence_without_full_content():
    report = build_source_fact_report(
        project_id="project-1",
        source_count=1,
        documents=[
            {
                "id": "doc-readme",
                "source_id": "source-1",
                "relative_path": "README.md",
                "checksum": "a" * 64,
                "size_bytes": 25,
                "content": "# Project title\n\nA line.\n",
            },
            {
                "id": "doc-code",
                "source_id": "source-1",
                "relative_path": "src/main.py",
                "checksum": "b" * 64,
                "size_bytes": 18,
                "content": "def main():\n    pass\n",
            },
        ],
    )

    assert report["status"] == "ready"
    assert report["source_snapshot"]["document_count"] == 2
    assert report["document_facts"] == [
        {
            "kind": "document_text_metrics",
            "relative_path": "README.md",
            "non_empty_line_count": 2,
            "evidence": {
                "document_id": "doc-readme",
                "source_id": "source-1",
                "relative_path": "README.md",
                "checksum": "a" * 64,
            },
        },
        {
            "kind": "document_text_metrics",
            "relative_path": "src/main.py",
            "non_empty_line_count": 2,
            "evidence": {
                "document_id": "doc-code",
                "source_id": "source-1",
                "relative_path": "src/main.py",
                "checksum": "b" * 64,
            },
        },
    ]
    assert report["markdown_headings"] == [
        {
            "title": "Project title",
            "level": 1,
            "line_number": 1,
            "evidence": report["document_facts"][0]["evidence"],
        }
    ]
    assert "A line." not in str(report)
