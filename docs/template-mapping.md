# 文档模板映射说明

> 状态：Active
> Owner：RAG 团队
> Last Updated：2026-05-16

说明本仓库文档资产与 `docs/` 结构（requirements/design/features/guides/adr/devlog）之间的归口关系。用于避免需求、设计、过程记录互相混写。

## 1. 归类入口

### 1.1 工程协作与流程

| 来源文档 | 归口 |
|---|---|
| `.github` 协作要求、`README`、`CHANGELOG`、`CONTRIBUTING`（如存在） | 根文档与 `docs/guides/*` |
| `docs/DEVLOG.md`（已删除） | 已拆分并迁移至 `docs/devlog/*.md` 各日报文件 |
| `docs/TEST*`、`pytest` 输出 | `docs/guides/testing.md` |

### 1.2 需求与边界

| 来源文档 | 归口 |
|---|---|
| 项目目标、范围、产品定位 | `docs/requirements/project-background-and-scope.md` |
| 模块清单、MVP 列表、验收边界 | `docs/requirements/functional-modules.md` |
| 典型交互场景、用户行为 | `docs/requirements/use-cases.md` |
| MVP 冻结/不含项 | `docs/requirements/mvp-scope-freeze.md` |

### 1.3 系统设计

| 来源文档 | 归口 |
|---|---|
| 总览与架构关系 | `docs/design/system-design-overview.md` |
| 架构风格/依赖关系/分层 | `docs/design/architecture-overview.md` |
| API 与契约定义 | `docs/design/api-spec.md` |
| 数据持久化结构与一致性 | `docs/design/database-design.md` |
| 权限与可见性规则 | `docs/design/permission-matrix.md` |
| 状态流转与验收规则 | `docs/design/state-flow-and-acceptance.md` |
| 风险登记 | `docs/design/risk-register.md` |
| 页面结构与导航约束 | `docs/design/ui-wireframes.md` |
| 重大接口变更清单 | `docs/design/api-changes.md` |

### 1.4 功能规格

| 来源文档 | 归口 |
|---|---|
| 单一功能实现行为说明 | `docs/features/*.md` |

### 1.5 决策与待办

| 来源文档 | 归口 |
|---|---|
| 长期影响决策 | `docs/adr/*.md` |
| 已识别但未完成 | `docs/BACKLOG.md` |

### 1.6 开发过程

| 来源文档 | 归口 |
|---|---|
| 过程日志、调试记录、临时决策 | `docs/devlog/*.md` |
| AI 任务计划（主动创建）| `docs/plans/{B-ID}-{slug}.md` |
| AI 任务计划（工具自动生成）| `docs/superpowers/plans/{YYYY-MM-DD}-{slug}.md` |

## 2. 历史文档归口

以下文档保留为历史基线，不作为当前定稿主要入口：

- `docs/architecture/*`
- `docs/release/*`
- `docs/superpowers/*`

当与 `requirements/design` 冲突时，以 `requirements/design` 为当前有效说明。

## 3. 维护同步约束

- 更新 `requirements/*` 或 `design/*` 时，需同步 `docs/README.md` 与本文件中的归口关系清单。
- 新增功能说明优先放 `docs/features/*.md`，避免在 `requirements`/`design` 里混入实施计划。
- 任何跨模块接口约定变更若影响兼容性，需同步 `docs/design/api-changes.md` 或新增 ADR。
