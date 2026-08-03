"""Read-only storage checks for v3 migration and maintenance operations."""
from __future__ import annotations

import os
import shutil
from pathlib import Path
from typing import Any


MINIMUM_SAFETY_BYTES = 64 * 1024 * 1024


class StoragePreflightError(ValueError):
    pass


def preflight_storage_target(
    target_path: str | Path,
    *,
    current_data_root: str | Path,
    legacy_data_root: str | Path,
) -> dict[str, Any]:
    """Inspect a migration target without creating or modifying it."""

    raw_target = str(target_path).strip()
    target = _resolved(raw_target)
    current_root = _resolved(current_data_root)
    legacy_root = _resolved(legacy_data_root)
    checks: list[dict[str, Any]] = []

    _add_check(
        checks,
        "outside_current_v3",
        not _paths_overlap(target, current_root),
        "target must not overlap the current v3 data root",
    )
    _add_check(
        checks,
        "outside_legacy_v2",
        not _paths_overlap(target, legacy_root),
        "target must not overlap the v2 data root",
    )

    target_exists = target.exists()
    target_is_directory = target_exists and target.is_dir()
    target_is_symlink = Path(raw_target).expanduser().is_symlink()
    _add_check(
        checks,
        "target_is_directory",
        not target_exists or target_is_directory,
        "existing target must be a directory",
    )
    _add_check(
        checks,
        "target_is_not_symlink",
        not target_is_symlink,
        "target must not be a symbolic link",
    )

    target_empty = False
    if not target_exists:
        target_empty = True
    elif target_is_directory:
        try:
            target_empty = next(target.iterdir(), None) is None
        except OSError:
            target_empty = False
    _add_check(
        checks,
        "target_is_empty",
        target_empty,
        "migration target must be empty",
    )

    existing_parent = _nearest_existing_parent(target)
    parent_is_directory = existing_parent.is_dir()
    writable = parent_is_directory and os.access(existing_parent, os.W_OK)
    _add_check(
        checks,
        "parent_is_writable",
        writable,
        "nearest existing parent must be a writable directory",
    )

    source_bytes, source_readable = _tree_size(current_root)
    _add_check(
        checks,
        "source_is_readable",
        source_readable,
        "current v3 data root must be a readable directory",
    )
    required_bytes = source_bytes * 2 + MINIMUM_SAFETY_BYTES
    try:
        available_bytes = shutil.disk_usage(existing_parent).free if parent_is_directory else 0
    except OSError:
        available_bytes = 0
    _add_check(
        checks,
        "sufficient_free_space",
        available_bytes >= required_bytes,
        "target volume must have enough space for copy, verification, and safety margin",
    )

    return {
        "ready": all(bool(check["passed"]) for check in checks),
        "target_path": str(target),
        "existing_parent": str(existing_parent),
        "target_exists": target_exists,
        "target_empty": target_empty,
        "source_bytes": source_bytes,
        "required_bytes": required_bytes,
        "available_bytes": available_bytes,
        "checks": checks,
    }


def _resolved(value: str | Path) -> Path:
    raw = str(value).strip()
    if not raw:
        raise StoragePreflightError("storage path must not be empty")
    try:
        return Path(raw).expanduser().resolve(strict=False)
    except (OSError, RuntimeError, ValueError) as exc:
        raise StoragePreflightError("storage path cannot be resolved") from exc


def _paths_overlap(left: Path, right: Path) -> bool:
    return left == right or left in right.parents or right in left.parents


def _nearest_existing_parent(path: Path) -> Path:
    candidate = path
    while not candidate.exists() and candidate != candidate.parent:
        candidate = candidate.parent
    return candidate


def _tree_size(root: Path) -> tuple[int, bool]:
    if not root.exists() or root.is_symlink() or not root.is_dir():
        return 0, False

    total = 0
    readable = True
    stack = [root]
    while stack:
        directory = stack.pop()
        try:
            entries = list(os.scandir(directory))
        except OSError:
            readable = False
            continue
        for entry in entries:
            try:
                if entry.is_symlink():
                    continue
                if entry.is_dir(follow_symlinks=False):
                    stack.append(Path(entry.path))
                elif entry.is_file(follow_symlinks=False):
                    total += entry.stat(follow_symlinks=False).st_size
            except OSError:
                readable = False
                continue
    return total, readable


def _add_check(
    checks: list[dict[str, Any]],
    code: str,
    passed: bool,
    message: str,
) -> None:
    checks.append({"code": code, "passed": bool(passed), "message": message})


__all__ = [
    "MINIMUM_SAFETY_BYTES",
    "StoragePreflightError",
    "preflight_storage_target",
]
