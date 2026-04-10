from pathlib import Path
from typing import List, Optional

from backend.app.config import RAW_PATH
from backend.app.modules.preprocess.tagger import build_tags, infer_domain
from backend.app.schemas.document import Document


def load_markdown_documents(source_dir: Optional[Path] = None) -> List[Document]:
    """Load all markdown files under source_dir into Document objects."""
    base_dir = source_dir or RAW_PATH
    if not base_dir.exists():
        return []

    documents = []
    for file_path in sorted(base_dir.rglob("*.md")):
        content = file_path.read_text(encoding="utf-8")
        domain = infer_domain(file_path, content)
        tags = build_tags(file_path, content)
        documents.append(Document.from_path(file_path=file_path, content=content, domain=domain, tags=tags))

    return documents
