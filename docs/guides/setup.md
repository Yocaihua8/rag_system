# 开发环境与启动

> 状态：Active
> Owner：RAG 团队
> Last Updated：2026-08-01
> Scope：独立后端、前端、桌面、插件和 Docker 的环境搭建
> Related：`../../README.md`、`../design/system-design-overview.md`、`testing.md`、`troubleshooting.md`

## 1. 前置要求

- Python 3.10+
- Node.js 20+ 与 npm
- Git
- 桌面构建额外需要 Rust/Cargo 和目标平台原生工具链
- Docker 运行额外需要 Docker Desktop 或兼容 Compose 环境
- Ollama 仅在使用本地模型时需要

## 2. 安装基础环境

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r backend/requirements/dev.txt
npm ci
Copy-Item backend/.env.example backend/.env
```

`backend/requirements/dev.txt` 包含 `base.txt`，并增加 pytest、PyInstaller 和 pip-audit。根 npm workspace 只安装 `frontend` 与 `src-tauri`；Obsidian 插件独立安装：

```powershell
npm --prefix integrations/obsidian-plugin ci
```

## 3. 依赖状态

| 包 | 安装状态 | 当前用途 |
|----|----------|----------|
| `qdrant-client` | `base.txt` 必装 | 只有配置 `RAG_VECTOR_STORE_PROVIDER=qdrant` 时启用 local mode，默认仍走 SQLite |
| `jieba` | `base.txt` 必装 | 当前源码尚未调用，不能据此宣称已启用中文分词 |
| `pinia` | `frontend/package.json` 已声明 | 当前前端状态使用 reactive singleton，源码尚未创建 Pinia store |
| `pymupdf` | 未列入 requirements | PDF 抽取的可选依赖，按需执行 `python -m pip install pymupdf` |
| `sentence-transformers` | 未列入 requirements | Cross-Encoder reranker 的可选依赖，未安装时跳过 rerank |

可选包体积和平台依赖较大，应只在确实需要对应能力时安装。

## 4. 本地运行

后端终端：

```powershell
.\.venv\Scripts\python.exe -m backend
```

默认地址为 `http://127.0.0.1:8765`；`GET /api/health`、`/docs`、`/redoc` 和 `/openapi.json` 可用，`GET /` 返回 404 是正常设计。

前端终端：

```powershell
npm run frontend:dev
```

浏览器访问 `http://127.0.0.1:5173`。默认 API base 为 `http://127.0.0.1:8765`；覆盖时在启动或构建前设置：

```powershell
$env:VITE_API_BASE_URL = 'http://127.0.0.1:18765'
npm run frontend:dev
```

该值进入公开前端产物，不得包含凭证。

## 5. 构建与预览

```powershell
npm run frontend:build
npm --workspace frontend run preview
```

构建输出为 `frontend/dist/`，preview 默认监听 `127.0.0.1:4173`。FastAPI 不托管该目录。

## 6. 常用后端配置

| 变量 | 默认或行为 |
|------|------------|
| `RAG_RUNTIME_DIR` | 默认仓库内 `runtime/v2/` |
| `RAG_AUTH_ENABLED` | 默认关闭 |
| `RAG_AUTH_API_KEY` / `RAG_AUTH_JWT_SECRET` | 启用认证时必填，不得提交 |
| `KI_CORS_ORIGINS` | 精确 Origin 列表；默认本机 5173/4173 和 Tauri Origin |
| `RAG_LLM_PROVIDER` | 本地降级、OpenAI-compatible API 或 Ollama |
| `RAG_EMBED_PROVIDER` | 默认本地 hashing；`api` 使用 OpenAI-compatible embeddings |
| `RAG_VECTOR_STORE_PROVIDER` | 默认 SQLite；`qdrant` 启用 local mode |

CORS 不接受 `*`，不启用 cookie credentials。其他主机名的页面必须把完整 Origin 加入允许列表。

## 7. 桌面应用

```powershell
npm run frontend:build
npm run desktop:dev
cargo check --manifest-path src-tauri/Cargo.toml
npm run desktop:build:windows
```

Tauri 打包 `frontend/dist/` 并启动 `127.0.0.1:8765` sidecar。bundle 成功后仍需在安装应用中验证 sidecar、REST、SSE 和核心用户流程；macOS/Linux 必须在目标平台单独构建。

## 8. Obsidian 插件

```powershell
npm --prefix integrations/obsidian-plugin test
npm --prefix integrations/obsidian-plugin run typecheck
npm --prefix integrations/obsidian-plugin run build
```

插件仅支持桌面 Obsidian。测试、类型检查和构建应串行执行；浏览器不持有插件 Bearer token。

## 9. Docker 双服务

```powershell
Copy-Item ops/docker/.env.example ops/docker/.env
docker compose --project-directory ops/docker -f ops/docker/compose.yaml config
ops\docker\start.ps1 -NoOpen
```

- 前端：`http://127.0.0.1:4173`
- 后端健康：`http://127.0.0.1:8765/api/health`
- API 文档：`http://127.0.0.1:8765/docs`

Compose 分别构建前端和后端镜像。Nginx 只服务静态文件，不反向代理 API；`KI_PUBLIC_API_URL` 必须是浏览器可达地址，`KI_CORS_ORIGINS` 必须包含页面 Origin。
