# ADR-010 前后端运行时分离

> 状态：Accepted
> Date：2026-08-01
> Owner：RAG 团队
> Related：docs/architecture/overview.md, docs/architecture/backend/api.md, docs/operations/setup.md, docs/integrations/desktop.md

## 1. 背景

Vue 构建产物曾输出到后端静态目录并由 FastAPI 托管，开发、Docker 和 Tauri 也依赖同源 `/api`。这使前端依赖、构建产物和后端运行时互相绑定，并掩盖桌面 WebView 到 sidecar 的真实网络边界。

## 2. 决策

- FastAPI 采用 API-only 运行时，只提供 `/api/*`、`/docs`、`/redoc` 和 OpenAPI；`GET /` 返回 404，不再托管前端文件。
- 后端以 `python -m backend` 启动，默认监听 `127.0.0.1:8765`。
- Vue 以独立 workspace 构建到 `frontend/dist/`；开发端口为 `5173`，预览和 Docker 对外端口为 `4173`。
- 前端统一用 `VITE_API_BASE_URL` 构造 `fetch` 与 `EventSource` 的绝对 URL，默认 API 为 `http://127.0.0.1:8765`。
- 后端用 `KI_CORS_ORIGINS` 配置精确 Origin；默认只放行本机 `5173`、`4173`、`tauri://localhost` 和 `http://tauri.localhost`。不启用通配符或 cookie credentials，只允许 GET、POST、OPTIONS 及认证/内容类型请求头。
- Docker 使用前端和后端两个服务、两个镜像及两个健康检查；前端不反向代理 API。
- Tauri 直接打包 `frontend/dist/`，sidecar 只包含后端。CSP 的 `connect-src` 仅允许 Tauri IPC 与 `http://127.0.0.1:8765`。

## 3. 不变边界

本决策不修改 HTTP 方法、路径、请求/响应字段、SQLite Schema 或 Agent 工具权限白名单。跨域只改变浏览器访问地址与部署边界。

## 4. 影响与取代关系

ADR-006 的 Vue 3 + Vite 选型仍然有效；其中“构建到后端静态目录并由 FastAPI 托管”和“开发代理同源 `/api`”两项被本 ADR 取代。ADR-001 的 FastAPI 选择和 API 行为继续有效。

## 5. 验证

- 后端根路由 404，API、SSE、认证头、允许/拒绝 Origin 和 OPTIONS 契约通过。
- 前端单测断言绝对 API URL；Vitest、构建和 4173→18765 的真实跨域 E2E 通过。
- Compose 配置、双镜像、双健康检查和 4173→8765 访问通过。
- Tauri 结构契约、sidecar、CSP、原生构建和安装后 API 连通性分别验证并如实记录。
