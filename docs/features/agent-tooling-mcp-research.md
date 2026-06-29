# MCP / 插件能力研究

> 状态：Active
> Owner：RAG 团队
> Last Updated：2026-06-30
> Scope：B-117 MCP / 插件能力研究结论；本文件不代表已实现 MCP 接入
> Related：docs/requirements/project-background-and-scope.md, docs/requirements/functional-modules.md, docs/design/permission-matrix.md, docs/design/system-design-overview.md, docs/BACKLOG.md

## 1. 研究结论

B-117 结论：Knowledge Island 当前不接入 MCP 插件市场，不加载任意第三方 MCP server，不开放 shell、文件写入、网络爬取、远程动作或任意命令执行。

MCP 后续只适合作为**受控只读工具 / 只读资源的适配协议**进入规划，且必须复用现有 Agent 工具边界：

- 工具必须显式 allowlist，不接受远端动态工具列表自动进入可用工具。
- 工具必须由用户手动触发，模型不得自动调用外部工具。
- 工具输入必须展示给用户并校验，工具输出必须经过结构校验、长度限制和脱敏/净化。
- 每次工具调用必须写入本地审计记录，至少包含项目、工具名、参数摘要、状态、错误和时间。
- MCP server 声明的 `readOnlyHint`、`destructiveHint` 等 annotation 只能作为 UI 提示，不能作为权限依据。

因此，B-117 只关闭研究项；不修改运行时代码、不新增 API、不新增数据库 schema。

## 2. 当前项目基线

Knowledge Island 已有 Agent 工具能力，但边界非常窄：

| 当前能力 | 现状 |
|----------|------|
| 工具白名单 | `webapp/agent_tools.py` 只开放 `project_overview` 和 `search_sources` |
| 触发方式 | 前端手动点击运行；回答区只给出建议，不自动执行 |
| 权限 | 只读；不开放 shell、文件写入或任意命令 |
| 审计 | `agent_tool_runs` 保存工具运行历史、参数、结果、状态和错误 |
| 上下文回填 | 用户显式选择成功工具运行后，下一问通过 `tool_run_id` 带入来源 |

这组边界和 MCP 的安全建议是一致方向：MCP tools 可以被模型发现和调用，但官方文档也要求应用侧提供用户可见的工具暴露、确认、输入展示、超时、结果校验和审计。

## 3. MCP 能力映射

| MCP 能力 | 官方定位 | 对 Knowledge Island 的适配判断 |
|----------|----------|-------------------------------|
| Tools | 可被模型调用的外部操作，使用 `tools/list` 发现、`tools/call` 执行 | 高风险；仅允许映射为现有 Agent 工具面板里的受控只读工具，不允许模型自动调用 |
| Resources | 应用驱动读取的被动上下文，使用 `resources/list` / `resources/read` | 相对适合；未来可考虑把可信 MCP resource 映射为只读外部资料源，但必须限定项目和 URI allowlist |
| Prompts | 用户显式选择的结构化提示模板，使用 `prompts/list` / `prompts/get` | 可参考但非优先；现有 Prompt 预设已覆盖主要场景，暂不导入第三方 prompt |
| Registry / plugin market | 发现和分发第三方 server 或插件 | 不纳入；会带来供应链、权限、数据外泄和任意能力扩展风险 |

## 4. 推荐后续方案

如果后续要从研究进入实现，推荐只做一个最小安全切片：

1. 新增**本地只读 MCP 适配层**，只连接用户在配置文件中显式写入的本机 server。
2. 读取 server 的 tools/resources 后，先进入"候选能力"列表，不自动暴露给模型或问答流程。
3. 用户逐个启用能力，并为每个能力绑定项目、参数 schema、结果长度上限和是否允许作为问答上下文。
4. 只有被启用且标记为只读的能力才出现在 Agent 工具面板；运行仍需用户手动点击。
5. 调用结果进入现有 `agent_tool_runs` 审计表；失败、超时、schema 不匹配和未知工具都记录为失败审计。

这个切片的目标是"把可信只读外部资料接入当前项目上下文"，不是"开放插件生态"。

## 5. 必须拒绝的范围

以下能力不应作为 B-117 后续实现的一部分：

- 第三方插件市场、远程插件自动安装或自动更新。
- 加载任意 MCP server 并把全部 tools 自动暴露给模型。
- `shell`、`exec`、文件写入、删除文件、移动文件、修改项目源码等工具。
- 未经用户确认的工具自动调用，包括基于模型建议直接调用工具。
- 自动网页抓取、登录态浏览器操作、邮件/日历/IM 发送等外部副作用操作。
- 保存 MCP server 令牌、OAuth client secret、API Key 明文。
- 把工具返回的原始 HTML、脚本、二进制或超长内容直接注入 prompt。

## 6. 安全准入清单

任何未来 MCP 只读接入任务开始前，必须同时满足：

- **显式启用**：默认关闭；没有配置时系统行为完全不变。
- **本机优先**：默认只允许 `127.0.0.1` / 本机 stdio server；远程 server 单独研究。
- **能力 allowlist**：按 server + tool/resource 名称逐项启用，不信任远端声明自动授权。
- **只读证明**：权限由本地配置和代码路径约束，不依赖 MCP annotation 自证。
- **参数校验**：只接受 JSON Schema 内的字段，拒绝额外参数。
- **结果约束**：限制大小、类型和字段；清理 HTML/脚本；禁止回传敏感配置。
- **用户确认**：工具运行前展示 server、工具名、参数和影响范围。
- **审计可追踪**：所有调用进入 `agent_tool_runs` 或新审计表；跨项目上下文拒绝。
- **失败可降级**：MCP server 不可用时不影响导入、检索和问答主流程。

## 7. 验收建议

若未来新建实现任务，最低测试应覆盖：

- 未启用 MCP 时，现有 `GET /api/agent/tools` 仍只返回 `project_overview` 和 `search_sources`。
- 配置了未 allowlist 的 server/tool 时，不出现在前端工具列表。
- tool annotation 声明只读但本地未授权时，调用仍被拒绝。
- 工具参数出现额外字段时被拒绝，并记录失败审计。
- 工具超时、返回超长内容、返回 HTML/script、返回 schema 不匹配时均失败降级。
- 成功工具结果只能在同项目 `tool_run_id` 下被下一问引用，跨项目拒绝。

## 8. 参考资料

- [MCP Understanding servers](https://modelcontextprotocol.io/docs/learn/server-concepts)：tools、resources、prompts 的职责和用户交互模型。
- [MCP Tools specification 2025-11-25](https://modelcontextprotocol.io/specification/2025-11-25/server/tools)：`tools/list`、`tools/call`、tool schema、annotation 与安全要求。
