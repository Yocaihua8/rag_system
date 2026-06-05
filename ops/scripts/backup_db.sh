#!/bin/bash
set -e

DB_PATH="${KI_DB_PATH:-runtime/knowledge_island/knowledge_island.db}"
QDRANT_DIR="${KI_QDRANT_DIR:-runtime/qdrant}"
BACKUP_DIR="${KI_BACKUP_DIR:-data/backups}"

mkdir -p "$BACKUP_DIR"
STAMP=$(date +%Y%m%d_%H%M)
sqlite3 "$DB_PATH" ".dump" > "$BACKUP_DIR/ki_${STAMP}.sql"

if [ -d "$QDRANT_DIR" ]; then
  tar czf "$BACKUP_DIR/qdrant_${STAMP}.tar.gz" "$QDRANT_DIR"
fi

ls -t "$BACKUP_DIR"/ki_*.sql 2>/dev/null | tail -n +8 | xargs rm -f
ls -t "$BACKUP_DIR"/qdrant_*.tar.gz 2>/dev/null | tail -n +8 | xargs rm -f

echo "备份完成：$BACKUP_DIR/ki_${STAMP}.sql"
