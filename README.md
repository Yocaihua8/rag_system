# Knowledge Island
Knowledge Island 是面向个人开发学习的本地项目知识教练。它把项目代码、文档和笔记整理为可检索资料，通过有来源的问答、项目知识分析、覆盖评估和学习计划，帮助用户理解当前项目；经用户预览和确认后，还可以由 Obsidian 桌面插件把受管成果发布回 Vault。

当前正式版本为 `v2.0.0`。默认业务入口是 Vue 3 + FastAPI 本地 Web 应用；Tauri 2 复用同一前端并携带后端 sidecar；Obsidian Bridge 是独立的 desktop-only 插件。旧 PySide6 实现已归档到 `archive/src-desktop-legacy/`，不参与当前运行链路。

## 当前状态

| 项目面 | 当前事实 |
|--------|----------|
| 产品版本 | `v2.0.0` 已发布；历史发布证据见 `docs/release/V2_0_0_READINESS_2026-07-24.md` |
| Web 主入口 | `app.py` 启动 FastAPI/Uvicorn，默认监听 `127.0.0.1:8765` |
| 前端入口 | `教练 / 学习地图 / 学习计划 / 资料 / 设置`；使用应用状态切页，不使用 URL Router |
| 本地数据 | 默认写入 `runtime/v2/app.db`；正式 Web 启动会拒绝把非空旧代际库当作 v2 库写入 |
| 桌面壳 | Tauri 2 + 后端 sidecar；Windows NSIS 为默认 bundle，macOS/Linux 通过单独命令构建 |
| Obsidian | 独立桌面插件同步 Markdown 事件，只执行主应用已确认的受控发布，不覆盖冲突文件 |
| 授权状态 | 仓库公开，但当前没有 `LICENSE`；公开可读不等于已经授予开源使用权 |

## 已实现能力

- 项目目录、浏览器文件/文件夹、文本笔记、GitHub 仓库、Notion ZIP、Obsidian Vault 和受控网页抓取等后端导入能力；不同入口在当前主界面的可达范围并不完全相同。
- 文档分块、BM25 风格关键词召回、本地 hashing 向量、可选 OpenAI-compatible Embedding、可选 Qdrant local mode 和可选 Cross-Encoder rerank。
- 同源 HTTP API 与 SSE 流式问答；无模型时生成本地来源组合回答，模型调用失败时明确回退并返回 warning。
- 项目聊天线程、消息分支、来源抽屉、回答反馈、检索调试/复盘、双模型对比和两个只读 Agent 工具。
- 基于真实来源的项目分析、知识点、通用技能映射、项目覆盖评估、学习计划草稿/确认/进度和历史版本。
- Obsidian 配对、增量 Markdown 事件同步、离线事件重放、发布预览、确认后排队、冲突阻断和执行结果回报。
- 可选共享 API Key + HS256 JWT 保护。认证默认关闭，当前不是多用户、团队、租户或 RBAC 系统。

详细功能边界见 [`docs/features/README.md`](docs/features/README.md)；94 个当前 HTTP 操作的字段级契约以 [`docs/design/api-spec.md`](docs/design/api-spec.md) 为准，FastAPI OpenAPI 仅作为操作清单和调试入口。

## 已知边界

- 产品评价只描述“当前项目、当前来源版本”的知识覆盖，不代表整体职业能力。
- v2 不自动迁移、删除或覆盖 1.x 数据；用户需要在 v2 中重新导入项目。
- 当前主资料弹窗没有暴露全部后端导入/管理能力；部分可见控件尚未接线，具体缺口记录在 `docs/BACKLOG.md § 6`。
- `/api/health` 只是进程活性检查，不验证 SQLite、LLM、Embedding 或 Qdrant 的完整可用性。
- Tauri 静态配置和构建通过不等于安装包内 WebView 到 sidecar 的 API 连通性已经被动态覆盖；原生运行时仍需按发布清单验证。
- Windows 发布安装包未签名；macOS/Linux v2 原生产物不由 Windows 发布证据替代。

## 快速开始

### 前置要求

- Python 3.10+
- Node.js 20+ 与 npm
- Git
- 可选：Ollama（本地生成模型）
- 可选：`pymupdf`（PDF 正文抽取）

### Windows

```powershell
git clone https://github.com/Yocaihua8/rag_system.git
Set-Location rag_system

python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt

npm ci
npm run build

Copy-Item .env.example .env
.\.venv\Scripts\python.exe app.py
```

浏览器访问 `http://127.0.0.1:8765`。生产启动要求 `backend/static_dist/index.html` 已存在，因此首次运行前必须先执行 `npm run build`。

macOS/Linux 对应命令和 Docker 启动方式见 [`docs/guides/setup.md`](docs/guides/setup.md)。

## 配置原则

- 未配置 LLM 时，问答使用检索片段生成本地回答。
- `RAG_LLM_PROVIDER=api` 使用 OpenAI-compatible chat completion；`ollama` 使用本地 Ollama。
- `RAG_EMBED_PROVIDER=api` 且配置有效时调用 OpenAI-compatible `/embeddings`；其他情况使用本地 `hashing-96`。当前活动 Embedding factory 不接入 Ollama Embedding。
- `RAG_VECTOR_STORE_PROVIDER=qdrant` 启用 Qdrant local mode；不可用时回退 SQLite 兼容副本。
- API Key 优先放在操作系统环境变量或未提交的 `.env` 中。模型 Profile 只保存 `env:*` / `saved:*` 引用，接口不返回明文 Key。

完整变量、可选依赖和降级路径见 [`docs/guides/setup.md`](docs/guides/setup.md) 与 [`docs/guides/security.md`](docs/guides/security.md)。

## 开发与验证

```powershell
# Python 后端与 Web 契约
.\.venv\Scripts\python.exe -m pytest tests\test_backend tests\test_webapp -q

# Vue 单测与构建
npm run test:unit
npm run build

# 浏览器主流程（先构建，再启动隔离后端）
npm run test:e2e

# 文档门禁
pwsh -NoProfile -File scripts\check-placeholders.ps1
pwsh -NoProfile -File scripts\check-doc-links.ps1
.\.venv\Scripts\python.exe scripts\check_docs_consistency.py
```

Obsidian 插件在 `integrations/obsidian-plugin/` 下独立执行：

```powershell
Set-Location integrations\obsidian-plugin
npm ci
npm test
npm run typecheck
npm run build
```

Tauri 命令：

```powershell
npm run tauri:dev
npm run tauri:build:windows
```

`tauri:dev` 不会自动构建 sidecar；Windows 正式 bundle 使用 `tauri:build:windows`。完整测试矩阵见 [`docs/guides/testing.md`](docs/guides/testing.md)。

## 目录结构

```text
.
├── app.py                         # FastAPI/Uvicorn 默认入口
├── backend/                       # API、领域逻辑、配置、provider、SQLite
├── frontend/                      # Vue 3 源码
├── src-tauri/                     # Tauri 桌面壳
├── integrations/obsidian-plugin/  # Obsidian Bridge
├── tests/                         # backend/webapp pytest
├── e2e/                           # Playwright 主流程
├── ops/                           # 本地运维脚本
├── docs/                          # 正式文档、计划、日志和历史快照
├── archive/src-desktop-legacy/    # 只读历史实现
└── runtime/v2/                    # 默认 v2 运行数据（不入库）
```

## 文档入口

| 入口 | 用途 |
|------|------|
| [`docs/README.md`](docs/README.md) | 文档地图、阅读顺序、状态和维护规则 |
| [`docs/requirements/`](docs/requirements/) | 产品范围、功能模块、用例和 v2.0.0 范围冻结 |
| [`docs/design/`](docs/design/) | 架构、API、数据库、权限、状态流和前后端契约 |
| [`docs/features/`](docs/features/) | 功能行为与实现边界 |
| [`docs/guides/`](docs/guides/) | 搭建、测试、发布、安全、运维和排障 |
| [`docs/adr/`](docs/adr/) | 架构决策记录 |
| [`docs/BACKLOG.md`](docs/BACKLOG.md) | 待办、技术债和已知问题 |
| [`template-mapping.md`](template-mapping.md) | docs-template 1.0.0 的 profile、packs 和项目扩展映射 |

贡献前请阅读 [`CONTRIBUTING.md`](CONTRIBUTING.md)、[`CODE_OF_CONDUCT.md`](CODE_OF_CONDUCT.md) 和 [`SECURITY.md`](SECURITY.md)。
