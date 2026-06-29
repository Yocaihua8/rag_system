# 开发环境与启动

> 状态：Active
> Owner：RAG 团队
> Last Updated：2026-06-26

## 1. 环境要求

- Python 3.10+（仓库默认以 3.11 为主）
- Node.js 20+ / npm 10+（B-141 起用于 Vue 3 + Vite 前端构建；当前本机验证为 Node 24 + npm 11）
- Rust stable + Cargo + rustup（仅 B-145 Tauri Windows 桌面打包需要；Web MVP 浏览器模式不需要）
- Windows WebView2 + MSVC Build Tools（仅 B-145 Tauri Windows 桌面打包需要）
- Web MVP 不强依赖 Ollama 或 API Key；配置 Ollama 或 DeepSeek Key 后可启用真实 LLM 回答
- 可选：Ollama 本地服务（B-146 起可作为 Web MVP 本地 LLM provider）
- 可选：API Key（DeepSeek/OpenAI/兼容端点）
- 可选：`pymupdf`（Web MVP PDF 正文抽取；未安装时 PDF 会明确跳过）
- 可选：`sentence-transformers`（B-125 起用于本地 Cross-Encoder Reranker；未安装时自动跳过）

## 2. 最小启动步骤

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
npm install
npm run build
cp .env.example .env
cp .env .env.local # 按需
```

启动默认 Web MVP：

```bash
.venv\Scripts\python.exe app.py
```

浏览器打开：

```text
http://127.0.0.1:8765
```

当前默认入口使用 FastAPI + Uvicorn、SQLite、可选 Qdrant local mode 和 Vue/Vite 生产前端；`pip install -r requirements.txt` 会安装必需 Web 运行时和 Qdrant Python client。Web 端 DeepSeek / OpenAI 兼容调用仍使用 Python 标准库 `urllib`，不依赖 `openai` SDK。PDF 正文抽取是可选能力，需要额外执行 `pip install pymupdf`；未安装时 PDF 会返回 `pdf extraction requires optional parser` 并继续处理其他文件。旧 PySide6 桌面端代码已归档到 `archive/src-desktop-legacy/`，不再参与 Web/Tauri 启动链路。

B-141A 起仓库包含 Vue 3 + Vite 前端工程骨架。生产构建命令：

```powershell
npm run build
```

构建产物输出到 `webapp/static_dist/`，该目录不入库。`python app.py` 只服务 `webapp/static_dist/`；未构建或构建产物缺失时会在启动阶段提示先执行 `npm run build`，不再回退到 legacy `webapp/static/`。

Docker 镜像构建会在独立 Node 阶段执行 `npm ci && npm run build`，并把生成的 `webapp/static_dist/` 复制到最终 Python 镜像中。运行阶段只安装 `requirements-docker.txt` 中的 Web 运行依赖，并以非 root `appuser` 启动。因此 Docker 启动不需要宿主机提前执行 `npm run build`，但重新拉取或修改前端源码后仍需重新 `docker compose --project-directory . -f compose.yaml up --build -d`。

## 3. Tauri Windows 桌面打包验证（B-145）

Tauri 桌面壳复用同一份 Vue/Vite 生产构建产物和 FastAPI API。Windows 打包前需要额外安装开发依赖：

```powershell
pip install -r requirements-dev.txt
npm install --include=optional
```

`npm install --include=optional` 用于确保 `@tauri-apps/cli` 的 Windows native binding（例如 `@tauri-apps/cli-win32-x64-msvc`）被安装；如果 `npx tauri --version` 提示缺少 native binding，先重跑该命令。

完整 Tauri 构建还需要 Rust stable MSVC 工具链。可用以下命令检查：

```powershell
cargo --version
rustc --version
rustup --version
```

如果新终端找不到 `cargo`，确认 `%USERPROFILE%\.cargo\bin` 已加入当前 PowerShell 的 `Path`。

单独构建 FastAPI sidecar：

```powershell
.\scripts\build-backend-sidecar.ps1
```

该脚本会先执行 `npm run build`，再用 PyInstaller 打包 `app.py`，并生成：

```text
src-tauri/binaries/knowledge-island-backend-x86_64-pc-windows-msvc.exe
```

完整 Windows Tauri 打包命令：

```powershell
npm run tauri:build:windows
```

该命令会先运行 `scripts/build-backend-sidecar.ps1`，再执行 `tauri build`。本机必须能运行 `cargo`；未安装 Rust 工具链时，`npx tauri info` 会显示 `rustc` / `Cargo` 缺失，需先安装 rustup。

首次 Windows installer 打包会下载并缓存 Tauri 管理的 NSIS 工具包；如果下载超时，先确认网络/代理后重试。成功后会生成：

```text
src-tauri/target/release/bundle/nsis/Knowledge Island_0.1.0_x64-setup.exe
```

启用 API Key + JWT 认证（可选）：

```powershell
$env:RAG_AUTH_ENABLED = "1"
$env:RAG_AUTH_API_KEY = "replace-with-your-local-admin-key"
$env:RAG_AUTH_JWT_SECRET = "replace-with-a-long-random-secret"
$env:RAG_AUTH_JWT_TTL_SECONDS = "3600" # 可选，最小 60 秒
.venv\Scripts\python.exe app.py
```

默认不设置 `RAG_AUTH_ENABLED` 时认证关闭。认证启用后，`/api/health` 和静态首页仍可无凭证访问，其他 `/api/*`、`/docs`、`/redoc`、`/openapi.json` 需要 `X-API-Key` 或 Bearer JWT。第一版没有登录页；脚本或后续客户端可先用 `POST /api/auth/token` 携带 `X-API-Key` 换取短期 JWT。

## 4. Docker 一键启动

非技术用户优先使用根目录双击入口：

```text
Start-KnowledgeIsland-Docker.bat
Stop-KnowledgeIsland-Docker.bat
README-Docker-Quickstart.txt
```

双击启动后访问：

```text
http://127.0.0.1:8765
```

Windows PowerShell：

```powershell
.\scripts\docker_up.ps1
```

脚本会：

- 创建 `docker-workspace/` 作为 Docker 模式默认导入目录。
- 使用 `ki-runtime` named volume 作为容器 `/app/runtime` 持久化目录。
- 从 Windows User 环境读取 `DEEPSEEK_API_KEY` 并注入给 Compose（不打印 Key）。
- 从 Windows User 环境读取 `RAG_EMBED_API_KEY` 并注入给 Compose（不打印 Key）。
- 执行 `docker compose --project-directory . -f compose.yaml up --build -d`，镜像构建阶段会生成并内置 Vue/Vite 生产前端。
- 打开 `http://127.0.0.1:8765`。

Docker 模式下推荐优先使用 Web 侧栏的“选择本机文件夹导入”。浏览器会读取用户选择的本地项目文件夹，并把允许的文本文件、DOCX 和 PDF 二进制内容上传给本地服务入库；这种方式可以直接选择 `E:\Code\your-project`，不需要填写 Windows 路径。PDF 正文抽取需要镜像或运行环境安装可选 `pymupdf`，未安装时会在导入结果中显示跳过原因。

如果继续使用挂载目录导入，Web 页面创建项目空间时目录填写：

```text
/workspace
```

该路径对应宿主机的 `docker-workspace/`。如果要导入其他宿主机目录，可设置：

```powershell
$env:KNOWLEDGE_ISLAND_WORKSPACE="E:\Code\your-project"
.\scripts\docker_up.ps1
```

也可以直接使用 Compose：

```powershell
docker compose --project-directory . -f compose.yaml up --build -d
docker compose --project-directory . -f compose.yaml logs -f web
docker compose --project-directory . -f compose.yaml down
```

启用 DeepSeek 真实回答（可选）：

推荐方式是在 Web 页面打开 **设置 → 模型设置**，填写 API 地址、模型名和 API Key，然后点击“测试连接”。页面不会回显 API Key 明文。

同一个设置页也提供 **模型 Profile**。可保存多个 provider / API 地址 / 模型名组合，并选择一个默认 Profile 供问答优先使用。Profile 只保存 `api_key_ref`，例如 `env:RAG_LLM_API_KEY`、`env:DEEPSEEK_API_KEY` 或 `saved:RAG_LLM_API_KEY`，不会保存 API Key 明文；没有默认 Profile 时继续使用模型设置页的单配置行为。

同一个设置页也提供 **Prompt 预设**。可为当前项目空间保存“项目问答 / 代码解释 / 学习复盘”等本地预设，并选择一个默认预设影响真实 LLM 的回答风格和结构；该功能不需要新增依赖，不保存 API Key，也不会改变检索参数。

也可以使用 Windows User 环境变量：

```powershell
[System.Environment]::SetEnvironmentVariable("DEEPSEEK_API_KEY", "sk-xxx", "User")
[System.Environment]::SetEnvironmentVariable("RAG_LLM_PROVIDER", "api", "User")
```

重启终端后再运行 `app.py`。未配置 API Key 时，Web 端自动使用本地片段回答。

Windows 上应用会读取 User/Machine 级持久环境变量；如果当前终端没有继承新设置的 `DEEPSEEK_API_KEY`，`load_settings()` 仍会尝试从 Windows 持久环境中读取。

启用 Ollama 本地真实回答（可选）：

Tauri/Web 首次运行时，工作台顶部的 **首次运行向导** 会调用 `/api/ollama/status` 检测本机 Ollama，并可通过 `/api/ollama/pull` 拉取 `qwen2.5:3b`、`qwen2.5:7b` 或 `deepseek-r1:8b`。该向导不自动安装或启动 Ollama；如果服务不可达，需要先手动安装并启动 Ollama。

1. 安装并启动 Ollama。
2. 拉取默认模型：

```powershell
ollama pull qwen2.5:7b
```

3. 在 Web 页面打开 **设置 → 模型设置**，选择 provider 为 `ollama`，API 地址填写 `http://localhost:11434`，模型名填写 `qwen2.5:7b`，API Key 留空。

也可以使用环境变量：

```powershell
[System.Environment]::SetEnvironmentVariable("RAG_LLM_PROVIDER", "ollama", "User")
[System.Environment]::SetEnvironmentVariable("RAG_OLLAMA_HOST", "http://localhost:11434", "User")
[System.Environment]::SetEnvironmentVariable("RAG_OLLAMA_MODEL", "qwen2.5:7b", "User")
```

Ollama 不可达时，`OllamaLLM.is_available()` 会输出 `WARNING`，不会阻断 Web MVP 启动；问答会继续回退到本地片段回答。

启用真实 Embedding（可选）：

```powershell
[System.Environment]::SetEnvironmentVariable("RAG_EMBED_PROVIDER", "api", "User")
[System.Environment]::SetEnvironmentVariable("RAG_EMBED_API_BASE", "https://api.openai.com/v1", "User")
[System.Environment]::SetEnvironmentVariable("RAG_EMBED_API_MODEL", "text-embedding-3-small", "User")
[System.Environment]::SetEnvironmentVariable("RAG_EMBED_API_KEY", "sk-xxx", "User")
```

Embedding 服务必须支持 OpenAI-compatible `/embeddings`。未配置或请求失败时，Web MVP 会回退到本地 hashing 向量，导入不中断。

启用 Qdrant 向量索引（可选）：

```powershell
[System.Environment]::SetEnvironmentVariable("RAG_VECTOR_STORE_PROVIDER", "qdrant", "User")
[System.Environment]::SetEnvironmentVariable("RAG_QDRANT_PATH", "$env:APPDATA\KnowledgeIsland\qdrant", "User")
[System.Environment]::SetEnvironmentVariable("RAG_QDRANT_COLLECTION", "knowledge_island_chunks", "User")
[System.Environment]::SetEnvironmentVariable("RAG_QDRANT_VECTOR_SIZE", "96", "User")
```

Qdrant 以 local mode 运行，不需要独立服务。未启用、依赖缺失或查询失败时，Web MVP 会打印 `WARNING` 并回退 SQLite `chunk_vectors`。

启用 Cross-Encoder Reranker 精排（可选）：

```powershell
pip install sentence-transformers
[System.Environment]::SetEnvironmentVariable("RAG_RERANKER_ENABLED", "true", "User")
[System.Environment]::SetEnvironmentVariable("RAG_RERANKER_MODEL", "cross-encoder/ms-marco-MiniLM-L-6-v2", "User")
```

Reranker 默认关闭。启用后，Web MVP 会在 BM25 + 向量混合召回后，对候选 chunk 做本地 Cross-Encoder 精排，并在命中来源中写入 `rerank_score`。`sentence-transformers` 未安装时会输出 `WARNING` 并跳过精排，检索和问答继续按原排序运行。

## 5. 常见校验

- 检查 `http://127.0.0.1:8765/api/health` 是否返回 `{"status": "ok"}`。
- FastAPI 自动接口文档可访问 `http://127.0.0.1:8765/docs`，但正式契约以 `docs/design/api-spec.md` 为准。
- 如果启用了 `RAG_AUTH_ENABLED=1`，访问 `/api/projects` 无凭证应返回 `401 {"error":"authentication required"}`；携带正确 `X-API-Key` 或 `Authorization: Bearer <jwt>` 应返回 200。
- 创建项目空间时，本地目录必须对当前后端进程真实存在；Docker 模式下 Windows 路径不会直接存在于容器内，推荐改用“选择本机文件夹导入”。
- Web MVP 无 Ollama、无 API Key 时仍可导入文本与 DOCX 正文并进行关键词问答。
- Web MVP 配置 Ollama 后，`/api/answer` 可优先请求本地 Ollama `/api/chat`；服务不可达或请求失败时回退到本地片段回答。
- Web MVP 配置 DeepSeek Key 后，`/api/answer` 会优先请求 OpenAI-compatible Chat Completions；请求失败时回退到本地片段回答。
- Web MVP 设置默认模型 Profile 后，`/api/answer` 会优先使用该 Profile 的 provider、API 地址、模型名、温度、最大 tokens 和 Key 引用；Ollama Profile 不需要 API Key；没有默认 Profile 时继续使用现有单配置。
- Web MVP 每次提问后会在 SQLite 中保存当前项目的聊天记录；刷新页面或切换项目后，工作台会通过 `/api/chat/messages` 重新加载最近对话。真实 LLM 回答会带入同项目最近 3 轮历史作为上下文。
- Web MVP 工作台的 Agent 工具当前只开放只读 `project_overview` 和 `search_sources`，会写入 `agent_tool_runs` 审计记录；不开放 shell、任意命令执行或任意文件写入。
- Web MVP 工作台会通过 `/api/agent/tools/runs` 展示当前项目工具运行历史，用于查看工具名、状态、查询参数和错误原因。
- Web MVP 问答没有可用来源时，回答区显示建议工具 `search_sources` 和查询词，并提供按钮让用户手动运行；不会自动执行工具。
- Web MVP 用户运行 `search_sources` 后，下一轮问答会显式携带该 `tool_run_id`，把工具命中的来源片段合并进回答上下文；跨项目或非成功工具记录会被拒绝。
- Web MVP 工作台提供检索调试区域，可用当前查询词临时调整 `top_k`、最低分、关键词/向量开关，并查看命中 chunk、分数、来源质量和上下文预览；这些参数不持久化。
- Web MVP 设置 `RAG_VECTOR_STORE_PROVIDER=qdrant` 后，导入/更新/删除会同步 Qdrant local collection，搜索的向量候选由 Qdrant 返回；未启用或失败时仍可用 SQLite `chunk_vectors` fallback。
- Web MVP 设置 `RAG_RERANKER_ENABLED=true` 且安装 `sentence-transformers` 后，搜索和问答来源可返回 `rerank_score`；未安装依赖或未启用时 `rerank_score` 为 `null`。
- B-145 Tauri Windows 打包前可运行 `npx tauri info` 检查 WebView2、MSVC、Rust、Cargo 和 `frontendDist`；完整打包命令为 `npm run tauri:build:windows`。
- Web MVP 工作台可将一次检索诊断保存为检索复盘记录，记录查询词、参数、命中来源、来源质量和人工备注，便于后续补资料或调参。
- Web MVP 配置 `RAG_EMBED_PROVIDER=api` 和 `RAG_EMBED_API_KEY` 后，导入 chunk 时会优先请求 OpenAI-compatible Embeddings；请求失败时回退本地向量。
- Web MVP 资料库页可直接导入文本笔记；笔记会作为当前项目空间的 `note:` 虚拟来源参与检索和问答，不依赖磁盘文件是否存在。
- Web MVP 资料库页可创建文档集合，并把文档加入或移出集合；集合只影响资料库列表过滤，删除集合不会删除文档。
- 模型设置页可通过 `GET/POST /api/settings/llm` 读取或保存 API Base、模型名和 API Key 状态，并通过 `/api/settings/llm/test` 做连接测试。
- 模型 Profile 可通过 `GET/POST /api/model-profiles` 等接口管理，测试指定 Profile 不会覆盖 `.env` 或自动切换默认 Profile。
