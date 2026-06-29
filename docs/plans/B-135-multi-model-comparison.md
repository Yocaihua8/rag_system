# B-135 多模型并排对比 Plan

> 状态：Active
> 创建时间：2026-06-29
> 创建方：Codex
> 关联 BACKLOG：B-135
> 关联功能文档：docs/features/multi-model-comparison.md
> 关联设计文档：docs/design/api-spec.md

## 1. 目标

执行 B-135：在现有 Model Profile、检索和回答链路基础上，新增同一问题对 2 个不同 Profile 的并排对比能力，并在 Vue 工作台提供最小可用入口。

## 2. 前置条件

- 已阅读 `AGENTS.md`
- 已阅读 `docs/design/api-spec.md`
- 已检查 `webapp/answer_api.py`、`webapp/routes/answers.py`、`webapp/model_profiles.py`、`webapp/llm.py`
- 已检查 Vue 工作台、回答 API helper、全局状态和现有前端静态测试

## 3. 任务拆解

每完成一项，立即执行：① 勾选此处 ② `git commit` 保存进度 ③ 更新 § 9 状态快照。
未完成项不得删除。

- [x] 任务 1：写 B-135 红灯测试，覆盖 `/api/answer/compare` 选择 2 个 Profile、复用检索上下文、错误校验和 Vue 工作台 wiring
- [x] 任务 2：实现后端 compare API，新增 Profile 客户端构造、结果结构和路由分发，不改变 `/api/answer` 与 SSE 行为
- [ ] 任务 3：实现 Vue 工作台最小并排对比入口，包含 Profile 选择、提交状态、错误状态和双列结果展示
- [ ] 任务 4：同步 `docs/features/multi-model-comparison.md` 与 `docs/design/api-spec.md`
- [ ] 任务 5：运行 B-135 验证清单，关闭 BACKLOG 状态并删除本 plan

## 4. 影响范围

| 类型 | 路径 / 模块 | 变更方向 |
|------|------------|---------|
| 代码 | `webapp/answer_api.py` | 新增 compare 响应构造 |
| 代码 | `webapp/routes/answers.py` | 新增 `/api/answer/compare` 分发 |
| 代码 | `frontend/src/api/answer.js` | 新增 compare API helper |
| 代码 | `frontend/src/state/app-state.js` | 新增 compare 相关状态 |
| 代码 | `frontend/src/App.vue` | 接入 compare 调用和状态流转 |
| 代码 | `frontend/src/views/WorkbenchView.vue` | 传递 Profile 和 compare 事件 |
| 代码 | `frontend/src/components/ModelComparisonPanel.vue` | 新增并排对比 UI |
| 测试 | `tests/test_webapp/test_api.py` | 新增 compare API 行为测试 |
| 测试 | `tests/test_webapp/test_frontend_vue_app.py` | 新增 Vue wiring 静态测试 |
| 文档 | `docs/features/multi-model-comparison.md` | 新增/完善功能说明 |
| 文档 | `docs/design/api-spec.md` | 新增 compare 接口契约 |
| 文档 | `docs/BACKLOG.md` | B-135 状态流转与 plan 路径 |

## 5. 依赖与冲突

### 5.1 依赖的其他 plan

| plan 文件 | 依赖原因 |
|-----------|---------|
| N/A | B-135 可在当前 B-134 基线独立实现；B-136 反向依赖 B-135 的新端点 |

### 5.2 与现有 plan 的重叠

| 冲突 plan | 重叠范围（文件 / 模块 / 接口） | 解决方式 |
|-----------|-------------------------------|---------|
| `docs/plans/B-145-tauri-windows-packaging.md` | 仅 `docs/BACKLOG.md` 元数据同文件重叠；B-145 代码范围是 `src-tauri/`、sidecar 脚本和打包文档 | 分区：本 plan 不碰 Tauri、sidecar、打包脚本 |
| `docs/superpowers/plans/2026-05-11-project-knowledge-base-ui-skeleton.md` | 旧 PySide6 UI skeleton 计划，不涉及 Web MVP compare API 或 Vue 工作台 | N/A |
| `docs/superpowers/plans/2026-05-11-project-knowledge-points.md` | 旧 `src/` knowledge point 计划，不涉及 Web MVP answer API | N/A |
| `docs/superpowers/plans/2026-05-16-knowledge-island-core-models.md` | 旧 `src/` core model 计划，不涉及 Web MVP answer API | N/A |

## 6. 完成标准

- [ ] 功能行为符合 `docs/features/multi-model-comparison.md` 的业务规则
- [ ] B-135 新增测试通过
- [ ] `tests/test_webapp` 相关回归通过
- [ ] 相关文档已同步（见下方"回流清单"）
- [ ] BACKLOG 条目 `B-135` 状态已更新为 `done`

## 7. 回流清单

| 内容 | 目标文档 | 是否完成 |
|------|----------|----------|
| 多模型并排对比功能边界和 UI 行为 | `docs/features/multi-model-comparison.md` | [ ] |
| `/api/answer/compare` 请求、响应和错误契约 | `docs/design/api-spec.md` | [ ] |

## 8. 执行记录

- 2026-06-29：创建 plan。当前隔离 worktree 基于 B-134 完成基线；B-145 为打包验证阻塞，按文件边界分区处理。
- 2026-06-29：任务 1 红灯测试已运行：`E:\Code\knowledage_island\.venv\Scripts\python.exe -m pytest tests\test_webapp\test_api.py -q -k "answer_compare"` 结果 2 failed，失败原因为 `/api/answer/compare` 当前返回 404；`E:\Code\knowledage_island\.venv\Scripts\python.exe -m pytest tests\test_webapp\test_frontend_vue_app.py -q -k "multi_model_comparison"` 结果 2 failed，失败原因为缺少 `compareAnswers` helper 和 `ModelComparisonPanel.vue`。
- 2026-06-29：任务 2 后端实现新增 `/api/answer/compare`，复用检索上下文但不写聊天消息；验证命令：`E:\Code\knowledage_island\.venv\Scripts\python.exe -m pytest tests\test_webapp\test_api.py -q -k "answer_compare"` 为 2 passed；`E:\Code\knowledage_island\.venv\Scripts\python.exe -m pytest tests\test_webapp\test_api.py -q -k "answer_compare or default_model_profile or answer_stream"` 为 4 passed。

## 9. 状态快照

- **最后更新**：2026-06-29
- **进度**：已完成 1 / 5 项（见 § 3 勾选状态）
- **最新 commit**：`2d55120` — test: 增加多模型对比红灯测试
- **代码状态**：`fix/B-135-b136-model-compare-openapi` 分支；红灯测试已提交，目标失败原因符合预期
- **下一步**：任务 2：实现后端 compare API
- **续任务须知**：B-136 应在 B-135 完成后执行，以便 OpenAPI schema 覆盖新增 `/api/answer/compare`。
