from __future__ import annotations

from dataclasses import dataclass
from html import escape, unescape
import re


@dataclass(frozen=True)
class NormalizedContent:
    raw_content: str
    normalized_markdown: str
    plain_text: str
    rendered_html: str


_MARKDOWN_TYPES = {"md", "markdown"}
_FENCED_CODE = re.compile(r"```.*?```", re.DOTALL)
_SCRIPT_OR_STYLE = re.compile(r"(?is)<(script|style)\b[^>]*>.*?</\1>")
_HTML_TAG = re.compile(r"(?s)<[^>]+>")
_HEADING = re.compile(r"^(#{1,6})\s+(.+)$")
_LIST_ITEM = re.compile(r"^\s*[-*+]\s+(.+)$")
_ORDERED_LIST_ITEM = re.compile(r"^\s*\d+[.)]\s+(.+)$")
_LINK = re.compile(r"!?\[([^\]]*)\]\([^)]+\)")
_EMPHASIS = re.compile(r"[*_]{1,3}([^*_]+)[*_]{1,3}")


def normalize_document_content(raw_content: str, source_type: str) -> NormalizedContent:
    """Return normalized Markdown, plain text, and safe render HTML for imported text."""
    if source_type.lower() in _MARKDOWN_TYPES:
        normalized = normalize_markdown(raw_content)
        plain_text = markdown_to_plain_text(normalized)
        rendered_html = render_markdown_to_safe_html(normalized)
        return NormalizedContent(
            raw_content=raw_content,
            normalized_markdown=normalized,
            plain_text=plain_text,
            rendered_html=rendered_html,
        )

    return NormalizedContent(
        raw_content=raw_content,
        normalized_markdown=raw_content,
        plain_text=raw_content,
        rendered_html=f"<pre><code>{escape(raw_content)}</code></pre>",
    )


def normalize_markdown(markdown: str) -> str:
    text = markdown.replace("\r\n", "\n").replace("\r", "\n").lstrip("\ufeff")
    parts: list[str] = []
    cursor = 0
    for match in _FENCED_CODE.finditer(text):
        parts.append(_clean_markdown_text(text[cursor:match.start()]))
        parts.append(_normalize_lines(match.group(0)))
        cursor = match.end()
    parts.append(_clean_markdown_text(text[cursor:]))
    return _collapse_blank_lines("".join(parts)).strip()


def markdown_to_plain_text(markdown: str) -> str:
    lines: list[str] = []
    in_code = False
    for raw_line in markdown.split("\n"):
        line = raw_line.rstrip()
        if line.startswith("```"):
            in_code = not in_code
            continue
        if in_code:
            lines.append(line)
            continue
        heading = _HEADING.match(line)
        if heading:
            lines.append(_inline_markdown_to_text(heading.group(2).strip()))
            continue
        list_item = _LIST_ITEM.match(line) or _ORDERED_LIST_ITEM.match(line)
        if list_item:
            lines.append(_inline_markdown_to_text(list_item.group(1).strip()))
            continue
        lines.append(_inline_markdown_to_text(line.strip()))
    return _collapse_blank_lines("\n".join(lines)).strip()


def render_markdown_to_safe_html(markdown: str) -> str:
    html_parts: list[str] = []
    paragraph: list[str] = []
    list_items: list[str] = []
    code_lines: list[str] = []
    code_language = ""
    in_code = False

    def flush_paragraph() -> None:
        if paragraph:
            text = " ".join(part.strip() for part in paragraph if part.strip())
            if text:
                html_parts.append(f"<p>{escape(_inline_markdown_to_text(text))}</p>")
            paragraph.clear()

    def flush_list() -> None:
        if list_items:
            html_parts.append("<ul>")
            html_parts.extend(f"<li>{escape(item)}</li>" for item in list_items)
            html_parts.append("</ul>")
            list_items.clear()

    for raw_line in markdown.split("\n"):
        line = raw_line.rstrip()
        if line.startswith("```"):
            if in_code:
                language_attr = f' class="language-{escape(code_language)}"' if code_language else ""
                html_parts.append(
                    f"<pre><code{language_attr}>{escape(chr(10).join(code_lines))}</code></pre>"
                )
                code_lines.clear()
                code_language = ""
                in_code = False
            else:
                flush_paragraph()
                flush_list()
                code_language = line[3:].strip()
                in_code = True
            continue

        if in_code:
            code_lines.append(line)
            continue

        if not line.strip():
            flush_paragraph()
            flush_list()
            continue

        heading = _HEADING.match(line)
        if heading:
            flush_paragraph()
            flush_list()
            level = len(heading.group(1))
            text = _inline_markdown_to_text(heading.group(2).strip())
            html_parts.append(f"<h{level}>{escape(text)}</h{level}>")
            continue

        list_item = _LIST_ITEM.match(line) or _ORDERED_LIST_ITEM.match(line)
        if list_item:
            flush_paragraph()
            list_items.append(_inline_markdown_to_text(list_item.group(1).strip()))
            continue

        flush_list()
        paragraph.append(line)

    if in_code:
        language_attr = f' class="language-{escape(code_language)}"' if code_language else ""
        html_parts.append(
            f"<pre><code{language_attr}>{escape(chr(10).join(code_lines))}</code></pre>"
        )
    flush_paragraph()
    flush_list()
    return "\n".join(html_parts)


def _clean_markdown_text(text: str) -> str:
    cleaned = _SCRIPT_OR_STYLE.sub("", text)
    cleaned = _HTML_TAG.sub("", cleaned)
    return _normalize_lines(unescape(cleaned))


def _normalize_lines(text: str) -> str:
    return "\n".join(line.rstrip() for line in text.split("\n"))


def _collapse_blank_lines(text: str) -> str:
    return re.sub(r"\n{3,}", "\n\n", text)


def _inline_markdown_to_text(text: str) -> str:
    value = _LINK.sub(lambda match: match.group(1), text)
    value = _EMPHASIS.sub(lambda match: match.group(1), value)
    value = value.replace("`", "")
    return value
