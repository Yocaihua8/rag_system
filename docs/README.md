# Knowledge Island 文档总览

> 状态：Active
> Owner：RAG 团队
> Last Updated：2026-08-01
> Scope：当前需求、设计、功能、决策、操作指南和临时执行计划
> Related：`../README.md`、`BACKLOG.md`、`../CHANGELOG.md`

本文档树只保存当前有效的产品和工程事实。已完成变更进入 `CHANGELOG.md` 与 Git 历史；未完成事项进入 `BACKLOG.md`。仓库不再维护 DevLog、readiness 快照、已验收 preview 或工具生成的历史 plan。

## 1. 阅读顺序

1. [`../README.md`](../README.md)：产品定位、快速开始与仓库结构
2. [`requirements/README.md`](requirements/README.md)：产品范围、用户用例和版本边界
3. [`features/README.md`](features/README.md)：用户能力与当前可达性
4. [`design/README.md`](design/README.md)：系统、API、数据、状态和界面契约
5. [`adr/README.md`](adr/README.md)：Accepted 架构决策
6. [`guides/setup.md`](guides/setup.md) 与 [`guides/testing.md`](guides/testing.md)：搭建和验证
7. [`guides/runbook.md`](guides/runbook.md)：启停、健康检查、备份与恢复
8. [`BACKLOG.md`](BACKLOG.md)：未完成事项和已知问题

## 2. 目录

| 路径 | 内容 | 事实边界 |
|------|------|----------|
| [`requirements/`](requirements/) | 产品背景、模块、用例和版本范围 | 为什么做、为谁做、当前包含什么 |
| [`design/`](design/) | 完整系统、API、数据、权限、状态和 UI 契约 | 如何组成、边界和不变量 |
| [`features/`](features/) | 逐项用户能力规格 | 当前可达行为和明确限制 |
| [`adr/`](adr/) | Accepted ADR 与模板 | 重要技术决策和取舍 |
| [`guides/`](guides/) | 搭建、测试、运行、发布、安全和协作 | 可执行操作 |
| [`plans/`](plans/) | 当前 Active/Interrupted AI plan 与模板 | 完成后删除活动 plan |
| [`style-guide.md`](style-guide.md) | 写作、元数据和链接规范 | 文档维护规则 |
| [`glossary.md`](glossary.md) | 项目术语 | 统一含义和缩写 |
| [`BACKLOG.md`](BACKLOG.md) | `todo/doing/blocked/wontfix` 事项与开放问题 | 不保存已完成历史 |

目录内部保持扁平。前端、后端、Desktop、Obsidian、Docker 和 GitHub 只作为统一系统的组成写入对应设计、功能或指南，不建立专题子目录。

## 3. 事实优先级

发生冲突时按以下顺序判断：

1. 当前源码、配置、Schema 和测试；
2. Accepted ADR；
3. `design/` 与 `features/` 当前规格；
4. `guides/` 可执行说明；
5. `BACKLOG.md` 中的计划性内容。

无法从源码确认的内容标记为 `TBD`、`N/A` 或“待确认”，不得把设想写成已实现事实。

## 4. 更新规则

| 变更 | 必须同步 |
|------|----------|
| 产品范围、角色或版本边界 | `requirements/` |
| 功能行为 | `features/<name>.md` |
| HTTP 路径、参数或响应 | `design/api-spec.md`；破坏性变化同步 `design/api-changes.md` 与必要 ADR |
| SQLite 表、字段、索引或迁移 | `design/database-design.md` |
| 页面、组件或交互流程 | `design/ui-wireframes.md`、页面/组件契约和对应功能规格 |
| 跨模块架构边界 | `design/system-design-overview.md`、`design/architecture-overview.md` 与必要 ADR |
| Desktop、Obsidian、GitHub | 对应功能规格以及 `guides/` 中按操作目的归类的文档 |
| 命令、依赖、Docker、发布或安全 | `guides/` |
| 未完成事项 | `BACKLOG.md` |
| 已完成且对使用者/维护者有意义 | `CHANGELOG.md` |

新 ADR 使用 [`adr/ADR-000-template.md`](adr/ADR-000-template.md)，并追加到 [`adr/README.md`](adr/README.md)。新功能、RFC 和 plan 分别使用 [`features/feature-template.md`](features/feature-template.md)、[`design/rfc-template.md`](design/rfc-template.md) 和 [`plans/plan-template.md`](plans/plan-template.md)。

## 5. 计划生命周期

- 涉及代码或跨文件行为变更时，先在 `BACKLOG.md` 建立 `B-xxx`，状态设为 `doing`。
- 冲突扫描后，在 `plans/{B-ID}-{slug}.md` 创建执行 plan，并把路径回写 BACKLOG。
- 执行中按任务勾选、提交和更新状态快照；中断时保留 plan。
- 完成后回流对应文档和 `CHANGELOG.md`，从 BACKLOG 移除完成条目并删除 plan。

完整规则见 [`plans/README.md`](plans/README.md) 和根 [`AGENTS.md`](../AGENTS.md)。

## 6. 文档门禁

从仓库根目录执行：

```powershell
pwsh -NoProfile -File scripts/check-placeholders.ps1
pwsh -NoProfile -File scripts/check-doc-links.ps1
.\.venv\Scripts\python.exe scripts/check_docs_consistency.py
```

门禁检查活动目录索引、元数据、内部链接、占位符和已删除路径引用；历史文件不再作为例外输入。
