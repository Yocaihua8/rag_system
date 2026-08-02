from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

from backend.domain.import_rules import IGNORED_DIR_NAMES, is_supported_text_path


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
DEFAULT_MAX_ENTRIES = 5_000


class ProjectInspectionError(RuntimeError):
    """Raised when a registered project root cannot be inspected safely."""


def inspect_project(
    root_path: Path,
    *,
    max_entries: int = DEFAULT_MAX_ENTRIES,
    cancellation_requested: Callable[[], bool] | None = None,
) -> dict[str, Any]:
    """Inspect project structure without reading file contents.

    The result intentionally contains relative paths only. Symlink directories
    are never traversed, and ignored build/tooling directories are skipped.
    """

    if max_entries < 1:
        raise ValueError("max_entries must be positive")

    root = root_path.expanduser().resolve()
    if not root.exists():
        raise ProjectInspectionError("project root does not exist")
    if not root.is_dir():
        raise ProjectInspectionError("project root is not a directory")

    supported_files = 0
    total_files = 0
    visited_entries = 0
    skipped_symlinks = 0
    manifests: list[str] = []
    top_level: list[dict[str, str]] = []
    suffix_counts: dict[str, int] = {}
    truncated = False

    for child in sorted(root.iterdir(), key=lambda item: item.name.lower()):
        if child.is_symlink():
            kind = "symlink"
        elif child.is_dir():
            kind = "directory"
        else:
            kind = "file"
        top_level.append({"name": child.name, "kind": kind})
        if len(top_level) >= 100:
            break

    pending = [root]
    while pending:
        if cancellation_requested is not None and cancellation_requested():
            raise ProjectInspectionError("project inspection cancelled")

        directory = pending.pop()
        try:
            children = sorted(directory.iterdir(), key=lambda item: item.name.lower())
        except OSError as exc:
            raise ProjectInspectionError("project directory cannot be read") from exc

        for child in children:
            visited_entries += 1
            if visited_entries > max_entries:
                truncated = True
                pending.clear()
                break

            relative = child.relative_to(root).as_posix()
            if child.is_symlink():
                skipped_symlinks += 1
                continue
            if child.is_dir():
                if child.name.lower() not in IGNORED_DIR_NAMES:
                    pending.append(child)
                continue
            if not child.is_file():
                continue

            total_files += 1
            lower_name = child.name.lower()
            if lower_name in MANIFEST_NAMES:
                manifests.append(relative)
            if is_supported_text_path(child):
                supported_files += 1
                suffix = child.suffix.lower() or lower_name
                suffix_counts[suffix] = suffix_counts.get(suffix, 0) + 1

    return {
        "root_exists": True,
        "total_files": total_files,
        "supported_files": supported_files,
        "manifest_paths": sorted(manifests)[:100],
        "top_level": top_level,
        "suffix_counts": dict(
            sorted(suffix_counts.items(), key=lambda item: (-item[1], item[0]))[:50]
        ),
        "skipped_symlinks": skipped_symlinks,
        "visited_entries": min(visited_entries, max_entries),
        "truncated": truncated,
    }
