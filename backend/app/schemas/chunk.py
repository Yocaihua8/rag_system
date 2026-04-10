from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class Chunk:
    chunk_id: str
    document_id: str
    domain: str
    type: str
    tags: List[str] = field(default_factory=list)
    content: str = ""
    order: int = 0

    def to_dict(self) -> Dict:
        return {
            "chunk_id": self.chunk_id,
            "document_id": self.document_id,
            "domain": self.domain,
            "type": self.type,
            "tags": self.tags,
            "content": self.content,
            "order": self.order,
        }
