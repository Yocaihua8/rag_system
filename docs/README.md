# Knowledge Island 文档总览

> 状态：Active
> Owner：RAG 团队
> Last Updated：2026-08-01
> Scope：当前产品、架构、集成、运维和治理文档
> Related：`../README.md`、`BACKLOG.md`、`../CHANGELOG.md`

本文档树只保存当前有效的产品和工程事实。已完成变更进入 `CHANGELOG.md` 与 Git 历史；未完成事项进入 `BACKLOG.md`。仓库不再维护 DevLog、readiness 快照、已验收 preview 或工具生成的历史 plan。

## 1. 阅读顺序

1. [`../README.md`](../README.md)：产品定位、快速开始与仓库结构
2. [`product/overview.md`](product/overview.md)：范围和版本边界
3. [`product/features/README.md`](product/features/README.md)：功能入口与可达性
4. [`architecture/overview.md`](architecture/overview.md)：运行时和分层边界
5. [`architecture/backend/api.md`](architecture/backend/api.md)：HTTP 字段级契约
6. [`architecture/backend/data.md`](architecture/backend/data.md)：SQLite 结构与迁移约束
7. [`operations/setup.md`](operations/setup.md) 与 [`operations/testing.md`](operations/testing.md)：搭建和验证
8. [`BACKLOG.md`](BACKLOG.md)：未完成事项和已知问题

## 2. 目录

| 路径 | 内容 | 事实边界 |
|------|------|----------|
| [`product/`](product/) | 产品概览、模块、用例、术语和功能规格 | 用户可见行为与明确边界 |
| [`architecture/backend/`](architecture/backend/) | API、数据、模型 Profile、集合、批次和 Prompt | 后端实现与契约 |
| [`architecture/frontend/`](architecture/frontend/) | 页面、组件、视觉和工作台结构 | 前端展示与交互契约 |
| [`architecture/contracts/`](architecture/contracts/) | 前后端对照、权限、状态与验收 | 跨模块不变量 |
| [`architecture/decisions/`](architecture/decisions/) | Accepted ADR 索引和记录 | 重要决策与取舍 |
| [`integrations/`](integrations/) | Tauri、Obsidian、GitHub | 外部/桌面边界 |
| [`operations/`](operations/) | 搭建、Docker、测试、发布、安全、支持、排障 | 可执行操作 |
| [`governance/plans/`](governance/plans/) | 当前 Active/Interrupted AI plan | 完成后删除 |
| [`governance/templates/`](governance/templates/) | ADR、功能、RFC、计划等模板 | 新文档起点 |
| [`governance/`](governance/) | 分支、开源、许可证、风险和写作规范 | 协作规则 |
| [`BACKLOG.md`](BACKLOG.md) | `todo/doing/blocked/wontfix` 事项与开放问题 | 不保存已完成历史 |

## 3. 事实优先级

发生冲突时按以下顺序判断：

1. 当前源码、配置、Schema 和测试；
2. Accepted ADR；
3. `architecture/` 与 `product/` 当前规格；
4. `operations/` 可执行说明；
5. `BACKLOG.md` 中的计划性内容。

无法从源码确认的内容标记为 `TBD`、`N/A` 或“待确认”，不得把设想写成已实现事实。

## 4. 更新规则

| 变更 | 必须同步 |
|------|----------|
| 功能行为 | `product/features/<name>.md` |
| HTTP 路径、参数或响应 | `architecture/backend/api.md`；破坏性变化另建 ADR |
| SQLite 表、字段、索引或迁移 | `architecture/backend/data.md` |
| 页面、组件或交互流程 | `architecture/frontend/` 和对应功能规格 |
| 跨模块架构边界 | `architecture/overview.md` 与必要 ADR |
| 桌面、Obsidian、GitHub | `integrations/` |
| 命令、依赖、Docker、发布或安全 | `operations/` |
| 未完成事项 | `BACKLOG.md` |
| 已完成且对使用者/维护者有意义 | `CHANGELOG.md` |

新 ADR 使用 [`governance/templates/adr-template.md`](governance/templates/adr-template.md)，并追加到 [`architecture/decisions/README.md`](architecture/decisions/README.md)。

## 5. 计划生命周期

- 涉及代码或跨文件行为变更时，先在 `BACKLOG.md` 建立 `B-xxx`，状态设为 `doing`。
- 冲突扫描后，在 `governance/plans/{B-ID}-{slug}.md` 创建执行 plan，并把路径回写 BACKLOG。
- 执行中按任务勾选、提交和更新状态快照；中断时保留 plan。
- 完成后回流对应文档和 `CHANGELOG.md`，从 BACKLOG 移除完成条目并删除 plan。

完整规则见 [`governance/plans/README.md`](governance/plans/README.md) 和根 [`AGENTS.md`](../AGENTS.md)。

## 6. 文档门禁

从仓库根目录执行：

```powershell
pwsh -NoProfile -File tools/docs/check-placeholders.ps1
pwsh -NoProfile -File tools/docs/check-doc-links.ps1
.\.venv\Scripts\python.exe tools/docs/check_docs_consistency.py
```

门禁检查活动目录索引、元数据、内部链接、占位符和已删除路径引用；历史文件不再作为例外输入。
