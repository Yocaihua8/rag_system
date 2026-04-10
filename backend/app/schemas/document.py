from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List


@dataclass
class Document:
    id: str
    title: str
    domain: str
    type: str
    source: str
    tags: List[str] = field(default_factory=list)
    content: str = ""
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    importance: int = 3
    status: str = "active"

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "title": self.title,
            "domain": self.domain,
            "type": self.type,
            "source": self.source,
            "tags": self.tags,
            "content": self.content,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "importance": self.importance,
            "status": self.status,
        }

    @classmethod
    def from_path(cls, file_path: Path, content: str, domain: str, tags: List[str]) -> "Document":
        title = file_path.stem
        for line in content.splitlines():
            if line.strip().startswith("#"):
                title = line.strip().lstrip("#").strip() or file_path.stem
                break

        return cls(
            id=file_path.stem,
            title=title,
            domain=domain,
            type="markdown",
            source=str(file_path),
            tags=tags,
            content=content,
        )
