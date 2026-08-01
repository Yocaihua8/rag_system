# FastAPI API-only 运行时

> 状态：Active
> Owner：RAG 团队
> Last Updated：2026-08-01
> Scope：FastAPI/Uvicorn 入口、路由、CORS 和静态文件边界
> Related：`../../architecture/backend/api.md`、`../../architecture/decisions/ADR-001-fastapi-migration.md`、`../../architecture/decisions/ADR-010-runtime-separation.md`

## 行为

- `python -m backend` 启动 Uvicorn，默认监听 `127.0.0.1:8765`。
- 运行时只提供 `/api/*`、SSE、`/docs`、`/redoc` 和 `/openapi.json`。
- `GET /` 返回 404；后端不检查、不复制、不托管 `frontend/dist/`。
- `backend/api/` 和 `backend/routes/` 只适配 HTTP，不直接操作 SQLite。

## CORS

默认允许以下精确 Origin：

- `http://127.0.0.1:5173`、`http://localhost:5173`
- `http://127.0.0.1:4173`、`http://localhost:4173`
- `tauri://localhost`、`http://tauri.localhost`

`KI_CORS_ORIGINS` 可用逗号分隔覆盖列表。不允许 `*`，不启用 cookie credentials，只允许现有 GET/POST/OPTIONS 和必要的 Authorization、Content-Type、X-API-Key 请求头。

## 兼容性

运行时分离不改变 HTTP 方法、路径、字段、错误格式、SSE 事件、SQLite Schema 或认证/Agent 权限。字段级契约继续以 [`../../architecture/backend/api.md`](../../architecture/backend/api.md) 为准。

## 验证

- 根路由 404；健康、OpenAPI 与既有 API 正常。
- 默认/自定义允许 Origin 返回正确 CORS header，拒绝 Origin 不获得放行。
- OPTIONS、认证 header 和 SSE 保持可用。
- 后端在不存在前端构建产物时仍能启动。
