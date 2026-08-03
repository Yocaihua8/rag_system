# 权限与安全边界

> 状态：Active
> Owner：RAG 团队
> Last Updated：2026-08-02
> Scope：v2/v3 认证、CORS、数据隔离、密钥、Agent 与 Obsidian 权限
> Related：`architecture-overview.md`、`agent-runtime-and-tool-contract.md`、`api-spec.md`、`database-design.md`、`../guides/security.md`、`../adr/ADR-012-agent-product-and-permissions.md`

## 1. 身份模型

当前产品是本地单用户应用，没有用户、团队、成员、角色或租户表。`project_id` 是数据筛选边界，不是安全租户 ID。

后端可通过 `RAG_AUTH_ENABLED=1` 启用单一共享 API Key 与 HS256 JWT：

| 凭证 | 入口 | 生命周期 |
|------|------|----------|
| `X-API-Key` | `RAG_AUTH_API_KEY` | 进程环境配置；服务端不写 SQLite |
| Bearer JWT | `POST /api/auth/token` | 用 `RAG_AUTH_JWT_SECRET` 签发；默认 3600 秒；无服务端撤销列表 |
| `X-KI-Desktop-Token` | Tauri 启动 sidecar 时通过进程环境注入 | 仅当前父子进程生命周期；不写 CLI、日志、SQLite 或浏览器持久存储 |
| Obsidian Bearer Token | 插件配对成功时一次返回 | 服务端只保存 hash；连接可撤销 |

共享 Key/JWT 只增加单用户服务访问门槛，不提供成员身份、RBAC 或项目级授权。

## 2. HTTP 权限矩阵

默认认证关闭时，本机可访问所有 API。认证开启时：

| 路径 | 认证规则 |
|------|----------|
| `/api/health`、`/api/v3/health` | 始终放行；v3 health 只返回代际、revision 和 executor 状态 |
| `/api/auth/token` | 路由内校验 `X-API-Key`；认证关闭时返回 404 |
| `/api/obsidian/pairing/complete`、`/connections/revoke`、`/sync/events`、`/publications/pending`、`/publications/result` | 由配对码或插件 Bearer Token 自认证，不走应用 Key/JWT 中间件 |
| 其他 `/api/*`，包括 `/api/v3/*` | 需要有效 `X-API-Key` 或 Bearer JWT |
| `/docs`、`/redoc`、`/openapi.json` | 需要有效 `X-API-Key` 或 Bearer JWT |
| `/` | 无产品路由，返回 404 |

当前浏览器接线限制：

- `frontend/src/api/client.js` 的 GET/POST 不附加 `X-API-Key` 或 `Authorization`；
- 问答使用原生 `EventSource`，当前没有 query token、cookie 或自定义认证 Header 方案；
- 因此 Vue 主路径只承诺默认关闭认证的本地模式。开启后端认证并不自动得到可用的浏览器登录、刷新或 SSE 认证链。

`KI_DESKTOP_MODE=1` 是独立于 Web Key/JWT 的桌面认证边界：服务端必须精确绑定 `127.0.0.1` 和显式非零端口，所有 `/api/*`（包括 health）、`/docs`、`/redoc` 与 `/openapi.json` 都只接受匹配的 `X-KI-Desktop-Token`。Web API Key/JWT 不能替代该令牌，`/api/auth/token` 在桌面模式返回 404；上表中的 Obsidian 自认证路由继续由自身凭证校验。该模式当前默认关闭，正式桌面入口仍使用现有 Vue/Tauri 基线。

## 3. CORS

默认精确 Origin allowlist 为：

- `http://127.0.0.1:5173`、`http://localhost:5173`；
- `http://127.0.0.1:5174`、`http://localhost:5174`；
- `http://127.0.0.1:4173`、`http://localhost:4173`；
- `http://127.0.0.1:4174`、`http://localhost:4174`；
- `tauri://localhost`、`http://tauri.localhost`。

`KI_CORS_ORIGINS` 可以提供逗号分隔的精确 Origin。包含 `*` 会在启动配置校验中被拒绝。

| 配置 | 当前值 |
|------|--------|
| Methods | `GET`、`POST`、`OPTIONS` |
| Headers | `Authorization`、`Content-Type`、`Idempotency-Key`、`Last-Event-ID`、`X-API-Key`、`X-KI-Desktop-Token`、`X-Request-ID` |
| Cookie credentials | `false` |
| 通配符 | 禁止 |

CORS 中间件包裹认证中间件，使合法浏览器预检在业务认证前得到处理；CORS 不是身份认证，也不会把非 allowlist Origin 变成可信用户。

## 4. 数据与操作边界

| 对象 / 操作 | 当前限制 | 执行位置 |
|-------------|----------|----------|
| 项目数据 | 文档、集合、批次、会话、评估、Coach 学习、发布按 `project_id` 校验 | routes、domain、storage |
| 文档集合 | 集合与文档必须属于同一项目 | `backend/routes/documents.py` |
| 工具上下文 | `tool_run_id` 必须属于当前项目 | `backend/domain/answers.py` |
| 学习计划 | 结构更新、进度更新和确认分别校验修订/hash | Coach domain/store |
| 逐点学习 | 会话绑定项目和分析运行；attempt 校验会话版本、幂等键、exercise 与当前步骤；stale 或终态只读 | Coach learning domain/store |
| SQL 练习 | 只接受结构化 fixture 和学习者 SQL；不接受应用数据库路径或连接；临时数据库只读执行 | `backend/domain/sql_learning.py` |
| Obsidian 路径 | 规范化后必须位于连接的 `output_root`，仅处理 Markdown | Obsidian domain/plugin |
| 发布覆盖 | 必须是受管文件且 expected hash 匹配 | Obsidian domain/plugin |
| 网络抓取 | 只允许 http/https 公网目标，重定向后再次校验；限制 robots、大小、类型和超时 | web fetch domain |
| v3 项目检查 | 只遍历登记项目根的相对结构元数据，不读取正文，不进入忽略目录，不跟随目录符号链接 | `backend/runtime/project_inspector.py` |
| v3 命令 | 资源创建、运行控制、重试和审批决议要求幂等键；控制/决议同时要求资源 version，审批还校验 request hash | v3 application/store |
| v3 数据 | 只打开 `data_generation=v3` 且 Alembic revision 匹配的数据文件；未标记、v2 或未知代际 fail closed | `backend/storage/v3/database.py` |

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

## 6. Agent 与工作流能力

### 6.1 v2 工具

Agent 工具白名单硬编码在 `backend/domain/agent_tools.py`，当前只有：

- `project_overview`；
- `search_sources`。

工具不执行 shell、不写项目文件、不开放任意命令，也不加载第三方 MCP/插件市场。每次允许或拒绝的运行都会写入 `agent_tool_runs`，因此“工具只读”描述的是对项目业务数据/文件的能力，不表示执行过程零写入；审计写入是预期行为。

### 6.2 v3 alpha

v3 使用类型化安全节点注册表。注册表目前允许 `trigger.manual`、Agent 计划、来源读取/检索、项目分析、模型合成/比较、评估/学习计划、产物、审批、Obsidian 发布和 branch/join；显式拒绝 shell、脚本、任意 HTTP/MCP、任意文件系统或路径节点。

安全注册不等于执行授权：

- 当前运行创建 API 只接受固定 `project.inspect.v1`；
- executor 只执行 `trigger.manual`、`project.analyze`、`artifact.create`；
- `POST /api/v3/workflows/validate` 只验证 DAG；其他工作流 API 可以保存不可变 draft、发布、绑定和归档，但不会执行调用方 DAG；
- 当前固定工作流是只读分析，没有写节点，不会生成审批请求；
- 审批列表、详情和 resolve API 是后续写工作流的基础，不能据此宣称项目文件、外部系统或 Obsidian 写入已经可用。

项目检查产物与 SSE 事件会移除项目绝对根路径，也不包含文件正文；项目资源本身仍返回登记的 `root_path`，所以 v3 API 不是对不受信调用方隐藏本地路径的多租户接口。

## 7. Obsidian 发布权限

- 配对码一次性、限时且数据库只存 hash；每项目最多一个 active 连接。
- 插件 Token 只允许 Obsidian 专用路由，不能代替应用 Key/JWT 调用普通业务 API。
- 同一连接下 `event_id` 幂等，离线重试不能重复应用事件。
- 浏览器只能预览和确认；插件负责领取、Vault 写入和回传终态。
- 无管理标记、项目/稳定 ID 不匹配、hash 冲突或路径越界时必须返回冲突/失败，不允许自动合并或覆盖。

## 8. 明确不具备的能力

- 用户账户、团队成员、角色权限、租户隔离或 SSO；
- 浏览器登录页、凭证持久化、刷新 Token 或已认证 EventSource；
- v3 自定义发布 DAG 执行、可视化工作流前端或已接线生产 Agent 前端；
- Agent shell、任意脚本、任意网络/MCP 工具、动态权限扩张或未经审批的文件/外部写入；
- SQL 练习连接正式应用数据库、执行来源 DDL、写操作、Schema 探测、扩展加载或任意 SQLite 函数；
- 服务端保存 Obsidian 令牌明文；
- cookie 会话、跨站 credentials 或通配符 CORS。
