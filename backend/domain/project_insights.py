"""Deterministic, source-traceable v3 project overview calculations."""
from __future__ import annotations

import hashlib
from collections import Counter
from pathlib import PurePosixPath
from typing import Any, Mapping, Sequence


MANIFEST_NAMES = {
    "cargo.toml",
    "composer.json",
    "go.mod",
    "package.json",
    "pom.xml",
    "pyproject.toml",
    "requirements.txt",
    "build.gradle",
    "build.gradle.kts",
}


def build_project_insight_overview(
    *, project_id: str, source_count: int, documents: Sequence[Mapping[str, Any]]
) -> dict[str, Any]:
    """Build an overview from public document metadata only, never content."""

    ordered = sorted(documents, key=lambda item: (str(item["relative_path"]), str(item["id"])))
    suffixes = Counter(_extension(str(item["relative_path"])) for item in ordered)
    manifests = [
        str(item["relative_path"])
        for item in ordered
        if PurePosixPath(str(item["relative_path"])).name.lower() in MANIFEST_NAMES
    ]
    return {
        "project_id": project_id,
        "status": "ready" if ordered else "source_required",
        "source_snapshot": {
            "source_count": int(source_count),
            "document_count": len(ordered),
            "total_bytes": sum(int(item["size_bytes"]) for item in ordered),
            "fingerprint": source_snapshot_fingerprint(ordered),
        },
        "file_types": [
            {"extension": extension, "count": count}
            for extension, count in sorted(suffixes.items(), key=lambda item: (-item[1], item[0]))
        ],
        "manifest_paths": manifests,
        "evidence": [
            {
                "document_id": str(item["id"]),
                "source_id": item.get("source_id"),
                "relative_path": str(item["relative_path"]),
                "checksum": str(item["checksum"]),
            }
            for item in ordered
        ],
    }


def _extension(relative_path: str) -> str:
    suffix = PurePosixPath(relative_path).suffix.lower()
    return suffix or "[no_extension]"


def source_snapshot_fingerprint(documents: Sequence[Mapping[str, Any]]) -> str:
    """Return the stable identity for one persisted v3 document snapshot."""

    ordered = sorted(documents, key=lambda item: (str(item["relative_path"]), str(item["id"])))
    fingerprint_input = "\n".join(
        f"{item['relative_path']}:{item['checksum']}" for item in ordered
    )
    return hashlib.sha256(fingerprint_input.encode("utf-8")).hexdigest()
