# B-118 多用户 / 团队空间研究

> 状态：Active
> 创建时间：2026-06-30
> 创建方：Codex
> 关联 BACKLOG：B-118
> 关联功能文档：docs/features/team-workspace-research.md
> 关联设计文档：docs/design/permission-matrix.md, docs/design/system-design-overview.md, docs/requirements/project-background-and-scope.md

## 1. 目标

完成多用户 / 团队空间研究，明确当前 Web MVP 是否进入实现、未来如进入实现需要拆分哪些前置能力。研究只产出文档和后续边界，不新增用户表、权限表、团队空间接口、前端入口或运行时代码。

## 2. 前置条件

- 已读取 `AGENTS.md`、`README.md`、`docs/README.md`、`docs/BACKLOG.md`、`docs/requirements/project-background-and-scope.md`、`docs/requirements/functional-modules.md`、`docs/design/permission-matrix.md`、`docs/design/system-design-overview.md`、`docs/design/architecture-overview.md`、`docs/features/authentication.md`。
- 已确认 B-140 只是可选单用户认证层，不等于用户体系、组织体系或 RBAC。
- 已确认当前数据隔离主要依赖 `project_id`，没有 `user_id / team_id / role` 等多租户字段。
- 当前工作区存在非 B-118 既有未提交改动；执行时只暂存 B-118 相关文件和 `docs/BACKLOG.md` 的 B-118 hunk。

## 3. 任务拆解

- [ ] 梳理当前单用户边界与团队空间能力差距，形成研究文档初稿。
- [ ] 同步权限矩阵、系统范围和文档索引，运行文档验证。
- [ ] 同步 BACKLOG 完成状态，删除本 plan。

## 4. 影响范围

| 类型 | 路径 / 模块 | 变更方向 |
|------|------------|---------|
| 文档 | `docs/features/team-workspace-research.md` | 新增 |
| 文档 | `docs/design/permission-matrix.md` | 修改 |
| 文档 | `docs/design/system-design-overview.md` | 修改 |
| 文档 | `docs/requirements/project-background-and-scope.md` | 修改 |
| 文档 | `docs/requirements/functional-modules.md` | 修改 |
| 文档 | `docs/features/README.md` | 修改 |
| 文档 | `docs/README.md` | 修改 |
| 文档 | `docs/BACKLOG.md` | 修改 |

## 5. 依赖与冲突

### 5.1 依赖的其他 plan

| plan 文件 | 依赖原因 |
|-----------|---------|
| N/A | 无直接依赖 |

### 5.2 与现有 plan 的重叠

| 冲突 plan | 重叠范围（文件 / 模块 / 接口） | 解决方式 |
|-----------|-------------------------------|---------|
| N/A | N/A | N/A |

创建本 plan 时扫描到 `docs/superpowers/plans/` 下 3 个旧 plan，均为 legacy PySide6 / 旧领域模型计划，不涉及当前 Web MVP 权限矩阵、团队空间研究文档或本次影响范围。

## 6. 完成标准

- [ ] `docs/features/team-workspace-research.md` 给出明确研究结论、非目标、能力差距和后续任务拆分。
- [ ] 正式文档继续明确当前仍是本地单用户应用，多用户 / 团队空间不进入当前实现。
- [ ] 运行文档相关验证命令并记录结果。
- [ ] 相关文档已同步（见下方"回流清单"）。
- [ ] BACKLOG 条目 `B-118` 状态已更新为 `done`。

## 7. 回流清单

| 内容 | 目标文档 | 是否完成 |
|------|----------|----------|
| 多用户 / 团队空间研究结论、非目标、后续拆分 | `docs/features/team-workspace-research.md` | [ ] |
| 当前单用户权限边界与未来 RBAC 前置条件 | `docs/design/permission-matrix.md` | [ ] |
| 系统边界中的单用户/团队空间结论 | `docs/design/system-design-overview.md` | [ ] |
| 项目范围与功能模块边界同步 | `docs/requirements/project-background-and-scope.md`, `docs/requirements/functional-modules.md` | [ ] |
| 新研究文档索引 | `docs/README.md`, `docs/features/README.md` | [ ] |
| B-118 完成状态 | `docs/BACKLOG.md` | [ ] |

## 8. 执行记录

- 2026-06-30：B-118 明确为 research 小项，只做文档结论和后续任务拆分，不改运行时代码、API 或数据库 schema。

## 9. 状态快照

- **最后更新**：2026-06-30 00:00
- **进度**：已完成 0 / 3 项（见 § 3 勾选状态）
- **最新 commit**：N/A
- **代码状态**：`fix/b-08-concurrent-index`；工作区存在非 B-118 既有改动，需精确暂存
- **下一步**：梳理当前单用户边界与团队空间能力差距，形成研究文档初稿
- **续任务须知**：只暂存 B-118 相关文件和 `docs/BACKLOG.md` 的 B-118 hunk
