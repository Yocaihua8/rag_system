from __future__ import annotations

from pathlib import Path, PurePosixPath
from typing import Any

from webapp.document_processing import process_uploaded_file
from webapp.import_rules import IGNORED_DIR_NAMES
from webapp.models import ImportResult, Project
from webapp.storage import KnowledgeStore


DEFAULT_BROWSER_PROJECT_NAME = "浏览器导入项目"


def import_uploaded_files(
    store: KnowledgeStore,
    files: list[dict[str, Any]],
    project: Project,
) -> ImportResult:
    imported = 0
    skipped = 0
    created = 0
    updated = 0
    unchanged = 0
    errors: list[str] = []
    skipped_details: list[dict[str, str]] = []
    seen_paths: set[str] = set()

    for entry in files:
        raw_path = str(entry.get("relative_path", ""))
        clean_path, reason = validate_uploaded_relative_path(raw_path)
        if reason:
            skipped += 1
            skipped_details.append({"path": raw_path, "reason": reason})
            continue
        if _is_in_ignored_dir(clean_path):
            skipped += 1
            skipped_details.append({"path": clean_path, "reason": "ignored directory"})
            continue
        processed = process_uploaded_file(clean_path, entry)
        if not processed.is_importable:
            skipped += 1
            skipped_details.append({"path": clean_path, "reason": processed.skipped_reason})
            continue

        seen_paths.add(clean_path)
        source_path = Path(str(project.root_path)) / Path(clean_path)
        result = store.upsert_document(project.id, source_path, clean_path, processed.content)
        if result.action == "created":
            created += 1
        elif result.action == "updated":
            updated += 1
        else:
            unchanged += 1
        imported += 1

    deleted = store.delete_documents_not_in(project.id, seen_paths)
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


def create_browser_upload_project(store: KnowledgeStore, project_name: str) -> Project:
    clean_name = project_name.strip() or DEFAULT_BROWSER_PROJECT_NAME
    return store.create_project(clean_name, Path(f"browser-upload:{clean_name}"))


def is_browser_upload_root(root_path: Path) -> bool:
    return str(root_path).startswith("browser-upload:")


def validate_uploaded_relative_path(raw_path: str) -> tuple[str, str]:
    clean_path = raw_path.replace("\\", "/").lstrip("/")
    if not clean_path:
        return raw_path, "invalid relative path"
    if ":" in clean_path:
        return raw_path, "invalid relative path"
    path = PurePosixPath(clean_path)
    if path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
        return raw_path, "invalid relative path"
    return path.as_posix(), ""


def _is_in_ignored_dir(relative_path: str) -> bool:
    parts = PurePosixPath(relative_path).parts
    return any(part in IGNORED_DIR_NAMES for part in parts[:-1])
