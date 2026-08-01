# 可选 API 认证

> 状态：Active
> Owner：RAG 团队
> Last Updated：2026-08-01
> Scope：本地单实例的共享 API Key 与短期 JWT
> Related：`../design/permission-matrix.md`、`../design/api-spec.md`、`../guides/security.md`

## 1. 用户目标

部署者可为本地 API 启用共享凭证保护。该能力不是用户账户、登录页、多租户或 RBAC。

## 2. 启用与凭证

默认关闭。启用时设置：

```text
RAG_AUTH_ENABLED=1
RAG_AUTH_API_KEY=<共享管理 Key>
RAG_AUTH_JWT_SECRET=<HS256 签名密钥>
RAG_AUTH_JWT_TTL_SECONDS=3600
```

- 脚本可发送 `X-API-Key`。
- 客户端可用 `X-API-Key` 调用 `POST /api/auth/token`，再发送 `Authorization: Bearer <jwt>`。
- `/api/health` 放行；其余 `/api/*` 以及 `/docs`、`/redoc`、`/openapi.json` 受保护。
- 缺失、错误或过期凭证返回 401，不在响应或日志中泄露密钥。

## 3. 当前可达边界

- 后端认证、API Key 和 JWT 请求路径已实现并有测试。
- 当前 Vue API helper 没有统一附加认证 header；原生 `EventSource` 也不能设置自定义认证 header。
- 因此启用认证后的浏览器普通请求和 SSE 问答尚未形成可用闭环，不能把认证描述为当前 Vue 登录能力。
- CORS 只控制浏览器 Origin，不替代认证；认证也不改变 Agent 只读白名单。
