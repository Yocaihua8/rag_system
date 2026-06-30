# 权限矩阵

> 状态：Active
> Owner：RAG 团队
> Last Updated：2026-06-30
> Scope：Knowledge Island Web MVP 本地单用户权限边界
> Related：docs/design/api-spec.md, docs/design/architecture-overview.md

## 1. 角色定义

当前版本仍是**本地单用户应用**。默认认证关闭，只有一个隐式角色：本机用户（即访问 `127.0.0.1:8765` 的浏览器用户）。B-140 起可通过环境变量启用单用户认证层，用于远程访问或脚本调用场景；该认证层不等同于多用户 / RBAC。

B-118 已完成研究并确认：团队空间不进入当前实现。后续若启动多用户能力，必须先新增身份体系、租户模型、成员关系、角色权限、成员级审计和迁移方案，不能复用当前单用户 API Key/JWT 作为团队账号体系。

| 角色 | 定义 | 认证方式 |
|------|------|----------|
| 本机用户 | 启动 `app.py` 的用户，对所有数据有完整读写权限 | 默认无认证；启用认证后使用 `X-API-Key` 或 Bearer JWT |

多用户 / RBAC 支持不属于当前 Web MVP；研究结论见 `docs/features/team-workspace-research.md`。

## 2. 接口权限矩阵

默认配置下，所有 `/api/*` 接口对本机用户开放，无 Token 认证。设置 `RAG_AUTH_ENABLED=1` 后，权限边界如下：

| 路径 | 认证启用时权限 |
|------|----------------|
| `/` 与静态资源 | 放行 |
| `/api/health` | 放行 |
| `/api/auth/token` | 路由内部校验 `X-API-Key` 后签发短期 JWT |
| `/api/*` 其他接口 | 需要有效 `X-API-Key` 或 `Authorization: Bearer <jwt>` |
| `/docs`、`/redoc`、`/openapi.json` | 需要有效 `X-API-Key` 或 Bearer JWT |

以下为**硬编码限制**（不受用户配置控制）：

| 限制类型 | 规则 | 执行位置 |
|----------|------|----------|
| Agent 工具白名单 | 仅允许 `project_overview` 和 `search_sources`，其他工具名一律拒绝 | `webapp/agent_tools.py` |
| API Key 不回显 | `GET /api/settings/llm` 和 `GET /api/model-profiles` 响应不含 API Key 明文 | `webapp/api.py` |
| 跨项目工具注入拒绝 | `tool_run_id` 与当前 `project_id` 不匹配时拒绝注入上下文 | `webapp/answers.py` |
| 跨项目集合操作拒绝 | 文档与集合必须属于同一 `project_id` | `webapp/api.py` |
| 工具只读约束 | Agent 工具不开放文件写入、shell 执行或任意命令 | `webapp/agent_tools.py` |
| MCP / 插件接入禁用 | 当前不加载第三方 MCP server、插件市场或任意外部工具；B-117 后续若进入实现，也必须先走只读 allowlist、用户手动触发和审计记录 | 研究结论：`docs/features/agent-tooling-mcp-research.md` |
| 多用户 / 团队空间禁用 | 当前没有 `users/teams/memberships/roles`，`project_id` 不是租户边界；不得把单用户 JWT/API Key 解释为团队账号 | 研究结论：`docs/features/team-workspace-research.md` |

## 3. 数据级权限规则

- **项目隔离**：文档、集合、会话、预设均按 `project_id` 过滤，API 层强制校验
- **无用户 ID 概念**：所有数据属于单一本机用户，无用户间数据隔离需求
- **Key 引用隔离**：API Key 只保存受控引用（`env:*` / `saved:*`），不保存明文
- **认证密钥隔离**：`RAG_AUTH_API_KEY` 与 `RAG_AUTH_JWT_SECRET` 只从环境变量读取，不写入 SQLite，不通过接口回显

## 4. 系统文件访问边界

| 动作 | 权限要求 |
|------|----------|
| 读取本地文件（导入）| 文件系统 ACL 许可（运行 `app.py` 的用户权限）|
| 写入运行时数据库 | `runtime/docker/` 目录可写 |
| 读取 API Key | 仅从环境变量或 Windows 持久环境读取，不回显 |
| 执行 Agent 工具 | 白名单内只读工具，审计记录写入 `agent_tool_runs` |

## 5. 计划变更

- **B-118（P3）**：多用户 / 团队空间研究已收口；当前仍不实现团队空间，后续若实现须拆分身份、租户、RBAC、审计和迁移设计
- **B-117（P3）**：MCP / 插件能力研究已收口；当前仍不开放插件市场、shell、文件写入或任意命令执行
- **B-136（P3）**：OpenAPI 对外开放，须评估是否需要 API Key 鉴权
