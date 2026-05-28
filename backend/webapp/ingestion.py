from __future__ import annotations

from pathlib import Path

from backend.webapp.document_processing import process_local_file
from backend.webapp.import_rules import IGNORED_DIR_NAMES, TEXT_SUFFIXES
from backend.webapp.models import ImportResult
from backend.webapp.source_import import VIRTUAL_SOURCE_PREFIXES, virtual_source_relative_paths
from backend.webapp.storage import KnowledgeStore


def preview_import_directory(store: KnowledgeStore, project_id: str, root_path: Path) -> dict[str, object]:
    root = Path(root_path)
    importable = 0
    skipped = 0
    skipped_details: list[dict[str, str]] = []
    protected_relative_paths = virtual_source_relative_paths(store, project_id)

    for path in sorted(root.rglob("*")):
        if _is_in_ignored_dir(path, root):
            continue
        if not path.is_file():
            continue
        relative_path = _safe_relative_path(path, root)
        if path.suffix.lower() not in TEXT_SUFFIXES:
            skipped += 1
            skipped_details.append({"path": relative_path, "reason": "unsupported file type"})
            continue
        if relative_path in protected_relative_paths:
            skipped += 1
            skipped_details.append({"path": relative_path, "reason": "reserved note path"})
            continue
        importable += 1

    return {
        "project_id": project_id,
        "importable": importable,
        "skipped": skipped,
        "skipped_details": skipped_details,
    }


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
    protected_relative_paths = virtual_source_relative_paths(store, project_id)

    for path in _iter_importable_files(root):
        if not path.is_file() or path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        relative_path = _safe_relative_path(path, root)
        if relative_path in protected_relative_paths:
            skipped += 1
            skipped_details.append({"path": relative_path, "reason": "reserved note path"})
            continue
        try:
            processed = process_local_file(path, root)
            if not processed.is_importable:
                skipped += 1
                skipped_details.append({
                    "path": processed.relative_path,
                    "reason": processed.skipped_reason,
                })
                continue
            content = processed.content
            relative_path = processed.relative_path
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

    deleted = store.delete_documents_not_in(
        project_id,
        seen_paths,
        preserve_source_prefixes=VIRTUAL_SOURCE_PREFIXES,
    )
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
