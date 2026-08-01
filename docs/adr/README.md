# ADR 说明

> 状态：Active
> Owner：RAG 团队
> Last Updated：2026-08-01
> Scope：Knowledge Island 架构决策的触发规则、状态和索引
> Related：`../design/architecture-overview.md`、`ADR-000-template.md`

ADR（Architecture Decision Record）用于记录重要架构决策，重点不是"做了什么"，而是"为什么这样做"。

## 1. 何时需要新增 ADR

**完整的强制 / 非强制触发条件**以 [`../README.md`](../README.md) 的文档治理规则为权威源，本节不再复述。

速查：出现跨模块的技术选型、存储/权限/认证/状态机变化、破坏性契约变更、替代现有方案时，**必须**新建 ADR；可逆的局部重构直接记录在 Git 提交和关联文档中。

## 2. 文件命名规范

```text
ADR-001-short-title.md
ADR-002-short-title.md
```

## 3. 最低内容要求

- 背景
- 决策结论
- 备选方案
- 影响
- 后续动作（含实施计划 / 回滚策略 / 验证方式）

模板见 [`ADR-000-template.md`](ADR-000-template.md)。复制后从下一个可用编号开始，不把模板当作真实决策。

## 4. 已有 ADR 索引

| 编号 | 标题 | 状态 | 日期 |
|------|------|------|------|
| [ADR-001](ADR-001-fastapi-migration.md) | 迁移至 FastAPI（替代 Python stdlib HTTP） | Accepted | 2026-05-26 |
| [ADR-002](ADR-002-sqlite-storage.md) | SQLite 作为关系数据源与兼容副本 | Accepted | 2026-05-21 |
| [ADR-003](ADR-003-agent-readonly-whitelist.md) | Agent 工具只读白名单硬编码 | Accepted | 2026-05-26 |
| [ADR-004](ADR-004-api-key-reference.md) | API Key 只保存引用，不持久化明文 | Accepted | 2026-05-26 |
| [ADR-005](ADR-005-remote-auth.md) | 远程访问认证机制（API Key + JWT） | Accepted | 2026-05-26 |
| [ADR-006](ADR-006-vue-vite-frontend.md) | 前端框架选型（Vue 3 + Vite） | Accepted | 2026-05-26 |
| [ADR-007](ADR-007-qdrant-vector-store.md) | Qdrant 本地向量存储 | Accepted | 2026-06-28 |
| [ADR-008](ADR-008-project-knowledge-coach-v2.md) | 项目知识教练与 v2 数据代际 | Accepted | 2026-07-23 |
| [ADR-009](ADR-009-obsidian-plugin-bridge.md) | Obsidian 桌面插件桥与受控写回 | Accepted | 2026-07-23 |
| [ADR-010](ADR-010-runtime-separation.md) | 前后端运行时分离 | Accepted | 2026-08-01 |
