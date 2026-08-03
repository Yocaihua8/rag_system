# B-176 v3 真实业务联调

> 状态：Active
> 创建时间：2026-08-03
> 创建方：Codex
> 关联 BACKLOG：B-176
> 关联功能文档：`../features/agent-tasks-and-runs.md`
> 关联设计文档：`../design/api-spec.md`、`../design/database-design.md`、`../design/agent-runtime-and-tool-contract.md`

## 1. 目标

把已完成的 v3 任务/固定项目检查平行前端，推进为具备真实业务资料、项目洞察、设置、产物导出和受限工作流执行能力的端到端应用。本 plan 的第一段是 Sources：项目根目录中已登记的资料必须可由后端安全发现、持久化并在 React 项目页展示；不能读取未绑定路径、不能把文件正文或绝对路径泄露到列表响应。

本 plan 不切换正式入口，不删除 Vue，不修改 Tauri/Docker 指向，也不把 v2 API 或数据写入 v3。

## 2. 前置条件

- 已阅读 `AGENTS.md`、`docs/requirements/agent-product-v3.md`、ADR-012 至 ADR-018 和 `docs/guides/v3-upgrade.md`。
- B-173（v3 后端 alpha）、B-174（桌面与存储基础）、B-175（React 平行前端）和 B-178（消息流与 P1）均已完成；当前无其他 Active/Interrupted plan。
- v3 Sources 仅在用户已绑定项目根内工作；文件读取、索引和后续写操作继续遵守 `agent-runtime-and-tool-contract.md` 的白名单和确认边界。

## 3. 任务拆解

- [x] 冻结 Sources 第一段的 API、路径允许范围、响应脱敏和数据库迁移边界；补充设计契约。
- [x] 实现 Sources 的后端发现/读取索引、查询 API、持久化和幂等/失败行为，补后端与集成测试。
- [x] 通过生成的 OpenAPI 类型把 Sources 列表和受控导入接入 `frontend-v3/` 项目页，补组件测试与真实浏览器联调。
- [x] 在 Sources 闭环通过后，按同一边界实现 Project Insights 的资料快照概览：只基于 v3 Documents 元数据动态计算，不读正文、不写入结论，补真实后端合同、生成类型、前端状态和测试。
- [x] 实现 v3 模型 Profile 元数据设置：使用独立表、受控 Key 引用和幂等写请求完成列表、新增、编辑、默认选择和确认删除；不接入模型调用或 Key 录入。
- [x] 实现 Artifact 受控导出：预览不写入，明确确认时固定版本/hash 并只写入受管 v3 目录；不复用已完成 Run 的审批。
- [ ] 独立评估并分段实现持久分析、其余设置和工作流执行；每一段先补真实后端合同再开放 UI。
- [ ] 在所有 B-176 分段完成后，执行完整 Web/desktop 联调矩阵；同步功能、设计、CHANGELOG、DevLog，移除 BACKLOG 条目并删除本 plan。

## 4. 影响范围

| 类型 | 路径 / 模块 | 变更方向 |
|------|------------|---------|
| 代码 | `backend/api/v3/`、`backend/storage/v3/`、v3 Alembic migrations | 增加 Sources 能力及后续真实业务 API |
| 代码 | `frontend-v3/src/`、`frontend-v3/openapi/` | 接入生成类型的真实业务 UI |
| 测试 | `tests/backend/`、`tests/integration/`、`frontend-v3/src/**/*.test.tsx` | 新增分段回归与端到端验证 |
| 文档 | `docs/features/`、`docs/design/`、`docs/guides/`、`CHANGELOG.md`、`docs/devlog/` | 只回流已实现且验证的事实 |

## 5. 依赖与冲突

### 5.1 依赖的其他 plan

| plan 文件 | 依赖原因 |
|-----------|---------|
| N/A | 当前没有未完成前置 plan。 |

### 5.2 与现有 plan 的重叠

| 冲突 plan | 重叠范围（文件 / 模块 / 接口） | 解决方式 |
|-----------|-------------------------------|---------|
| N/A | 当前 `docs/plans/` 没有 Active 或 Interrupted plan。 | N/A |

## 6. 完成标准

- [ ] 每个开放的 v3 业务能力都有真实后端合同、持久化边界、生成类型、前端状态和覆盖该能力的测试。
- [ ] Sources、洞察、设置、导出和工作流执行不会越出已绑定项目、v3 数据代际、只读/确认和令牌边界。
- [ ] 真实本地后端的 Playwright Web 联调覆盖任务、审批、工作流、产物及新开放业务能力；Desktop 切换门禁另行满足。
- [ ] 不使用演示数据、v2 回退或前端业务状态机伪造未实现能力。
- [ ] 必要文档、CHANGELOG 和当日 DevLog 已回流；B-176 已从 BACKLOG 移除且本 plan 已删除。

## 7. 回流清单

| 内容 | 目标文档 | 是否完成 |
|------|----------|----------|
| Sources API、授权范围、响应脱敏和错误语义 | `docs/design/v3-sources-contract.md` | [x] |
| v3 Sources/Document 数据模型与迁移 | `docs/design/v3-sources-contract.md` | [x] |
| 业务能力可达性和限制 | `docs/features/project-sources.md`、`docs/features/agent-tasks-and-runs.md` | [x] |
| Project Insights 资料快照概览合同和前端状态 | `docs/design/v3-project-insights-contract.md`、`docs/features/project-insights.md` | [x] |
| v3 模型 Profile 设置合同和前端状态 | `docs/design/v3-model-profiles-contract.md`、`docs/features/model-profile-settings-v3.md` | [x] |
| Artifact 受控导出合同和前端状态 | `docs/design/v3-artifact-export-contract.md`、`docs/features/artifact-export-v3.md` | [x] |
| 开发过程、验证和下一步 | `docs/devlog/2026/08/2026-08-03.md` | [ ] |
| 用户可见完成事实 | `CHANGELOG.md` | [ ] |

## 8. 执行记录

- 2026-08-03：用户明确要求进入开发阶段。当前无活动 plan；根据 v3 迁移顺序创建 B-176。第一段选 Sources，因为 `sources/documents/document_chunks` 已在独立 v3 schema 中预留，但 alpha API 只暴露 projects，React 项目页明确保持资料不可用状态。
- 2026-08-03：冻结第一段的安全合同：只读扫描已绑定根、响应不泄露正文或绝对路径、v3 Store 幂等写入；现有 Schema 已满足本段，无需 Alembic migration。
- 2026-08-03：完成 Sources 后端与平行 React 闭环。定向 Sources、v3 API contract 和 Store 测试 41 项通过；React typecheck、44 项单测、OpenAPI 类型生成与 production build 通过。Playwright 真实浏览器联调仍在本 plan 的最终矩阵中，尚未作为本段完成证据。
- 2026-08-03：启动 Project Insights 子阶段，先冻结不读正文、只依据 v3 Documents 元数据计算的资料快照概览。持久化分析、LLM、知识点和评估不在本段范围。
- 2026-08-03：完成 Project Insights 资料快照概览：新增只读 overview API 和生成类型，React 项目页展示扫描前资料缺口与扫描后的文件数、大小、类型/清单；定向 Python 42 项、React typecheck、45 项单测、OpenAPI 生成和 production build 通过。正式浏览器 E2E 仍留在最终联调矩阵。
- 2026-08-03：完成 v3 模型 Profile 元数据设置：Profile 只保存固定白名单 Key 引用，React 可对真实 v3 Profile 新增、编辑、设默认和确认删除；不接入 Key 录入、模型调用或 v2 数据。定向 Python 43 项、React typecheck、46 项单测、OpenAPI 生成和 production build 通过。
- 2026-08-03：冻结 Artifact 受控导出合同。现有 Approval 资源绑定运行中 Step，不能复用已完成 Artifact 伪造审批；导出改用独立的预览/确认两阶段，确认请求固定 Artifact hash/version 并只写入受管 v3 目录，后续实现前不得开放任意目标路径。
- 2026-08-03：完成 Artifact 受控导出。后端提供 ready Artifact 的只读预览和带 `Idempotency-Key` 的确认接口，文件名由服务端固定并只写入 `<KI_DATA_ROOT>/artifacts/exports/`；React 详细过程先显示快照与不可自动撤销提示，再发送确认。定向 Python 44 项、React typecheck、47 项单测、OpenAPI 生成、production build 与三项文档门禁通过。真实浏览器 E2E 仍留在最终联调矩阵。
- 2026-08-03：补齐导出确认中断恢复。若文件写入后数据库状态提交前进程中断，后续确认仅在既有受管文件与当前 ready 快照完全一致时继续提交；不同内容或不可读目标仍拒绝。定向导出/API 契约 14 项与三项文档门禁通过。

## 9. 状态快照

- **最后更新**：2026-08-03 14:12 CST
- **进度**：已完成 6 / 8 项（见 § 3 勾选状态）
- **最新 commit**：`f9ff591` — fix: 恢复中断的 v3 导出确认
- **代码状态**：`refactor/agent-v3`；Sources、资料快照概览、模型 Profile 设置和受控导出的后端、React、测试和文档已提交；正式入口未切换。
- **下一步**：独立冻结并实现持久洞察分析、其余设置或工作流执行中的一个最小真实切片；不把它们混入当前导出切片。
- **续任务须知**：v3 `sources/documents/document_chunks` 已在 `0001_v3_initial` 中建表，但当前 alpha HTTP 仅使用 `projects`；不得用 v2 导入接口或数据根填充 React v3 页面。
