# FastAPI 运行时迁移

> 状态：Active
> Owner：RAG 团队
> Last Updated：2026-05-28
> Scope：B-139 FastAPI + Uvicorn 运行时迁移边界；B-144 后端目录聚合后的启动与静态服务边界
> Related：docs/adr/ADR-001-fastapi-migration.md, docs/design/architecture-overview.md, docs/design/api-spec.md, docs/BACKLOG.md

## 1. 功能定位

B-139 是 Web MVP 的运行时技术栈迁移，不新增用户业务功能。迁移目标是把 HTTP 服务层从 Python stdlib `http.server` 切换到 FastAPI + Uvicorn，同时保持现有本地浏览器使用方式、API 契约和静态前端入口兼容。

## 2. 用户可见行为

- `python backend/app.py` 仍作为本地默认启动方式。
- 默认访问地址仍为 `http://127.0.0.1:8765`。
- B-144 后，静态首页只来自 Vue/Vite 构建产物 `backend/webapp/static_dist/`；构建产物缺失时返回 503 构建提示。
- `/api/*` 现有路径、请求字段、响应字段和错误格式保持兼容。
- `/api/answer/stream` 继续使用 SSE，事件名保持 `token`、`done`、`answer_error`。
- FastAPI 自动文档页面作为迁移后的接口调试入口提供，但不替代 `docs/design/api-spec.md`。

## 3. 非目标

- 不实现 B-140 认证中间件。
- 不启动 B-141 Vue 3 + Vite 前端工程化。
- 不修改 SQLite schema。
- 不迁移或删除 legacy `src/` 桌面端。
- 不改变导入、检索、回答、Agent 工具等业务规则。

## 4. 架构落点

FastAPI 只替换表现层 HTTP server 和路由适配方式。业务层仍由 `backend/webapp/answers.py`、`backend/webapp/search.py`、`backend/webapp/ingestion.py`、`backend/webapp/agent_tools.py` 等模块负责；数据层仍由 `backend/webapp/storage.py` 作为 SQLite 唯一入口。

## 5. 验收标准

- `/api/health` 返回 `{"status":"ok"}`。
- 静态首页可访问。
- 未知 `/api/*` 返回现有 JSON 错误格式。
- SSE 响应为 `text/event-stream`，并保持现有事件协议。
- `tests/test_webapp` 通过，或明确记录非 B-139 引起的既有失败。
