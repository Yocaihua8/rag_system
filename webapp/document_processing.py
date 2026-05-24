from __future__ import annotations

import base64
import binascii
import io
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from zipfile import BadZipFile, ZipFile
from xml.etree import ElementTree

from webapp.import_rules import MAX_TEXT_FILE_BYTES, TEXT_SUFFIXES

PDF_SKIP_REASON = "pdf extraction requires optional parser"
BINARY_CONTENT_REQUIRED_REASON = "binary content is required"
INVALID_BINARY_CONTENT_REASON = "invalid binary content"
EMPTY_TEXT_REASON = "no extractable text"

_DOCX_TEXT_TAG = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t"
_DOCX_PARAGRAPH_TAG = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}p"
_BINARY_SUFFIXES = {".docx", ".pdf"}


@dataclass(frozen=True)
class ProcessedDocument:
    relative_path: str
    content: str = ""
    skipped_reason: str = ""

    @property
    def is_importable(self) -> bool:
        return not self.skipped_reason


def process_local_file(path: Path, root: Path) -> ProcessedDocument:
    relative_path = path.relative_to(root).as_posix()
    suffix = path.suffix.lower()
    if suffix not in TEXT_SUFFIXES:
        return ProcessedDocument(relative_path, skipped_reason="unsupported file type")
    if path.stat().st_size > MAX_TEXT_FILE_BYTES:
        return ProcessedDocument(relative_path, skipped_reason="file too large")
    if suffix not in _BINARY_SUFFIXES:
        return ProcessedDocument(
            relative_path,
            content=path.read_text(encoding="utf-8", errors="ignore"),
        )
    data = path.read_bytes()
    return process_bytes(relative_path, data)


def process_uploaded_file(relative_path: str, entry: dict) -> ProcessedDocument:
    suffix = PurePosixPath(relative_path).suffix.lower()
    if suffix not in TEXT_SUFFIXES:
        return ProcessedDocument(relative_path, skipped_reason="unsupported file type")

    raw_base64 = entry.get("content_base64")
    if raw_base64 is not None:
        try:
            data = base64.b64decode(str(raw_base64), validate=True)
        except (binascii.Error, ValueError):
            return ProcessedDocument(relative_path, skipped_reason=INVALID_BINARY_CONTENT_REASON)
        if (
            _uploaded_size(entry, len(data)) > MAX_TEXT_FILE_BYTES
            or len(data) > MAX_TEXT_FILE_BYTES
        ):
            return ProcessedDocument(relative_path, skipped_reason="file too large")
        return process_bytes(relative_path, data)

    if suffix in _BINARY_SUFFIXES:
        return ProcessedDocument(relative_path, skipped_reason=BINARY_CONTENT_REQUIRED_REASON)

    content = str(entry.get("content", ""))
    if len(content.encode("utf-8")) > MAX_TEXT_FILE_BYTES:
        return ProcessedDocument(relative_path, skipped_reason="file too large")
    return ProcessedDocument(relative_path, content=content)


def process_bytes(relative_path: str, data: bytes) -> ProcessedDocument:
    suffix = PurePosixPath(relative_path).suffix.lower()
    if suffix == ".pdf":
        return _process_pdf_bytes(relative_path, data)
    if suffix == ".docx":
        return _process_docx_bytes(relative_path, data)
    content = data.decode("utf-8", errors="ignore")
    return ProcessedDocument(relative_path, content=content)


def _process_pdf_bytes(relative_path: str, data: bytes) -> ProcessedDocument:
    try:
        import pymupdf
    except ImportError:
        return ProcessedDocument(relative_path, skipped_reason=PDF_SKIP_REASON)

    try:
        with pymupdf.open(stream=data, filetype="pdf") as document:
            pages = [
                page.get_text("text", sort=True).strip()
                for page in document
            ]
    except Exception:
        return ProcessedDocument(relative_path, skipped_reason=INVALID_BINARY_CONTENT_REASON)

    content = "\n\n".join(page for page in pages if page).strip()
    if not content:
        return ProcessedDocument(relative_path, skipped_reason=EMPTY_TEXT_REASON)
    return ProcessedDocument(relative_path, content=content)


def _process_docx_bytes(relative_path: str, data: bytes) -> ProcessedDocument:
    try:
        with ZipFile(io.BytesIO(data)) as archive:
            document_xml = archive.read("word/document.xml")
    except (BadZipFile, KeyError, OSError):
        return ProcessedDocument(relative_path, skipped_reason=INVALID_BINARY_CONTENT_REASON)

    try:
        root = ElementTree.fromstring(document_xml)
    except ElementTree.ParseError:
        return ProcessedDocument(relative_path, skipped_reason=INVALID_BINARY_CONTENT_REASON)

    paragraphs: list[str] = []
    for paragraph in root.iter(_DOCX_PARAGRAPH_TAG):
        text = "".join(node.text or "" for node in paragraph.iter(_DOCX_TEXT_TAG)).strip()
        if text:
            paragraphs.append(text)
    if not paragraphs:
        fallback_text = "\n".join(
            (node.text or "").strip() for node in root.iter(_DOCX_TEXT_TAG)
        ).strip()
        if fallback_text:
            paragraphs.append(fallback_text)
    content = "\n".join(paragraphs).strip()
    if not content:
        return ProcessedDocument(relative_path, skipped_reason=EMPTY_TEXT_REASON)
    return ProcessedDocument(relative_path, content=content)


def _uploaded_size(entry: dict, fallback: int) -> int:
    try:
        return int(entry.get("size", fallback))
    except (TypeError, ValueError):
        return fallback
