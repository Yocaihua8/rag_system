# B-162 持久评估、双层差距与学习计划

> ⚠️ 创建此文件前，必须已完成以下操作（AI 自检）：
> - [x] `docs/BACKLOG.md` 中 B-162 状态为 `doing`
> - [x] B-162 说明列已填入本文件路径
> - [x] 关联功能文档和设计文档已按实际范围填写

> 状态：Active
> 创建时间：2026-07-23
> 创建方：Codex
> 关联 BACKLOG：B-162
> 关联功能文档：docs/features/project-knowledge-coach.md
> 关联设计文档：docs/design/architecture-overview.md, docs/design/database-design.md, docs/design/api-spec.md

## 1. 目标

在 B-161 有来源的项目知识模型上实现可恢复的定向评估、项目知识覆盖与辅助技能聚合，以及可编辑、排序、确认且保留版本的学习计划。新闭环只使用 `/api/coach/*`，旧 `/api/assessment/*` 契约和数据保持不变。

## 2. 前置条件

- B-161 已完成并提交，当前可展示分析只选择 `completed / stale` 运行
- ADR-008 与 `docs/features/project-knowledge-coach.md` 已冻结评估阈值、当前项目边界和计划版本语义
- 分支为 `feature/project-knowledge-coach-v2`

## 3. 任务拆解

- [x] 新增评估与学习计划领域模型、六张持久化表、跨项目约束和存储测试
- [x] 实现定向评估会话、规则/模型评分、恢复语义、覆盖率与技能差距聚合，并接入三个 Coach API
- [x] 实现学习计划新草稿生成、编辑排序、确认与来源解析，并接入四个 Coach API
- [ ] 同步 OpenAPI、数据库、功能与测试文档，完成 B-162 回归并关闭任务

## 4. 影响范围

| 类型 | 路径 / 模块 | 变更方向 |
|------|------------|---------|
| 代码 | `backend/domain/coach_models.py`, `backend/domain/coach_assessment.py`, `backend/domain/learning_plans.py` | 新增评估、覆盖与计划领域行为 |
| 代码 | `backend/storage/coach_progress_store.py`, `backend/storage/knowledge_store.py` | 新增六张表与项目隔离的读写入口 |
| 代码 | `backend/routes/coach.py`, `backend/api/openapi_schema.py` | 新增七个 Coach API operation |
| 测试 | `tests/test_backend/`, `tests/test_webapp/` | 存储、规则、恢复、聚合、计划与 API 契约 |
| 文档 | `docs/features/project-knowledge-coach.md`, `docs/design/api-spec.md`, `docs/design/database-design.md`, `docs/design/architecture-overview.md`, `docs/guides/testing.md` | 将 B-162 已实现行为回流为当前事实 |

## 5. 依赖与冲突

### 5.1 依赖的其他 plan

| plan 文件 | 依赖原因 |
|-----------|---------|
| N/A | B-161 已完成并删除其 plan |

### 5.2 与现有 plan 的重叠

| 冲突 plan | 重叠范围（文件 / 模块 / 接口） | 解决方式 |
|-----------|-------------------------------|---------|
| N/A | N/A | N/A |

> 已扫描 `docs/plans/` 与 `docs/superpowers/plans/`，未发现其他标记为 `Active` 或 `Interrupted` 的任务 plan；历史 superpowers plan 仅涉及已归档 legacy 路径。

## 6. 完成标准

- [ ] 功能行为符合 `docs/features/project-knowledge-coach.md` 的 B-162 业务规则
- [ ] 作答前响应不泄露评分依据，评估与计划数据严格按项目隔离
- [ ] B-162 相关单元、API、OpenAPI 和回归测试通过
- [ ] 相关文档已同步（见下方回流清单）
- [ ] BACKLOG B-162 状态已更新为 `done`

## 7. 回流清单

| 内容 | 目标文档 | 是否完成 |
|------|----------|----------|
| 评估会话、评分和覆盖聚合 | `docs/features/project-knowledge-coach.md`, `docs/design/api-spec.md` | [ ] |
| 评估与计划 schema | `docs/design/database-design.md` | [ ] |
| 学习计划版本、编辑与确认语义 | `docs/features/project-knowledge-coach.md`, `docs/design/api-spec.md` | [ ] |
| 测试方式与架构状态 | `docs/guides/testing.md`, `docs/design/architecture-overview.md` | [ ] |

## 8. 执行记录

- 2026-07-23：冲突扫描无重叠；旧 `/api/assessment/*`、已归档桌面评估模型和 B-163 Obsidian 发布不在本任务中修改。
- 2026-07-23：覆盖响应将携带 `knowledge_points / skills / recent_assessments`；学习计划响应将携带可解析 `sources`，满足 B-164 前端只读展示需要。
- 2026-07-23：陈旧分析允许只读查看既有评估结果，但阻止发起新评估和确认新计划。
- 2026-07-23：评估存储固定分析运行和知识点；公开题目默认隐藏评分依据，答案与结果单事务写入并支持同答案幂等重放。
- 2026-07-23：学习计划确认会归档旧确认版本；确认后仅任务进度可改，结构、排序和来源保持不可变。
- 2026-07-23：定向评估支持知识点/技能节点、活动会话恢复与显式重开；题面排除服务端评分依据，复制题面不会获得规则分。
- 2026-07-23：覆盖聚合固定当前分析运行，区分知识点未评估、技能无项目证据/未验证/部分验证/已验证，并为低置信结果显式加标。
- 2026-07-23：评估相关 36 项聚焦测试通过；后端与 Web 全量回归为 476 通过、2 个已知旧断言失败，分别待 B-164 更新“资料”导航 E2E、待 B-165 修正 Tauri sidecar 静态断言。
- 2026-07-23：学习计划按 `needs_work / developing / unassessed` 生成确定性草稿；模型只可润色任务文本，来源、关联、排序和时长保持服务端控制。
- 2026-07-23：`current` 同时返回最新草稿、当前确认版和历史版本；旧运行来源按发布时快照解析，草稿结构与确认版进度分别使用结构/进度哈希。
- 2026-07-23：来源指纹在评估与计划写入前复核；历史草稿不可再编辑或确认，草稿结构更新强制任务回到 `todo`，重复确认不受后续进度变化影响。
- 2026-07-23：B-162 聚焦回归 56 项通过；后端与 Web 全量回归为 490 通过、2 个既有静态断言失败，失败边界未变化。

## 9. 状态快照

- **最后更新**：2026-07-23
- **进度**：已完成 3 / 4 项
- **最新 commit**：`49a0295` — fix: 防止历史学习计划草稿重新激活
- **代码状态**：`feature/project-knowledge-coach-v2`；评估、覆盖聚合、学习计划与七个 Coach API 已提交，历史草稿复活边界已修正
- **下一步**：同步 OpenAPI、数据库、功能与测试文档，完成 B-162 回归并关闭任务
- **续任务须知**：状态阈值固定为 `<0.50 / 0.50–0.74 / ≥0.75`；新计划生成不得覆盖已确认计划
