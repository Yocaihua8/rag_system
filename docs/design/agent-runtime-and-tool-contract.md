# Agent Runtime 与工具契约

> 状态：Active
> Owner：RAG 团队
> Last Updated：2026-08-02
> Scope：v3 任务执行、持久状态、消息事件、工作流节点、审批和工具安全边界
> Related：`../requirements/agent-product-v3.md`、`../features/agent-tasks-and-runs.md`、`api-spec.md`、`database-design.md`、`permission-matrix.md`

## 1. 职责边界

| 层 | 职责 | 禁止事项 |
|----|------|----------|
| HTTP/API | 请求校验、鉴权、错误映射、SSE 输出和用例调用 | 直接执行步骤或操作 SQLite |
| Application | 创建任务、运行、审批、工作流发布等用例编排 | 承载 HTTP 对象或 UI 文案 |
| Domain/Workflow | 状态转换、DAG 校验、节点定义、重试与审批规则 | 访问数据库或任意外部资源 |
| Worker | 租约领取、容量控制、取消、恢复和节点调用 | 以内存状态代替持久状态 |
| Infrastructure | SQLite、模型、检索、解析、文件和连接器适配 | 绕过领域权限或审批 |

HTTP 创建运行时只提交持久状态；执行器由应用 lifespan 启动并从数据库领取步骤。浏览器或 SSE 连接断开不能取消持久运行。

当前 alpha 已按上述边界实现 `backend/api/v3/`、`backend/application/agent_service.py`、`backend/runtime/` 与 `backend/storage/v3/`。v2 路由和 Vue 继续运行；独立 `frontend-v3/` 已接入当前真实 v3 切片，但尚未成为正式入口。

## 2. 核心实体和状态

### Task 与 Run

- Task 固定绑定 `project_id`，保存任务标题、消息和最近运行。
- Run 固定绑定 Task、工作流 key/version/checksum 快照和深度档位；固定 `project.inspect.v1`、固定 `project.source-facts.v1` 的 `workflow_version_id` 可以为空，或使用满足受限执行合同的已发布/已绑定工作流。
- Task/Run：`queued / running / waiting_approval / paused / completed / failed / cancelled`。
- Run 在应用重启恢复期间可以为 `recovering`。

### Step

状态为 `pending / queued / running / waiting_approval / succeeded / failed / skipped / cancelled / recovery_required`。步骤尝试独立保存开始/结束时间、租约、错误和结果摘要。

### Approval 与 Artifact

- Approval：`pending / approved / rejected / expired`。
- Artifact：`draft / ready / exported / failed`。
- 当前审批决议和内部产物创建是幂等写操作并追加事件；产物导出节点尚不可执行。

## 3. 调度和恢复

- lifespan executor 默认启动两个 worker；`KI_AGENT_MAX_CONCURRENCY` 允许 1-2，不能扩大到无界并发。
- worker 通过数据库领取持久 Run/Step，默认租约 30 秒并按租约三分之一周期心跳；轮询默认 100ms。参数分别由 `KI_AGENT_LEASE_SECONDS` 和 `KI_AGENT_POLL_INTERVAL_MS` 在受限范围内覆盖。
- 运行暂停后不再领取新步骤；pause/resume/cancel 使用资源 `expected_version` 与幂等键，运行状态变化与事件在同一事务内保存。
- `project.inspect.v1` 与 `project.source-facts.v1` 的分析步骤最多三次 attempt，即首次失败后最多自动重试两次；每次尝试独立保存。触发和产物步骤不自动重试。
- 启动时会处理过期租约；读/分析步骤可重新排队，结果不明确的写步骤按 `recovery_required` 边界处理。
- 当前 executor 没有可执行的项目写或外部写节点，因此“同项目写串行、等待审批释放容量和写后恢复”仍是目标安全合同，不是本 alpha 已验收的写执行能力。

## 4. 事件与 SSE

`agent_events` 为每个 Run 保存单调递增的 `sequence`。事件至少包含：

```text
id, run_id, step_id?, sequence, event_type, payload, created_at
```

- 服务端先提交状态和事件，再向 SSE 客户端发送。
- 客户端通过 `Last-Event-ID` 或 `after_sequence` 恢复；重复序号必须忽略。
- 事件 payload 使用 Pydantic discriminated union；事件中不得出现 API Key、令牌、完整敏感输入或任意本地绝对路径。
- 断开 SSE 不影响 Run；Run 终态后事件历史仍可读取。

### 4.1 Agent 消息流

当前 alpha 在 Run、Step、Approval、Artifact 与 tool output 事件之外，已经实现以下 Agent 消息事件：

| 事件 | 关键 payload | 语义 |
|------|--------------|------|
| `assistant.message.started` | `message_id`、`message_type`、`format` | 为当前 Run 建立稳定回答身份 |
| `assistant.message.delta` | `message_id`、`chunk_index`、`text` | 追加一个语义分块，不按 token 落库 |
| `assistant.message.completed` | `message_id`、`chunk_count`、`char_count`、`content_hash` | 完整任务消息与回答终态已持久化 |
| `assistant.message.interrupted` | `message_id`、`reason`、`recoverable` | 回答未完成；可见部分和中断原因可恢复 |

当前实现还补齐 `step.waiting_approval / step.failed / step.cancelled / step.recovery_required` 与 `approval.expired`。审批过期由独立周期任务检查，不依赖空闲执行槽。`artifact.created.payload.status=ready` 继续表达当前内部产物就绪；导出执行尚未实现时不得发出虚构的导出完成事件。

任务消息保存长期会话事实，事件保存实时生成与运行事实，React 前端 reducer 只负责去重和界面投影。完整决策见 [`ADR-016`](../adr/ADR-016-agent-message-stream.md)。P1 Revision 3 的确定性演示事件仍只证明原型交互；生产闭环另由真实后端 Playwright 用例验证。

## 5. 工作流版本与当前开放边界

- v3 Schema、Store 和 HTTP 已实现 Workflow Definition、不可变 Workflow Version 与项目 Binding；Version 保存 DAG、版本号和内容 checksum。
- HTTP 开放 validate、创建/列表/详情、新 draft、publish、bind、archive 和 binding 列表。新 draft 与 archive 使用 Definition `expected_version`，publish 同时校验 Version checksum，bind 只接受已发布 Version 并校验 workflow/binding version。
- 发布不原地改写 DAG；归档只改变 Definition 状态并保留历史 Version，归档后拒绝新草稿。
- 当前 `project.inspect.v1`（version 2）和 `project.source-facts.v1`（version 1）由应用层以固定 checksum 和固定四步快照创建新 Run；前者读取绑定项目根的结构元数据，后者只读取已持久 v3 Documents。两者都不依赖调用方提交任意 DAG；`project.inspect.v1` version 1 历史运行继续按其持久版本读取和恢复。
- v3 首版只允许一个 `trigger.manual`，且必须存在至少一个可达终点。
- 校验必须拒绝循环、孤立节点、无效边、端口类型不匹配、必填参数缺失、无效资源引用和未受审批保护的写节点。

## 6. 节点注册表

首版只允许以下节点类型：

| 分类 | 节点 |
|------|------|
| 触发 | `trigger.manual` |
| Agent | `agent.plan`、`agent.respond`（仅固定项目检查工作流可执行） |
| 来源 | `source.search`、`source.read` |
| 分析 | `project.analyze`、`insight.assess`、`learning.plan` |
| 模型 | `llm.synthesize`、`llm.compare` |
| 产物 | `artifact.create`、`artifact.export` |
| 确认/集成 | `approval.request`、`obsidian.publish` |
| 控制 | `control.branch`、`control.join` |

每个节点声明版本、输入/输出端口、Pydantic 配置模型、读写类别、可重试性、取消能力和执行器。不存在“自定义脚本”或可传任意 URL/命令/路径的配置。

注册表表示可校验的安全类型，不等于当前可执行能力。alpha executor 只实现：

- `trigger.manual`：读取持久 Task prompt；
- `project.analyze`：运行受限项目结构检查，或按 `persisted_source_facts` 读取 v3 Documents；
- `artifact.create`：保存内部 `project_inspection` 或 `project_source_facts` JSON 产物。

当前 `agent.respond` 分析节点只读取固定项目检查或资料事实报告的结构化结果，生成普通中文摘要并发出 Agent 消息事件；不调用 shell、网络、任意路径或未批准工具。两个固定工作流均依次包含 `trigger.manual`、`project.analyze`、`artifact.create` 和 `agent.respond`，Quick 仍不超过四步。

P1 中“找出问题 / 整理资料 / 做一份计划”的通用澄清路径仍是演示合同，不表示 alpha executor 已具备通用自然语言规划器。

其他注册节点即使通过 validate、保存并发布，也不能通过当前运行创建 API 执行；`RunCreateRequest.workflow_key` 只接受两个固定工作流或满足受限执行合同的已发布绑定图。

## 7. 权限与路径

- 当前检查只接受创建 Project 时登记且当时仍存在的目录；保存规范化绝对根用于后续校验，但检查输出、事件和产物只返回相对结构元数据。
- `project.inspect` 不读取文件正文，不进入 `.git/node_modules/build/dist/.venv` 等忽略目录，不跟随目录符号链接，并受最大遍历条目数与取消检查限制。
- `project.source-facts` 不读取项目根：只从 v3 Store 取回已持久 Documents 内容，固定资料 hash、逐文档行数和有限 Markdown 标题证据。后续扫描变更只标记旧报告 metadata 为过期。
- 项目文件、外部系统、导出和发布写节点在注册表中必须受 `approval.request` 支配；当前 executor 不执行这些写节点。
- Approval Schema 和 resolve API 冻结目标、payload、资源版本、request hash 与 CAS version；当前固定项目检查不会创建审批。
- Desktop 随机端口和启动令牌仍是目标合同，当前 Tauri/Vue 兼容运行时尚未切换到 v3；Web 继续使用主 FastAPI 的可选 API Key/JWT 边界。

## 8. 深度档位

| 档位 | 最多步骤 | 最多检索轮次 |
|------|----------|--------------|
| Quick | 4 | 1 |
| Standard | 8 | 3 |
| Deep | 16 | 6 |

档位是上限，不要求用满。运行创建后保存实际档位，worker 不接受前端临时扩大上限。

## 9. 当前实现状态

| 能力 | 当前状态 |
|------|----------|
| 独立 v3 数据根、SQLAlchemy/Alembic 与代际 fail-closed | alpha 已实现；默认 `runtime/v3/app.db`，revision `0001_v3_initial` |
| `/api/v3` 资源和 envelope | alpha 已实现；项目、任务、消息、运行、控制、事件、审批、产物、workflow validate 与版本化工作流管理 |
| 持久运行 | alpha 已实现固定四步 `project.inspect.v1` version 2，由 lifespan executor 执行并生成内部 JSON 产物与中文回答；version 1 历史可读 |
| SSE | alpha 已实现持久事件、单调 sequence、`Last-Event-ID` / `after_sequence` 回放 |
| Agent 回答流 | alpha 已实现并通过定向、真实 lifespan 集成和全量门禁；完整/中断消息与终结事件保持事务一致 |
| 审批与写动作 | 数据和 API 基础已存在；当前没有可执行写工作流或端到端审批写回 |
| 工作流管理 | validate、Definition/不可变 Version/Binding 的创建、读取、发布、绑定和归档已实现；自定义发布 DAG 执行未实现 |
| 前端 | v2 Vue 保留且未改接 v3；独立 React 工作台已接真实 v3 固定任务闭环，正式入口切换仍受后续门禁约束 |

因此可以把当前能力描述为“v3 后端 alpha 垂直切片、版本化工作流管理基础与平行 React 工作台”，不能描述为自定义工作流执行、完整可视化编排或正式前端迁移已经完成。
