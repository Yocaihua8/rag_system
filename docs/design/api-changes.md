# API 变化记录

> 状态：Active
> Owner：RAG 团队
> Last Updated：2026-08-02
> Scope：对调用方有迁移影响的 HTTP API 变化与新增版本边界
> Related：`api-spec.md`、`agent-runtime-and-tool-contract.md`、`../adr/ADR-015-v3-data-api-storage.md`、`../adr/ADR-016-agent-message-stream.md`、`../../CHANGELOG.md`

## 1. 当前变化：新增 v3 alpha 命名空间

当前源码在主 FastAPI 下新增 `/api/v3` sub-app，同时完整保留 v2 路由和现有 Vue。该变化对 v2 调用方是加法兼容：没有重命名、删除或重定向既有 `/api/*` 路径，也没有把 v2 数据自动迁移到 v3。

v3 调用方必须显式适配以下不同契约：

| 维度 | v2 当前契约 | v3 alpha 契约 |
|------|-------------|---------------|
| 路径 | 既有 `/api/*` | 独立 `/api/v3/*` |
| 成功响应 | 各业务响应结构 | `data + meta.request_id` envelope |
| 错误响应 | 兼容 `error` 字符串/业务结构 | `error.code/message/details + request_id` |
| 写命令幂等 | 按现有各接口规则 | 资源与工作流管理命令统一要求 `Idempotency-Key`；工作流 validate 除外 |
| 并发控制 | 按现有业务规则 | run/approval 控制使用 `expected_version`，审批同时冻结 request hash |
| 数据 | `runtime/v2/app.db` | 默认 `runtime/v3/app.db`，拒绝未标记或非 v3 数据库 |
| 当前前端 | Vue 已接线 | React 在独立 `frontend-v3/` 接入；正式入口仍未切换 |

当前 v3 OpenAPI 提供项目、任务、消息、运行、控制、SSE、审批、产物、工作流 validate，以及 Definition/不可变 Version/项目 Binding 的创建、读取、发布、绑定和归档。发布要求 expected checksum 与 Definition version，归档保留历史 Version。自定义发布工作流仍不能创建 Run；运行创建只接受固定 `project.inspect.v1`，不能把管理 API 写成任意 DAG 已可执行。

## 2. alpha.1 → alpha.2 变化

alpha.2 已通过 v3 定向、真实 lifespan 集成及后端/集成/仓库门禁。以下是当前可达的调用方合同；独立 React 调用方已经存在，但它仍是 alpha，不代表正式入口切换、自定义发布 DAG 或通用自然语言规划器已经完成。

| 变化 | alpha.1 | alpha.2 | 调用方影响 |
|------|---------|---------|------------|
| OpenAPI 应用版本 | `3.0.0-alpha.1` | `3.0.0-alpha.2` | 客户端生成物必须记录对应版本 |
| 创建任务请求 | `project_id/title/message` | 不变 | 无请求迁移 |
| 创建任务响应 data | `task/replayed` | `task/initial_message/replayed` | 保存 `initial_message.id`；幂等回放继续使用同一消息 |
| 创建 Run 请求 | `workflow_key/depth` | 新增必填 `input_message_id` | 破坏性变化；必须引用同 Task 的用户消息 |
| 手动 Run 重试并发 | 不限制同一失败源的不同命令 | 同一失败源只允许一个直接 retry Run | 原 Key 可回放；其他 Key 返回 `409 state_conflict`，调用方应刷新任务运行列表 |
| Task 运行发现 | 无按 Task 查询 Run 的接口 | 新增 `GET /tasks/{task_id}/runs` | 加法兼容；刷新时按服务端最近 Run 恢复，不依赖本地伪状态 |
| 幂等 Header 的 OpenAPI 声明 | Schema 中可被生成器视为可选 | 所有持久写命令标记 `Idempotency-Key` 为 required | 生成客户端必须显式传 Header；缺失返回 `422 validation_error` |
| 运行输入 | 读取 Task prompt | 在 trigger Step 冻结消息 ID 与内容 hash，执行时回读不可变任务消息并校验 hash | 后续消息不改变已创建 Run；Step/SSE 不复制完整输入正文 |
| 固定工作流 | key `project.inspect.v1`、version 1、三步 | key 不变、version 2、增加 `agent.respond` 为第四步 | 不得把 version 2 错写成新 API key；旧 version 1 历史仍可读取 |
| SSE | Run/Step/Approval/Artifact/Tool 基础事件 | 新增 Agent 消息事件，并补齐 Step 与 Approval 终态事件 | 客户端按 sequence 去重并支持未知的新增事件 |
| OpenAPI 事件类型 | 运行时事件为通用 SSE | `AgentEvent` 使用 `event_type` discriminated union | components 已显式暴露并通过契约测试；生产 React 前端已获授权生成 TS 类型 |

新增事件：

- `assistant.message.started / delta / completed / interrupted`
- `step.waiting_approval / failed / cancelled / recovery_required`
- `approval.expired`

`artifact.created.payload.status=ready` 继续表示当前内部产物就绪。导出执行未实现前，没有 `artifact.exported` 合同。

### 2.1 v3 alpha 客户端迁移顺序

1. 调用 `POST /api/v3/tasks`，从 `data.initial_message.id` 保存首条输入消息 ID。
2. 调用 `POST /api/v3/tasks/{task_id}/runs` 时提交该 ID；跨任务消息、非用户消息或不存在消息会失败。
3. 刷新或直接打开 Task 时调用 `GET /api/v3/tasks/{task_id}/runs?limit=1`，以返回的 Run ID 恢复详情和事件游标。
4. SSE reducer 先按 `sequence` 去重，再按稳定 `message_id/chunk_index` 拼接回答；刷新历史以任务消息为准。
5. 只有收到服务端 completed/interrupted、Run、Step 或 Approval 事件后才推进最终状态，不从按钮回调推断成功。
6. 保留对未知新增事件的安全忽略/日志能力，避免 alpha 后续加法事件让整个连接失败。

### 2.2 兼容与回滚

- 变化只影响 `/api/v3` alpha 调用方；v2 Vue 和 `/api/*` 不需要迁移。
- 已保存 workflow version 1 Run、Step、消息和事件不改写，通过原读取接口继续可见。
- 若 alpha.2 回滚，保留 `runtime/v3/` 供诊断，不把 version 2 Run 改写为 version 1，也不把 v3 消息导入 v2。
- 客户端不能通过省略 `input_message_id` 兼容 alpha.2；回滚时应使用匹配 alpha.1 的客户端版本。

## 3. 代际迁移与回滚

- v2 调用方继续使用原路径和数据，不需要迁移。
- v3 试用数据必须写入独立 v3 数据根；不得把 `KI_V3_DB_PATH` 指向 v2 或未标记数据库。
- 回滚 v3 alpha 代码时保留 `runtime/v3/` 原文件，不把 v3 表导入 v2；现有 v2 服务和 Vue 仍是可运行基线。
- v3 alpha 尚未冻结长期兼容承诺；后续修改其路径、envelope、状态或字段时仍须在本文件登记。

后续发生破坏性变化时，本文件必须记录受影响版本、旧/新契约、迁移步骤、回滚方式和对应 ADR；普通兼容性补充直接同步 [`api-spec.md`](api-spec.md) 与 [`../../CHANGELOG.md`](../../CHANGELOG.md)。
