# ADR 说明

> 状态：Active
> Owner：RAG 团队
> Last Updated：2026-08-02
> Scope：Knowledge Island 架构决策的职责、生命周期和当前索引
> Related：[文档总览](../README.md)、[系统设计总览](../design/system-design-overview.md)、[ADR 模板](ADR-000-template.md)

ADR（Architecture Decision Record）记录影响系统边界的重要决策及其取舍，回答“为什么采用这个方案”。当前实现细节以源码、测试和 [`design/`](../design/) 为准；ADR 保留决策发生时的背景，不代替功能规格、操作指南、BACKLOG 或 CHANGELOG。

## 1. 职责边界

- 跨模块技术选型、存储、权限、认证、状态机、破坏性契约或对既有决策的取代，需要新增或更新 ADR。
- 可逆的局部实现调整记录在关联设计文档、CHANGELOG 和 Git 历史中，不为每次重构新增 ADR。
- 未完成事项只进入 [`BACKLOG.md`](../BACKLOG.md)；ADR 不用来维护任务进度。
- 决策与当前实现发生偏差时，在 ADR 中标明取代或偏差关系，并在当前设计/功能文档中写清可达行为。

完整触发条件以 [`docs/README.md`](../README.md) 的文档治理规则为准。

## 2. 状态与文件命名

ADR 状态使用 `Proposed`、`Accepted`、`Deprecated`、`Superseded` 或 `Rejected`。仅部分结论被新 ADR 取代时，原 ADR 可保持 `Accepted`，但必须在元数据、正文和索引中说明取代范围。

```text
ADR-001-short-title.md
ADR-002-short-title.md
```

## 3. 最低内容要求

- 背景与决策范围
- 决策结论及原因
- 备选方案
- 正负面影响
- 回滚策略与验证方式
- 与其他 ADR、当前设计和功能规格的关系

从 [`ADR-000-template.md`](ADR-000-template.md) 复制新文件，使用下一个可用编号，并同步更新本索引。模板不是已生效决策。

## 4. ADR 索引

| 编号 | 标题 | 状态 | 日期 | 当前关系 |
|------|------|------|------|----------|
| [ADR-001](ADR-001-fastapi-migration.md) | 迁移至 FastAPI（替代 Python stdlib HTTP） | Accepted | 2026-05-26 | FastAPI 选择有效；静态托管边界见 ADR-010 |
| [ADR-002](ADR-002-sqlite-storage.md) | SQLite 作为关系数据源与兼容副本 | Accepted | 2026-05-21 | SQLite 仍是关系数据唯一入口，向量兼容副本与 ADR-007 并存 |
| [ADR-003](ADR-003-agent-readonly-whitelist.md) | Agent 工具只读白名单硬编码 | Superseded | 2026-05-26 | 当前 v2 实现仍使用；v3 目标权限由 ADR-012 取代 |
| [ADR-004](ADR-004-api-key-reference.md) | 模型 Profile 的 API Key 只保存引用 | Accepted | 2026-05-26 | 仅约束 Profile/SQLite；兼容全局设置的落盘边界见正文 |
| [ADR-005](ADR-005-remote-auth.md) | 远程访问认证机制（API Key + JWT） | Accepted | 2026-05-26 | 默认关闭；启用后 Vue 与原生 EventSource 尚未接入凭证 |
| [ADR-006](ADR-006-vue-vite-frontend.md) | 前端框架选型（Vue 3 + Vite） | Superseded | 2026-05-26 | 当前 v2 仍使用；v3 由 ADR-014 取代，运行时分离由 ADR-010 保持 |
| [ADR-007](ADR-007-qdrant-vector-store.md) | Qdrant 本地向量存储 | Accepted | 2026-06-28 | Qdrant local mode 可配置启用，SQLite 保留兼容副本 |
| [ADR-008](ADR-008-project-knowledge-coach-v2.md) | 项目知识教练与 v2 数据代际 | Superseded | 2026-07-23 | 当前 v2 运行事实保留；v3 产品和数据目标由 ADR-012、ADR-015 取代 |
| [ADR-009](ADR-009-obsidian-plugin-bridge.md) | Obsidian 桌面插件桥与受控写回 | Accepted | 2026-07-23 | desktop-only 插件、幂等同步和受控发布边界有效 |
| [ADR-010](ADR-010-runtime-separation.md) | 前后端运行时分离 | Accepted | 2026-08-01 | 取代 ADR-006 的静态托管/同源请求部分，不拆分产品领域 |
| [ADR-011](ADR-011-interactive-learning-sql-sandbox.md) | 逐知识点学习会话与只读 SQL 沙箱 | Accepted | 2026-08-01 | 增量会话模型与隔离只读 SQL 评分边界已由 B-171 当前提交验证 |
| [ADR-012](ADR-012-agent-product-and-permissions.md) | v3 通用项目 Agent 与权限边界 | Accepted | 2026-08-02 | 取代 ADR-003 的 v3 工具范围和 ADR-008 的目标产品定位；v2 实现保留到切换 |
| [ADR-013](ADR-013-durable-dag-executor.md) | SQLite 持久化 DAG 执行器 | Accepted | 2026-08-02 | v3 任务、租约、并发、事件和恢复的权威决策 |
| [ADR-014](ADR-014-react-typescript-frontend.md) | v3 前端采用 React 与 TypeScript | Accepted | 2026-08-02 | P2 批准后取代 ADR-006 的 Vue 框架选择；运行时分离继续有效 |
| [ADR-015](ADR-015-v3-data-api-storage.md) | v3 数据代际、API 与存储 | Accepted | 2026-08-02 | 独立 v3 数据根、`/api/v3`、SQLAlchemy Core 与 Alembic |
