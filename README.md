# Knowledge Island

Knowledge Island 当前是面向个人开发学习的本地项目知识教练，并正在按已批准规格重构为桌面优先、本地优先的通用项目 Agent。现有 v2 仍是可运行基线；v3 目标能力只有在对应代码和测试完成后才视为可用。

当前正式版本为 `v2.0.0`。Vue 前端、FastAPI 后端和 Tauri 桌面壳拥有独立依赖与构建边界；Obsidian Bridge 继续作为独立 desktop-only 插件维护。

## 当前边界

| 项目面 | 当前事实 |
|--------|----------|
| 后端 | `python -m backend`，默认 `http://127.0.0.1:8765`；只提供 API、SSE 和接口文档，根路由返回 404 |
| 前端 | Vue 3 + Vite，开发端口 `5173`，预览/Docker 端口 `4173`，构建产物为 `frontend/dist/` |
| 通信 | `VITE_API_BASE_URL` 生成绝对 API URL；后端以精确 CORS allowlist 接受本机前端和 Tauri Origin |
| 数据 | 默认 `runtime/v2/app.db`；不自动迁移、删除或覆盖 1.x 数据 |
| 桌面 | Tauri 2 打包 `frontend/dist/` 并启动只含后端的 sidecar |
| Obsidian | 独立插件同步 Markdown 事件，只执行用户已确认的受控发布，不覆盖冲突文件 |
| 发布 | `v2.0.0` 已发布；Windows x64 NSIS 未签名，其他目标平台需从当前源码独立验证 |

`/api/health` 只证明 HTTP 进程可响应，不代表 SQLite、LLM、Embedding、Qdrant 或完整问答流程就绪。

## 已实现能力

- 项目目录、浏览器文件/文件夹、文本笔记、GitHub 仓库、Notion ZIP、Obsidian Vault 和受控 URL 的导入能力。
- 文档分块、BM25 关键词召回、本地 hashing 向量、可选 OpenAI-compatible Embedding、可选 Qdrant local mode 和可选 Cross-Encoder rerank。
- HTTP API 与 SSE 流式问答；模型不可用时明确回退到有来源的本地回答。
- 多会话聊天、来源抽屉、回答反馈、检索诊断/复盘、双模型对比和两个只读 Agent 工具。
- 项目分析、知识点和技能映射、项目覆盖评估、定向评估、逐知识点交互学习和版本化学习计划；项目存在可解析 SQLite Schema 证据时可生成隔离的只读 SQL 练习。
- Obsidian 配对、增量事件、离线重放、发布预览、用户确认、冲突阻断和结果回报。
- 可选共享 API Key + HS256 JWT；默认关闭，当前不是多用户、团队、租户或 RBAC 系统。

主界面仍有少量未接线控件；正式边界和后续事项见 [`docs/features/`](docs/features/) 与 [`docs/BACKLOG.md`](docs/BACKLOG.md)。

## 快速开始

前置：Python 3.10+、Node.js 20+、npm、Git。

```powershell
git clone https://github.com/Yocaihua8/rag_system.git
Set-Location rag_system

python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r backend/requirements/dev.txt
npm ci
Copy-Item backend/.env.example backend/.env
```

终端一：

```powershell
.\.venv\Scripts\python.exe -m backend
```

终端二：

```powershell
npm run frontend:dev
```

浏览器访问 `http://127.0.0.1:5173`。前端默认访问 `http://127.0.0.1:8765`；需要其他地址时，在前端构建环境中设置 `VITE_API_BASE_URL`。

## 常用命令

```powershell
# 前端
npm run frontend:dev
npm run frontend:test
npm run frontend:build
npm run frontend:e2e

# 后端
.\.venv\Scripts\python.exe -m pytest tests/backend tests/integration tests/repository -q
.\.venv\Scripts\python.exe -m backend

# 桌面
npm run desktop:dev
npm run desktop:build:windows

# Docker
ops\docker\start.ps1
ops\docker\stop.ps1
```

Obsidian 插件独立验证：

```powershell
npm --prefix integrations/obsidian-plugin ci
npm --prefix integrations/obsidian-plugin test
npm --prefix integrations/obsidian-plugin run typecheck
npm --prefix integrations/obsidian-plugin run build
```

完整搭建、测试和 Docker 说明见 [`docs/guides/`](docs/guides/)。

## 仓库结构

```text
.
├── backend/                 # Python 入口、依赖、API、领域、存储、后端镜像
├── frontend/                # Vue/Vite/Vitest/Playwright、dist、Nginx、前端镜像
├── src-tauri/               # Tauri npm 工具、Rust 壳与 sidecar 脚本
├── integrations/            # 独立 Obsidian 插件
├── ops/docker/              # Compose、环境样例与启停脚本
├── scripts/                 # 文档链接、占位符和源码事实检查
├── tests/                   # backend、integration、repository、e2e
└── docs/
    ├── requirements/        # 背景、用例和版本范围
    ├── design/              # 统一系统设计与契约
    ├── features/            # 逐项用户功能规格
    ├── adr/                 # Accepted 架构决策
    ├── guides/              # 搭建、测试、运行、发布和协作
    ├── devlog/              # 按年月组织的开发过程日志
    └── plans/               # 执行中 plan 与模板
```

根 npm 清单只编排 `frontend` 与 `src-tauri` 两个 workspace。运行数据、用户 `.env`、虚拟环境、依赖目录和临时目录不属于源码。

## 文档入口

- [`docs/README.md`](docs/README.md)：文档地图与事实优先级
- [`docs/requirements/`](docs/requirements/)：产品背景、目标用户、用例和维护版本范围
- [`docs/design/`](docs/design/)：完整系统、API、数据、权限、状态与 UI 契约
- [`docs/features/`](docs/features/)：逐项用户能力和当前可达性
- [`docs/adr/`](docs/adr/)：Accepted 架构决策
- [`docs/guides/`](docs/guides/)：搭建、测试、运行、发布、安全和协作
- [`docs/plans/`](docs/plans/)：执行中 plan 与模板，任务完成后删除活动 plan
- [`docs/devlog/`](docs/devlog/)：每日过程、问题、决定和下一步
- [`docs/BACKLOG.md`](docs/BACKLOG.md)：仅保存未完成事项

过程事实进入每日 DevLog；已完成且对使用者/维护者有意义的事实进入 [`CHANGELOG.md`](CHANGELOG.md) 和 Git 历史。继续禁止 readiness 快照、已验收 preview 和完成 plan 归档。

贡献前请阅读 [`CONTRIBUTING.md`](CONTRIBUTING.md)、[`CODE_OF_CONDUCT.md`](CODE_OF_CONDUCT.md)、[`SECURITY.md`](SECURITY.md) 和 [`AGENTS.md`](AGENTS.md)。
