# B-175 React 生产前端基础与 P1 Revision 3 实施

> 状态：Active
> 创建时间：2026-08-02
> 创建方：Codex
> 关联 BACKLOG：B-175
> 关联功能文档：`../features/agent-tasks-and-runs.md`
> 关联设计文档：`../design/ui-prototype-brief-v3.md`、`../adr/ADR-014-react-typescript-frontend.md`、`../adr/ADR-017-approved-p1-react-implementation-gate.md`

## 1. 目标

在独立 `frontend-v3/` 中建立 React/TypeScript 生产前端基础，并把已批准的 P1 Revision 3 信息架构实现为可测试的 Tasks、Project、工作流和设置页面。第一阶段只消费真实可用的 `/api/v3` 合同，后端缺失能力使用诚实空态或不可用说明，不复制演示数据，不修改现有 Vue 页面和正式运行入口。

## 2. 前置条件

- 用户已于 2026-08-02 明确批准按 P1 Revision 3 进入实现；门禁变更见 ADR-017。
- B-178 已因 Sites 外部传输阻塞转为 `Interrupted`，与本计划的仓库代码范围分区。
- B-174 尚未实施；桌面令牌、存储迁移、备份恢复和 Tauri 切换不属于本计划可宣称能力。
- v3 后端当前可提供 health、projects、tasks/messages、runs/steps/events、approvals、artifacts 和工作流定义 API；固定执行仍限 `project.inspect.v1` version 2。

## 3. 任务拆解

每完成一项，立即执行：① 勾选此处 ② `git commit` 保存进度 ③ 更新 § 9 状态快照 ④ 追加当日 DevLog。

- [x] 完成门禁迁移、B-175 计划、React 依赖与 OpenAPI 生成边界。
- [x] 建立 `frontend-v3/` workspace、Hash Router、Query/UI 状态 Provider、主题 token 和测试基础。
- [x] 实现 Tasks、Project、工作流、设置四个一级页面及桌面/窄屏应用壳；只接入真实能力并明确未实现边界。
- [x] 实现 v3 JSON client、幂等写封装、SSE parser/reducer 与当前固定检查任务闭环。
- [x] 完成 typecheck、单测、构建、真实后端浏览器闭环、响应式与文档门禁并回流阶段事实。
- [ ] 用户验收 React 高保真实现，并确认工作流编辑与通用两轮引导继续留在后续真实 API 阶段后关闭 B-175。

## 4. 影响范围

| 类型 | 路径 / 模块 | 变更方向 |
|------|------------|---------|
| 前端 | `frontend-v3/` | 新增 React/TypeScript/Vite workspace、页面、组件、API 与测试 |
| 根编排 | `package.json`、`package-lock.json` | 平行加入 `frontend-v3` workspace 与独立脚本；不切换正式入口 |
| 后端契约 | `scripts/`、`frontend-v3/src/api/generated/` | 导出 v3 OpenAPI 并生成 TypeScript 类型，不改变后端行为 |
| 仓库测试 | `tests/repository/` | 新增 v3 前端结构、生成类型和 Vue 保留契约 |
| 文档 | `docs/adr/`、`docs/design/`、`docs/features/`、`docs/guides/`、`CHANGELOG.md`、`docs/devlog/` | 同步门禁、当前实现和验证边界 |

## 5. 依赖与冲突

### 5.1 依赖的其他 plan

| plan 文件 | 依赖原因 |
|-----------|---------|
| N/A | B-172、B-173 后端基础已完成；B-174 不阻塞 Web 基础，但阻塞桌面与存储相关能力验收 |

### 5.2 与现有 plan 的重叠

| 冲突 plan | 重叠范围（文件 / 模块 / 接口） | 解决方式 |
|-----------|-------------------------------|---------|
| `B-178-guided-agent-conversation.md` | UI 文档、DevLog、Sites staging | 分区：B-178 只保留 Sites 外部发布恢复；B-175 修改仓库前端与当前规格，不改 Sites project 状态 |

## 6. 完成标准

- [x] 四个一级页面和设置五分区可达，320px–桌面布局无横向溢出，键盘可完成主要操作。
- [x] 亮色、暗色、跟随系统 token 可用；危险动作、离线和错误状态不只依赖颜色。
- [x] OpenAPI 生成类型、JSON client、幂等写与 SSE reducer 有测试，生产代码无演示数据回退。
- [x] `typecheck`、Vitest、React Testing Library、Vite build、定向真实后端闭环和仓库/文档门禁通过。
- [x] 现有 Vue、Tauri、Docker 和 `/api/v2` 未切换；B-174/B-176/B-177 未实现能力没有被描述为完成。
- [ ] BACKLOG 条目 B-175 已移除，完成事实已写入 `CHANGELOG.md` 与 Git 历史。

## 7. 回流清单

| 内容 | 目标文档 | 是否完成 |
|------|----------|----------|
| 用户授权与 P2 验收迁移 | `../adr/ADR-017-approved-p1-react-implementation-gate.md`、`../design/ui-prototype-brief-v3.md` | [x] |
| React 目录、状态与 API 边界 | `../adr/ADR-014-react-typescript-frontend.md`、`../design/frontend-backend-contract-check.md` | [x] |
| Tasks 与 SSE 真实行为 | `../features/agent-tasks-and-runs.md`、`../design/agent-runtime-and-tool-contract.md` | [x] |
| 启动、测试和阶段边界 | `../guides/v3-upgrade.md`、`../guides/testing.md`、`../../CHANGELOG.md` | [x] |

## 8. 执行记录

- 2026-08-02：用户明确表示“可以按照这份原型进行实现”。ADR-017 将该指令解释为 B-175 开工授权，并把原独立 P2 验收并入实现阶段；没有扩大为最终切换授权。
- 2026-08-02：Sites `list_sites` 再次发生相同传输错误；B-178 保留恢复信息并转为外部阻塞，不由 B-175 删除或伪关闭。
- 第一阶段真实闭环限定为 `health → projects → task + initial_message → run → SSE → messages/steps/artifacts`；Settings、Sources、Insights、任意工作流执行和导出不得使用假数据补齐。
- 2026-08-02：提交 `da4ffde` 建立平行 React 工作台；固定项目检查使用真实 v3 API，工作流编辑、资料、洞察、导出和桌面运维保持禁用。
- 2026-08-02：独立复审后修复同步错误状态叠加、Run 切换消息污染、历史产物归属、恢复停止出口、未决写幂等和失败 Run 重复重试；未用演示数据补齐缺失能力。
- 2026-08-02：最终验证为 React 42 项、真实后端 E2E 3 项、Vue 105 项、Python 全量 674 项及三项文档门禁全部通过。

## 9. 状态快照

- **最后更新**：2026-08-02 21:34:00 +08:00
- **进度**：已完成 5 / 6 项（见 § 3 勾选状态）
- **最新 commit**：`da4ffde` — 建立 React v3 Agent 工作台
- **代码状态**：`refactor/agent-v3`；`frontend-v3/`、真实 v3 闭环及工程门禁已提交，当前只剩计划/DevLog 状态回流
- **下一步**：由用户验收高保真实现；确认缺失能力继续在后续真实 API 阶段处理后，移除 B-175 并删除本 plan
- **续任务须知**：Vue/Tauri/Docker 入口保持不变；B-174 未完成能力必须显示真实不可用边界；B-178 Sites 发布恢复从 `list_sites` 开始
