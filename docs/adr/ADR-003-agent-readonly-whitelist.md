# ADR-003 Agent 工具只读白名单硬编码

> 状态：Accepted
> Date：2026-05-26
> Owner：RAG 团队
> Related：`../design/architecture-overview.md §7`、`../features/agent-tooling-mcp-research.md`、`../design/api-spec.md`

## 1. 背景

Web MVP 引入 Agent 工具能力（`/api/agent/tools/*`），允许系统在回答生成中调用辅助工具，提升来源召回质量。设计时面临核心安全问题：

**用户知识库中可能包含恶意指令**（prompt injection）。若 Agent 工具支持任意代码执行、文件写入或网络请求，恶意内容可通过 RAG 检索注入工具调用链，造成：
- 本地文件系统损坏或数据泄露
- 网络请求代理（SSRF）
- 意外删除知识库数据

与此同时，B-117（MCP 插件能力研究）的结论是：**当前不接入 MCP 插件市场或任意 MCP server**，未来仅允许按 allowlist、只读、用户手动触发、审计记录方式评估最小适配层。

## 2. 决策结论

Agent 工具采用**源码级硬编码只读白名单**：`webapp/agent_tools.py` 中的 `READ_ONLY_TOOLS` 常量列表定义全部可用工具，当前包含：

| 工具名 | 操作类型 | 说明 |
|--------|----------|------|
| `project_overview` | 只读 | 读取当前项目文档数、分块数、向量数、聊天记录数 |
| `search_sources` | 只读 | 按查询词检索当前项目来源片段 |

任何不在白名单中的 `tool_name` 均被拒绝（返回 `"unknown or disabled tool"` 错误），且**拒绝记录写入 `agent_tool_runs` 审计表**。

白名单工具均标记 `"read_only": True`，在代码层面禁止触发写入路径。工具只能由**用户手动触发**（点击前端按钮），系统不自动调用。

## 3. 决策原因

1. **最小攻击面**：白名单硬编码在源码中，无运行时动态注册路径，不存在通过 API 或配置文件注入恶意工具的向量
2. **prompt injection 防御**：知识库内容通过 RAG 进入上下文，若工具支持写入或执行，恶意 chunk 可操纵工具调用；只读工具不改变系统状态，即使注入成功也无法造成破坏
3. **审计完整性**：每次工具调用（包括被拒绝的）均写入 `agent_tool_runs`，记录 `tool_name / arguments / result / status / error`；本地单用户可随时核查工具使用历史
4. **用户确认前置**：工具不由 LLM 自动触发，只在用户点击"运行"按钮后执行，保留人工决策环节
5. **与 B-117 结论一致**：MCP 研究明确了"不接入任意 MCP server"的边界，硬编码白名单是该结论的代码级实现

## 4. 备选方案

### 4.1 方案 A：动态工具注册（用户可配置）

- 优点：灵活，支持用户自定义工具扩展
- 缺点：安全边界不可静态审计；恶意工具可通过配置注入；单用户场景下收益有限
- 未采用原因：攻击面过大，与 B-117 结论直接冲突

### 4.2 方案 B：MCP 协议接入（标准 tool calling）

- 优点：可复用 MCP 生态工具；标准化接口定义
- 缺点：B-117 研究已结论"暂不接入"；MCP server 可任意定义写入/执行工具；未建立 allowlist 审核机制前安全边界不清晰
- 未采用原因：B-117 结论；准入门槛未达到（需先建立 allowlist、只读约束、用户手动触发、审计记录机制）

### 4.3 方案 C：基于能力描述的运行时过滤（LLM 判断是否只读）

- 优点：灵活，自然语言描述即可定义工具约束
- 缺点：依赖 LLM 判断，不可形式化验证；prompt injection 可绕过 LLM 的约束判断
- 未采用原因：安全约束不应依赖 LLM 的运行时推理，应在代码层面静态保证

## 5. 影响

### 5.1 正面影响

- 工具能力可静态审计：读 `READ_ONLY_TOOLS` 列表即可完整了解系统工具边界
- 误用 / 滥用有完整记录：`agent_tool_runs` 表保留所有工具调用，含被拒绝的调用
- 用户不会意外触发写入操作：工具设计约束在代码中硬化，不依赖 UI 或文档说明

### 5.2 负面影响

- 扩展工具需修改源码：无法通过 UI 或配置添加新工具；对于需要自定义工具的场景，迭代周期相对长
- 当前工具集仅 2 个：能力有限，不覆盖写入、网络请求、代码执行等场景（设计如此）

### 5.3 对现有系统的改动点

| 模块 | 内容 |
|------|------|
| `webapp/agent_tools.py` | `READ_ONLY_TOOLS` 常量；`run_agent_tool()` 白名单校验与 `agent_tool_runs` 写入 |
| `webapp/routes/agent_tools.py` | `/api/agent/tools`、`/api/agent/tools/run`、`/api/agent/tools/runs` 路由 |
| `webapp/storage.py` | `agent_tool_runs` 表（`tool_name / arguments / result / status / error`）|

## 6. 后续动作

### 6.1 已完成

- `webapp/agent_tools.py`：`READ_ONLY_TOOLS` + `run_agent_tool()` 白名单校验 + 审计写入
- B-117：MCP 研究结论确立准入门槛，本 ADR 是该结论的代码级实现

### 6.2 未来扩展条件

新增工具须同时满足：
1. 操作纯只读（不修改任何持久化状态）
2. 在 `READ_ONLY_TOOLS` 中显式声明
3. 新增 `agent_tool_runs` 审计字段（如有新参数类型）
4. 用户手动触发（不由 LLM 自动调用）

MCP 接入条件：满足 B-117 结论中的全部准入门槛（allowlist + 只读 + 用户手动触发 + 审计记录）。

### 6.3 回滚策略

N/A —— 白名单收紧只会减少能力，不会破坏现有功能；若需回滚工具扩展，从 `READ_ONLY_TOOLS` 移除对应条目即可。
