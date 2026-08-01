# 开发环境与启动

> 状态：Active
> Owner：RAG 团队
> Last Updated：2026-08-01
> Scope：独立后端、前端、桌面和插件的本地搭建
> Related：`../../README.md`、`../architecture/overview.md`、`testing.md`、`docker.md`

## 1. 前置要求

- Python 3.10+
- Node.js 20+ 与 npm
- Git
- 桌面构建：Rust/Cargo 和目标平台原生工具链
- 可选：Ollama、`pymupdf`、Qdrant/Cross-Encoder 运行依赖

## 2. 安装

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r backend/requirements/dev.txt
npm ci
Copy-Item backend/.env.example backend/.env
```

根 npm workspace 只安装 `frontend` 和 `src-tauri`。Obsidian 插件在 `integrations/obsidian-plugin/` 下独立执行 `npm ci`。

`backend/.env` 只用于本机配置且不得提交。模型 Key 优先放操作系统环境变量；Profile 只保存引用。

## 3. 本地运行

后端终端：

```powershell
.\.venv\Scripts\python.exe -m backend
```

后端默认监听 `http://127.0.0.1:8765`。可用入口：

- `GET /api/health`
- `/docs`
- `/redoc`
- `/openapi.json`

`GET /` 按设计返回 404。

前端终端：

```powershell
npm run frontend:dev
```

浏览器访问 `http://127.0.0.1:5173`。默认 API base 为 `http://127.0.0.1:8765`；覆盖示例：

```powershell
$env:VITE_API_BASE_URL = 'http://127.0.0.1:18765'
npm run frontend:dev
```

该值进入浏览器可见构建产物，不得放凭证。

## 4. 构建与预览

```powershell
npm run frontend:build
npm --workspace frontend run preview
```

构建输出为 `frontend/dist/`，预览默认端口 `4173`。FastAPI 不检查或托管该目录。

## 5. 后端配置

| 变量 | 默认/行为 |
|------|-----------|
| `RAG_RUNTIME_DIR` | 默认仓库内 `runtime/v2/` |
| `RAG_AUTH_ENABLED` | 默认关闭 |
| `RAG_AUTH_API_KEY` | 启用认证时的共享 API Key；不要提交 |
| `RAG_AUTH_JWT_SECRET` | 启用 JWT 时设置；不要提交 |
| `KI_CORS_ORIGINS` | 逗号分隔精确 Origin；默认本机 5173/4173 与 Tauri Origin |
| `RAG_LLM_PROVIDER` | 本地 fallback、OpenAI-compatible API 或 Ollama |
| `RAG_EMBED_PROVIDER` | 默认本地 hashing；`api` 使用 OpenAI-compatible embeddings |
| `RAG_VECTOR_STORE_PROVIDER` | 默认 SQLite；`qdrant` 启用 local mode并保留 SQLite fallback |

CORS 不接受 `*`，不启用 cookie credentials。若从其他主机名访问前端，必须显式加入该前端页面的 Origin。

## 6. 桌面

```powershell
npm run frontend:build
npm run desktop:dev
npm run desktop:build:windows
```

Tauri 打包 `frontend/dist/`，并启动 `127.0.0.1:8765` 后端 sidecar。静态配置或 bundle 成功不等于安装后 API 连通性已通过；需验证 sidecar、CORS、SSE 和核心流程。

## 7. Obsidian 插件

```powershell
npm --prefix integrations/obsidian-plugin ci
npm --prefix integrations/obsidian-plugin test
npm --prefix integrations/obsidian-plugin run typecheck
npm --prefix integrations/obsidian-plugin run build
```

插件为 desktop-only。浏览器不持有插件 Bearer token，不调用插件专用领取/回传接口。

## 8. Docker

Docker 通过 `ops/docker/` 的前后端双服务启动，详见 [`docker.md`](docker.md)。前端和后端地址必须同时对使用者可达，前端不会反向代理 API。
