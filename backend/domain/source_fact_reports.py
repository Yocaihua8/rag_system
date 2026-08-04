"""Deterministic reports derived only from persisted v3 document snapshots."""
from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from backend.domain.project_insights import source_snapshot_fingerprint


ANALYZER_VERSION = "source-facts.v1"
MAX_HEADINGS = 20


def build_source_fact_report(
    *, project_id: str, source_count: int, documents: Sequence[Mapping[str, Any]]
) -> dict[str, Any]:
    """Build a bounded, evidence-linked report without filesystems or models."""

    ordered = sorted(documents, key=lambda item: (str(item["relative_path"]), str(item["id"])))
    evidence = [_evidence(item) for item in ordered]
    headings = _markdown_headings(ordered)
    document_facts = [
        {
            "kind": "document_text_metrics",
            "relative_path": str(item["relative_path"]),
            "non_empty_line_count": _non_empty_line_count(str(item.get("content") or "")),
            "evidence": _evidence(item),
        }
        for item in ordered
    ]
    return {
        "report_kind": "project_source_facts",
        "analyzer_version": ANALYZER_VERSION,
        "project_id": project_id,
        "status": "ready" if ordered else "source_required",
        "source_snapshot": {
            "source_count": int(source_count),
            "document_count": len(ordered),
            "total_bytes": sum(int(item["size_bytes"]) for item in ordered),
            "fingerprint": source_snapshot_fingerprint(ordered),
        },
        "document_facts": document_facts,
        "markdown_headings": headings,
        "evidence": evidence,
    }


def _evidence(item: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "document_id": str(item["id"]),
        "source_id": item.get("source_id"),
        "relative_path": str(item["relative_path"]),
        "checksum": str(item["checksum"]),
    }


def _non_empty_line_count(content: str) -> int:
    return sum(1 for line in content.splitlines() if line.strip())


def _markdown_headings(documents: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    headings: list[dict[str, Any]] = []
    for document in documents:
        if not str(document["relative_path"]).lower().endswith(".md"):
            continue
        for line_number, line in enumerate(str(document.get("content") or "").splitlines(), start=1):
            clean = line.strip()
            if not clean.startswith("#"):
                continue
            marker, separator, title = clean.partition(" ")
            if not separator or not title.strip() or set(marker) != {"#"}:
                continue
            headings.append(
                {
                    "title": title.strip(),
                    "level": len(marker),
                    "line_number": line_number,
                    "evidence": _evidence(document),
                }
            )
            if len(headings) >= MAX_HEADINGS:
                return headings
    return headings
