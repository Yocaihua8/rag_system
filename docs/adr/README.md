# ADR 说明

> 状态：Active
> Owner：RAG 团队
> Last Updated：2026-06-28

ADR（Architecture Decision Record）用于记录重要架构决策，重点不是"做了什么"，而是"为什么这样做"。

## 1. 何时需要新增 ADR

**完整的强制 / 非强制触发条件**以 `../README.md § 4 何时应新建 ADR` 为权威源，本节不再复述。

速查：出现跨模块的技术选型、存储/权限/认证/状态机变化、破坏性契约变更、替代现有方案时，**必须**新建 ADR；可逆的局部重构、实现细节调整、个人偏好类改动写入 `../devlog/` 即可。

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

模板见 `ADR-000-template.md`。

## 4. 已有 ADR 索引

| 编号 | 标题 | 状态 | 日期 |
|------|------|------|------|
| ADR-001 | 迁移至 FastAPI（替代 Python stdlib HTTP） | Accepted | 2026-05-26 |
| ADR-005 | 远程访问认证机制（API Key + JWT） | Accepted | 2026-05-26 |
| ADR-006 | 前端框架选型（Vue 3 + Vite） | Accepted | 2026-05-26 |
| ADR-007 | Qdrant 本地向量存储 | Accepted | 2026-06-28 |

## 5. 待新建 ADR（已识别但尚未落地）

以下重大决策已实施，应补充 ADR 以保留历史理由：

| 草稿编号 | 决策主题 | 触发条件 | 关联 BACKLOG |
|---------|----------|----------|-------------|
| ADR-002 | SQLite 作为关系数据源与兼容副本 | 存储模型选择，影响 ingestion / backup；向量查询替换见 ADR-007 | — |
| ADR-003 | Agent 工具只读白名单硬编码 | 权限模型，影响安全边界 | — |
| ADR-004 | API Key 只保存引用（`env:*` / `saved:*`），不持久化明文 | 安全约束，影响 settings / profiles | — |
