# OpenAPI / Swagger 接口文档

> 状态：Draft
> Owner：RAG 团队
> Last Updated：2026-06-29
> 关联 BACKLOG：B-136

## 1. 功能目标

为当前 Web MVP HTTP API 提供 OpenAPI 3.0 schema，使 `/openapi.json`、`/docs` 和 `/redoc` 能展示可读的接口清单、请求结构和响应结构。

## 2. MVP 范围

- 保留 FastAPI 默认 `/docs`、`/redoc` 和 `/openapi.json` 入口。
- 为兼容分发的 `/api/{path:path}` 端点补充显式 OpenAPI path schema。
- 覆盖当前 `docs/design/api-spec.md` 中列出的 Web MVP API。
- 认证开启时继续保护 `/docs`、`/redoc` 和 `/openapi.json`。

## 3. 边界

- 不改后端业务路由行为。
- 不新增数据库 schema。
- 不把 OpenAPI schema 作为远程多用户 API 承诺；本项目仍是本地优先应用。
- 字段 schema 以当前文档和测试覆盖的契约为准，复杂历史备份结构允许先以对象 schema 表达。

## 4. 文档来源

正式接口契约仍维护在 `docs/design/api-spec.md`。OpenAPI schema 是运行时可视化和联调辅助入口，必须与该文档同步更新。

