#!/bin/sh
set -e

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
COMPOSE_FILE="$PROJECT_ROOT/compose.yaml"

if ! command -v docker >/dev/null 2>&1; then
  echo "未找到 docker 命令。请先安装并启动 Docker。"
  exit 1
fi

WORKSPACE="${KNOWLEDGE_ISLAND_WORKSPACE:-$PROJECT_ROOT/docker-workspace}"
mkdir -p "$WORKSPACE"

export KNOWLEDGE_ISLAND_WORKSPACE="$WORKSPACE"
export RAG_LLM_PROVIDER="${RAG_LLM_PROVIDER:-api}"

docker compose --project-directory "$PROJECT_ROOT" -f "$COMPOSE_FILE" up --build -d

echo "知识岛 Docker Web 已启动：http://127.0.0.1:${KI_PORT:-8765}"
echo "Docker 内导入目录请填写：/workspace"
echo "宿主机对应目录：$WORKSPACE"
