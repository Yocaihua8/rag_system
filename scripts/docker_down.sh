#!/bin/sh
set -e

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
COMPOSE_FILE="$PROJECT_ROOT/compose.yaml"

if ! command -v docker >/dev/null 2>&1; then
  echo "未找到 docker 命令。请先安装并启动 Docker。"
  exit 1
fi

docker compose --project-directory "$PROJECT_ROOT" -f "$COMPOSE_FILE" down "$@"
