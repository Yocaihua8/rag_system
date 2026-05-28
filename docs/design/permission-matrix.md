# 权限矩阵

> 状态：Active
> Owner：RAG 团队
> Last Updated：2026-05-26
> Scope：Knowledge Island Web MVP 本地单用户权限边界
> Related：docs/design/api-spec.md, docs/design/architecture-overview.md

## 1. 角色定义

当前版本仍是**本地单用户应用**。默认认证关闭，只有一个隐式角色：本机用户（即访问 `127.0.0.1:8765` 的浏览器用户）。B-140 起可通过环境变量启用单用户认证层，用于远程访问或脚本调用场景；该认证层不等同于多用户 / RBAC。

| 角色 | 定义 | 认证方式 |
|------|------|----------|
| 本机用户 | 启动 `backend/app.py` 的用户，对所有数据有完整读写权限 | 默认无认证；启用认证后使用 `X-API-Key` 或 Bearer JWT |

多用户 / RBAC 支持列为 P3 研究项（B-118），实施前需重新设计。

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
| Agent 工具白名单 | 仅允许 `project_overview` 和 `search_sources`，其他工具名一律拒绝 | `backend/webapp/agent_tools.py` |
| API Key 不回显 | `GET /api/settings/llm` 和 `GET /api/model-profiles` 响应不含 API Key 明文 | `backend/webapp/api.py` |
| 跨项目工具注入拒绝 | `tool_run_id` 与当前 `project_id` 不匹配时拒绝注入上下文 | `backend/webapp/answers.py` |
| 跨项目集合操作拒绝 | 文档与集合必须属于同一 `project_id` | `backend/webapp/api.py` |
| 工具只读约束 | Agent 工具不开放文件写入、shell 执行或任意命令 | `backend/webapp/agent_tools.py` |

## 3. 数据级权限规则

- **项目隔离**：文档、集合、会话、预设均按 `project_id` 过滤，API 层强制校验
- **无用户 ID 概念**：所有数据属于单一本机用户，无用户间数据隔离需求
- **Key 引用隔离**：API Key 只保存受控引用（`env:*` / `saved:*`），不保存明文
- **认证密钥隔离**：`RAG_AUTH_API_KEY` 与 `RAG_AUTH_JWT_SECRET` 只从环境变量读取，不写入 SQLite，不通过接口回显

## 4. 系统文件访问边界

| 动作 | 权限要求 |
|------|----------|
| 读取本地文件（导入）| 文件系统 ACL 许可（运行 `backend/app.py` 的用户权限）|
| 写入运行时数据库 | `runtime/docker/` 目录可写 |
| 读取 API Key | 仅从环境变量或 Windows 持久环境读取，不回显 |
| 执行 Agent 工具 | 白名单内只读工具，审计记录写入 `agent_tool_runs` |

## 5. 计划变更

- **B-118（P3）**：多用户 / 团队空间研究，实施前须引入认证层（JWT / Session）和 RBAC 模型
- **B-136（P3）**：OpenAPI 对外开放，须评估是否需要 API Key 鉴权
