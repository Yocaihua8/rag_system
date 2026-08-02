# B-172 v3 通用项目 Agent 产品与工程治理基线

> 状态：Active
> 创建时间：2026-08-02
> 创建方：Codex
> 关联 BACKLOG：B-172
> 关联功能文档：`../features/agent-tasks-and-runs.md`
> 关联设计文档：`../design/ui-prototype-brief-v3.md`、`../design/v3-document-migration.md`

## 1. 目标

把已确认的 Knowledge Island v3 通用项目 Agent 方向转化为可执行的产品、架构、原型和文档治理契约，为后续 B-173 后端重构提供稳定边界，同时保持现有 Vue 前端不变。

## 2. 前置条件

- 已读取 `AGENTS.md`、`docs/README.md`、`docs/BACKLOG.md`、`docs/plans/README.md` 和当前 Git 状态。
- 已扫描 `docs/plans/`，创建时不存在 Active/Interrupted plan，工作区干净。
- 用户已明确授权新增 `docs/devlog/`，该授权覆盖仓库旧有的 DevLog 禁止规则。
- UI 必须依次通过 P1、P2；P2 未明确批准前不创建 React 生产前端、不修改现有 Vue 页面。

## 3. 任务拆解

- [x] 冻结 v3 产品范围、任务/运行能力和两轮 UI 原型验收契约。
- [x] 新增并登记 v3 产品权限、持久化 DAG、React 前端和 v3 数据/API ADR。
- [x] 建立 DevLog、文档吸收矩阵并更新仓库文档治理规则和检查器。
- [ ] 运行文档与仓库测试，回流 CHANGELOG，移除 B-172 并删除本 plan。

## 4. 影响范围

| 类型 | 路径 / 模块 | 变更方向 |
|------|-------------|----------|
| 代码 | `scripts/check_docs_consistency.py`、文档仓库测试 | 允许并校验按年月组织的 DevLog |
| 文档 | `docs/requirements/`、`docs/design/`、`docs/features/` | 新增 v3 目标规格和原型契约 |
| 文档 | `docs/adr/` | 新增 ADR-012 至 ADR-015 |
| 文档 | `docs/devlog/`、根规则和索引 | 新增并同步治理边界 |
| 前端 | `frontend/` | 不修改，仅作为当前 v2 事实源 |

## 5. 依赖与冲突

### 5.1 依赖的其他 plan

| plan 文件 | 依赖原因 |
|-----------|---------|
| N/A | 当前没有其他活动 plan。 |

### 5.2 与现有 plan 的重叠

| 冲突 plan | 重叠范围 | 解决方式 |
|-----------|----------|----------|
| N/A | N/A | 创建时已扫描，无冲突。 |

## 6. 完成标准

- [ ] v3 目标规格与原型门禁完整、无未决实现选择。
- [ ] 四份 ADR 已登记，旧 ADR 的取代关系清楚。
- [ ] DevLog 规则、模板、当日日志和检查器一致。
- [ ] 文档门禁与相关仓库测试通过。
- [ ] BACKLOG 中 B-172 已移除，完成事实已写入 CHANGELOG 与 Git 历史。

## 7. 回流清单

| 内容 | 目标文档 | 是否完成 |
|------|----------|----------|
| v3 产品范围与非目标 | `../requirements/agent-product-v3.md` | [ ] |
| UI 原型结构、状态和门禁 | `../design/ui-prototype-brief-v3.md` | [ ] |
| 旧文档吸收与删除规则 | `../design/v3-document-migration.md` | [ ] |
| 架构取舍 | `../adr/ADR-012-agent-product-and-permissions.md` 至 `ADR-015-v3-data-api-storage.md` | [ ] |
| 过程记录 | `../devlog/2026/08/2026-08-02.md` | [ ] |

## 8. 执行记录

- 2026-08-02：确认当前 `main` 工作区干净，无活动 plan；从 `refactor/agent-v3` 分支开始执行。
- 2026-08-02：DevLog 为用户明确要求，不沿用旧的禁止规则。

## 9. 状态快照

- **最后更新**：2026-08-02 12:57 +08:00
- **进度**：已完成 3 / 4 项
- **最新 commit**：`fdc34cf` — Merge pull request #7 from Yocaihua8/agent/b-171-interactive-learning
- **代码状态**：`refactor/agent-v3`；创建 plan 前工作区干净；现有 Vue 未修改
- **下一步**：保存治理基线提交，回流 CHANGELOG 后关闭 B-172
- **续任务须知**：后端可在原型评审期间推进；React 生产前端受 P2 门禁阻断
