# 认证中间件

> 状态：Active
> Owner：RAG 团队
> Last Updated：2026-05-26
> Scope：B-140 API Key + JWT 认证中间件
> Related：docs/adr/ADR-005-remote-auth.md, docs/design/permission-matrix.md, docs/design/api-spec.md, docs/BACKLOG.md

## 1. 功能定位

B-140 为 Web MVP 增加可选启用的单用户认证中间件，服务于后续多客户端和远程访问场景。它不是多用户系统，不新增用户表、密码登录、注册页面或 RBAC。

## 2. 启用方式

默认认证关闭。设置以下环境变量后启用：

```text
RAG_AUTH_ENABLED=1
RAG_AUTH_API_KEY=<用户自定义管理 Key>
RAG_AUTH_JWT_SECRET=<JWT 签名密钥>
```

可选：

```text
RAG_AUTH_JWT_TTL_SECONDS=3600
```

## 3. 认证方式

| 方式 | 适用场景 | 说明 |
|------|----------|------|
| `X-API-Key` | 脚本、curl、桌面端、移动端 | 直接使用用户配置的管理 Key |
| `Authorization: Bearer <jwt>` | 前端或多客户端 | 通过 `POST /api/auth/token` 获取短期 JWT |

## 4. 路径规则

| 路径 | 认证启用时行为 |
|------|----------------|
| `/` 与静态资源 | 放行 |
| `/api/health` | 放行 |
| `/api/auth/token` | 路由内部校验 `X-API-Key` |
| `/api/*` 其他接口 | 需要认证 |
| `/docs`、`/redoc`、`/openapi.json` | 需要认证 |

## 5. 错误格式

| 场景 | HTTP 状态 | 响应 |
|------|-----------|------|
| 缺少凭证 | 401 | `{"error":"authentication required"}` |
| 凭证错误或过期 | 401 | `{"error":"invalid credentials"}` |

## 6. 非目标

- 不新增登录页。
- 不新增用户表或权限表。
- 不保存 JWT。
- 不实现 token 服务端撤销列表。
- 不改变 Agent 工具只读白名单。

## 7. 验收标准

- 认证关闭时，现有本地使用方式完全兼容。
- 认证启用时，受保护 API 无凭证必须返回 401。
- 正确 API Key 和正确 JWT 均可访问受保护 API。
- 错误、过期或伪造 JWT 均被拒绝。
- API 响应不泄露 `RAG_AUTH_API_KEY` 或 `RAG_AUTH_JWT_SECRET`。
