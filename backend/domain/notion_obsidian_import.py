from __future__ import annotations

import base64
import binascii
import io
from pathlib import Path, PurePosixPath
from zipfile import BadZipFile, ZipFile

from backend.domain.document_processing import process_bytes, process_local_file
from backend.domain.import_rules import IGNORED_DIR_NAMES, MAX_TEXT_FILE_BYTES, TEXT_SUFFIXES
from backend.domain.models import ImportResult
from backend.storage import KnowledgeStore

NOTION_SOURCE_PREFIX = "notion-zip:"
OBSIDIAN_SOURCE_PREFIX = "obsidian-vault:"


def import_notion_zip(
    store: KnowledgeStore,
    project_id: str,
    filename: object,
    content_base64: object,
) -> ImportResult:
    clean_filename = _clean_zip_filename(filename)
    data = _decode_zip_content(content_base64)

    imported = 0
    skipped = 0
    created = 0
    updated = 0
    unchanged = 0
    errors: list[str] = []
    skipped_details: list[dict[str, str]] = []

    try:
        with ZipFile(io.BytesIO(data)) as archive:
            for entry in sorted(archive.infolist(), key=lambda item: item.filename):
                if entry.is_dir():
                    continue
                relative_path, reason = _validate_relative_path(entry.filename)
                if reason:
                    skipped += 1
                    skipped_details.append({"path": entry.filename, "reason": reason})
                    continue
                if _is_in_ignored_dir(relative_path):
                    continue
                if PurePosixPath(relative_path).suffix.lower() not in TEXT_SUFFIXES:
                    skipped += 1
                    skipped_details.append({"path": relative_path, "reason": "unsupported file type"})
                    continue
                if entry.file_size > MAX_TEXT_FILE_BYTES:
                    skipped += 1
                    skipped_details.append({"path": relative_path, "reason": "file too large"})
                    continue
                try:
                    processed = process_bytes(relative_path, archive.read(entry))
                except OSError as exc:
                    skipped += 1
                    errors.append(f"{relative_path}: {exc}")
                    skipped_details.append({"path": relative_path, "reason": str(exc)})
                    continue
                if not processed.is_importable:
                    skipped += 1
                    skipped_details.append({"path": relative_path, "reason": processed.skipped_reason})
                    continue
                result = store.upsert_document(
                    project_id,
                    Path(f"{NOTION_SOURCE_PREFIX}{clean_filename}#{relative_path}"),
                    _prefixed_relative_path("notion", processed.relative_path),
                    processed.content,
                )
                created, updated, unchanged = _count_action(result.action, created, updated, unchanged)
                imported += 1
    except BadZipFile as exc:
        raise ValueError("invalid notion zip") from exc

    return ImportResult(
        imported=imported,
        skipped=skipped,
        errors=errors,
        skipped_details=skipped_details,
        created=created,
        updated=updated,
        unchanged=unchanged,
        deleted=0,
    )


def import_obsidian_vault(
    store: KnowledgeStore,
    project_id: str,
    vault_path: object,
) -> ImportResult:
    if not isinstance(vault_path, str) or not vault_path.strip():
        raise ValueError("vault_path is required")
    root = Path(vault_path.strip()).expanduser()
    if not root.exists() or not root.is_dir():
        raise ValueError("obsidian vault path does not exist")

    imported = 0
    skipped = 0
    created = 0
    updated = 0
    unchanged = 0
    errors: list[str] = []
    skipped_details: list[dict[str, str]] = []

    for path in sorted(root.rglob("*")):
        if not path.is_file() or _is_path_in_ignored_dir(path, root):
            continue
        relative_path = path.relative_to(root).as_posix()
        if path.suffix.lower() not in TEXT_SUFFIXES:
            skipped += 1
            skipped_details.append({"path": relative_path, "reason": "unsupported file type"})
            continue
        try:
            processed = process_local_file(path, root)
        except OSError as exc:
            skipped += 1
            errors.append(f"{relative_path}: {exc}")
            skipped_details.append({"path": relative_path, "reason": str(exc)})
            continue
        if not processed.is_importable:
            skipped += 1
            skipped_details.append({"path": processed.relative_path, "reason": processed.skipped_reason})
            continue
        result = store.upsert_document(
            project_id,
            Path(f"{OBSIDIAN_SOURCE_PREFIX}{root.as_posix()}#{processed.relative_path}"),
            _prefixed_relative_path("obsidian", processed.relative_path),
            processed.content,
        )
        created, updated, unchanged = _count_action(result.action, created, updated, unchanged)
        imported += 1

    return ImportResult(
        imported=imported,
        skipped=skipped,
        errors=errors,
        skipped_details=skipped_details,
        created=created,
        updated=updated,
        unchanged=unchanged,
        deleted=0,
    )


def _clean_zip_filename(filename: object) -> str:
    if not isinstance(filename, str) or not filename.strip():
        raise ValueError("filename is required")
    clean_filename = Path(filename.strip()).name
    if PurePosixPath(clean_filename).suffix.lower() != ".zip":
        raise ValueError("filename must end with .zip")
    return clean_filename


def _decode_zip_content(content_base64: object) -> bytes:
    if not isinstance(content_base64, str) or not content_base64.strip():
        raise ValueError("content_base64 is required")
    try:
        return base64.b64decode(content_base64, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise ValueError("content_base64 is invalid") from exc


def _validate_relative_path(raw_path: str) -> tuple[str, str]:
    clean_path = raw_path.replace("\\", "/").lstrip("/")
    if not clean_path:
        return raw_path, "invalid relative path"
    if ":" in clean_path:
        return raw_path, "invalid relative path"
    path = PurePosixPath(clean_path)
    if path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
        return raw_path, "invalid relative path"
    return path.as_posix(), ""


def _prefixed_relative_path(prefix: str, relative_path: str) -> str:
    return f"{prefix}/{relative_path.strip('/')}"


def _is_in_ignored_dir(relative_path: str) -> bool:
    parts = PurePosixPath(relative_path).parts
    return any(part in IGNORED_DIR_NAMES for part in parts[:-1])


def _is_path_in_ignored_dir(path: Path, root: Path) -> bool:
    try:
        parts = path.relative_to(root).parts
    except ValueError:
        return True
    return any(part in IGNORED_DIR_NAMES or part in {".obsidian", ".trash"} for part in parts[:-1])


def _count_action(action: str, created: int, updated: int, unchanged: int) -> tuple[int, int, int]:
    if action == "created":
        created += 1
    elif action == "updated":
        updated += 1
    else:
        unchanged += 1
    return created, updated, unchanged
