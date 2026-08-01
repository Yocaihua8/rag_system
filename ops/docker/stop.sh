#!/bin/sh
set -eu

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
REPOSITORY_ROOT="$(CDPATH= cd -- "$SCRIPT_DIR/../.." && pwd)"
COMPOSE_FILE="$SCRIPT_DIR/compose.yaml"

if ! command -v docker >/dev/null 2>&1; then
  echo "未找到 docker 命令。请先安装并启动 Docker。"
  exit 1
fi

docker compose --project-directory "$REPOSITORY_ROOT" -f "$COMPOSE_FILE" down "$@"
