# 架构总览

> 状态：Active
> Owner：RAG 团队
> Last Updated：2026-08-01
> Scope：当前源码分层、依赖方向和运行时约束
> Related：`system-design-overview.md`、`api-spec.md`、`database-design.md`、`permission-matrix.md`、`../adr/ADR-010-runtime-separation.md`

## 1. 运行时拓扑

```text
浏览器 / Tauri WebView
  Vue + Vite（dev 5173，preview/Docker 4173）
              │ VITE_API_BASE_URL；REST + SSE
              ▼
FastAPI API（127.0.0.1:8765）
  backend/api + backend/routes
              │ 参数校验与用例编排
              ▼
领域服务（backend/domain）
  导入、检索、回答、Coach、Obsidian、只读 Agent 工具
              │ 唯一持久化边界
              ▼
SQLite + 可选 Qdrant local mode
  runtime/v2/app.db + runtime/v2/vectors/qdrant
```

- `python -m backend` 启动 API；FastAPI 不读取或托管 `frontend/dist`。
- `frontend/` 拥有 Vue、Vite、Vitest、Playwright、Nginx 配置和前端构建产物。
- `src-tauri/` 打包 `frontend/dist`，sidecar 只承载后端。
- `integrations/obsidian-plugin/` 是独立工程，不进入根 npm workspace。
- `ops/docker/compose.yaml` 编排独立前端、后端服务；前端不反向代理 API。

端口、CORS、CSP 和运行时拆分决策见 [ADR-010](../adr/ADR-010-runtime-separation.md)。

## 2. 代码分层

| 层 | 路径 | 职责 | 禁止依赖 |
|----|------|------|----------|
| 入口与配置 | `backend/__main__.py`、`backend/config/` | 加载环境、路径和 Uvicorn 配置 | 页面状态、业务 SQL |
| HTTP 适配 | `backend/api/`、`backend/routes/` | CORS/认证、参数校验、响应映射、SSE、用例分发 | 直接操作 SQLite |
| 领域 | `backend/domain/` | 导入、检索、回答、Coach、Agent、Obsidian 规则 | FastAPI Request/Response、页面组件 |
| 存储 | `backend/storage/` | Schema 初始化和全部 SQLite 读写 | 页面规则、HTTP 对象 |
| 表现 | `frontend/src/` | 状态展示、输入、API 调用和用户交互 | SQL、服务端权限或业务结论重算 |
| 桌面/插件 | `src-tauri/`、`integrations/obsidian-plugin/` | 原生承载与受控 Vault 交互 | 复制领域规则、绕过 HTTP 权限 |

依赖方向是“入口/表现 → HTTP → 领域 → 存储”。跨层需要新增能力时先在领域和契约中定义，不把业务规则写进 Vue、Tauri 或插件。

## 3. HTTP 与浏览器边界

- 当前公开契约共有 86 个唯一 `/api` 路径、94 个 GET/POST 操作（31 GET、63 POST）。
- `GET /api/answer/stream` 与 `POST /api/ollama/pull` 在 FastAPI 中单独注册为 SSE；其余业务操作由 `/api/{path:path}` 分发。
- Vue 的 `fetch` 和 `EventSource` 都从 `VITE_API_BASE_URL` 构造绝对 URL，默认 `http://127.0.0.1:8765`。
- 后端 CORS 只允许精确 Origin、GET/POST/OPTIONS 和 `Authorization`、`Content-Type`、`X-API-Key`；不允许通配符或 cookie credentials。
- 后端可选认证默认关闭。当前 Vue 不附加 API Key/JWT，原生 `EventSource` 也没有自定义认证 Header，因此启用认证后的浏览器主流程不是已完成链路。

## 4. 数据与模型边界

- v2 默认数据根为 `runtime/v2/`；正式应用启动在写入前验证 `app_metadata.data_generation=v2`。
- SQLite 是业务状态和向量兼容副本的权威源；Qdrant 只在启用时提供向量候选，失败时回退 SQLite。
- LLM、外部 Embedding、PDF 抽取和 Cross-Encoder 均可选；不可用时分别回退来源片段回答、hashing 向量、跳过 PDF 和保持原排序。
- 模型 Profile 只在 SQLite 保存受控 Key 引用。兼容全局 LLM 设置另有明文写入用户应用数据 `.env` 的行为，不能把两者混为同一安全语义。
- `GET /api/health` 只证明进程活性，不证明 SQLite、模型、Qdrant、Tauri sidecar 或完整用户流程就绪。

## 5. 界面集成边界

- `frontend/src/App.vue` 是页面装配、共享状态和 API 用例的唯一集成 Owner。
- 当前主视图键只有 `coach`、`learning-map`、`learning-plan`、`settings`；资料使用 `LibraryModal`，不是路由或第五个 `currentView`。
- `vue-router` 未使用，`pinia` 虽已声明依赖但当前未接入。
- `LibraryView`、`AssessmentView` 等兼容组件存在不代表主导航可达。
- 来源、覆盖、评估、计划权限和发布状态以后端响应为准，前端不得重新推导或伪造。

## 6. 不允许的耦合

- FastAPI 托管前端或前端/Nginx 反向代理 API。
- API/routes 层直接写 SQL，或前端/Tauri/插件直接访问 SQLite。
- 组件内散落 `fetch`、复制 `App.vue` 状态机或在浏览器重算业务状态。
- Agent 工具执行 shell、文件写入或未列入白名单的操作。
- Obsidian 插件跳过预览确认、受管标记、路径和 hash 校验。
- 将静态构建、`/api/health` 或安装包生成误作端到端运行证明。
