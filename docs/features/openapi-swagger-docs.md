# OpenAPI / Swagger 接口文档

> 状态：Active
> Owner：RAG 团队
> Last Updated：2026-07-01
> 关联 BACKLOG：B-136

## 1. 功能目标

为当前 Web MVP HTTP API 提供 OpenAPI 3.0 schema，使 `/openapi.json`、`/docs` 和 `/redoc` 能展示可读的接口清单、请求结构和响应结构。

## 2. MVP 范围

- 保留 FastAPI 默认 `/docs`、`/redoc` 和 `/openapi.json` 入口。
- 为兼容分发的 `/api/{path:path}` 端点补充显式 OpenAPI path schema。
- 覆盖当前 `docs/design/api-spec.md` 中列出的 Web MVP API。
- 认证开启时继续保护 `/docs`、`/redoc` 和 `/openapi.json`。
- schema 定义集中维护在 `backend/api/openapi_schema.py`，由 `backend.api.server.create_app()` 安装。

## 3. 边界

- 不改后端业务路由行为。
- 不新增数据库 schema。
- 不把 OpenAPI schema 作为远程多用户 API 承诺；本项目仍是本地优先应用。
- 字段 schema 以当前文档和测试覆盖的契约为准，复杂历史备份结构允许先以对象 schema 表达。
- 不移除或重命名现有 `/api/{path:path}` 兼容分发路由，只替换 OpenAPI 可见路径。

## 4. 文档来源

正式接口契约仍维护在 `docs/design/api-spec.md`。OpenAPI schema 是运行时可视化和联调辅助入口，必须与该文档同步更新。

## 5. 运行时行为

- `GET /openapi.json` 返回 OpenAPI 3.0 schema。
- `GET /docs` 加载 Swagger UI，并读取同一个 `/openapi.json`。
- `GET /redoc` 保留 FastAPI 默认 ReDoc 入口。
- schema paths 显式列出 Web MVP 当前 API operation，不再只显示 `/api/{path}` catch-all。
- `POST` operation 使用通用 JSON object requestBody；复杂响应也先以 object schema 表达，具体字段见 `docs/design/api-spec.md`。
- 认证开启时，`/docs`、`/redoc` 和 `/openapi.json` 与其他受保护 API 一样需要 `X-API-Key` 或 Bearer JWT。
