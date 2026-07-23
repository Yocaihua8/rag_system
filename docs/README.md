# 文档总览

> 状态：Active
> Owner：RAG 团队
> Last Updated：2026-07-23
> Related：CONTRIBUTING.md, CHANGELOG.md, AGENTS.md

本仓库的文档按"项目约束 → 架构设计 → 开发流程"分层组织，遵循 `docs/style-guide.md` 写作规范。新的文档目录降低历史冗余，并保持与现有 `docs/architecture`、`docs/release` 历史文档的兼容。

---

## 0. 产品代际边界

- **当前 1.x**：默认入口仍是本地 Web MVP；Vue 当前以 `聊 / 库 / 设` 为主线，Obsidian 仅支持一次性只读导入。
- **2.0 目标**：产品定位为本地项目知识教练，一级入口冻结为 `教练 / 学习地图 / 学习计划 / 资料 / 设置`；评估使用覆盖层，Obsidian 同时是资料源和用户确认后的成果出口。
- **状态解释**：设计文档的 `Active` 表示设计决策有效，不表示其中明确标注为“2.0 目标”的能力已经上线。当前接口和行为以源码、测试及 `design/api-spec.md` 为准。
- **停止方向**：B-157“全局资料库 / 跨工作区共享资料”不再作为 2.0 前置能力。

## 1. 阅读顺序

**先读（理解项目是什么）：**

1. `requirements/project-background-and-scope.md` — 项目背景、目标用户、范围与约束
2. `requirements/functional-modules.md` — 各功能模块边界与优先级
3. `features/project-knowledge-coach.md` — Knowledge Island 2.0 教练闭环、评价口径与兼容边界
4. `design/system-design-overview.md` — 系统级设计、核心流程、非功能约束
5. `design/architecture-overview.md` — 架构结论、技术栈、分层职责、备选方案
6. `design/database-design.md` — SQLite 表结构、实体关系、迁移规范
7. `design/api-spec.md` — HTTP API 接口清单与契约说明
8. `design/model-profiles-design.md` — 模型 Profile 多配置设计（B-111/B-112 已落地，接口以 api-spec 为准）
9. `design/document-collections-design.md` — 文档集合分组设计（B-113/B-114 已落地）
10. `design/import-batches-design.md` — 导入批次历史设计（B-115/B-116 已落地）
11. `design/api-route-split-blueprint.md` — API 兼容分发按领域拆分蓝图（B-131/B-138，B-155 后路径位于 `backend/`）

**再读（参与开发）：**

12. `../CONTRIBUTING.md` — 贡献流程、代码规范、测试要求、文档要求
13. `guides/setup.md` — 环境搭建与启动步骤
14. `guides/branch-conventions.md` — 分支命名与提交规范
15. `guides/testing.md` — 测试分层与回归清单
16. `guides/release-process.md` — 发布检查与打包步骤

**按需读：**

17. `BACKLOG.md` — 未完成项、技术债与优先级（含预估工时）
18. `adr/` — 重大架构决策记录
19. `devlog/` — 开发过程日志（日报/周报）
20. `plans/` — AI 任务计划（关心"当前任务进度"时）
21. `../CHANGELOG.md` — 对外发布变更记录
22. `design/permission-matrix.md` — 权限边界说明
23. `design/ui-wireframes.md` — 当前 1.x 页面事实与 2.0 目标信息架构、页面布局
24. `design/codex-workspace-chat-import-design.md` — 项目知识教练工作流、资料导入与 Obsidian 受控发布边界
25. `design/codex-ui-visual-system.md` — Codex 中性视觉令牌、组件状态、动效与无障碍规范
26. `design/state-flow-and-acceptance.md` — 状态流转与验收标准
27. `design/risk-register.md` — 风险清单
28. `design/api-changes.md` — API 变更分级与迁移指南
29. `style-guide.md` — 文档写作规范
30. `design/legacy-conversation-sessions-design.md` — legacy 多轮对话设计与 B-20 实现边界
31. `features/agent-tooling-mcp-research.md` — B-117 MCP / 插件能力研究结论（不代表已实现 MCP 接入）
32. `features/team-workspace-research.md` — B-118 多用户 / 团队空间研究结论（不代表已实现多用户或团队空间）
33. `features/web-crawling-research.md` — B-119 网页自动抓取研究结论（不代表已实现网页自动抓取）
34. `release/WEB_MVP_READINESS_2026-05-20.md` — Web MVP 收口快照（历史）

---

## 2. 目录说明

| 路径 | 用途 | 是否必需 |
|------|------|----------|
| `requirements/` | 项目背景、功能模块、用户范围 | 是 |
| `design/` | 架构、接口、数据库、权限、状态流转、风险 | 是 |
| `guides/` | 启动、分支、测试、发布等开发指引 | 是 |
| `adr/` | 重大架构决策记录 | 按需 |
| `devlog/` | 开发过程日志（日报/周报）| 是 |
| `plans/` | AI 任务计划（与 BACKLOG 联动，执行完删除） | 按需 |
| `features/` | 功能级规格文档 | 按需 |
| `BACKLOG.md` | 待办、技术债与优先级 | 是 |
| `style-guide.md` | 文档写作规范 | 是 |
| `release/` | 发布说明与历史快照 | 按需 |
| `architecture/` | Legacy 企业基线架构文档（历史参考，非当前默认）| 否 |

仓库根目录保留 `template-mapping.md`，定义历史文档与新结构的归类关系。

---

## 3. 维护规则

| 变更场景 | 需更新的文档 |
|----------|-------------|
| 新增需求 / 调整范围 | `requirements/project-background-and-scope.md` |
| 新增模块 / 改动功能 | `requirements/functional-modules.md` |
| API 接口变更 | `design/api-spec.md` |
| API 破坏性变更 | `design/api-spec.md` + `design/api-changes.md` |
| 数据库 Schema 变更 | `design/database-design.md` + ADR（必要时）|
| 架构模式 / 分层边界变化 | `design/architecture-overview.md` + ADR（必要时）|
| 产品定位 / 一级入口变化 | `requirements/project-background-and-scope.md` + `design/ui-wireframes.md` + `design/codex-workspace-chat-import-design.md` |
| 页面结构 / 交互变更 | `design/ui-wireframes.md` |
| 视觉令牌 / 组件状态 / 动效变更 | `design/codex-ui-visual-system.md` |
| 重大架构决策 | `adr/ADR-XXX.md` |
| 已知问题 / 技术债 | `BACKLOG.md` |
| 版本发布 | `../CHANGELOG.md` |

`docs/README.md` 的目录说明必须与实际文件保持一致。

---

## 4. 何时应新建 ADR

**强制新建 ADR**：

- 技术选型存在多个可行方案，影响 ≥ 2 个模块（如：向量库迁移 Qdrant、引入 FastAPI）
- 存储模型 / 权限模型 / 认证方式发生变化
- 跨模块数据契约的破坏性变更
- 用新方案**替代**现有方案（需保留历史理由）
- 依赖变更带来新的安全、合规或成本风险

**非强制（写 devlog 即可）**：

- 可逆的局部重构
- 不影响对外契约的实现细节调整
- 个人偏好或风格微调

ADR 模板见 `adr/ADR-000-template.md`。

---

## 5. 文档状态约定

建议统一使用以下状态：

- `Draft`：草稿
- `In Review`：评审中
- `Active`：当前有效
- `Deprecated`：已废弃（需在文档头部注明 `Deprecated since` 与 `Replaced by`）
- `Archived`：已归档

状态只描述文档本身是否有效。同一份 `Active` 设计文档包含当前实现和目标设计时，必须逐节标注“当前 1.x”与“2.0 目标”。

---

## 6. 历史文档兼容说明

以下旧文档保持可读，但作为历史参考归档，不作为第一默认阅读页：

- `architecture/ARCHITECTURE_ENTERPRISE_BASELINE.md`
- `architecture/STRUCTURE_BASELINE.md`
- `architecture/SYSTEM_ARCHITECTURE.md`
- `architecture/RAG_PIPELINE.md`
- `architecture/DATA_MODEL.md`
- `architecture/LLM_PROVIDER_DESIGN.md`

当它们与 `AGENTS.md`、`requirements/`、`design/`、`guides/` 冲突时，以 `AGENTS.md` 与当前 `requirements/`、`design/` 为准。当前默认入口以本地 Web MVP（`app.py`）为准，历史架构文档不定义当前默认启动方式。
