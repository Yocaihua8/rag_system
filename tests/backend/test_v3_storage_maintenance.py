from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
import sqlite3

import pytest

import backend.storage.v3.maintenance as maintenance
from backend.storage.v3.store import AgentStore


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


def _initialized_store(data_root: Path) -> AgentStore:
    store = AgentStore(data_root / "app.db")
    store.initialize()
    store.create_project(
        name="Backup project",
        root_path=data_root,
        idempotency_key="project",
        request_hash="project-hash",
    )
    return store


def test_online_backup_is_consistent_validated_and_idempotent(tmp_path: Path):
    data_root = tmp_path / "v3"
    data_root.mkdir()
    store = _initialized_store(data_root)
    try:
        first = maintenance.create_v3_backup(
            store.db_path,
            current_data_root=data_root,
            backups_dir=data_root / "backups",
            idempotency_key="backup-request-1",
            retention=7,
        )
        replay = maintenance.create_v3_backup(
            store.db_path,
            current_data_root=data_root,
            backups_dir=data_root / "backups",
            idempotency_key="backup-request-1",
            retention=7,
        )
    finally:
        store.close()

    backup = first["backup"]
    backup_dir = data_root / "backups" / backup["backup_id"]
    manifest = maintenance.validate_v3_backup(backup_dir)
    with sqlite3.connect(backup_dir / "app.db") as connection:
        project_count = connection.execute("SELECT COUNT(*) FROM projects").fetchone()[0]

    assert first["replayed"] is False
    assert replay["replayed"] is True
    assert replay["backup"] == backup
    assert manifest["data_generation"] == "v3"
    assert manifest["schema_revision"] == "0001_v3_initial"
    assert project_count == 1
    assert {path.name for path in backup_dir.iterdir()} == {
        "app.db",
        "manifest.json",
        "manifest.sha256",
    }
    assert len(list((data_root / "backups").glob("backup-*"))) == 1


def test_backup_validation_rejects_database_tampering(tmp_path: Path):
    data_root = tmp_path / "v3"
    data_root.mkdir()
    store = _initialized_store(data_root)
    try:
        result = maintenance.create_v3_backup(
            store.db_path,
            current_data_root=data_root,
            backups_dir=data_root / "backups",
            idempotency_key="tamper-test",
        )
    finally:
        store.close()
    backup_dir = data_root / "backups" / result["backup"]["backup_id"]
    with (backup_dir / "app.db").open("ab") as output:
        output.write(b"tampered")

    with pytest.raises(maintenance.BackupValidationError, match="size does not match"):
        maintenance.validate_v3_backup(backup_dir)

    manifest_path = backup_dir / "manifest.json"
    manifest_path.write_text("{}\n", encoding="utf-8")
    with pytest.raises(maintenance.BackupValidationError, match="manifest hash"):
        maintenance.validate_v3_backup(backup_dir)


def test_backup_retention_only_prunes_valid_managed_backups(tmp_path: Path):
    data_root = tmp_path / "v3"
    data_root.mkdir()
    store = _initialized_store(data_root)
    unknown = data_root / "backups" / "user-notes"
    unknown.mkdir(parents=True)
    (unknown / "keep.txt").write_text("keep", encoding="utf-8")
    corrupt = data_root / "backups" / "backup-corrupt"
    corrupt.mkdir()
    (corrupt / "keep.txt").write_text("keep", encoding="utf-8")
    try:
        results = [
            maintenance.create_v3_backup(
                store.db_path,
                current_data_root=data_root,
                backups_dir=data_root / "backups",
                idempotency_key=f"retention-{index}",
                retention=2,
            )
            for index in range(3)
        ]
    finally:
        store.close()

    managed = [
        path
        for path in (data_root / "backups").glob("backup-*")
        if len(path.name) == 39
    ]
    assert len(managed) == 2
    assert results[-1]["pruned_backup_ids"] == [results[0]["backup"]["backup_id"]]
    assert (unknown / "keep.txt").read_text(encoding="utf-8") == "keep"
    assert (corrupt / "keep.txt").read_text(encoding="utf-8") == "keep"
    for directory in managed:
        maintenance.validate_v3_backup(directory)


def test_backup_rejects_unmanaged_backup_directory(tmp_path: Path):
    data_root = tmp_path / "v3"
    data_root.mkdir()
    store = _initialized_store(data_root)
    try:
        with pytest.raises(maintenance.BackupError, match="managed v3 backups"):
            maintenance.create_v3_backup(
                store.db_path,
                current_data_root=data_root,
                backups_dir=tmp_path / "other-backups",
                idempotency_key="wrong-root",
            )
    finally:
        store.close()

    assert not (tmp_path / "other-backups").exists()


def test_restore_replaces_closed_database_and_reinitializes_store(tmp_path: Path):
    data_root = tmp_path / "v3"
    data_root.mkdir()
    store = _initialized_store(data_root)
    backup = maintenance.create_v3_backup(
        store.db_path,
        current_data_root=data_root,
        backups_dir=data_root / "backups",
        idempotency_key="restore-source",
    )["backup"]
    store.create_project(
        name="Created after backup",
        root_path=data_root / "after-backup-project",
        idempotency_key="project-after-backup",
        request_hash="project-after-backup-hash",
    )
    store.checkpoint()
    store.close()

    result = maintenance.restore_v3_backup(
        store.db_path,
        data_root / "backups" / backup["backup_id"],
        expected_backup_sha256=backup["database_sha256"],
        expected_revision="0001_v3_initial",
        activate=store.initialize,
    )
    try:
        projects = store.list_projects()
    finally:
        store.close()

    assert result["restored"] is True
    assert result["database_info"]["data_generation"] == "v3"
    assert [project["name"] for project in projects] == ["Backup project"]
    assert not list(data_root.glob(".app.db.restore-*"))


def test_restore_activation_failure_rolls_back_original_database(tmp_path: Path):
    data_root = tmp_path / "v3"
    data_root.mkdir()
    store = _initialized_store(data_root)
    backup = maintenance.create_v3_backup(
        store.db_path,
        current_data_root=data_root,
        backups_dir=data_root / "backups",
        idempotency_key="rollback-source",
    )["backup"]
    store.create_project(
        name="Must survive rollback",
        root_path=data_root / "rollback-project",
        idempotency_key="rollback-project",
        request_hash="rollback-project-hash",
    )
    store.checkpoint()
    store.close()
    activation_count = 0

    def fail_once_then_initialize():
        nonlocal activation_count
        activation_count += 1
        if activation_count == 1:
            raise RuntimeError("simulated activation failure")
        return store.initialize()

    with pytest.raises(maintenance.RestoreError, match="original database was restored"):
        maintenance.restore_v3_backup(
            store.db_path,
            data_root / "backups" / backup["backup_id"],
            expected_backup_sha256=backup["database_sha256"],
            expected_revision="0001_v3_initial",
            activate=fail_once_then_initialize,
        )
    try:
        project_names = [project["name"] for project in store.list_projects()]
    finally:
        store.close()

    assert activation_count == 2
    assert set(project_names) == {"Backup project", "Must survive rollback"}
    assert not list(data_root.glob(".app.db.restore-*"))
