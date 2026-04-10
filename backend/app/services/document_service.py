import json
from pathlib import Path
from typing import List, Optional

from backend.app.config import CHUNKS_PATH, PROCESSED_PATH
from backend.app.modules.knowledge_base.ingestion.markdown_loader import load_markdown_documents
from backend.app.modules.preprocess.splitter import split_document
from backend.app.schemas.chunk import Chunk
from backend.app.schemas.document import Document


def load_all_markdown_documents() -> List[Document]:
    return load_markdown_documents()


def save_processed_documents(documents: List[Document], output_path: Optional[Path] = None) -> Path:
    target = output_path or (PROCESSED_PATH / "documents.jsonl")
    target.parent.mkdir(parents=True, exist_ok=True)

    lines = [json.dumps(doc.to_dict(), ensure_ascii=False) for doc in documents]
    target.write_text("\n".join(lines), encoding="utf-8")
    return target


def build_chunks_for_documents(
    documents: List[Document], chunk_size: int = 500, overlap: int = 50, save_to_disk: bool = True
) -> List[Chunk]:
    chunks = []
    for doc in documents:
        chunks.extend(split_document(doc, chunk_size=chunk_size, overlap=overlap))

    if save_to_disk:
        chunk_path = CHUNKS_PATH / "chunks.jsonl"
        chunk_path.parent.mkdir(parents=True, exist_ok=True)
        lines = [json.dumps(chunk.to_dict(), ensure_ascii=False) for chunk in chunks]
        chunk_path.write_text("\n".join(lines), encoding="utf-8")

    return chunks
