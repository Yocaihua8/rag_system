#!/bin/bash
set -e

RUNTIME_DIR="${KI_RUNTIME_DIR:-runtime}"

if [ ! -d "$RUNTIME_DIR" ]; then
  echo "无需清理：$RUNTIME_DIR 不存在"
  exit 0
fi

find "$RUNTIME_DIR" -type f \( -name "*.tmp" -o -name "*.bak" \) -delete
find "$RUNTIME_DIR" -type d -name "__pycache__" -prune -exec rm -rf {} +

echo "运行时临时文件清理完成：$RUNTIME_DIR"
