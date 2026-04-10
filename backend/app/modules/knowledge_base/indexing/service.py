from __future__ import annotations

from dataclasses import dataclass

from llama_index.core import Document
from llama_index.core.node_parser import SentenceSplitter


@dataclass
class IndexBuildResult:
    documents: int
    chunks: int


class IndexService:
    def __init__(self) -> None:
        self._splitter = SentenceSplitter(chunk_size=512, chunk_overlap=64)

    def build_from_texts(self, texts: list[str]) -> IndexBuildResult:
        docs = [Document(text=t) for t in texts if t.strip()]
        nodes = self._splitter.get_nodes_from_documents(docs)
        return IndexBuildResult(documents=len(docs), chunks=len(nodes))
