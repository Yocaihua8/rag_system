# 文档总览

> 状态：Active
> Owner：RAG 团队
> Last Updated：2026-06-30
> Related：CONTRIBUTING.md, CHANGELOG.md, AGENTS.md

本仓库的文档按"项目约束 → 架构设计 → 开发流程"分层组织，遵循 `docs/style-guide.md` 写作规范。新的文档目录降低历史冗余，并保持与现有 `docs/architecture`、`docs/release` 历史文档的兼容。

---

## 1. 阅读顺序

**先读（理解项目是什么）：**

1. `requirements/project-background-and-scope.md` — 项目背景、目标用户、范围与约束
2. `requirements/functional-modules.md` — 各功能模块边界与优先级
3. `design/system-design-overview.md` — 系统级设计、核心流程、非功能约束
4. `design/architecture-overview.md` — 架构结论、技术栈、分层职责、备选方案
5. `design/database-design.md` — SQLite 表结构、实体关系、迁移规范
6. `design/api-spec.md` — HTTP API 接口清单与契约说明
7. `design/model-profiles-design.md` — 模型 Profile 多配置设计（B-111/B-112 已落地，接口以 api-spec 为准）
8. `design/document-collections-design.md` — 文档集合分组设计（B-113/B-114 已落地）
9. `design/import-batches-design.md` — 导入批次历史设计（B-115/B-116 已落地）
10. `design/api-route-split-blueprint.md` — `webapp/api.py` 按领域拆分蓝图（B-131）

**再读（参与开发）：**

11. `../CONTRIBUTING.md` — 贡献流程、代码规范、测试要求、文档要求
12. `guides/setup.md` — 环境搭建与启动步骤
13. `guides/branch-conventions.md` — 分支命名与提交规范
14. `guides/testing.md` — 测试分层与回归清单
15. `guides/release-process.md` — 发布检查与打包步骤

**按需读：**

16. `BACKLOG.md` — 未完成项、技术债与优先级（含预估工时）
17. `adr/` — 重大架构决策记录
18. `devlog/` — 开发过程日志（日报/周报）
19. `plans/` — AI 任务计划（关心"当前任务进度"时）
20. `../CHANGELOG.md` — 对外发布变更记录
21. `design/permission-matrix.md` — 权限边界说明
22. `design/ui-wireframes.md` — 页面布局与核心交互
23. `design/state-flow-and-acceptance.md` — 状态流转与验收标准
24. `design/risk-register.md` — 风险清单
25. `design/api-changes.md` — API 变更分级与迁移指南
26. `style-guide.md` — 文档写作规范
27. `design/legacy-conversation-sessions-design.md` — legacy 多轮对话设计与 B-20 实现边界
28. `features/agent-tooling-mcp-research.md` — B-117 MCP / 插件能力研究结论（不代表已实现 MCP 接入）
29. `features/team-workspace-research.md` — B-118 多用户 / 团队空间研究结论（不代表已实现多用户或团队空间）
30. `features/web-crawling-research.md` — B-119 网页自动抓取研究结论（不代表已实现网页自动抓取）
31. `release/WEB_MVP_READINESS_2026-05-20.md` — Web MVP 收口快照（历史）

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
| 页面结构 / 交互变更 | `design/ui-wireframes.md` |
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
