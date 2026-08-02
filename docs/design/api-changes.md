# API 变化记录

> 状态：Active
> Owner：RAG 团队
> Last Updated：2026-08-02
> Scope：对调用方有迁移影响的 HTTP API 变化与新增版本边界
> Related：`api-spec.md`、`agent-runtime-and-tool-contract.md`、`../adr/ADR-015-v3-data-and-api-generation.md`、`../../CHANGELOG.md`

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
| 当前前端 | Vue 已接线 | 尚无生产前端接线 |

当前 v3 OpenAPI 提供项目、任务、消息、运行、控制、SSE、审批、产物、工作流 validate，以及 Definition/不可变 Version/项目 Binding 的创建、读取、发布、绑定和归档。发布要求 expected checksum 与 Definition version，归档保留历史 Version。自定义发布工作流仍不能创建 Run；当前 executor 只执行固定 `project.inspect.v1`，不能把管理 API 写成任意 DAG 已可执行。

## 2. 迁移与回滚

- v2 调用方继续使用原路径和数据，不需要迁移。
- v3 试用数据必须写入独立 v3 数据根；不得把 `KI_V3_DB_PATH` 指向 v2 或未标记数据库。
- 回滚 v3 alpha 代码时保留 `runtime/v3/` 原文件，不把 v3 表导入 v2；现有 v2 服务和 Vue 仍是可运行基线。
- v3 alpha 尚未冻结长期兼容承诺；后续修改其路径、envelope、状态或字段时仍须在本文件登记。

后续发生破坏性变化时，本文件必须记录受影响版本、旧/新契约、迁移步骤、回滚方式和对应 ADR；普通兼容性补充直接同步 [`api-spec.md`](api-spec.md) 与 [`../../CHANGELOG.md`](../../CHANGELOG.md)。
