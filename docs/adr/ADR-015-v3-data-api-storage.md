# ADR-015 v3 数据代际、API 与存储

> 状态：Accepted
> Date：2026-08-02
> Owner：RAG 团队
> Scope：v3 SQLite、迁移工具、HTTP 契约、数据根和代际隔离
> Related：`../design/database-design.md`、`../design/api-spec.md`、`ADR-002-sqlite-storage.md`、`ADR-010-runtime-separation.md`

## 1. 背景

v3 的任务、运行、DAG、审批和产物模型与 v2 Schema/API 差异较大。仓库已确认当前 `runtime/v2/app.db` 不含业务数据，但删除属于不可逆操作，执行前仍需重新校验。继续在 v2 API/Schema 上追加兼容字段会长期保留两套语义。

## 2. 决策结论

- v3 使用独立 `runtime/v3/app.db`，SQLAlchemy 2 Core 作为存储访问层，Alembic 管理 v3 内部前向迁移。
- SQLite 启用 WAL、foreign keys、busy timeout；需要抢占或串行写入的事务使用 `BEGIN IMMEDIATE`。
- 公共 API 全部使用 `/api/v3`，不提供 `/api/v2` 兼容层；v2 路由保留到最终切换，随后整体删除。
- Pydantic DTO/OpenAPI 是前端类型事实源；响应与错误使用统一 envelope。
- v3 不自动导入、覆盖或迁移 v2 数据。
- 删除 `runtime/v2/app.db` 前必须重新确认业务表为空、进程未占用且没有待写 WAL；任一条件不满足立即停止。只允许删除这一准确文件。
- Desktop 使用随机环回端口和一次性启动令牌；Web 模式使用独立认证边界。

## 3. 决策原因

1. 新代际隔离避免在破坏性 Schema/API 重构中误伤旧数据。
2. SQLAlchemy Core 与 Alembic 提供显式 SQL/事务和可追踪迁移，不引入重 ORM 领域耦合。
3. 单一 `/api/v3` 语义避免长期维护兼容层和前端条件分支。
4. 删除前 fail-closed 能保留用户数据安全边界。

## 4. 备选方案

### 4.1 原地升级 v2 数据库和 API

- 优点：路径和客户端变化较少。
- 缺点：回滚困难，旧数据与新状态机容易混合。
- 未采用原因：当前没有需要迁移的业务数据，代际隔离更安全清晰。

### 4.2 PostgreSQL + 外部队列

- 优点：支持多实例和更强并发。
- 缺点：破坏本地免运维目标，Desktop 安装复杂。
- 未采用原因：首版仅单用户、单服务进程和两并发。

## 5. 影响

### 5.1 正面影响

- API、Schema、备份和迁移都有明确 v3 边界。
- v2 可以在切换前独立运行和回滚。

### 5.2 负面影响

- 旧客户端不能调用 v3，最终切换必须同步完成。
- 需要新的 migration、OpenAPI 客户端生成和数据库仓库测试。

### 5.3 对现有系统的改动点

- 后端配置默认数据根变更为 `runtime/v3/`。
- 新增 v3 路由、统一 envelope 和幂等/版本校验。
- 最终删除 v2 路由、Vue 调用和已确认空数据库。

## 6. 后续动作

### 6.1 实施计划

| 项目 | 内容 |
|------|------|
| 实施开始日期 | 2026-08-02 |
| 实施结束日期 | TBD |
| 实施负责人 | RAG 团队 / Codex |
| 里程碑 | Schema、migration、API 垂直切片、数据/备份、最终切换 |

### 6.2 回滚策略

| 项目 | 内容 |
|------|------|
| 回滚触发条件 | v3 Schema、API 或恢复验证失败 |
| 回滚步骤 | 停用 v3 路由和配置，恢复 v2 入口；保留失败 v3 DB 供诊断，不覆盖 v2 |
| 数据回滚说明 | v2 和 v3 数据根独立；不执行反向自动迁移 |
| 回滚责任人 | RAG 团队 |
| 不可回滚的点 | 用户已批准的外部写入不由数据库回滚撤销 |

### 6.3 验证方式

- 新数据库从空目录通过 Alembic 初始化并达到 head。
- API envelope、幂等、并发版本、SSE 续传和安全令牌测试通过。
- 删除预检对非空表、锁定数据库和 WAL fail closed。

### 6.4 待办项

- B-173 实现后以当前 OpenAPI 和 Schema 校准设计文档。
