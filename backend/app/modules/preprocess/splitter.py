from typing import List

from backend.app.schemas.chunk import Chunk
from backend.app.schemas.document import Document


def split_document(document: Document, chunk_size: int = 500, overlap: int = 50) -> List[Chunk]:
    """Split document content by fixed character window."""
    if chunk_size <= 0:
        raise ValueError("chunk_size must be > 0")
    if overlap < 0 or overlap >= chunk_size:
        raise ValueError("overlap must be >= 0 and < chunk_size")

    text = document.content.strip()
    if not text:
        return []

    chunks = []
    start = 0
    order = 0

    while start < len(text):
        end = min(start + chunk_size, len(text))
        chunk_text = text[start:end].strip()
        if chunk_text:
            chunks.append(
                Chunk(
                    chunk_id="{0}_{1}".format(document.id, order),
                    document_id=document.id,
                    domain=document.domain,
                    type=document.type,
                    tags=document.tags,
                    content=chunk_text,
                    order=order,
                )
            )
        if end == len(text):
            break
        start = end - overlap
        order += 1

    return chunks
