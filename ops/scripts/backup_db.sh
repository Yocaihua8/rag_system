#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
DB_PATH="${KI_DB_PATH:-$PROJECT_ROOT/runtime/webapp/knowledge_island.db}"
BACKUP_DIR="${KI_BACKUP_DIR:-$PROJECT_ROOT/runtime/backups}"
BACKUP_RETENTION="${KI_BACKUP_RETENTION:-7}"
QDRANT_DIR="${KI_QDRANT_DIR:-${RAG_QDRANT_PATH:-}}"

if [[ ! "$BACKUP_RETENTION" =~ ^[0-9]+$ ]] || (( BACKUP_RETENTION < 1 )); then
  echo "KI_BACKUP_RETENTION must be a positive integer." >&2
  exit 1
fi

if [[ ! -f "$DB_PATH" ]]; then
  echo "SQLite database not found: $DB_PATH" >&2
  exit 1
fi

mkdir -p "$BACKUP_DIR"

TIMESTAMP="$(date +%Y%m%d-%H%M%S)"
DB_BACKUP_PATH="$BACKUP_DIR/knowledge_island-db-$TIMESTAMP.sqlite3"

if command -v sqlite3 >/dev/null 2>&1; then
  sqlite3 "$DB_PATH" ".backup \"$DB_BACKUP_PATH\""
else
  echo "sqlite3 not found; falling back to file copy. Stop the app first for a fully consistent copy." >&2
  cp "$DB_PATH" "$DB_BACKUP_PATH"
fi

echo "Database backup written: $DB_BACKUP_PATH"

if [[ -n "$QDRANT_DIR" && -d "$QDRANT_DIR" ]]; then
  QDRANT_BACKUP_PATH="$BACKUP_DIR/qdrant-$TIMESTAMP.tar.gz"
  tar -czf "$QDRANT_BACKUP_PATH" -C "$(dirname "$QDRANT_DIR")" "$(basename "$QDRANT_DIR")"
  echo "Qdrant backup written: $QDRANT_BACKUP_PATH"
fi

prune_old_backups() {
  local pattern="$1"
  mapfile -t backup_files < <(find "$BACKUP_DIR" -maxdepth 1 -type f -name "$pattern" | sort -r)
  if (( ${#backup_files[@]} > BACKUP_RETENTION )); then
    printf '%s\0' "${backup_files[@]:BACKUP_RETENTION}" | xargs -0 rm -f
  fi
}

prune_old_backups "knowledge_island-db-*.sqlite3"
prune_old_backups "qdrant-*.tar.gz"
