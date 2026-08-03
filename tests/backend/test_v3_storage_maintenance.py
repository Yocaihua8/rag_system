from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

import backend.storage.v3.maintenance as maintenance


def _check(result: dict, code: str) -> bool:
    return next(item["passed"] for item in result["checks"] if item["code"] == code)


def test_preflight_accepts_empty_isolated_target_without_creating_it(tmp_path: Path):
    current = tmp_path / "runtime" / "v3"
    legacy = tmp_path / "runtime" / "v2"
    target = tmp_path / "new-location" / "knowledge-island-v3"
    current.mkdir(parents=True)
    legacy.mkdir(parents=True)
    (current / "app.db").write_bytes(b"v3-data")

    result = maintenance.preflight_storage_target(
        target,
        current_data_root=current,
        legacy_data_root=legacy,
    )

    assert result["ready"] is True
    assert result["target_path"] == str(target.resolve())
    assert result["target_exists"] is False
    assert result["source_bytes"] == len(b"v3-data")
    assert result["required_bytes"] == len(b"v3-data") * 2 + 64 * 1024 * 1024
    assert not target.exists()
    assert all(check["passed"] for check in result["checks"])


def test_preflight_rejects_current_v3_and_legacy_v2_overlaps(tmp_path: Path):
    current = tmp_path / "runtime" / "v3"
    legacy = tmp_path / "runtime" / "v2"
    current.mkdir(parents=True)
    legacy.mkdir(parents=True)

    inside_current = maintenance.preflight_storage_target(
        current / "moved",
        current_data_root=current,
        legacy_data_root=legacy,
    )
    parent_of_legacy = maintenance.preflight_storage_target(
        tmp_path / "runtime",
        current_data_root=current,
        legacy_data_root=legacy,
    )

    assert inside_current["ready"] is False
    assert _check(inside_current, "outside_current_v3") is False
    assert parent_of_legacy["ready"] is False
    assert _check(parent_of_legacy, "outside_legacy_v2") is False


def test_preflight_rejects_nonempty_or_non_directory_target(tmp_path: Path):
    current = tmp_path / "current"
    legacy = tmp_path / "legacy"
    current.mkdir()
    legacy.mkdir()
    nonempty = tmp_path / "nonempty"
    nonempty.mkdir()
    (nonempty / "keep.txt").write_text("keep", encoding="utf-8")
    file_target = tmp_path / "file-target"
    file_target.write_text("keep", encoding="utf-8")

    nonempty_result = maintenance.preflight_storage_target(
        nonempty,
        current_data_root=current,
        legacy_data_root=legacy,
    )
    file_result = maintenance.preflight_storage_target(
        file_target,
        current_data_root=current,
        legacy_data_root=legacy,
    )

    assert nonempty_result["ready"] is False
    assert _check(nonempty_result, "target_is_empty") is False
    assert file_result["ready"] is False
    assert _check(file_result, "target_is_directory") is False


def test_preflight_rejects_symbolic_link_target(tmp_path: Path):
    current = tmp_path / "current"
    legacy = tmp_path / "legacy"
    real_target = tmp_path / "real-target"
    linked_target = tmp_path / "linked-target"
    current.mkdir()
    legacy.mkdir()
    real_target.mkdir()
    try:
        linked_target.symlink_to(real_target, target_is_directory=True)
    except OSError as exc:
        pytest.skip(f"directory symlinks are unavailable: {exc}")

    result = maintenance.preflight_storage_target(
        linked_target,
        current_data_root=current,
        legacy_data_root=legacy,
    )

    assert result["ready"] is False
    assert _check(result, "target_is_not_symlink") is False


def test_preflight_rejects_insufficient_space_without_writing(
    monkeypatch,
    tmp_path: Path,
):
    current = tmp_path / "current"
    legacy = tmp_path / "legacy"
    target = tmp_path / "target"
    current.mkdir()
    legacy.mkdir()
    monkeypatch.setattr(
        maintenance.shutil,
        "disk_usage",
        lambda _path: SimpleNamespace(total=100, used=100, free=0),
    )

    result = maintenance.preflight_storage_target(
        target,
        current_data_root=current,
        legacy_data_root=legacy,
    )

    assert result["ready"] is False
    assert result["available_bytes"] == 0
    assert _check(result, "sufficient_free_space") is False
    assert not target.exists()
