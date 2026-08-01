# 权限与安全边界

> 状态：Active
> Owner：RAG 团队
> Last Updated：2026-08-01
> Scope：认证、CORS、数据隔离、密钥、Agent 与 Obsidian 权限
> Related：`architecture-overview.md`、`api-spec.md`、`database-design.md`、`../guides/security.md`

## 1. 身份模型

当前产品是本地单用户应用，没有用户、团队、成员、角色或租户表。`project_id` 是数据筛选边界，不是安全租户 ID。

后端可通过 `RAG_AUTH_ENABLED=1` 启用单一共享 API Key 与 HS256 JWT：

| 凭证 | 入口 | 生命周期 |
|------|------|----------|
| `X-API-Key` | `RAG_AUTH_API_KEY` | 进程环境配置；服务端不写 SQLite |
| Bearer JWT | `POST /api/auth/token` | 用 `RAG_AUTH_JWT_SECRET` 签发；默认 3600 秒；无服务端撤销列表 |
| Obsidian Bearer Token | 插件配对成功时一次返回 | 服务端只保存 hash；连接可撤销 |

共享 Key/JWT 只增加单用户服务访问门槛，不提供成员身份、RBAC 或项目级授权。

## 2. HTTP 权限矩阵

默认认证关闭时，本机可访问所有 API。认证开启时：

| 路径 | 认证规则 |
|------|----------|
| `/api/health` | 始终放行 |
| `/api/auth/token` | 路由内校验 `X-API-Key`；认证关闭时返回 404 |
| `/api/obsidian/pairing/complete`、`/connections/revoke`、`/sync/events`、`/publications/pending`、`/publications/result` | 由配对码或插件 Bearer Token 自认证，不走应用 Key/JWT 中间件 |
| 其他 `/api/*` | 需要有效 `X-API-Key` 或 Bearer JWT |
| `/docs`、`/redoc`、`/openapi.json` | 需要有效 `X-API-Key` 或 Bearer JWT |
| `/` | 无产品路由，返回 404 |

当前浏览器接线限制：

- `frontend/src/api/client.js` 的 GET/POST 不附加 `X-API-Key` 或 `Authorization`；
- 问答使用原生 `EventSource`，当前没有 query token、cookie 或自定义认证 Header 方案；
- 因此 Vue 主路径只承诺默认关闭认证的本地模式。开启后端认证并不自动得到可用的浏览器登录、刷新或 SSE 认证链。

## 3. CORS

默认精确 Origin allowlist 为：

- `http://127.0.0.1:5173`、`http://localhost:5173`；
- `http://127.0.0.1:4173`、`http://localhost:4173`；
- `tauri://localhost`、`http://tauri.localhost`。

`KI_CORS_ORIGINS` 可以提供逗号分隔的精确 Origin。包含 `*` 会在启动配置校验中被拒绝。

| 配置 | 当前值 |
|------|--------|
| Methods | `GET`、`POST`、`OPTIONS` |
| Headers | `Authorization`、`Content-Type`、`X-API-Key` |
| Cookie credentials | `false` |
| 通配符 | 禁止 |

CORS 中间件包裹认证中间件，使合法浏览器预检在业务认证前得到处理；CORS 不是身份认证，也不会把非 allowlist Origin 变成可信用户。

## 4. 数据与操作边界

| 对象 / 操作 | 当前限制 | 执行位置 |
|-------------|----------|----------|
| 项目数据 | 文档、集合、批次、会话、评估、Coach、发布按 `project_id` 校验 | routes、domain、storage |
| 文档集合 | 集合与文档必须属于同一项目 | `backend/routes/documents.py` |
| 工具上下文 | `tool_run_id` 必须属于当前项目 | `backend/domain/answers.py` |
| 学习计划 | 结构更新、进度更新和确认分别校验修订/hash | Coach domain/store |
| Obsidian 路径 | 规范化后必须位于连接的 `output_root`，仅处理 Markdown | Obsidian domain/plugin |
| 发布覆盖 | 必须是受管文件且 expected hash 匹配 | Obsidian domain/plugin |
| 网络抓取 | 只允许 http/https 公网目标，重定向后再次校验；限制 robots、大小、类型和超时 | web fetch domain |

应用进程以启动用户的文件系统权限读取导入路径和写入运行时目录；本项目不额外突破操作系统 ACL。

## 5. API Key 与敏感值

必须区分两套现有存储行为：

| 能力 | 保存内容 | 明文位置 / 回显 |
|------|----------|-----------------|
| 模型 Profile | SQLite `model_profiles.api_key_ref` 只允许空值、`env:RAG_LLM_API_KEY`、`env:DEEPSEEK_API_KEY`、`saved:RAG_LLM_API_KEY`；即受控的 `env:*` / `saved:*` 引用 | 列表响应只返回引用、`has_api_key` 和来源，不返回值 |
| 兼容全局 LLM 设置 | `POST /api/settings/llm` 接收非空 `api_key` 后调用 `save_setting()` | 明文以引号值写入用户应用数据目录 `KnowledgeIsland/.env`；GET 只返回是否存在和来源 |
| 应用认证 | `RAG_AUTH_API_KEY`、`RAG_AUTH_JWT_SECRET` | 只从环境读取，不写数据库、不通过接口回显 |
| Obsidian 服务端 | `code_hash`、`token_hash` | 数据库不保存明文配对码/令牌 |
| Obsidian 插件 | 连接令牌 | 为离线恢复保存在当前 Vault 插件 `data.json`；依赖 Vault 文件权限保护 |

所以“接口不回显明文”不等于“系统从不在磁盘保存明文”。安全说明和备份策略必须覆盖用户应用数据 `.env` 与插件数据文件。

## 6. Agent 工具

Agent 工具白名单硬编码在 `backend/domain/agent_tools.py`，当前只有：

- `project_overview`；
- `search_sources`。

工具不执行 shell、不写项目文件、不开放任意命令，也不加载第三方 MCP/插件市场。每次允许或拒绝的运行都会写入 `agent_tool_runs`，因此“工具只读”描述的是对项目业务数据/文件的能力，不表示执行过程零写入；审计写入是预期行为。

## 7. Obsidian 发布权限

- 配对码一次性、限时且数据库只存 hash；每项目最多一个 active 连接。
- 插件 Token 只允许 Obsidian 专用路由，不能代替应用 Key/JWT 调用普通业务 API。
- 同一连接下 `event_id` 幂等，离线重试不能重复应用事件。
- 浏览器只能预览和确认；插件负责领取、Vault 写入和回传终态。
- 无管理标记、项目/稳定 ID 不匹配、hash 冲突或路径越界时必须返回冲突/失败，不允许自动合并或覆盖。

## 8. 明确不具备的能力

- 用户账户、团队成员、角色权限、租户隔离或 SSO；
- 浏览器登录页、凭证持久化、刷新 Token 或已认证 EventSource；
- Agent 文件写入、shell、任意网络工具或动态权限扩张；
- 服务端保存 Obsidian 令牌明文；
- cookie 会话、跨站 credentials 或通配符 CORS。
