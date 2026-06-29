from __future__ import annotations

import os
import re
from datetime import datetime
from pathlib import Path
from textwrap import wrap
from typing import Any

from webapp.models import ChatMessage

SUPPORTED_RESULT_EXPORT_FORMATS = {"markdown", "pdf"}


def export_chat_message_result(
    message: ChatMessage,
    project_name: str,
    export_format: str,
    title: str = "",
    output_dir: Path | None = None,
) -> dict[str, Any]:
    normalized_format = export_format.strip().lower()
    if normalized_format not in SUPPORTED_RESULT_EXPORT_FORMATS:
        raise ValueError("format must be markdown or pdf")

    output_dir = output_dir or result_output_dir()
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    export_title = title.strip() or _default_title(message.question)
    extension = "md" if normalized_format == "markdown" else "pdf"
    filename = f"{_filename_slug(export_title)}-{timestamp}-{message.id[:8]}.{extension}"
    path = output_dir / filename

    if normalized_format == "markdown":
        data = _markdown_bytes(message, project_name, export_title)
        mime_type = "text/markdown; charset=utf-8"
    else:
        data = _pdf_bytes(message, project_name, export_title)
        mime_type = "application/pdf"

    path.write_bytes(data)
    return {
        "format": normalized_format,
        "filename": filename,
        "path": str(path),
        "mime_type": mime_type,
        "bytes": path.stat().st_size,
    }


def result_output_dir() -> Path:
    configured = os.getenv("KI_OUTPUT_DIR") or os.getenv("RAG_OUTPUT_DIR")
    if configured:
        return Path(configured)
    return Path("data") / "outputs"


def _markdown_bytes(message: ChatMessage, project_name: str, title: str) -> bytes:
    lines = [
        f"# {title}",
        "",
        f"- 项目：{project_name}",
        f"- 消息 ID：{message.id}",
        f"- 导出时间：{datetime.now().isoformat(timespec='seconds')}",
        "",
        "## 问题",
        "",
        message.question,
        "",
        "## 回答",
        "",
        message.answer,
        "",
        "## 来源",
        "",
    ]
    if message.sources:
        for index, source in enumerate(message.sources, start=1):
            lines.extend(_source_markdown_lines(index, source))
    else:
        lines.append("无")
    lines.append("")
    return "\n".join(lines).encode("utf-8")


def _source_markdown_lines(index: int, source: dict[str, Any]) -> list[str]:
    path = str(source.get("path") or source.get("relative_path") or source.get("document_id") or "未知来源")
    lines = [f"{index}. `{path}`"]
    snippet = str(source.get("snippet") or "").strip()
    if snippet:
        lines.extend(["", f"   > {snippet}"])
    chunk_id = str(source.get("chunk_id") or "").strip()
    if chunk_id:
        lines.append(f"   - chunk_id：`{chunk_id}`")
    return lines


def _pdf_bytes(message: ChatMessage, project_name: str, title: str) -> bytes:
    markdown_text = _markdown_bytes(message, project_name, title).decode("utf-8")
    plain_lines = _plain_lines_for_pdf(markdown_text)
    pages = _paginate_pdf_lines(plain_lines)
    objects: list[bytes] = [
        b"",
        b"",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]
    page_ids: list[int] = []

    def add_object(body: bytes) -> int:
        objects.append(body)
        return len(objects)

    font_id = 3
    for page_lines in pages:
        stream = _pdf_content_stream(page_lines)
        content_id = add_object(
            b"<< /Length "
            + str(len(stream)).encode("ascii")
            + b" >>\nstream\n"
            + stream
            + b"\nendstream"
        )
        page_id = add_object(
            (
                f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
                f"/Resources << /Font << /F1 {font_id} 0 R >> >> "
                f"/Contents {content_id} 0 R >>"
            ).encode("ascii")
        )
        page_ids.append(page_id)

    objects[0] = b"<< /Type /Catalog /Pages 2 0 R >>"
    kids = " ".join(f"{page_id} 0 R" for page_id in page_ids)
    objects[1] = f"<< /Type /Pages /Kids [{kids}] /Count {len(page_ids)} >>".encode("ascii")
    return _build_pdf(objects)


def _plain_lines_for_pdf(markdown_text: str) -> list[str]:
    lines: list[str] = []
    for raw_line in markdown_text.splitlines():
        line = re.sub(r"^#{1,6}\s*", "", raw_line).replace("`", "")
        line = line.replace("：", ": ")
        if not line.strip():
            lines.append("")
            continue
        wrapped = wrap(line, width=84, replace_whitespace=False, drop_whitespace=False)
        lines.extend(wrapped or [line])
    return lines or [""]


def _paginate_pdf_lines(lines: list[str]) -> list[list[str]]:
    page_size = 46
    return [lines[index : index + page_size] for index in range(0, len(lines), page_size)] or [[""]]


def _pdf_content_stream(lines: list[str]) -> bytes:
    commands = ["BT", "/F1 11 Tf", "14 TL", "50 742 Td"]
    for line in lines:
        commands.append(f"<{_pdf_hex_text(line)}> Tj")
        commands.append("T*")
    commands.append("ET")
    return "\n".join(commands).encode("ascii")


def _pdf_hex_text(text: str) -> str:
    cleaned = "".join(char if char >= " " else " " for char in text)
    return ("\ufeff" + cleaned).encode("utf-16-be").hex().upper()


def _build_pdf(objects: list[bytes]) -> bytes:
    pdf = bytearray(b"%PDF-1.4\n")
    offsets: list[int] = []
    for index, body in enumerate(objects, start=1):
        offsets.append(len(pdf))
        pdf.extend(f"{index} 0 obj\n".encode("ascii"))
        pdf.extend(body)
        pdf.extend(b"\nendobj\n")
    xref_offset = len(pdf)
    pdf.extend(f"xref\n0 {len(objects) + 1}\n".encode("ascii"))
    pdf.extend(b"0000000000 65535 f \n")
    for offset in offsets:
        pdf.extend(f"{offset:010d} 00000 n \n".encode("ascii"))
    pdf.extend(
        (
            "trailer\n"
            f"<< /Size {len(objects) + 1} /Root 1 0 R >>\n"
            "startxref\n"
            f"{xref_offset}\n"
            "%%EOF\n"
        ).encode("ascii")
    )
    return bytes(pdf)


def _default_title(question: str) -> str:
    cleaned = " ".join(question.strip().split())
    return cleaned[:40] or "回答结果"


def _filename_slug(title: str) -> str:
    ascii_slug = re.sub(r"[^A-Za-z0-9_-]+", "-", title).strip("-").lower()
    return ascii_slug or "result"
