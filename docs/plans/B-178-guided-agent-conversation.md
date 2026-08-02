# B-178 新手引导式首页与可重放 Agent 消息流

> 状态：Active
> 创建时间：2026-08-02
> 创建方：Codex
> 关联 BACKLOG：B-178
> 关联功能文档：`../features/agent-tasks-and-runs.md`
> 关联设计文档：`../design/ui-prototype-brief-v3.md`、`../design/api-spec.md`、`../design/agent-runtime-and-tool-contract.md`

## 1. 目标

替换未通过评审的 P1 横屏原型，建立面向首次使用者的引导式首页、单一当前状态、分段回答与风险分级确认；同时补齐 v3 任务首消息、运行输入快照、可重放 Agent 消息事件和固定工作流回答节点。完成后仍不创建 React 生产前端、不修改现有 Vue 页面。

## 2. 前置条件

- B-172 工程治理与 B-173 v3 后端 alpha 已完成，当前分支为 `refactor/agent-v3`。
- P1/P2 两轮原型门禁继续生效；本轮 P1 使用演示数据且不调用真实 API。
- B-174 至 B-177 的既定用途保持不变，本任务作为已批准序列后的紧急 B-178 插入执行。

## 3. 任务拆解

每完成一项，立即执行：① 勾选此处 ② `git commit` 保存进度 ③ 更新 § 9 状态快照 ④ 追加当日 DevLog。

- [x] 建立 B-178 BACKLOG、plan 和当日 DevLog 恢复点。
- [ ] 以测试驱动补齐任务首消息、运行输入快照、Agent 消息事件、步骤/审批事件和 `agent.respond` 执行闭环。
- [ ] 创建并验证 P1 Revision 2 引导式横屏交互原型，不覆盖旧附件。
- [ ] 新增 ADR-016，并回流 UI、任务、runtime、API、API changes、CHANGELOG 与 DevLog。
- [ ] 运行完整后端/集成/仓库/文档门禁，发布 Sites 生产版本并关闭 B-178。

## 4. 影响范围

| 类型 | 路径 / 模块 | 变更方向 |
|------|------------|---------|
| 后端 | `backend/api/v3/`、`backend/application/`、`backend/runtime/`、`backend/storage/v3/`、`backend/domain/` | 修改任务响应、运行输入和持久事件；新增安全回答节点 |
| 测试 | `tests/backend/`、`tests/integration/`、`tests/repository/` | 新增/更新 v3 契约、执行、恢复和 OpenAPI 覆盖 |
| 原型 | 线程可视化目录与 Sites 独立源码 | 新增 P1 Revision 2；不进入 `frontend/` 或 `frontend-v3/` |
| 文档 | `docs/adr/`、`docs/design/`、`docs/features/`、`CHANGELOG.md`、`docs/devlog/` | 新增 ADR 并回流当前 alpha 事实和 P1 门禁 |

## 5. 依赖与冲突

### 5.1 依赖的其他 plan

| plan 文件 | 依赖原因 |
|-----------|---------|
| N/A | B-172、B-173 已关闭，无活动 plan 依赖 |

### 5.2 与现有 plan 的重叠

| 冲突 plan | 重叠范围（文件 / 模块 / 接口） | 解决方式 |
|-----------|-------------------------------|---------|
| N/A | N/A | `docs/plans/` 当前仅有规则与模板 |

## 6. 完成标准

- [ ] 后端行为符合 `../features/agent-tasks-and-runs.md` 的任务、消息、事件和恢复规则。
- [ ] P1 Revision 2 覆盖发送、分段回答、暂停、审批、失败、离线、恢复、取消和完成，且在 1440px、736px、320px 与 560px 高度下可用。
- [ ] v3 定向测试、后端/集成/仓库全量测试和三项文档门禁通过。
- [ ] ADR、API、runtime、UI、CHANGELOG 与 DevLog 已同步；P1 明确保持“等待用户确认”。
- [ ] Sites 生产部署成功并返回 URL。
- [ ] BACKLOG 条目 B-178 已移除，完成事实已写入 `CHANGELOG.md` 与 Git 历史。

## 7. 回流清单

| 内容 | 目标文档 | 是否完成 |
|------|----------|----------|
| 新手首页、状态优先级、文案与风险确认 | `../design/ui-prototype-brief-v3.md` | [ ] |
| 任务首消息、输入快照、回答流与恢复语义 | `../features/agent-tasks-and-runs.md`、`../design/agent-runtime-and-tool-contract.md` | [ ] |
| HTTP/SSE/OpenAPI alpha.2 变化 | `../design/api-spec.md`、`../design/api-changes.md` | [ ] |
| 持久消息与实时事件职责 | `../adr/ADR-016-agent-message-stream.md` | [ ] |
| 实际完成事实和验证 | `../../CHANGELOG.md`、`../devlog/2026/08/2026-08-02.md` | [ ] |

## 8. 执行记录

- 2026-08-02：用户明确否决当前 P1 的对话流、信息密度和防呆表现，并批准后端合同与 P1 一并调整。
- 当前 Vue 与 `/api/v2` 不在本任务修改范围；通用自然语言澄清仍是 P1 演示合同，不冒充 alpha 后端已实现能力。

## 9. 状态快照

- **最后更新**：2026-08-02 15:44:41 +08:00
- **进度**：已完成 1 / 5 项（见 § 3 勾选状态）
- **最新 commit**：待创建 B-178 治理提交
- **代码状态**：`refactor/agent-v3`；仅有 B-178 BACKLOG、plan 与当日 DevLog 治理改动；尚未修改后端或生产前端
- **下一步**：以测试驱动补齐任务消息、运行输入、Agent 事件与 `agent.respond`
- **续任务须知**：P1/P2 门禁继续生效；旧 P1 附件只读保留；Sites 发布前先查询是否存在旧创建结果
