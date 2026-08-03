# 设计文档索引

> 状态：Active
> Owner：RAG 团队
> Last Updated：2026-08-02
> Scope：Knowledge Island 完整系统的架构、契约、数据、状态、安全和界面设计
> Related：`../README.md`、`../requirements/README.md`、`../features/README.md`、`../adr/README.md`

本目录统一描述完整系统。Vue、FastAPI、SQLite、Tauri、Docker 与 Obsidian 是同一系统中的组成部分，不再建立前端、后端、集成或运维专题子目录。

| 文档 | 职责 |
|------|------|
| [`system-design-overview.md`](system-design-overview.md) | 系统组成、运行形态与依赖关系 |
| [`architecture-overview.md`](architecture-overview.md) | 分层边界、依赖方向与运行时约束 |
| [`api-spec.md`](api-spec.md) | 当前 HTTP/SSE 接口契约 |
| [`api-changes.md`](api-changes.md) | 破坏性 API 变化登记规则与当前记录 |
| [`database-design.md`](database-design.md) | SQLite 表、字段、索引和代际约束 |
| [`permission-matrix.md`](permission-matrix.md) | 认证、授权、CORS、密钥和 Agent 权限 |
| [`state-flow-and-acceptance.md`](state-flow-and-acceptance.md) | 导入、问答、Coach、发布与 sidecar 状态 |
| [`frontend-backend-contract-check.md`](frontend-backend-contract-check.md) | 可达界面与 API 接线对照 |
| [`ui-wireframes.md`](ui-wireframes.md) | 当前可达页面与区域结构 |
| [`page-module-contract.md`](page-module-contract.md) | 页面模块顺序和集成边界 |
| [`component-api-contract.md`](component-api-contract.md) | 活动组件 props、emits 与调用约束 |
| [`risk-register.md`](risk-register.md) | 当前架构和交付风险 |
| [`agent-runtime-and-tool-contract.md`](agent-runtime-and-tool-contract.md) | v3 持久运行、工作流节点、审批和工具安全合同 |
| [`ui-prototype-brief-v3.md`](ui-prototype-brief-v3.md) | P1/P2 原型覆盖、布局、状态与前端实施门禁 |
| [`v3-document-migration.md`](v3-document-migration.md) | 旧文档事实吸收、归并和安全删除矩阵 |
| [`v3-sources-contract.md`](v3-sources-contract.md) | v3 Sources 的路径、响应脱敏和持久化合同 |
| [`rfc-template.md`](rfc-template.md) | 设计提案模板，不代表已批准方案 |

重要决策见 [`../adr/README.md`](../adr/README.md)，未完成设计只进入 [`../BACKLOG.md`](../BACKLOG.md)。
