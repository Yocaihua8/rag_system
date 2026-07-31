# Knowledge Island 文档模板映射
> 状态：Active
> Owner：RAG 团队
> Last Updated：2026-07-31
> Scope：docs-template 1.0.0 到当前仓库文档、协作资产和历史扩展的语义映射
> Related：`README.md`、`docs/README.md`、`.docs-template/state.tsv`

本仓库以 `E:\Code\docs-template` 的 `scaffold/VERSION=1.0.0` 为本次结构基线。迁移方式是“按职责归类 + 以源码校准”，不是覆盖式复制，也不是把模板仓库的业务事实带入 Knowledge Island。

## 1. 启用配置

- Profile：`open-source`
- Packs：`access-control, ai-planning, api, architecture, core, data, frontend, frontend-api-contract, github, github-ci, glossary, migration, open-source, operations, release-support, requirements, security, tooling, tracking, workflow`
- Owner：`RAG 团队`
- GitHub Owner：`@Yocaihua8`
- Consumer 状态：`.docs-template/state.tsv`
- 严格门禁：`.docs-template/strict-ci` 已激活；活动文档占位符、本地链接、索引和元数据纳入 CI

`open-source` profile 在本项目中表示开源协作和治理文件已经准备。仓库当前没有 `LICENSE`，因此不得把“公开仓库”写成“已获得开源授权”；许可证选择继续记录为待项目所有者确认。

## 2. 工程协作类

| 来源或职责 | 归入位置 |
|------------|----------|
| 项目入口与运行边界 | `README.md` |
| AI 项目上下文与操作规则 | `AGENTS.md` |
| 人工贡献流程 | `CONTRIBUTING.md` |
| 版本变更 | `CHANGELOG.md` |
| 安全漏洞上报 | `SECURITY.md`、`docs/guides/security.md` |
| 社区行为 | `CODE_OF_CONDUCT.md` |
| Issue / PR / Owner | `.github/ISSUE_TEMPLATE/`、`.github/pull_request_template.md`、`.github/CODEOWNERS` |
| 文档 CI | `.github/workflows/docs-checks.yml` |
| 写作规范 | `docs/style-guide.md` |
| 分支与测试 | `docs/guides/branch-conventions.md`、`docs/guides/testing.md` |

模板中的 team-only `team-collaboration.md`、`onboarding.md` 和 `merge-conflict-playbook.md` 未启用：当前事实是个人/小规模维护，没有稳定的多角色 RACI 或值班组织。若团队扩大，先补真实 Owner 和流程再启用对应 pack。

## 3. 需求分析类

| 职责 | 归入位置 |
|------|----------|
| 背景、目标用户、范围和成功标准 | `docs/requirements/project-background-and-scope.md` |
| 功能模块与输入输出 | `docs/requirements/functional-modules.md` |
| 参与者、用例和验收 | `docs/requirements/use-cases.md` |
| v2.0.0 交付范围与变更规则 | `docs/requirements/mvp-scope-freeze.md` |

文件名保留模板的 `mvp-scope-freeze.md`，正文语义已校准为 v2.0.0 范围冻结，不以文件名推断项目仍处于 MVP。

## 4. 系统设计类

| 职责 | 归入位置 |
|------|----------|
| 系统边界与主流程 | `docs/design/system-design-overview.md` |
| 分层、依赖和运行面 | `docs/design/architecture-overview.md` |
| HTTP 契约与兼容变化 | `docs/design/api-spec.md`、`docs/design/api-changes.md` |
| 数据表、关系、代际和迁移 | `docs/design/database-design.md` |
| 权限与认证 | `docs/design/permission-matrix.md` |
| 状态与验收 | `docs/design/state-flow-and-acceptance.md` |
| 页面结构与视觉 | `docs/design/ui-wireframes.md`、`docs/design/codex-ui-visual-system.md` |
| 页面/组件文件边界 | `docs/design/page-module-contract.md`、`docs/design/component-api-contract.md` |
| 前后端可达能力和缺口 | `docs/design/frontend-backend-contract-check.md` |
| 风险 | `docs/design/risk-register.md` |
| RFC 模板 | `docs/design/rfc-template.md` |

`docs/design/*-design.md` 和 `api-route-split-blueprint.md` 是 Knowledge Island 的领域扩展。它们保留细节，但不替代 API、数据库和架构三份权威设计。

## 5. 功能规格类

- 每个功能归入 `docs/features/*.md`。
- 入口和完整索引归入 `docs/features/README.md`。
- 新功能先复制 `docs/features/feature-template.md`，替换 token 后再提交。
- 研究文档必须在标题或 Scope 中声明“研究 / 不代表已实现”；部分实现必须逐节列出当前切片。

## 6. 决策与风险类

| 职责 | 归入位置 |
|------|----------|
| 架构决策及替代方案 | `docs/adr/ADR-001-*.md` 至 `ADR-009-*.md` |
| ADR 模板与索引 | `docs/adr/ADR-000-template.md`、`docs/adr/README.md` |
| 跨模块提案 | `docs/design/rfc-template.md` |
| 当前风险与缓解 | `docs/design/risk-register.md` |

ADR 状态沿用 `Proposed / Accepted / Deprecated / Superseded`，不机械替换为普通文档状态。

## 7. 待办与规划类

| 职责 | 归入位置 |
|------|----------|
| 待办、技术债、已知问题 | `docs/BACKLOG.md` |
| 当前 AI 执行计划 | `docs/plans/B-xxx-*.md` |
| plan 生命周期与模板 | `docs/plans/README.md`、`docs/plans/plan-template.md` |

完成的 plan 必须先把结论回流到正式文档，再删除 plan 并将 BACKLOG 置为 `done`。`docs/superpowers/plans/` 的三份无状态旧计划属于历史扩展，不作为当前 Active/Interrupted 冲突 plan。

## 8. 开发过程记录类

| 记录 | 归入位置 |
|------|----------|
| 日报 | `docs/devlog/YYYY/MM/YYYY-MM-DD.md` |
| 周报 | `docs/devlog/YYYY/MM/YYYY-Www.md` |
| 写作模板 | `docs/devlog/devlog-template.md` |
| 问题/事故复盘模板 | `docs/devlog/postmortem-template.md` |
| 目录规则和索引 | `docs/devlog/README.md` |

DevLog 只记录过程。长期待办回流 BACKLOG，重大决策提升为 ADR，当前行为回流 requirements/design/features/guides。

## 9. 指南与运营类

| 职责 | 归入位置 |
|------|----------|
| 环境搭建 | `docs/guides/setup.md` |
| 测试和质量门禁 | `docs/guides/testing.md` |
| 发布和回滚 | `docs/guides/release-process.md` |
| 本地/Docker 运维 | `docs/guides/runbook.md` |
| 常见故障 | `docs/guides/troubleshooting.md` |
| 安全与内部响应 | `docs/guides/security.md` |
| 支持范围和版本政策 | `docs/guides/support-policy.md` |
| 许可证决策 | `docs/guides/license-selection.md` |
| 维护者治理 | `docs/guides/open-source-governance.md` |
| 技术迁移状态 | `docs/guides/technical-migration-plan.md` |
| 可复用接入/迁移指南 | `docs/guides/integration-guide-template.md`、`docs/guides/migration-guide-template.md` |

运行手册只写已核验命令。当前 `ops/scripts/backup_db.sh` 的默认路径与 v2 数据根存在漂移，因此在修复前不能被指南描述为可直接执行的 v2 备份方案。

## 10. 术语与扩展类

| 类型 | 位置 | 边界 |
|------|------|------|
| 当前术语 | `docs/glossary.md` | 统一 UI、API、数据和兼容词汇 |
| 发布证据 | `docs/release/` | 时间点快照，不定义未来状态 |
| 旧架构 | `docs/architecture/` | Archived，仅历史参考 |
| 工具生成历史 | `docs/superpowers/` | 历史规格/计划，不是当前任务 |
| 交互预览 | `docs/previews/` | 原型，不代表正式 Vue 已实现 |
| 旧桌面实现 | `archive/src-desktop-legacy/` | 代码历史，不得重新接入当前链路 |

模板的 commercial/business pack 未启用：当前没有客户报价、合同、SOW 或商业验收事实，不创建空白商务文档。

## 11. 同步约束

以下三处必须同步：

1. `README.md` 的项目结构和文档入口；
2. `docs/README.md` 的目录、正式文档和模板索引；
3. 本文件的 profile、packs、映射和项目扩展。

文件清单变化还必须更新 `.docs-template/state.tsv`；活动文档新增 token、失效链接或缺失索引应由文档门禁阻断。
