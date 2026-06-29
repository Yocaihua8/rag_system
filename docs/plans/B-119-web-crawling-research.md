# B-119 网页自动抓取研究

> 状态：Active
> 创建时间：2026-06-30
> 创建方：Codex
> 关联 BACKLOG：B-119
> 关联功能文档：docs/features/web-crawling-research.md
> 关联设计文档：docs/requirements/functional-modules.md, docs/design/api-spec.md, docs/design/system-design-overview.md

## 1. 目标

梳理 Knowledge Island 当前 URL 摘录导入与未来网页自动抓取之间的边界，输出可执行的研究结论：哪些能力保持不实现、未来若进入 B-132 需要满足哪些安全、合规、依赖和验收约束。完成后系统行为不发生代码变化，当前 `/api/import/url` 仍只保存用户手动粘贴正文。

## 2. 前置条件

- 已读取 `AGENTS.md`
- 已读取 `docs/BACKLOG.md`
- 已读取 `docs/requirements/functional-modules.md`
- 已读取 `docs/design/api-spec.md`
- 已读取 `docs/design/system-design-overview.md`
- 已扫描 `docs/plans/` 与 `docs/superpowers/plans/` 的现有计划文件

## 3. 任务拆解

每完成一项，立即执行：① 勾选此处 ② `git commit` 保存进度 ③ 更新 § 9 状态快照。
未完成项不得删除。

- [x] 梳理当前 URL 摘录边界、网页抓取能力差距和外部标准/依赖风险，形成研究文档。
- [x] 同步需求、接口、系统设计和文档索引，运行文档验证。
- [ ] 同步 BACKLOG 完成状态，删除本 plan。

## 4. 影响范围

| 类型 | 路径 / 模块 | 变更方向 |
|------|------------|---------|
| 文档 | `docs/features/web-crawling-research.md` | 新增 |
| 文档 | `docs/requirements/functional-modules.md` | 修改 |
| 文档 | `docs/requirements/project-background-and-scope.md` | 修改 |
| 文档 | `docs/design/api-spec.md` | 修改 |
| 文档 | `docs/design/system-design-overview.md` | 修改 |
| 文档 | `docs/features/README.md` | 修改 |
| 文档 | `docs/README.md` | 修改 |
| 文档 | `docs/BACKLOG.md` | 修改 |

## 5. 依赖与冲突

### 5.1 依赖的其他 plan

| plan 文件 | 依赖原因 |
|-----------|---------|
| N/A | 本次为独立研究文档，不依赖其他活动 plan。 |

### 5.2 与现有 plan 的重叠

| 冲突 plan | 重叠范围（文件 / 模块 / 接口） | 解决方式 |
|-----------|-------------------------------|---------|
| N/A | `docs/plans/` 中无活动任务；`docs/superpowers/plans/` 仅有历史 PySide6 / legacy 模型计划，未发现与 B-119 目标文档重叠。 | N/A |

## 6. 完成标准

全部勾选后方可删除本 plan 文件：

- [ ] 研究结论写入 `docs/features/web-crawling-research.md`
- [ ] 测试通过（参照 `../guides/testing.md` 最低要求）
- [ ] 相关文档已同步（见下方"回流清单"）
- [ ] BACKLOG 条目 `B-119` 状态已更新为 `done`

## 7. 回流清单

删除本文件前，确认以下内容已写入正式文档：

| 内容 | 目标文档 | 是否完成 |
|------|----------|----------|
| 网页自动抓取研究结论和推荐边界 | `docs/features/web-crawling-research.md` | [x] |
| URL 摘录当前能力与不支持自动抓取的边界 | `docs/requirements/functional-modules.md` | [x] |
| B-119 / B-132 范围边界 | `docs/requirements/project-background-and-scope.md` | [x] |
| `/api/import/url` 当前不联网、不抓取的接口契约 | `docs/design/api-spec.md` | [x] |
| 系统边界、安全约束和待补充设计 | `docs/design/system-design-overview.md` | [x] |
| 新功能文档索引 | `docs/features/README.md`, `docs/README.md` | [x] |

若产生了重大技术决策，**必须**在删除 plan 前新建对应 ADR。

## 8. 执行记录

- 2026-06-30：创建计划。当前工作区存在与本任务无关的未提交改动，B-119 仅暂存和提交本计划列出的文件。
- 2026-06-30：完成研究文档初稿。结论为当前保持手动 URL 摘录，B-132 若进入实现必须先满足 robots、SSRF、防登录态、内容净化和依赖隔离约束。
- 2026-06-30：完成需求、项目范围、API 契约、系统设计和文档索引回流；未修改运行时代码、接口实现或数据库 schema。

## 9. 状态快照

- **最后更新**：2026-06-30 00:56
- **进度**：已完成 2 / 3 项（见 § 3 勾选状态）
- **最新 commit**：`f833395` — docs: 完成 B-119 网页抓取研究结论
- **代码状态**：`fix/b-08-concurrent-index`；工作区存在与本任务无关的未提交改动；正式文档已回流，待验证后关闭 B-119
- **下一步**：同步 BACKLOG 完成状态，删除本 plan。
- **续任务须知**：只暂存 B-119 相关文件；不要吸收既有 `docs/architecture/*` 与 `scripts/check_docs_consistency.py` 改动。
