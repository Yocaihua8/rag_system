#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
RUNTIME_DIR="${KI_RUNTIME_DIR:-$PROJECT_ROOT/runtime}"
BACKUP_DIR="${KI_BACKUP_DIR:-$PROJECT_ROOT/runtime/backups}"
QDRANT_DIR="${KI_QDRANT_DIR:-${RAG_QDRANT_PATH:-}}"

if [[ ! -d "$RUNTIME_DIR" ]]; then
  echo "Runtime directory does not exist, nothing to clean: $RUNTIME_DIR"
  exit 0
fi

PROJECT_RUNTIME_ROOT="$(cd "$PROJECT_ROOT/runtime" 2>/dev/null && pwd -P || true)"
RUNTIME_REALPATH="$(cd "$RUNTIME_DIR" && pwd -P)"
if [[ -z "$PROJECT_RUNTIME_ROOT" || "$RUNTIME_REALPATH" != "$PROJECT_RUNTIME_ROOT"* ]]; then
  echo "Refusing to clean runtime outside project runtime directory: $RUNTIME_DIR" >&2
  exit 1
fi

echo "Cleaning transient files under $RUNTIME_DIR"
echo "Persistent data is preserved, including SQLite databases such as knowledge_island.db, runtime/backups, and Qdrant data."

prune_args=()
if [[ -n "$BACKUP_DIR" ]]; then
  prune_args+=( -path "$BACKUP_DIR" -prune -o )
fi
if [[ -n "$QDRANT_DIR" ]]; then
  prune_args+=( -path "$QDRANT_DIR" -prune -o )
fi

find "$RUNTIME_DIR" "${prune_args[@]}" -type d -name "__pycache__" -exec rm -rf {} +
find "$RUNTIME_DIR" "${prune_args[@]}" -type d -name ".pytest_cache" -exec rm -rf {} +
find "$RUNTIME_DIR" "${prune_args[@]}" -type f -name "*.pyc" -delete
find "$RUNTIME_DIR" "${prune_args[@]}" -type f \( -name "*.tmp" -o -name "*.temp" -o -name ".DS_Store" \) -delete

echo "Runtime cleanup complete."
