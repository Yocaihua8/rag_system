# ADR-010 前后端运行时分离

> 状态：Accepted
> Date：2026-08-01
> Owner：RAG 团队
> Scope：统一系统内的进程、依赖、构建产物与部署边界
> Related：[系统设计总览](../design/system-design-overview.md)、[架构总览](../design/architecture-overview.md)、[API 规格](../design/api-spec.md)、[搭建指南](../guides/setup.md)、[运行手册](../guides/runbook.md)、[ADR-006](ADR-006-vue-vite-frontend.md)

## 1. 背景

Vue 构建产物曾输出到后端静态目录并由 FastAPI 托管，开发、Docker 和 Tauri 也依赖同源 `/api`。这使前端依赖、构建产物和后端运行时互相绑定，并掩盖浏览器或桌面 WebView 到后端进程的真实网络边界。

运行时分离只划分进程、依赖、构建产物和部署职责。Knowledge Island 仍是一个统一产品系统：Vue、Tauri 和 Obsidian 插件是客户端或承载层，FastAPI 编排同一组领域能力，SQLite 仍由后端存储层统一访问。该决策不建立彼此独立的“前端业务”和“后端业务”，也不复制接口、领域规则或数据模型。

## 2. 决策

- FastAPI 采用 API-only 运行时，只提供 `/api/*`、`/docs`、`/redoc` 和 OpenAPI；`GET /` 返回 404，不再托管前端文件。领域规则和 SQLite 访问继续留在后端既有边界内。
- 后端以 `python -m backend` 启动，默认监听 `127.0.0.1:8765`。
- Vue 是同一系统的 Web 表现层，以独立 workspace 构建到 `frontend/dist/`；开发端口为 `5173`，预览和 Docker 对外端口为 `4173`。
- 前端统一用 `VITE_API_BASE_URL` 构造 `fetch` 与 `EventSource` 的绝对 URL，默认 API 为 `http://127.0.0.1:8765`。
- 后端用 `KI_CORS_ORIGINS` 配置精确 Origin；默认只放行本机 `5173`、`4173`、`tauri://localhost` 和 `http://tauri.localhost`。不启用通配符或 cookie credentials，只允许 GET、POST、OPTIONS 及认证/内容类型请求头。
- Docker 为同一系统部署前端和后端两个服务、两个镜像及两个健康检查；前端不反向代理 API。
- Tauri 直接打包 `frontend/dist/`，sidecar 只包含后端；桌面壳不复制业务逻辑。CSP 的 `connect-src` 仅允许 Tauri IPC 与 `http://127.0.0.1:8765`。
- Obsidian 插件继续作为受限客户端调用后端 `/api/obsidian/*`，不因 Web 运行时分离获得额外存储或领域权限。

## 3. 不变边界

本决策不修改 HTTP 方法、路径、请求/响应字段、SQLite Schema 或 Agent 工具权限白名单。跨域只改变客户端访问地址与部署边界；所有客户端仍共享同一 API 契约和后端数据边界。

## 4. 影响与取代关系

| 既有决策 | 当前关系 |
|----------|----------|
| ADR-001 FastAPI | 框架选择、API、SSE 与 OpenAPI 行为继续有效；FastAPI 当前为 API-only |
| ADR-006 Vue 3 + Vite | 框架和构建工具选择继续有效；“构建到后端静态目录并由 FastAPI 托管”和“开发代理同源 `/api`”被本 ADR 取代 |

该取代只涉及运行时托管与网络边界，不把系统设计文档拆成前端/后端专题，也不改变 Vue、FastAPI、SQLite、Tauri、Docker 与 Obsidian 在统一系统中的协作关系。

## 5. 验证

- 后端根路由 404，API、SSE、认证头、允许/拒绝 Origin 和 OPTIONS 契约通过。
- 前端单测断言绝对 API URL；Vitest、构建和 4173→18765 的真实跨域 E2E 通过。
- Compose 配置、双镜像、双健康检查和 4173→8765 访问通过。
- Tauri 结构契约、sidecar、CSP、原生构建和安装后 API 连通性分别验证并如实记录。
