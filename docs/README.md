# Knowledge Island 文档总览
> 状态：Active
> Owner：RAG 团队
> Last Updated：2026-07-30
> Scope：Knowledge Island v2.0.0 正式文档、过程记录、复用模板与历史扩展的统一入口
> Related：`../README.md`、`../AGENTS.md`、`../CONTRIBUTING.md`、`../template-mapping.md`

本目录按 docs-template 1.0.0 的职责组织文档。模板提供结构，项目源码、测试和发布证据提供事实；不得用模板占位内容替代项目结论，也不得把历史计划或未来方向写成当前已实现能力。

## 1. 模板消费状态

- Profile：`open-source`
- Packs：`access-control, ai-planning, api, architecture, core, data, frontend, frontend-api-contract, github, github-ci, glossary, migration, open-source, operations, release-support, requirements, security, tooling, tracking, workflow`
- 状态清单：`../.docs-template/state.tsv`
- 归类映射：`../template-mapping.md`
- 严格门禁：活动文档填完且本地占位符检查返回 0 后，才允许提交 `.docs-template/strict-ci`
- 许可证边界：仓库当前无 `LICENSE`；profile 表示“开源协作准备态”，不表示已经授予开源许可证

## 2. 当前事实边界

| 主题 | 当前权威事实 |
|------|--------------|
| 产品 | `v2.0.0` 已正式发布，主线为本地项目知识教练 |
| Web | Vue 3 + FastAPI/Uvicorn；默认 `127.0.0.1:8765` |
| 页面 | `教练 / 学习地图 / 学习计划 / 资料 / 设置`；资料是模态入口，评估是覆盖层 |
| 数据 | v2 默认 `runtime/v2/app.db`；正式 Web 写链路执行数据代际校验 |
| Tauri | 复用 Vue 构建产物并启动后端 sidecar；构建证据不能替代安装包动态连通性验证 |
| Obsidian | 独立 desktop-only 插件；增量同步与用户确认后的受控发布是两条不同链路 |
| 兼容 | 1.x 导入、聊天、评估等 API 仍有兼容用途；旧 PySide6 只在 archive 中保留 |

当文档与代码冲突时，先按下列优先级核验，不得直接选择对当前任务最方便的说法：

1. 当前源码、数据库建表代码和自动化测试；
2. `design/api-spec.md`、`design/database-design.md` 与已接受 ADR；
3. 当前功能、需求和指南；
4. release/devlog 历史快照；
5. `architecture/`、`superpowers/` 与 archive 历史材料。

## 3. 最小阅读顺序

### 理解产品

1. [`requirements/project-background-and-scope.md`](requirements/project-background-and-scope.md)
2. [`requirements/functional-modules.md`](requirements/functional-modules.md)
3. [`features/project-knowledge-coach.md`](features/project-knowledge-coach.md)
4. [`requirements/use-cases.md`](requirements/use-cases.md)
5. [`requirements/mvp-scope-freeze.md`](requirements/mvp-scope-freeze.md)

### 理解系统

1. [`design/system-design-overview.md`](design/system-design-overview.md)
2. [`design/architecture-overview.md`](design/architecture-overview.md)
3. [`design/api-spec.md`](design/api-spec.md)
4. [`design/database-design.md`](design/database-design.md)
5. [`design/permission-matrix.md`](design/permission-matrix.md)
6. [`design/ui-wireframes.md`](design/ui-wireframes.md)
7. [`design/state-flow-and-acceptance.md`](design/state-flow-and-acceptance.md)

### 参与开发

1. [`../AGENTS.md`](../AGENTS.md)
2. [`../CONTRIBUTING.md`](../CONTRIBUTING.md)
3. [`guides/setup.md`](guides/setup.md)
4. [`guides/testing.md`](guides/testing.md)
5. [`guides/branch-conventions.md`](guides/branch-conventions.md)
6. [`guides/security.md`](guides/security.md)
7. [`guides/release-process.md`](guides/release-process.md)

## 4. 目录说明

| 路径 | 职责 | 当前性质 |
|------|------|----------|
| [`requirements/`](requirements/) | 产品背景、模块、用例和版本范围 | 正式需求 |
| [`design/`](design/) | 系统、架构、API、数据、权限、状态、UI 和契约 | 正式设计 |
| [`features/`](features/) | 单一功能行为、边界和验收 | 正式功能规格 |
| [`guides/`](guides/) | 搭建、测试、发布、安全、运维、支持、迁移和排障 | 正式指南 |
| [`adr/`](adr/) | 重要架构决策及其理由 | 永久决策记录 |
| [`devlog/`](devlog/) | 按 `YYYY/MM/` 归档的开发过程和复盘 | 过程记录 |
| [`plans/`](plans/) | 与 BACKLOG 关联的当前 AI 执行计划 | 临时，完成即删除 |
| [`release/`](release/) | 已完成发布/候选的证据快照 | 项目扩展，历史证据 |
| [`architecture/`](architecture/) | 旧企业基线与早期架构材料 | 项目扩展，Archived |
| [`superpowers/`](superpowers/) | 旧工具生成的规格和计划 | 项目扩展，历史参考 |
| [`previews/`](previews/) | 交互原型和设计预览 | 项目扩展，不代表正式实现 |
| [`glossary.md`](glossary.md) | 当前术语、实体与废弃用词 | 正式词汇表 |
| [`BACKLOG.md`](BACKLOG.md) | 待办、技术债和已知问题 | 活动跟踪 |
| [`style-guide.md`](style-guide.md) | 文档写作与模板占位符规范 | 复用规范 |

## 5. 正式设计索引

| 文档 | 职责 |
|------|------|
| [`design/system-design-overview.md`](design/system-design-overview.md) | 系统边界与主流程 |
| [`design/architecture-overview.md`](design/architecture-overview.md) | 分层、依赖、运行面和架构约束 |
| [`design/api-spec.md`](design/api-spec.md) | HTTP 字段级契约 |
| [`design/api-changes.md`](design/api-changes.md) | 破坏性 API 变化与迁移 |
| [`design/database-design.md`](design/database-design.md) | SQLite 表、关系、代际和迁移规则 |
| [`design/permission-matrix.md`](design/permission-matrix.md) | 本地单用户、可选认证和插件令牌边界 |
| [`design/state-flow-and-acceptance.md`](design/state-flow-and-acceptance.md) | 业务状态和验收条件 |
| [`design/ui-wireframes.md`](design/ui-wireframes.md) | 当前页面结构与交互事实 |
| [`design/page-module-contract.md`](design/page-module-contract.md) | 页面装配和文件责任 |
| [`design/component-api-contract.md`](design/component-api-contract.md) | 关键组件 props/emits/边界 |
| [`design/frontend-backend-contract-check.md`](design/frontend-backend-contract-check.md) | 当前前后端可达能力与缺口 |
| [`design/codex-workspace-chat-import-design.md`](design/codex-workspace-chat-import-design.md) | 教练、资料与 Obsidian 工作流 |
| [`design/codex-ui-visual-system.md`](design/codex-ui-visual-system.md) | 视觉令牌、状态和无障碍 |
| [`design/risk-register.md`](design/risk-register.md) | 当前风险与发布门禁 |
| [`design/model-profiles-design.md`](design/model-profiles-design.md) | 模型 Profile 设计 |
| [`design/document-collections-design.md`](design/document-collections-design.md) | 文档集合设计 |
| [`design/import-batches-design.md`](design/import-batches-design.md) | 导入批次设计 |
| [`design/project-prompt-settings-design.md`](design/project-prompt-settings-design.md) | 项目 Prompt 预设设计 |
| [`design/chat-sessions-design.md`](design/chat-sessions-design.md) | 历史会话设计记录 |
| [`design/api-route-split-blueprint.md`](design/api-route-split-blueprint.md) | 已完成 API 拆分蓝图 |
| [`design/legacy-conversation-sessions-design.md`](design/legacy-conversation-sessions-design.md) | 已归档 legacy 会话设计 |

## 6. 可复用模板

下列文件允许保留合法的模板占位符，复制到新文件后必须全部替换；其他活动文档不得保留占位符。

| 模板 | 用途 |
|------|------|
| [`features/feature-template.md`](features/feature-template.md) | 功能规格 |
| [`adr/ADR-000-template.md`](adr/ADR-000-template.md) | ADR |
| [`design/rfc-template.md`](design/rfc-template.md) | RFC / 跨模块提案 |
| [`plans/plan-template.md`](plans/plan-template.md) | AI 执行计划 |
| [`devlog/devlog-template.md`](devlog/devlog-template.md) | 日报/迭代日志 |
| [`devlog/postmortem-template.md`](devlog/postmortem-template.md) | 问题/事故复盘 |
| [`guides/contributor-guide-template.md`](guides/contributor-guide-template.md) | 特定贡献场景指南 |
| [`guides/integration-guide-template.md`](guides/integration-guide-template.md) | API/第三方接入指南 |
| [`guides/migration-guide-template.md`](guides/migration-guide-template.md) | 使用方版本迁移指南 |

## 7. 文档状态

正式文档使用：

- `Draft`：尚未作为当前约束；
- `In Review`：正在评审；
- `Active`：当前有效；
- `Deprecated`：仍保留但不应继续采用；
- `Archived`：历史记录，不定义当前行为。

ADR 可使用 `Proposed / Accepted / Deprecated / Superseded`；plan 使用 `Draft / Active / Interrupted / Done`。实现进度写进正文或 BACKLOG，不把 `Implemented`、`Released` 等进度词混作正式文档状态。

## 8. 维护联动

| 变化 | 必须核对 |
|------|----------|
| 产品目标、用户或范围 | `requirements/`、相关 feature、BACKLOG |
| 功能行为或页面流程 | 对应 `features/*.md`、`design/ui-wireframes.md` |
| HTTP 方法、路径、字段或错误 | `design/api-spec.md`；破坏性变化再更新 `api-changes.md` |
| 数据表、字段、约束或代际 | `design/database-design.md` + 必要 ADR |
| 架构边界或技术选型 | `design/architecture-overview.md` + 必要 ADR |
| 权限、认证或 Agent 白名单 | `design/permission-matrix.md`、安全文档 + 必要 ADR |
| 启动、测试、部署或发布 | 对应 guide、CI、`CHANGELOG.md` |
| 新发现缺陷或技术债 | `BACKLOG.md § 6` 或新增 B-ID |
| 文档目录或模板 pack | 本文件、`../README.md`、`../template-mapping.md`、`.docs-template/state.tsv` |

## 9. ADR 触发条件

出现以下任一情况必须先评估 ADR：

- 存储、认证、权限、Agent 工具能力或数据代际变化；
- 影响两个及以上模块的技术选型；
- 跨模块或对外契约的破坏性变化；
- 用新方案替代当前已接受方案；
- 依赖变化引入新的安全、合规、成本或不可逆迁移风险。

可逆局部重构、无契约变化的实现细节和单纯文档修正不强制新增 ADR。模板见 [`adr/ADR-000-template.md`](adr/ADR-000-template.md)。

## 10. 历史材料边界

`architecture/`、`release/`、`superpowers/`、`previews/` 和 `archive/src-desktop-legacy/` 均保留为项目扩展或历史证据，不批量删除。它们与当前源码、正式需求/设计冲突时，不作为当前事实源；历史文件内的旧路径、旧状态和旧测试数可以保留，但入口文档必须明确其时间边界。
