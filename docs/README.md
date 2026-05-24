# 文档总览

> 状态：Active
> Owner：RAG 团队
> Last Updated：2026-05-22

本仓库的文档按“项目约束 → 架构设计 → 开发流程”分层组织。新的文档目录用于降低历史冗余，并保持与现有 `docs/architecture`、`docs/release` 历史文档的兼容。

## 1. 阅读顺序

**先读（理解项目是什么）：**

1. `requirements/project-background-and-scope.md`
2. `design/system-design-overview.md`
3. `design/architecture-overview.md`
4. `design/database-design.md`
5. `design/api-spec.md`
6. `design/model-profiles-design.md`（B-111 模型 Profile 多配置设计；当前仅为设计，不代表已建表）
7. `requirements/functional-modules.md`
8. `release/WEB_MVP_READINESS_2026-05-20.md`（本地 Web MVP 收口快照；当前能力以最新文档为准）

**再读（参与开发）：**

9. `../README.md`（项目入口与目录）
10. `../CONTRIBUTING.md`（若存在）
11. `guides/setup.md`
12. `guides/testing.md`
13. `guides/release-process.md`

**按需读：**

14. `BACKLOG.md`（未完成项与优先级）
15. `DEVLOG.md`（现有开发日志，保留历史）
16. `architecture/ARCHITECTURE_ENTERPRISE_BASELINE.md`（历史基线，仅作历史参考）
17. `../CHANGELOG.md`（发布变更）

## 2. 目录说明

| 路径 | 用途 | 是否必需 |
|------|------|----------|
| `requirements/` | 项目边界、模块与用户用例 | 是 |
| `design/` | 架构、接口、数据库、风险、状态流转 | 是 |
| `features/` | 功能级规格 | 建议 |
| `guides/` | 启动、测试、发布等开发指引 | 是 |
| `adr/` | 重大架构决策记录 | 可选 |
| `devlog/` | 开发过程日志索引 | 是 |
| `BACKLOG.md` | 待办与技术债务 | 是 |
| `release/` | 发布说明与非技术交付清单 | 是 |

在目录结构外，仓库根目录保留 `template-mapping.md`，用于定义历史文档、行为文档与新结构的归类关系。

## 3. 历史文档兼容说明

以下旧文档保持可读，但作为历史参考归档，不作为第一默认阅读页：

- `architecture/ARCHITECTURE_ENTERPRISE_BASELINE.md`
- `architecture/STRUCTURE_BASELINE.md`
- `architecture/SYSTEM_ARCHITECTURE.md`
- `architecture/RAG_PIPELINE.md`
- `architecture/DATA_MODEL.md`
- `architecture/LLM_PROVIDER_DESIGN.md`

当它们与 `AGENT.md`、`requirements/`、`design/`、`guides/` 冲突时，以 `AGENT.md` 与当前 `requirements/`、`design/` 为准，并补充更新对应文件。当前默认入口以本地 Web MVP 为准，历史架构文档不定义当前默认启动方式。

## 4. 文档一致性要求

- 需求变更先改 `requirements/`。
- 架构模式、端口边界变更同步改 `design/architecture-overview.md`。
- 接口或兼容约定变更同步改 `design/api-spec.md`，必要时新增 ADR。
- 日常行为改动先写进 `docs/devlog`（索引方式）并同步到 `CHANGELOG.md`（对外发布）和 `BACKLOG.md`（待办追踪）。
