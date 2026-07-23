# B-160 项目知识教练方向与 v2 数据代际冻结

> ⚠️ 创建此文件前，必须已完成以下操作（AI 自检）：
> - [x] `docs/BACKLOG.md` 中已有 B-160 条目，状态为 `doing`
> - [x] B-160 说明列已填入本文件路径
> - [x] 关联功能文档和设计文档已按实际范围填写

> 状态：Active
> 创建时间：2026-07-23
> 创建方：Codex
> 关联 BACKLOG：B-160
> 关联功能文档：docs/features/project-knowledge-coach.md
> 关联设计文档：docs/design/architecture-overview.md, docs/design/database-design.md, docs/design/api-spec.md, docs/design/ui-wireframes.md

## 1. 目标

将 Knowledge Island 的正式方向冻结为面向个人开发学习的本地项目知识教练，明确项目知识覆盖与通用技能树边界、v2 全新数据代际、Obsidian 插件桥和后续 B-161～B-165 的实现分工。

## 2. 前置条件

- B-159 Codex 风格视觉规范已在 `ec236b1` 独立提交
- 当前分支为 `feature/project-knowledge-coach-v2`，工作区无未提交改动

## 3. 任务拆解

- [x] 冻结产品定位、MVP、用例、功能边界与前端信息架构
- [x] 冻结 v2 数据代际和 Obsidian 插件桥架构，新增 ADR-008/ADR-009
- [ ] 同步文档索引、BACKLOG、风险与后续实现切片并完成一致性验证

## 4. 影响范围

| 类型 | 路径 / 模块 | 变更方向 |
|------|------------|---------|
| 文档 | `docs/requirements/`、`docs/features/` | 重写产品方向与 MVP |
| 文档 | `docs/design/`、`docs/adr/` | 冻结架构、数据、API 与交互边界 |
| 文档 | `docs/BACKLOG.md`、`docs/README.md` | 建立 B-160～B-165 路线与入口 |

## 5. 依赖与冲突

### 5.1 依赖的其他 plan

| plan 文件 | 依赖原因 |
|-----------|---------|
| N/A | B-159 已完成且无活动 plan |

### 5.2 与现有 plan 的重叠

| 冲突 plan | 重叠范围（文件 / 模块 / 接口） | 解决方式 |
|-----------|-------------------------------|---------|
| N/A | N/A | N/A |

> `docs/superpowers/plans/` 下三份无状态旧 PySide6 计划属于历史残留，不作为活动 plan，也不恢复其 legacy 架构。

## 6. 完成标准

- [ ] 功能行为符合 `docs/features/project-knowledge-coach.md` 的业务规则
- [ ] 文档一致性与 `git diff --check` 通过
- [ ] 回流清单全部完成
- [ ] BACKLOG B-160 状态更新为 `done`

## 7. 回流清单

| 内容 | 目标文档 | 是否完成 |
|------|----------|----------|
| 产品方向、用户闭环与范围 | `docs/requirements/*`, `docs/features/project-knowledge-coach.md` | [ ] |
| v2 数据代际与插件桥决策 | `docs/design/*`, `docs/adr/ADR-008*`, `docs/adr/ADR-009*` | [ ] |
| 路线、风险与文档入口 | `docs/BACKLOG.md`, `docs/README.md`, `docs/design/risk-register.md` | [ ] |

## 8. 执行记录

- 2026-07-23：冲突扫描未发现 Active/Interrupted plan；旧 superpowers plan 不参与当前架构。
- 2026-07-23：完成产品定位、MVP、用例、功能边界与前端信息架构冻结；校准 README，明确 legacy 掌握度模型不是当前 Web 能力。
- 2026-07-23：完成 v2 独立数据代际、Coach 领域边界和 Obsidian 插件受控写回决策，新增 ADR-008/ADR-009。

## 9. 状态快照

- **最后更新**：2026-07-23
- **进度**：已完成 2 / 3 项
- **最新 commit**：`8df99e1` — docs: 冻结项目知识教练产品与交互方向
- **代码状态**：`feature/project-knowledge-coach-v2`；架构、数据代际与 ADR 文档待提交
- **下一步**：同步文档索引、BACKLOG、风险与后续实现切片并完成一致性验证
- **续任务须知**：B-157 已按用户决策置为 wontfix；旧 runtime 数据不得删除或迁移
