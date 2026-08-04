"""Read-only storage checks for v3 migration and maintenance operations."""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import sqlite3
import threading
import uuid
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable


MINIMUM_SAFETY_BYTES = 64 * 1024 * 1024
BACKUP_FORMAT_VERSION = 1
_BACKUP_LOCK = threading.Lock()


class StoragePreflightError(ValueError):
    pass


class BackupError(RuntimeError):
    pass


class BackupValidationError(BackupError):
    pass


class RestoreError(RuntimeError):
    pass


class RestoreRollbackError(RestoreError):
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


def create_v3_backup(
    source_db_path: str | Path,
    *,
    current_data_root: str | Path,
    backups_dir: str | Path,
    idempotency_key: str,
    retention: int = 7,
) -> dict[str, Any]:
    """Create, validate, and atomically publish an online SQLite backup."""

    clean_key = str(idempotency_key).strip()
    if not clean_key or len(clean_key) > 200:
        raise BackupError("idempotency key must contain between 1 and 200 characters")
    if retention < 1 or retention > 100:
        raise BackupError("backup retention must be between 1 and 100")

    source = _resolved(source_db_path)
    current_root = _resolved(current_data_root)
    backup_root_input = Path(str(backups_dir).strip()).expanduser()
    backup_root = _resolved(backup_root_input)
    expected_backup_root = (current_root / "backups").resolve(strict=False)
    if backup_root != expected_backup_root:
        raise BackupError("backup directory must be the managed v3 backups directory")
    if backup_root_input.is_symlink():
        raise BackupError("backup directory must not be a symbolic link")
    if not current_root.is_dir():
        raise BackupError("current v3 data root is not a directory")
    if not source.is_file() or Path(str(source_db_path)).expanduser().is_symlink():
        raise BackupError("source v3 database must be a regular non-symlink file")

    key_hash = _sha256_bytes(clean_key.encode("utf-8"))
    backup_id = f"backup-{key_hash[:32]}"
    final_dir = backup_root / backup_id

    with _BACKUP_LOCK:
        backup_root.mkdir(parents=False, exist_ok=True)
        if not backup_root.is_dir() or backup_root.is_symlink():
            raise BackupError("managed v3 backup directory is invalid")
        if final_dir.exists():
            manifest = validate_v3_backup(final_dir)
            if manifest["idempotency_key_hash"] != key_hash:
                raise BackupValidationError("backup idempotency identity does not match")
            pruned = _prune_managed_backups(backup_root, retention=retention)
            return {
                "backup": _backup_summary(manifest),
                "replayed": True,
                "pruned_backup_ids": pruned,
            }

        staging_dir = backup_root / f".{backup_id}.tmp-{uuid.uuid4().hex}"
        staging_dir.mkdir(parents=False, exist_ok=False)
        try:
            source_identity = _database_identity(source, verify_integrity=False)
            destination = staging_dir / "app.db"
            with closing(sqlite3.connect(source, timeout=30)) as source_connection:
                with closing(
                    sqlite3.connect(destination, timeout=30)
                ) as destination_connection:
                    source_connection.backup(destination_connection)
                    destination_connection.commit()
                    journal_mode = destination_connection.execute(
                        "PRAGMA journal_mode = DELETE"
                    ).fetchone()
                    if not journal_mode or str(journal_mode[0]).lower() != "delete":
                        raise BackupValidationError(
                            "backup database could not be made self-contained"
                        )

            created_at = (
                datetime.now(timezone.utc).isoformat(timespec="microseconds")
                .replace("+00:00", "Z")
            )
            manifest = {
                "format_version": BACKUP_FORMAT_VERSION,
                "backup_id": backup_id,
                "created_at": created_at,
                "data_generation": source_identity["data_generation"],
                "schema_revision": source_identity["schema_revision"],
                "database_file": "app.db",
                "database_bytes": destination.stat().st_size,
                "database_sha256": _sha256_file(destination),
                "idempotency_key_hash": key_hash,
            }
            manifest_bytes = (
                json.dumps(manifest, ensure_ascii=False, sort_keys=True, indent=2)
                + "\n"
            ).encode("utf-8")
            (staging_dir / "manifest.json").write_bytes(manifest_bytes)
            (staging_dir / "manifest.sha256").write_text(
                f"{_sha256_bytes(manifest_bytes)}  manifest.json\n",
                encoding="ascii",
            )
            validate_v3_backup(
                staging_dir,
                expected_generation=source_identity["data_generation"],
                expected_revision=source_identity["schema_revision"],
                expected_backup_id=backup_id,
            )
            staging_dir.rename(final_dir)
        except BaseException:
            if staging_dir.exists() and staging_dir.parent == backup_root:
                shutil.rmtree(staging_dir)
            raise

        validated = validate_v3_backup(final_dir)
        pruned = _prune_managed_backups(backup_root, retention=retention)
        return {
            "backup": _backup_summary(validated),
            "replayed": False,
            "pruned_backup_ids": pruned,
        }


def validate_v3_backup(
    backup_dir: str | Path,
    *,
    expected_generation: str = "v3",
    expected_revision: str | None = None,
    expected_backup_id: str | None = None,
) -> dict[str, Any]:
    candidate = Path(str(backup_dir).strip()).expanduser()
    if candidate.is_symlink():
        raise BackupValidationError("backup directory must not be a symbolic link")
    directory = candidate.resolve(strict=False)
    if not directory.is_dir():
        raise BackupValidationError("backup directory does not exist")

    database_path = directory / "app.db"
    manifest_path = directory / "manifest.json"
    manifest_hash_path = directory / "manifest.sha256"
    for path in (database_path, manifest_path, manifest_hash_path):
        if not path.is_file() or path.is_symlink():
            raise BackupValidationError(f"backup file is missing or invalid: {path.name}")

    try:
        manifest_bytes = manifest_path.read_bytes()
        expected_manifest_hash = manifest_hash_path.read_text(encoding="ascii").split()[0]
        manifest = json.loads(manifest_bytes.decode("utf-8"))
    except (OSError, UnicodeError, ValueError, json.JSONDecodeError, IndexError) as exc:
        raise BackupValidationError("backup manifest is unreadable") from exc
    if _sha256_bytes(manifest_bytes) != expected_manifest_hash:
        raise BackupValidationError("backup manifest hash does not match")
    if not isinstance(manifest, dict) or manifest.get("format_version") != 1:
        raise BackupValidationError("backup manifest format is unsupported")
    backup_id = str(manifest.get("backup_id") or "")
    if not (
        backup_id.startswith("backup-")
        and len(backup_id) == 39
        and all(character in "0123456789abcdef" for character in backup_id[7:])
    ):
        raise BackupValidationError("backup id is invalid")
    if manifest.get("backup_id") != (expected_backup_id or directory.name):
        raise BackupValidationError("backup id does not match its directory")
    if manifest.get("database_file") != "app.db":
        raise BackupValidationError("backup database filename is invalid")
    if database_path.stat().st_size != manifest.get("database_bytes"):
        raise BackupValidationError("backup database size does not match")
    if not _is_hex_digest(manifest.get("database_sha256")):
        raise BackupValidationError("backup database hash is invalid")
    if _sha256_file(database_path) != manifest.get("database_sha256"):
        raise BackupValidationError("backup database hash does not match")
    try:
        created_at = datetime.fromisoformat(str(manifest["created_at"]).replace("Z", "+00:00"))
    except (KeyError, ValueError) as exc:
        raise BackupValidationError("backup creation time is invalid") from exc
    if created_at.tzinfo is None or created_at.utcoffset() != timezone.utc.utcoffset(created_at):
        raise BackupValidationError("backup creation time must use UTC")

    identity = _database_identity(database_path, verify_integrity=True)
    if identity["data_generation"] != expected_generation:
        raise BackupValidationError("backup data generation does not match")
    if manifest.get("data_generation") != identity["data_generation"]:
        raise BackupValidationError("backup manifest generation does not match database")
    if manifest.get("schema_revision") != identity["schema_revision"]:
        raise BackupValidationError("backup manifest revision does not match database")
    if expected_revision is not None and identity["schema_revision"] != expected_revision:
        raise BackupValidationError("backup schema revision does not match expected revision")
    if not _is_hex_digest(manifest.get("idempotency_key_hash")):
        raise BackupValidationError("backup idempotency hash is invalid")
    return manifest


def restore_v3_backup(
    source_db_path: str | Path,
    backup_dir: str | Path,
    *,
    expected_backup_sha256: str,
    expected_revision: str,
    activate: Callable[[], dict[str, Any]],
) -> dict[str, Any]:
    """Replace a closed v3 database and roll back if activation fails."""

    source = _resolved(source_db_path)
    raw_source = Path(str(source_db_path).strip()).expanduser()
    if raw_source.is_symlink() or not source.is_file():
        raise RestoreError("current v3 database must be a regular non-symlink file")
    if not _is_hex_digest(expected_backup_sha256):
        raise RestoreError("expected backup database hash is invalid")

    manifest = validate_v3_backup(
        backup_dir,
        expected_generation="v3",
        expected_revision=expected_revision,
    )
    if manifest["database_sha256"] != expected_backup_sha256:
        raise RestoreError("selected backup hash does not match confirmation")
    _database_identity(source, verify_integrity=True)

    operation_id = uuid.uuid4().hex
    stage = source.parent / f".{source.name}.restore-stage-{operation_id}"
    rollback = source.parent / f".{source.name}.restore-rollback-{operation_id}"
    backup_database = Path(backup_dir).expanduser().resolve() / "app.db"
    moved_sidecars: list[tuple[Path, Path]] = []
    activated = False
    try:
        shutil.copyfile(backup_database, stage)
        if _sha256_file(stage) != expected_backup_sha256:
            raise RestoreError("staged backup hash does not match confirmation")
        staged_identity = _database_identity(stage, verify_integrity=True)
        if staged_identity["schema_revision"] != expected_revision:
            raise RestoreError("staged backup revision does not match application head")

        os.replace(source, rollback)
        for suffix in ("-wal", "-shm"):
            sidecar = Path(f"{source}{suffix}")
            if sidecar.exists():
                rollback_sidecar = Path(f"{rollback}{suffix}")
                os.replace(sidecar, rollback_sidecar)
                moved_sidecars.append((rollback_sidecar, sidecar))
        os.replace(stage, source)
        try:
            database_info = activate()
            activated = True
        except BaseException as activation_error:
            failed = source.parent / f".{source.name}.restore-failed-{operation_id}"
            if source.exists():
                os.replace(source, failed)
            os.replace(rollback, source)
            for rollback_sidecar, original_sidecar in moved_sidecars:
                if rollback_sidecar.exists():
                    os.replace(rollback_sidecar, original_sidecar)
            try:
                activate()
            except BaseException as rollback_error:
                raise RestoreRollbackError(
                    "restored database failed and original database could not be reactivated"
                ) from rollback_error
            finally:
                if failed.exists():
                    failed.unlink()
            raise RestoreError(
                "restored database failed activation; original database was restored"
            ) from activation_error

        if rollback.exists():
            rollback.unlink()
        for rollback_sidecar, _original_sidecar in moved_sidecars:
            if rollback_sidecar.exists():
                rollback_sidecar.unlink()
        return {
            "backup": _backup_summary(manifest),
            "database_info": database_info,
            "restored": True,
        }
    except RestoreError:
        if stage.exists():
            stage.unlink()
        raise
    except (OSError, sqlite3.DatabaseError) as exc:
        if stage.exists():
            stage.unlink()
        if rollback.exists() and not activated:
            if source.exists():
                source.unlink()
            os.replace(rollback, source)
            for rollback_sidecar, original_sidecar in moved_sidecars:
                if rollback_sidecar.exists():
                    os.replace(rollback_sidecar, original_sidecar)
            try:
                activate()
            except BaseException as rollback_error:
                raise RestoreRollbackError(
                    "restore operation failed and original database could not be reactivated"
                ) from rollback_error
        raise RestoreError("v3 restore filesystem or SQLite operation failed") from exc


def _database_identity(db_path: Path, *, verify_integrity: bool) -> dict[str, str]:
    try:
        suffix = "?mode=ro&immutable=1" if verify_integrity else "?mode=ro"
        uri = f"{db_path.resolve().as_uri()}{suffix}"
        with closing(sqlite3.connect(uri, uri=True, timeout=30)) as connection:
            if verify_integrity:
                integrity_rows = connection.execute("PRAGMA integrity_check").fetchall()
                if integrity_rows != [("ok",)]:
                    raise BackupValidationError("backup SQLite integrity check failed")
            generation_row = connection.execute(
                "SELECT value FROM app_metadata WHERE key = 'data_generation'"
            ).fetchone()
            revision_row = connection.execute(
                "SELECT version_num FROM alembic_version"
            ).fetchone()
    except BackupValidationError:
        raise
    except (OSError, sqlite3.DatabaseError) as exc:
        raise BackupValidationError("backup is not a readable v3 SQLite database") from exc
    generation = str(generation_row[0]) if generation_row else ""
    revision = str(revision_row[0]) if revision_row else ""
    if generation != "v3" or not revision:
        raise BackupValidationError("backup is missing v3 generation or revision state")
    return {"data_generation": generation, "schema_revision": revision}


def _prune_managed_backups(backup_root: Path, *, retention: int) -> list[str]:
    managed: list[tuple[str, str, Path]] = []
    for child in backup_root.iterdir():
        if not child.name.startswith("backup-") or child.is_symlink():
            continue
        try:
            manifest = validate_v3_backup(child)
        except BackupValidationError:
            continue
        managed.append((str(manifest["created_at"]), str(manifest["backup_id"]), child))
    managed.sort()
    pruned: list[str] = []
    for _created_at, backup_id, directory in managed[:-retention]:
        if directory.parent == backup_root and directory.name == backup_id:
            shutil.rmtree(directory)
            pruned.append(backup_id)
    return pruned


def _backup_summary(manifest: dict[str, Any]) -> dict[str, Any]:
    return {
        key: manifest[key]
        for key in (
            "backup_id",
            "created_at",
            "data_generation",
            "schema_revision",
            "database_bytes",
            "database_sha256",
        )
    }


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _is_hex_digest(value: object) -> bool:
    text = str(value or "")
    return len(text) == 64 and all(character in "0123456789abcdef" for character in text)


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
    "BACKUP_FORMAT_VERSION",
    "BackupError",
    "BackupValidationError",
    "MINIMUM_SAFETY_BYTES",
    "StoragePreflightError",
    "RestoreError",
    "RestoreRollbackError",
    "create_v3_backup",
    "preflight_storage_target",
    "restore_v3_backup",
    "validate_v3_backup",
]
