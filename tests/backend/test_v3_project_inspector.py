from __future__ import annotations

from pathlib import Path

import pytest

from backend.runtime.project_inspector import ProjectInspectionError, inspect_project


def _write(path: Path, content: str = "demo") -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def test_inspect_project_returns_relative_metadata_without_file_contents(tmp_path: Path):
    _write(tmp_path / "package.json", '{"name":"demo"}')
    _write(tmp_path / "README.md", "project documentation")
    _write(tmp_path / "src" / "main.py", "print('secret-content')")
    _write(tmp_path / "config" / "pyproject.toml", "[project]")
    _write(tmp_path / "assets" / "logo.bin", "binary-placeholder")

    result = inspect_project(tmp_path)

    assert result == {
        "root_exists": True,
        "total_files": 5,
        "supported_files": 4,
        "manifest_paths": ["config/pyproject.toml", "package.json"],
        "top_level": [
            {"name": "assets", "kind": "directory"},
            {"name": "config", "kind": "directory"},
            {"name": "package.json", "kind": "file"},
            {"name": "README.md", "kind": "file"},
            {"name": "src", "kind": "directory"},
        ],
        "suffix_counts": {
            ".json": 1,
            ".md": 1,
            ".py": 1,
            ".toml": 1,
        },
        "skipped_symlinks": 0,
        "visited_entries": 8,
        "truncated": False,
    }
    assert "secret-content" not in repr(result)
    assert str(tmp_path) not in repr(result)


def test_inspect_project_does_not_descend_into_ignored_directories(tmp_path: Path):
    _write(tmp_path / "src" / "main.py")
    _write(tmp_path / "node_modules" / "dependency" / "package.json")
    _write(tmp_path / ".git" / "hooks" / "pre-commit.py")
    _write(tmp_path / "build" / "generated.py")
    _write(tmp_path / "dist" / "bundle.js")
    _write(tmp_path / ".venv" / "Lib" / "site.py")

    result = inspect_project(tmp_path)

    assert result["total_files"] == 1
    assert result["supported_files"] == 1
    assert result["manifest_paths"] == []
    assert result["suffix_counts"] == {".py": 1}
    assert result["truncated"] is False
    assert {entry["name"] for entry in result["top_level"]} == {
        ".git",
        ".venv",
        "build",
        "dist",
        "node_modules",
        "src",
    }


def test_inspect_project_counts_but_never_follows_directory_symlinks(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    outside = tmp_path.parent / f"{tmp_path.name}-outside"
    _write(outside / "private.py", "must not be scanned")
    link = tmp_path / "linked-outside"

    try:
        link.symlink_to(outside, target_is_directory=True)
    except OSError:
        link.mkdir()
        original_is_symlink = Path.is_symlink

        def fake_is_symlink(path: Path) -> bool:
            if path == link:
                return True
            return original_is_symlink(path)

        monkeypatch.setattr(Path, "is_symlink", fake_is_symlink)

    _write(tmp_path / "local.py")

    result = inspect_project(tmp_path)

    assert result["total_files"] == 1
    assert result["supported_files"] == 1
    assert result["skipped_symlinks"] == 1
    assert "private.py" not in result["manifest_paths"]
    assert {entry["name"]: entry["kind"] for entry in result["top_level"]} == {
        "linked-outside": "symlink",
        "local.py": "file",
    }


def test_inspect_project_stops_at_entry_limit_and_marks_result_truncated(tmp_path: Path):
    for index in range(10):
        _write(tmp_path / f"file-{index:02d}.py")

    result = inspect_project(tmp_path, max_entries=3)

    assert result["visited_entries"] == 3
    assert result["total_files"] == 3
    assert result["supported_files"] == 3
    assert result["suffix_counts"] == {".py": 3}
    assert result["truncated"] is True


def test_inspect_project_honors_cancellation_before_scanning(tmp_path: Path):
    _write(tmp_path / "main.py")
    cancellation_checks = 0

    def cancellation_requested() -> bool:
        nonlocal cancellation_checks
        cancellation_checks += 1
        return True

    with pytest.raises(ProjectInspectionError, match="project inspection cancelled"):
        inspect_project(tmp_path, cancellation_requested=cancellation_requested)

    assert cancellation_checks == 1


def test_inspect_project_rejects_missing_and_non_directory_roots(tmp_path: Path):
    missing = tmp_path / "missing"
    regular_file = _write(tmp_path / "project.txt")

    with pytest.raises(ProjectInspectionError, match="project root does not exist"):
        inspect_project(missing)

    with pytest.raises(ProjectInspectionError, match="project root is not a directory"):
        inspect_project(regular_file)


def test_inspect_project_rejects_non_positive_entry_limit(tmp_path: Path):
    with pytest.raises(ValueError, match="max_entries must be positive"):
        inspect_project(tmp_path, max_entries=0)
