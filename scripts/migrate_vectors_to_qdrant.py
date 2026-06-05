#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.knowledge_island.storage import KnowledgeStore
from backend.knowledge_island.vector_backend import QdrantVectorBackend


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Migrate SQLite chunk_vectors records to Qdrant local storage."
    )
    parser.add_argument(
        "--db-path",
        default="runtime/knowledge_island/knowledge_island.db",
    )
    parser.add_argument("--qdrant-path", default="runtime/qdrant")
    args = parser.parse_args()

    store = KnowledgeStore(Path(args.db_path))
    qdrant = QdrantVectorBackend(path=args.qdrant_path)
    total = 0
    for project in store.list_projects():
        records = store.list_chunk_vector_records(project.id)
        print(f"迁移项目 {project.name}：{len(records)} 条向量")
        for record in records:
            qdrant.upsert(
                chunk_id=str(record["chunk_id"]),
                project_id=project.id,
                vector=dict(record.get("vector", {})),
                payload={
                    "project_id": project.id,
                    "provider": str(record.get("provider", "local")),
                    "model": str(record.get("model", "hashing-96")),
                },
            )
        migrated = qdrant.count(project.id)
        total += migrated
        print(f"  ok: 已迁移 {migrated} 条")
    print(f"迁移完成：{total} 条向量")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
