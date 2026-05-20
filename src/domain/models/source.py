from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import uuid


@dataclass(frozen=True)
class Source:
    """文档导入来源，用于追踪本地路径和去重 checksum。"""

    id: str
    document_id: str
    source_type: str
    source_path: str
    imported_at: str
    checksum: str

    @classmethod
    def create(
        cls,
        document_id: str,
        source_type: str,
        source_path: str,
        checksum: str = "",
    ) -> "Source":
        return cls(
            id=str(uuid.uuid4()),
            document_id=document_id,
            source_type=source_type.strip(),
            source_path=source_path,
            imported_at=datetime.now(timezone.utc).isoformat(),
            checksum=checksum,
        )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "document_id": self.document_id,
            "source_type": self.source_type,
            "source_path": self.source_path,
            "imported_at": self.imported_at,
            "checksum": self.checksum,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Source":
        return cls(
            id=data["id"],
            document_id=data["document_id"],
            source_type=data["source_type"],
            source_path=data["source_path"],
            imported_at=data["imported_at"],
            checksum=data.get("checksum", ""),
        )
