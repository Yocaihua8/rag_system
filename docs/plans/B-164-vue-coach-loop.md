# B-164 Vue 项目知识教练闭环

> ⚠️ 创建此文件前，必须已完成以下操作（AI 自检）：
> - [x] `docs/BACKLOG.md` 中 B-164 状态为 `doing`
> - [x] B-164 说明列已填入本文件路径
> - [x] 关联功能文档和设计文档已按实际范围填写

> 状态：Active
> 创建时间：2026-07-23
> 创建方：Codex
> 关联 BACKLOG：B-164
> 关联功能文档：docs/features/frontend-engineering.md, docs/features/project-knowledge-coach.md
> 关联设计文档：docs/design/ui-wireframes.md, docs/design/architecture-overview.md, docs/design/api-spec.md

## 1. 目标

在现有 Codex 风格 Vue 外壳中完成 Knowledge Island 2.0 主闭环：默认“教练”继续复用聊天、会话、流式回答与依据抽屉；新增学习地图、来源查看、定向评估覆盖层、可编辑学习计划，以及 Obsidian 配对状态、预览确认发布和冲突提示。保留 1.x 导入与旧评估 API 兼容，不恢复管理后台式独立评估页。

## 2. 前置条件

- B-161～B-163 已完成，Coach 与 Obsidian 应用侧 API 可供 Vue 调用
- B-159 Codex 视觉与术语是受保护基线；B-157 全局资料库保持 `wontfix`
- 前端继续使用现有 `App.vue + app-state.js` 状态编排，不在本任务引入 Router、Pinia或大型依赖

## 3. 任务拆解

- [x] 新增 Coach/Obsidian API helper 与项目级状态骨架，重排主导航为教练、学习地图、学习计划、资料、设置
- [x] 实现学习地图、统一来源抽屉和按知识点/技能发起的评估覆盖层及组件测试
- [x] 实现学习计划编辑/排序/确认、Obsidian 发布预览确认，以及资料弹窗和设置连接管理组件及测试
- [x] 完成 `App.vue` 闭环接线、样式与 E2E 契约更新，回流正式文档并执行前端/后端回归

## 4. 影响范围

| 类型 | 路径 / 模块 | 变更方向 |
|------|------------|---------|
| 代码 | `frontend/src/api/coach.js`, `frontend/src/api/obsidian.js`, `frontend/src/state/app-state.js` | 新增 API helper 与 Coach/Obsidian 状态 |
| 代码 | `frontend/src/components/AppShell.vue`, `frontend/src/components/WorkspaceSidebar.vue`, `frontend/src/views/WorkbenchView.vue` | 重排导航并保留教练聊天主线 |
| 代码 | `frontend/src/views/LearningMapView.vue`, `frontend/src/components/CoachSourceDrawer.vue`, `frontend/src/components/CoachAssessmentOverlay.vue` | 新增学习地图、来源和评估覆盖层 |
| 代码 | `frontend/src/views/LearningPlanView.vue`, `frontend/src/components/ObsidianPublicationDialog.vue` | 新增计划和受控发布交互 |
| 代码 | `frontend/src/components/LibraryModal.vue`, `frontend/src/views/SettingsView.vue`, `frontend/src/App.vue`, `frontend/src/styles.css` | 接入真实 Obsidian 状态和完整页面编排 |
| 测试 | `frontend/src/**/*.test.js`, `tests/test_webapp/test_frontend_vue_app.py`, `tests/test_webapp/test_e2e_ui.py`, `tests/e2e/web-mvp-smoke.spec.js` | 更新组件、静态契约和浏览器 smoke |
| 文档 | `docs/features/frontend-engineering.md`, `docs/features/project-knowledge-coach.md`, `docs/design/ui-wireframes.md`, `docs/design/architecture-overview.md`, `docs/guides/testing.md` | 回流 B-164 当前实现事实 |

## 5. 依赖与冲突

### 5.1 依赖的其他 plan

| plan 文件 | 依赖原因 |
|-----------|---------|
| N/A | B-163 已完成并删除其 plan |

### 5.2 与现有 plan 的重叠

| 冲突 plan | 重叠范围（文件 / 模块 / 接口） | 解决方式 |
|-----------|-------------------------------|---------|
| N/A | N/A | N/A |

> 已扫描 `docs/plans/` 与 `docs/superpowers/plans/`，未发现其他标记为 `Active` 或 `Interrupted` 的任务 plan；`docs/plans/README.md` 的 Active 是文档状态，不是执行 plan。

## 6. 完成标准

- [x] 主导航、地图、计划、评估覆盖层和资料/设置行为符合 2.0 产品契约
- [x] 评估与技能状态明确限定为当前项目，不泄露作答前评分依据
- [x] 学习计划编辑、排序、确认与 Obsidian 预览确认不在前端复制业务规则
- [x] 前端单元测试、生产构建和相关 Web 回归通过
- [x] 相关文档已同步（见下方回流清单）
- [ ] BACKLOG B-164 状态已更新为 `done`

## 7. 回流清单

| 内容 | 目标文档 | 是否完成 |
|------|----------|----------|
| 2.0 一级导航与教练聊天复用 | `docs/features/frontend-engineering.md`, `docs/design/ui-wireframes.md` | [x] |
| 学习地图、来源与评估覆盖层 | `docs/features/project-knowledge-coach.md`, `docs/design/ui-wireframes.md` | [x] |
| 学习计划和 Obsidian 交互 | `docs/features/frontend-engineering.md`, `docs/design/architecture-overview.md` | [x] |
| 前端测试与验收命令 | `docs/guides/testing.md` | [x] |

## 8. 执行记录

- 2026-07-23：保持 `App.vue + app-state.js` 既有编排，避免在产品闭环任务中引入 Router/Pinia 或无关状态重构。
- 2026-07-23：Vue 只调用应用侧 Obsidian 配对、连接、预览和确认接口；插件令牌、事件同步、待执行队列和结果回传不进入浏览器状态。
- 2026-07-23：当前九个 Obsidian API 不提供应用侧发布终态查询；本任务处理预览/确认阶段的 `409` 冲突并明确 queued 等待插件，不伪造插件执行成功。
- 2026-07-23：Coach 与应用侧 Obsidian API helper、项目级状态骨架和五入口导航已落地；插件 token/sync/pending/result 未暴露到 Vue。API、状态、导航与教练工作台 21 项单测及生产构建通过。
- 2026-07-23：学习地图、统一来源抽屉和定向评估覆盖层已落地；完成态会话不重复展示最后一题，作答前不展示评分依据。相关 9 项组件测试及生产构建通过。
- 2026-07-23：学习计划草稿编辑/排序/确认、确认版进度更新、受控发布预览，以及资料弹窗和设置页的 Obsidian 连接管理组件已落地；界面不回显插件令牌，queued 不伪装为已写入。相关 24 项组件测试及生产构建通过。
- 2026-07-23：完成 `App.vue` 闭环接线、项目切换异步结果隔离、静态/E2E 契约和正式文档回流；Vue 92 项单测、生产构建、121 项 Coach/Obsidian/Web 聚焦回归、94 项静态 UI 契约、26 项文档契约和文档一致性检查通过。浏览器 smoke 用例本身通过，但 Windows 下 Playwright webServer 退出清理会挂起，纳入 B-165 发布验收修复，不在 B-164 中伪报整条命令通过。

## 9. 状态快照

- **最后更新**：2026-07-23
- **进度**：已完成 4 / 4 项
- **最新 commit**：`5592c57` — feat: 接通 Vue 项目知识教练闭环
- **代码状态**：`feature/project-knowledge-coach-v2`；B-164 代码、测试契约和文档回流已完成，待关闭 BACKLOG 与删除 plan
- **下一步**：关闭 B-164，并启动 B-165 修复 E2E 退出清理和执行 `v2.0.0` 发布验收
- **续任务须知**：旧 `/api/assessment/*` 与 `AssessmentView.vue` 保留兼容；新前端评估只使用 Coach API
