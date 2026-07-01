from __future__ import annotations

import hashlib
import ipaddress
import re
from pathlib import Path
from urllib.parse import urlparse

from backend.domain.import_rules import MAX_TEXT_FILE_BYTES
from backend.domain.models import ImportResult
from backend.storage import DocumentWriteResult, KnowledgeStore

NOTE_SOURCE_PREFIX = "note:"
NOTE_RELATIVE_PREFIX = "notes/"
URL_SOURCE_PREFIX = "url:"
URL_RELATIVE_PREFIX = "urls/"
WEB_SOURCE_PREFIX = "web:"
WEB_RELATIVE_PREFIX = "web/"
NOTION_SOURCE_PREFIX = "notion-zip:"
OBSIDIAN_SOURCE_PREFIX = "obsidian-vault:"
VIRTUAL_SOURCE_PREFIXES = (
    NOTE_SOURCE_PREFIX,
    URL_SOURCE_PREFIX,
    WEB_SOURCE_PREFIX,
    NOTION_SOURCE_PREFIX,
    OBSIDIAN_SOURCE_PREFIX,
)


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


def import_web_fetch_result(
    store: KnowledgeStore,
    project_id: str,
    preview: object,
) -> tuple[DocumentWriteResult, ImportResult]:
    if not isinstance(preview, dict):
        raise ValueError("preview is required")

    clean_url = _web_commit_url(preview.get("url"), "url")
    final_url = _web_commit_url(preview.get("final_url"), "final_url")
    title = _required_text(preview.get("title"), "title")
    content = _required_text(preview.get("content"), "content")
    fetched_at = _required_text(preview.get("fetched_at"), "fetched_at")
    content_type = _required_text(preview.get("content_type"), "content_type")
    content_hash = _required_text(preview.get("content_hash"), "content_hash")
    extractor_version = str(preview.get("extractor_version", "static-html-v1")).strip() or "static-html-v1"
    if preview.get("robots_allowed") is not True:
        raise ValueError("robots approval is required")

    content_bytes = content.encode("utf-8")
    if hashlib.sha256(content_bytes).hexdigest() != content_hash:
        raise ValueError("content hash does not match")
    try:
        content_length = int(preview.get("content_length", len(content_bytes)))
    except (TypeError, ValueError) as exc:
        raise ValueError("content_length is invalid") from exc
    if content_length != len(content_bytes):
        raise ValueError("content length does not match")

    body = (
        f"标题：{title}\n"
        f"来源 URL：{clean_url}\n"
        f"最终 URL：{final_url}\n"
        f"抓取时间：{fetched_at}\n"
        f"内容类型：{content_type}\n"
        f"内容哈希：{content_hash}\n"
        f"抽取器：{extractor_version}\n\n"
        f"{content}"
    )
    if len(body.encode("utf-8")) > MAX_TEXT_FILE_BYTES:
        raise ValueError("content is too large")

    web_id = _note_id(clean_url)
    relative_path = f"{WEB_RELATIVE_PREFIX}{web_id}.txt"
    source_path = Path(f"{WEB_SOURCE_PREFIX}{clean_url}")
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


def _required_text(value: object, field: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{field} is required")
    clean_value = value.strip()
    if not clean_value:
        raise ValueError(f"{field} is required")
    return clean_value


def _web_commit_url(value: object, field: str) -> str:
    clean_url = _required_text(value, field)
    try:
        parsed = urlparse(clean_url)
        port = parsed.port
    except ValueError as exc:
        raise ValueError(f"{field} is invalid") from exc
    if parsed.scheme not in {"http", "https"}:
        raise ValueError(f"{field} must use http or https")
    if parsed.username or parsed.password:
        raise ValueError("URL credentials are not allowed")
    if not parsed.hostname:
        raise ValueError(f"{field} host is required")
    if port and port != _default_port(parsed.scheme):
        raise ValueError("non-standard ports are not allowed")

    hostname = parsed.hostname.strip().rstrip(".").casefold()
    if hostname == "localhost" or hostname.endswith(".localhost"):
        raise ValueError("url resolves to private or local network")
    try:
        ip = ipaddress.ip_address(hostname)
    except ValueError:
        return clean_url
    if not ip.is_global:
        raise ValueError("url resolves to private or local network")
    return clean_url


def _default_port(scheme: str) -> int:
    return 443 if scheme == "https" else 80


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
