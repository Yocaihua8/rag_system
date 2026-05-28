from __future__ import annotations

import hashlib
import re
from pathlib import Path

from backend.webapp.import_rules import MAX_TEXT_FILE_BYTES
from backend.webapp.models import ImportResult
from backend.webapp.storage import DocumentWriteResult, KnowledgeStore

NOTE_SOURCE_PREFIX = "note:"
NOTE_RELATIVE_PREFIX = "notes/"
URL_SOURCE_PREFIX = "url:"
URL_RELATIVE_PREFIX = "urls/"
VIRTUAL_SOURCE_PREFIXES = (NOTE_SOURCE_PREFIX, URL_SOURCE_PREFIX)


def import_plain_text_note(
    store: KnowledgeStore,
    project_id: str,
    title: object,
    content: object,
) -> tuple[DocumentWriteResult, ImportResult]:
    if not isinstance(title, str):
        raise ValueError("title is required")
    if not isinstance(content, str):
        raise ValueError("content is required")
    clean_title = title.strip()
    clean_content = content.strip()
    if not clean_title:
        raise ValueError("title is required")
    if not clean_content:
        raise ValueError("content is required")
    if len(clean_content.encode("utf-8")) > MAX_TEXT_FILE_BYTES:
        raise ValueError("content is too large")

    note_id = _note_id(clean_title)
    relative_path = f"{NOTE_RELATIVE_PREFIX}{_safe_slug(clean_title)}-{note_id}.txt"
    source_path = Path(f"{NOTE_SOURCE_PREFIX}{project_id}/{note_id}")
    write_result = store.upsert_document(project_id, source_path, relative_path, clean_content)
    return write_result, _result_for_action(write_result.action)


def import_url_excerpt(
    store: KnowledgeStore,
    project_id: str,
    url: object,
    title: object,
    content: object,
) -> tuple[DocumentWriteResult, ImportResult]:
    if not isinstance(url, str):
        raise ValueError("url is required")
    if not isinstance(title, str):
        raise ValueError("title is required")
    if not isinstance(content, str):
        raise ValueError("content is required")
    clean_url = url.strip()
    clean_title = title.strip()
    clean_content = content.strip()
    if not clean_url:
        raise ValueError("url is required")
    if not clean_url.startswith(("http://", "https://")):
        raise ValueError("url must start with http:// or https://")
    if not clean_title:
        raise ValueError("title is required")
    if not clean_content:
        raise ValueError("content is required")

    body = f"标题：{clean_title}\n来源 URL：{clean_url}\n\n{clean_content}"
    if len(body.encode("utf-8")) > MAX_TEXT_FILE_BYTES:
        raise ValueError("content is too large")

    url_id = _note_id(clean_url)
    relative_path = f"{URL_RELATIVE_PREFIX}{url_id}.txt"
    source_path = Path(f"{URL_SOURCE_PREFIX}{clean_url}")
    write_result = store.upsert_document(project_id, source_path, relative_path, body)
    return write_result, _result_for_action(write_result.action)


def is_virtual_source_path(source_path: str) -> bool:
    return source_path.startswith(VIRTUAL_SOURCE_PREFIXES)


def virtual_source_relative_paths(store: KnowledgeStore, project_id: str) -> set[str]:
    return {
        document.relative_path
        for document in store.list_documents(project_id)
        if is_virtual_source_path(str(document.source_path))
    }


def _note_id(title: str) -> str:
    return hashlib.sha256(title.casefold().encode("utf-8")).hexdigest()[:12]


def _safe_slug(title: str) -> str:
    slug = re.sub(r"[^0-9A-Za-z\u4e00-\u9fff_-]+", "-", title.strip()).strip("-")
    return slug[:40] or "note"


def _result_for_action(action: str) -> ImportResult:
    return ImportResult(
        imported=1,
        skipped=0,
        errors=[],
        skipped_details=[],
        created=1 if action == "created" else 0,
        updated=1 if action == "updated" else 0,
        unchanged=1 if action == "unchanged" else 0,
        deleted=0,
    )
