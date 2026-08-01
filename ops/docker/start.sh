#!/bin/sh
set -eu

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
REPOSITORY_ROOT="$(CDPATH= cd -- "$SCRIPT_DIR/../.." && pwd)"
COMPOSE_FILE="$SCRIPT_DIR/compose.yaml"

if ! command -v docker >/dev/null 2>&1; then
  echo "未找到 docker 命令。请先安装并启动 Docker。"
  exit 1
fi

WORKSPACE="${KNOWLEDGE_ISLAND_WORKSPACE:-$REPOSITORY_ROOT/docker-workspace}"
mkdir -p "$WORKSPACE"
export KNOWLEDGE_ISLAND_WORKSPACE="$WORKSPACE"
export RAG_LLM_PROVIDER="${RAG_LLM_PROVIDER:-api}"

docker compose --project-directory "$REPOSITORY_ROOT" -f "$COMPOSE_FILE" up --build -d

echo "前端已启动：http://127.0.0.1:${KI_WEB_PORT:-4173}"
echo "后端 API：http://127.0.0.1:${KI_API_PORT:-8765}"
echo "Docker 内导入目录：/workspace"
echo "宿主机对应目录：$WORKSPACE"
