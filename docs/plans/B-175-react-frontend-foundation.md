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

- [ ] 完成门禁迁移、B-175 计划、React 依赖与 OpenAPI 生成边界。
- [ ] 建立 `frontend-v3/` workspace、Hash Router、Query/UI 状态 Provider、主题 token 和测试基础。
- [ ] 实现 Tasks、Project、工作流、设置四个一级页面及桌面/窄屏应用壳；只接入真实能力并明确未实现边界。
- [ ] 实现 v3 JSON client、幂等写封装、SSE parser/reducer 与当前固定检查任务闭环。
- [ ] 完成 typecheck、单测、构建、浏览器响应式与文档门禁，回流阶段事实并关闭 B-175。

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

- [ ] 四个一级页面和设置五分区可达，320px–桌面布局无横向溢出，键盘可完成主要操作。
- [ ] 亮色、暗色、跟随系统 token 可用；危险动作、离线和错误状态不只依赖颜色。
- [ ] OpenAPI 生成类型、JSON client、幂等写与 SSE reducer 有测试，生产代码无演示数据回退。
- [ ] `typecheck`、Vitest、React Testing Library、Vite build、定向真实后端闭环和仓库/文档门禁通过。
- [ ] 现有 Vue、Tauri、Docker 和 `/api/v2` 未切换；B-174/B-176/B-177 未实现能力没有被描述为完成。
- [ ] BACKLOG 条目 B-175 已移除，完成事实已写入 `CHANGELOG.md` 与 Git 历史。

## 7. 回流清单

| 内容 | 目标文档 | 是否完成 |
|------|----------|----------|
| 用户授权与 P2 验收迁移 | `../adr/ADR-017-approved-p1-react-implementation-gate.md`、`../design/ui-prototype-brief-v3.md` | [ ] |
| React 目录、状态与 API 边界 | `../adr/ADR-014-react-typescript-frontend.md`、`../design/frontend-backend-contract-check.md` | [ ] |
| Tasks 与 SSE 真实行为 | `../features/agent-tasks-and-runs.md`、`../design/agent-runtime-and-tool-contract.md` | [ ] |
| 启动、测试和阶段边界 | `../guides/v3-upgrade.md`、`../guides/testing.md`、`../../CHANGELOG.md` | [ ] |

## 8. 执行记录

- 2026-08-02：用户明确表示“可以按照这份原型进行实现”。ADR-017 将该指令解释为 B-175 开工授权，并把原独立 P2 验收并入实现阶段；没有扩大为最终切换授权。
- 2026-08-02：Sites `list_sites` 再次发生相同传输错误；B-178 保留恢复信息并转为外部阻塞，不由 B-175 删除或伪关闭。
- 第一阶段真实闭环限定为 `health → projects → task + initial_message → run → SSE → messages/steps/artifacts`；Settings、Sources、Insights、任意工作流执行和导出不得使用假数据补齐。

## 9. 状态快照

- **最后更新**：2026-08-02 19:08:55 +08:00
- **进度**：已完成 0 / 5 项（见 § 3 勾选状态）
- **最新 commit**：`2ca8998` — 调整 P1 工作流与设置交互
- **代码状态**：`refactor/agent-v3`；工作区将在治理文件创建后产生未提交文档改动，尚未创建 `frontend-v3/`
- **下一步**：提交门禁迁移，再建立 `frontend-v3/` workspace 与 OpenAPI 生成链
- **续任务须知**：Vue/Tauri/Docker 入口保持不变；B-174 未完成能力必须显示真实不可用边界；B-178 Sites 发布恢复从 `list_sites` 开始
