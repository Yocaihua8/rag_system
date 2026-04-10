import re
from typing import List, Optional, Set, Tuple

from backend.app.schemas.chunk import Chunk
from backend.app.schemas.document import Document
from backend.app.schemas.task import QueryTask


def _tokenize(text: str) -> Set[str]:
    return set(t for t in re.split(r"[^\w\u4e00-\u9fff]+", text.lower()) if t)


def _match_tags(required_tags: List[str], item_tags: List[str]) -> bool:
    if not required_tags:
        return True
    item_set = set(t.lower() for t in item_tags)
    return all(tag.lower() in item_set for tag in required_tags)


class SimpleRetrievalService:
    def __init__(self, documents: List[Document], chunks: List[Chunk]):
        self.documents = documents
        self.chunks = chunks

    def search_documents(
        self,
        question: str,
        domains: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
        top_k: int = 5,
    ) -> List[Document]:
        q_tokens = _tokenize(question)
        domain_set = set(d.lower() for d in (domains or []))
        tags = tags or []

        scored = []
        for doc in self.documents:
            if domain_set and doc.domain.lower() not in domain_set:
                continue
            if not _match_tags(tags, doc.tags):
                continue

            content_tokens = _tokenize(doc.title + "\n" + doc.content)
            overlap_score = len(q_tokens & content_tokens)
            tag_bonus = len(set(t.lower() for t in tags) & set(t.lower() for t in doc.tags))
            score = overlap_score * 2 + tag_bonus + doc.importance

            if score > 0:
                scored.append((score, doc))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [item[1] for item in scored[:top_k]]

    def search_chunks(self, task: QueryTask, top_k: int = 8) -> List[Chunk]:
        q_tokens = _tokenize(task.question)
        domain_set = set(d.lower() for d in task.target_domains)

        scored = []
        for chunk in self.chunks:
            if domain_set and chunk.domain.lower() not in domain_set:
                continue
            if not _match_tags(task.tags, chunk.tags):
                continue

            content_tokens = _tokenize(chunk.content)
            overlap_score = len(q_tokens & content_tokens)
            tag_bonus = len(set(t.lower() for t in task.tags) & set(t.lower() for t in chunk.tags))
            score = overlap_score * 2 + tag_bonus

            if score > 0:
                scored.append((score, chunk))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [item[1] for item in scored[:top_k]]
