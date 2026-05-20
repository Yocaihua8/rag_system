from __future__ import annotations

from pathlib import Path

from webapp.import_rules import IGNORED_DIR_NAMES, MAX_TEXT_FILE_BYTES, TEXT_SUFFIXES
from webapp.models import ImportResult
from webapp.storage import KnowledgeStore


def import_directory(store: KnowledgeStore, project_id: str, root_path: Path) -> ImportResult:
    root = Path(root_path)
    imported = 0
    skipped = 0
    created = 0
    updated = 0
    unchanged = 0
    errors: list[str] = []
    skipped_details: list[dict[str, str]] = []
    seen_paths: set[str] = set()

    for path in _iter_importable_files(root):
        if not path.is_file() or path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        try:
            if path.stat().st_size > MAX_TEXT_FILE_BYTES:
                skipped += 1
                skipped_details.append({
                    "path": path.relative_to(root).as_posix(),
                    "reason": "file too large",
                })
                continue
            content = path.read_text(encoding="utf-8", errors="ignore")
            relative_path = path.relative_to(root).as_posix()
            seen_paths.add(relative_path)
            result = store.upsert_document(project_id, path, relative_path, content)
            if result.action == "created":
                created += 1
            elif result.action == "updated":
                updated += 1
            else:
                unchanged += 1
            imported += 1
        except OSError as exc:
            skipped += 1
            relative_path = _safe_relative_path(path, root)
            errors.append(f"{relative_path}: {exc}")
            skipped_details.append({"path": relative_path, "reason": str(exc)})

    deleted = store.delete_documents_not_in(project_id, seen_paths)
    return ImportResult(
        imported=imported,
        skipped=skipped,
        errors=errors,
        skipped_details=skipped_details,
        created=created,
        updated=updated,
        unchanged=unchanged,
        deleted=deleted,
    )


def _iter_importable_files(root: Path):
    for path in sorted(root.rglob("*")):
        if _is_in_ignored_dir(path, root):
            continue
        yield path


def _is_in_ignored_dir(path: Path, root: Path) -> bool:
    try:
        relative_parts = path.relative_to(root).parts
    except ValueError:
        return True
    return any(part in IGNORED_DIR_NAMES for part in relative_parts[:-1])


def _safe_relative_path(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return str(path)
