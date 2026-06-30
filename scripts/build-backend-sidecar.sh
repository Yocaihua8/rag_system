#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
PROJECT_ROOT="$(CDPATH= cd -- "$SCRIPT_DIR/.." && pwd)"
TAURI_BINARY_DIR="$PROJECT_ROOT/src-tauri/binaries"
BACKEND_NAME="knowledge-island-backend"
PYTHON_BIN="${PYTHON:-}"
TARGET_TRIPLE="${KI_TAURI_TARGET_TRIPLE:-}"

if [ -z "$PYTHON_BIN" ]; then
  if command -v python3 >/dev/null 2>&1; then
    PYTHON_BIN="python3"
  else
    PYTHON_BIN="python"
  fi
fi

if [ -z "$TARGET_TRIPLE" ]; then
  if ! command -v rustc >/dev/null 2>&1; then
    echo "rustc is required to detect the Tauri target triple. Set KI_TAURI_TARGET_TRIPLE to override." >&2
    exit 1
  fi
  TARGET_TRIPLE="$(rustc -vV | awk '/^host:/ { print $2 }')"
fi

if [ -z "$TARGET_TRIPLE" ]; then
  echo "Unable to detect Tauri target triple." >&2
  exit 1
fi

cd "$PROJECT_ROOT"

echo "Building Vue/Vite frontend..."
npm run build

echo "Building FastAPI sidecar with PyInstaller for $TARGET_TRIPLE..."
"$PYTHON_BIN" -m PyInstaller \
  --noconfirm \
  --clean \
  --onefile \
  --name "$BACKEND_NAME" \
  --add-data "webapp/static_dist:webapp/static_dist" \
  app.py

SOURCE_BIN="$PROJECT_ROOT/dist/$BACKEND_NAME"
TARGET_BIN="$TAURI_BINARY_DIR/knowledge-island-backend-${TARGET_TRIPLE}"

if [ ! -f "$SOURCE_BIN" ]; then
  echo "Expected PyInstaller output was not found: $SOURCE_BIN" >&2
  exit 1
fi

mkdir -p "$TAURI_BINARY_DIR"
cp "$SOURCE_BIN" "$TARGET_BIN"
chmod +x "$TARGET_BIN"

echo "Created Tauri sidecar: $TARGET_BIN"
