# ops

工程运维目录，当前保留本地维护脚本说明。Docker 一键启动入口位于仓库根目录和 `scripts/`。

## Docker 快速启动

前置要求：

- 已安装并启动 Docker Desktop / Docker Engine。
- 首次启动需要网络拉取 `node:24-alpine`、`python:3.11-slim` 和 npm / pip 依赖。

从仓库根目录执行：

```bash
docker compose --project-directory . -f compose.yaml up --build -d
```

启动后访问：

```text
http://127.0.0.1:8765
```

健康检查：

```bash
curl http://127.0.0.1:8765/api/health
```

停止：

```bash
docker compose --project-directory . -f compose.yaml down
```

Windows 可继续使用：

```powershell
.\scripts\docker_up.ps1
.\scripts\docker_down.ps1
```

Linux / macOS 可使用：

```bash
./scripts/docker_up.sh
./scripts/docker_down.sh
```

## 目录与数据

| 路径 | 说明 |
|------|------|
| `Dockerfile` | 多阶段镜像：Node 构建 Vue/Vite，Python 运行 FastAPI |
| `compose.yaml` | Compose 服务定义，默认启动 `web` |
| `entrypoint.sh` | 容器启动入口，创建运行时目录并监听 `0.0.0.0:8765` |
| `.env.docker.example` | Docker 环境变量样例，不包含真实密钥 |
| `requirements-docker.txt` | 容器运行时 Python 依赖，不包含已归档桌面端依赖 |
| `scripts/docker_up.ps1` / `scripts/docker_down.ps1` | Windows PowerShell 启停脚本 |
| `scripts/docker_up.sh` / `scripts/docker_down.sh` | Linux / macOS shell 启停脚本 |
| `ki-runtime` volume | 容器内 `/app/runtime`，保存 SQLite 运行数据 |
| `docker-workspace/` | 默认宿主机导入目录，容器内路径为 `/workspace` |

## 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `KI_PORT` | `8765` | 宿主机暴露端口 |
| `RAG_LLM_PROVIDER` | `api` | LLM provider |
| `RAG_LLM_API_BASE` | `https://api.deepseek.com/v1` | OpenAI-compatible API 地址 |
| `RAG_LLM_API_MODEL` | `deepseek-chat` | 默认模型 |
| `RAG_LLM_API_KEY` / `DEEPSEEK_API_KEY` | 空 | LLM API Key，禁止提交真实值 |
| `RAG_EMBED_*` | 空 | OpenAI-compatible Embedding 配置 |
| `RAG_AUTH_ENABLED` | `false` | 是否启用 API Key / JWT 认证 |
| `KNOWLEDGE_ISLAND_WORKSPACE` | `./docker-workspace` | 宿主机导入目录 |

## 维护脚本

| 脚本 | 说明 |
|------|------|
| `ops/scripts/backup_db.sh` | 通过 `sqlite3 .dump` 备份 `KI_DB_PATH`，并在存在 Qdrant local 目录时打包 `KI_QDRANT_DIR`；默认保留最近 7 份 |
| `ops/scripts/rebuild_index.sh` | 调用本地 `POST /api/admin/rebuild-index`，重建当前 `VectorBackend` 索引 |
| `ops/scripts/cleanup_runtime.sh` | 清理 `runtime/` 下临时文件和 `__pycache__`，不删除数据库或 Qdrant 数据目录 |

## 验收命令

```bash
docker compose --project-directory . -f compose.yaml config
docker compose --project-directory . -f compose.yaml up --build -d
curl http://127.0.0.1:8765/api/health
docker exec knowledge-island-web id
docker compose --project-directory . -f compose.yaml down
```
