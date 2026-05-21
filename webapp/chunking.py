from __future__ import annotations

import re

DEFAULT_CHUNK_CHARS = 700
DEFAULT_OVERLAP_CHARS = 80


def split_into_chunks(
    content: str,
    max_chars: int = DEFAULT_CHUNK_CHARS,
    overlap_chars: int = DEFAULT_OVERLAP_CHARS,
) -> list[str]:
    normalized = content.strip()
    if not normalized:
        return []

    chunks: list[str] = []
    for block in _paragraph_blocks(normalized):
        if len(block) <= max_chars:
            chunks.append(block)
            continue
        chunks.extend(_split_long_block(block, max_chars, overlap_chars))
    return chunks


def count_tokens(text: str) -> int:
    return len(re.findall(r"[a-zA-Z0-9_]+|[\u4e00-\u9fff]", text))


def _paragraph_blocks(content: str) -> list[str]:
    return [block.strip() for block in re.split(r"\n\s*\n+", content) if block.strip()]


def _split_long_block(block: str, max_chars: int, overlap_chars: int) -> list[str]:
    chunks: list[str] = []
    start = 0
    step = max(max_chars - overlap_chars, 1)
    while start < len(block):
        chunk = block[start : start + max_chars].strip()
        if chunk:
            chunks.append(chunk)
        start += step
    return chunks
