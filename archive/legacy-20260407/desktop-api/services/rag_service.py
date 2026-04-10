from typing import List

from app.services.document_service import load_all_markdown_documents, build_chunks_for_documents
from app.services.retrieval_service import SimpleRetrievalService
from app.schemas.task import QueryTask


class RagService:
    def __init__(self) -> None:
        self._documents = []
        self._chunks = []

    def load(self) -> None:
        self._documents = load_all_markdown_documents()
        self._chunks = build_chunks_for_documents(self._documents, save_to_disk=True)

    def query(self, question: str, top_k: int = 5) -> dict:
        if not self._documents or not self._chunks:
            self.load()
        task = QueryTask(task_type="query", target_domains=[], tags=[], question=question)
        retriever = SimpleRetrievalService(self._documents, self._chunks)
        hits = retriever.search_chunks(task=task, top_k=top_k)
        hit_texts = [h.content for h in hits]
        answer = hit_texts[0] if hit_texts else ""
        return {"answer": answer, "hits": hit_texts}
