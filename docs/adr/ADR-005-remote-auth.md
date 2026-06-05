# ADR-005 远程访问认证机制（API Key + JWT）

> 状态：Accepted
> Date：2026-05-26
> Owner：RAG 团队
> Related：docs/design/permission-matrix.md, docs/design/api-spec.md, docs/features/authentication.md, docs/BACKLOG.md

## 1. 背景

Knowledge Island 当前是本地单用户应用，默认只监听 `127.0.0.1:8765`。B-139 已把 HTTP 服务层迁移到 FastAPI + Uvicorn，为后续前后端分离、多客户端和远程访问提供了标准中间件挂载点。

如果用户未来把服务绑定到局域网地址或容器网络，现有所有 `/api/*` 接口都会直接暴露项目文档、聊天记录、备份导出和模型配置摘要。B-140 的目标是在不引入用户系统、不修改数据库 schema 的前提下，先提供可选启用的单用户认证层。

## 2. 决策结论

采用**可选启用的单用户认证机制**：

- 默认关闭认证，保持本地开发与非技术用户一键启动体验不变。
- 通过环境变量启用：
  - `RAG_AUTH_ENABLED=1`
  - `RAG_AUTH_API_KEY=<用户自定义管理 Key>`
  - `RAG_AUTH_JWT_SECRET=<JWT 签名密钥>`
- 支持两种凭证：
  - `X-API-Key: <key>`，用于脚本、桌面端、移动端或临时调试。
  - `Authorization: Bearer <jwt>`，用于未来前端或多客户端持有短期访问令牌。
- 新增 `POST /api/auth/token`：客户端携带有效 `X-API-Key` 后换取短期 JWT。
- JWT 使用标准库 HMAC-SHA256 签名，不新增数据库表，不保存 token 状态。

## 3. 认证边界

| 路径 | 认证启用时行为 |
|------|----------------|
| `/` 与静态资源 | 放行，保证页面可加载 |
| `/api/health` | 放行，用于健康检查 |
| `/api/auth/token` | 放行到路由内部校验 API Key |
| `/api/*` 其他接口 | 必须携带有效 API Key 或 Bearer JWT |
| `/docs`、`/redoc`、`/openapi.json` | 必须携带有效 API Key 或 Bearer JWT |

当前 B-140 不新增登录页；认证启用后，浏览器 UI 需要后续前端集成凭证注入才能完整使用。B-140 的交付重点是后端安全边界。

## 4. 备选方案

### 4.1 只做 API Key

- 优点：实现最简单，脚本调用足够。
- 缺点：不满足 B-140 对 JWT 的要求；长期把主 Key 暴露给前端或移动端风险较高。
- 未采用原因：无法支撑后续多客户端令牌过期和最小暴露面。

### 4.2 完整用户系统 + JWT

- 优点：可支持多用户、密码登录、RBAC 和审计。
- 缺点：需要用户表、密码哈希、登录页、会话管理和迁移方案。
- 未采用原因：当前仍是本地单用户应用，B-118 多用户 / 团队空间尚未进入实现。

### 4.3 API Key + 短期 JWT

- 优点：不改数据库，易回滚；满足脚本和未来前端两类客户端；主 Key 不必长期暴露给普通请求。
- 缺点：JWT 无服务端撤销列表；密钥泄露后需要轮换环境变量。
- 采用原因：与当前本地单用户阶段匹配，复杂度最低。

## 5. 影响

| 模块 | 影响 |
|------|------|
| `backend/knowledge_island/auth.py` | 新增认证配置、API Key 校验、JWT 签发与验证 |
| `backend/knowledge_island/server.py` | 新增 FastAPI 中间件和 `/api/auth/token` 路由 |
| `docs/design/permission-matrix.md` | 从“无认证”更新为“默认关闭、可选启用” |
| `docs/design/api-spec.md` | 新增认证配置、错误格式和 token 接口说明 |
| `docs/guides/setup.md` | 增加环境变量启用方式 |

## 6. 安全约束

- 不硬编码默认 API Key 或 JWT secret。
- 认证启用但缺少 `RAG_AUTH_API_KEY` 或 `RAG_AUTH_JWT_SECRET` 时，服务必须拒绝启动或创建 app。
- API Key 比较必须使用常量时间比较。
- 接口响应不得回显 API Key 或 JWT secret。
- JWT 默认有效期为 1 小时，可通过 `RAG_AUTH_JWT_TTL_SECONDS` 调整，最小 60 秒。

## 7. 回滚策略

- 删除 B-140 相关 commits，恢复 `backend/knowledge_island/server.py` 无认证中间件状态。
- 清除 `RAG_AUTH_*` 环境变量即可回到无认证运行方式。
- 无数据库迁移，因此不需要数据回滚。

## 8. 验证方式

- 认证关闭时，现有 `tests/backend/` 与 `tests/frontend/` 必须继续通过。
- 认证启用时：
  - `/api/health` 无凭证返回 200。
  - `/api/projects` 无凭证返回 401。
  - `/api/projects` 携带正确 `X-API-Key` 返回 200。
  - `POST /api/auth/token` 使用正确 API Key 返回 Bearer token。
  - `/api/projects` 携带有效 Bearer token 返回 200。
  - 无效 API Key、过期 JWT、伪造 JWT 均返回 401。
