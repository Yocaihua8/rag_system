# B-141T Vue 评估页最小闭环迁移计划

> 状态：Active
> 创建时间：2026-05-28
> 创建方：Codex
> 关联 BACKLOG：B-141
> 关联功能文档：docs/features/frontend-engineering.md
> 关联设计文档：docs/design/architecture-overview.md（接口契约沿用 docs/design/api-spec.md，不新增或修改 API）

## 1. 目标

在 Vue 评估页迁移掌握评估最小闭环，复用既有 `/api/assessment/start` 和 `/api/assessment/answer` 契约，让用户在选中项目空间后可以开始评估、查看当前题目、提交回答、进入下一题，并查看结果概览、答题记录和待复测列表。

本片不修改后端接口、SQLite schema、出题/评分规则、回答反馈或 Workbench SSE/会话。

## 2. 前置条件

- B-141B 已提供 Vue 评估视图壳和共享状态字段。
- `docs/design/api-spec.md` 已定义 `/api/assessment/start` 与 `/api/assessment/answer` 契约。
- legacy 静态前端已有评估页流程，可作为 Vue 行为对齐参考。

## 3. 任务拆解

每完成一项，立即执行：① 勾选此处 ② `git commit` 保存进度 ③ 更新 § 9 状态快照。

- [x] 创建 B-141T plan，并将 BACKLOG 说明列追加本 plan 路径。
- [x] 增加 Vue 源码契约红灯测试，覆盖评估 API helper、评估页 UI 和 App 状态流。
- [x] 实现 `frontend/src/api/assessment.js`、`AssessmentView.vue`、`App.vue` 和共享状态的评估闭环串联。
- [x] 运行聚焦 Vue 测试和 Vite build，确认本片前端实现通过。
- [x] 同步功能文档、架构说明、测试指南、CHANGELOG 和 devlog。
- [x] 完成 Web MVP 全量、legacy 回归与浏览器烟测，并回写 plan 状态快照。

## 4. 影响范围

| 类型 | 路径 / 模块 | 变更方向 |
|------|------------|---------|
| 代码 | `frontend/src/api/assessment.js` | 新增：评估 API helper |
| 代码 | `frontend/src/components/AppShell.vue` | 修改：更新 Vue 迁移顶栏状态文案，避免仍宣称完整业务流程由 legacy 承载 |
| 代码 | `frontend/src/views/AssessmentView.vue` | 修改：增加评估题目、作答、进度、结果和待复测列表 |
| 代码 | `frontend/src/App.vue` | 修改：增加评估开始、提交、下一题和状态清理流 |
| 代码 | `frontend/src/state/app-state.js` | 修改：补充评估加载/提交/错误/状态字段 |
| 测试 | `tests/test_webapp/test_frontend_vue_app.py` | 修改：增加 Vue 评估源码契约和顶栏迁移状态测试 |
| 文档 | `docs/features/frontend-engineering.md` | 修改：同步 B-141T 用户可见行为和非目标 |
| 文档 | `docs/design/architecture-overview.md` | 修改：同步 Vue 评估页迁移状态 |
| 文档 | `docs/guides/testing.md` | 修改：补充 Vue 评估页验证要求 |
| 文档 | `CHANGELOG.md` | 修改：追加未发布变更 |
| 文档 | `docs/devlog/2026-05-28.md` | 修改：记录本片执行与验证 |
| 文档 | `docs/BACKLOG.md` | 修改：追加本 plan 路径 |

## 5. 依赖与冲突

### 5.1 依赖的其他 plan

| plan 文件 | 依赖原因 |
|-----------|---------|
| `docs/plans/B-141-vue-api-layout.md` | 需要 Vue 基础视图壳和共享状态模型 |
| `docs/plans/B-141-vue-project-space.md` | 评估页需要当前项目空间选择状态 |

### 5.2 与现有 plan 的重叠

创建本 plan 时扫描到 B-141A 至 B-141S 计划文件仍保留为 `Active`，但 § 9 均显示对应任务已完成；按项目规则视为已完成但未删除的迁移记录。本片只扩展评估页影响范围，不清理既有 plan 文件。

| 冲突 plan | 重叠范围（文件 / 模块 / 接口） | 解决方式 |
|-----------|-------------------------------|---------|
| `docs/plans/B-141-vue-api-layout.md` | `frontend/src/state/app-state.js`、`frontend/src/App.vue` 和基础评估视图壳 | 分区：B-141T 只扩展评估页闭环，不改基础布局 |
| `docs/plans/B-141-vue-project-space.md` | `frontend/src/App.vue` 当前项目状态 | 分区：B-141T 只读取当前项目 ID，不改项目空间选择/创建行为 |

## 6. 完成标准

- [x] 功能行为符合 `docs/features/frontend-engineering.md` 的 B-141T 业务规则。
- [x] Vue 评估页可在已选择项目空间时开始评估并显示当前题目。
- [x] Vue 评估页可提交当前题回答，展示评分状态、得分、匹配点、缺失点和来源。
- [x] Vue 评估页可进入下一题或完成本轮，并展示答题记录和待复测列表。
- [x] 评估 helper 只调用既有 `/api/assessment/start` 与 `/api/assessment/answer` 契约，不新增接口、不修改数据库 schema。
- [x] 测试通过（参照 `docs/guides/testing.md` 最低要求）。
- [x] 相关文档已同步（见下方"回流清单"）。
- [x] B-141 保持 `doing`；本片完成后不删除 B-141 总任务。

## 7. 回流清单

| 内容 | 目标文档 | 是否完成 |
|------|----------|----------|
| B-141T 用户可见行为、非目标和验收标准 | `docs/features/frontend-engineering.md` | [x] |
| Vue 评估页 helper、状态和组件职责 | `docs/design/architecture-overview.md` | [x] |
| Vue 评估页测试要求和回归检查 | `docs/guides/testing.md` | [x] |
| 未发布变更记录 | `CHANGELOG.md` | [x] |
| 当日执行记录和验证结果 | `docs/devlog/2026-05-28.md` | [x] |
| B-141 关联 plan 路径和状态 | `docs/BACKLOG.md` | [x] |

## 8. 执行记录

- 2026-05-28：创建 B-141T plan；冲突扫描显示 B-141A 至 B-141S 为已完成但未删除的迁移记录，本片按评估页最小闭环分区继续。
- 2026-05-28：新增 Vue 源码契约红灯测试；聚焦运行 `tests/test_webapp/test_frontend_vue_app.py` 得到 4 failed / 48 passed，失败点为缺少评估 helper、评估页 UI、App 状态流和 B-141T 文案。
- 2026-05-28：实现 Vue 评估 API helper、评估页最小闭环 UI 和 App 状态流；聚焦测试 `tests/test_webapp/test_frontend_vue_app.py` 为 52 passed。
- 2026-05-28：完成前端验证：Vue 源码测试 52 passed，`npm run build` 成功；构建产物未进入待提交范围。
- 2026-05-28：同步功能文档、架构说明、测试指南、CHANGELOG 和 devlog；B-141T 明确不迁移评估题库管理、历史评估列表、回答反馈、知识点画像、Workbench SSE/会话或数据库 schema。
- 2026-05-28：浏览器烟测发现 `AppShell` 顶栏仍显示 B-141B legacy 占位文案；补充源码契约断言并更新为当前 Vue 薄片迁移状态说明，聚焦 Vue 测试恢复为 52 passed。
- 2026-05-28：完成最终验证：Web MVP 全量 323 passed，legacy 业务层回归 179 passed，`npm run build` 成功；浏览器烟测用临时导入项目完成开始评估、提交回答、结果概览、答题记录和待复测列表验证，控制台 error 数 0，临时项目和本地服务已清理。

## 9. 状态快照

- **最后更新**：2026-05-28 01:00
- **进度**：已完成 6 / 6 项（见 § 3 勾选状态）
- **最新 commit**：`待提交` — docs: 更新 B-141T 验证快照
- **代码状态**：`fix/url-virtual-source-preserve`；工作区存在多项用户/历史未提交改动，本片仅允许暂存 B-141T 相关文件
- **下一步**：B-141 后续可继续迁移 Workbench SSE/会话、回答反馈、Agent 工具或检索调试
- **续任务须知**：不修改后端 `/api/assessment*` 契约、不修改数据库 schema；不要清理既有 B-141 历史 plan 文件
