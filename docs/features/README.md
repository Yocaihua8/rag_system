# 功能文档索引
> 状态：Active
> Owner：RAG 团队
> Last Updated：2026-07-30
> Scope：Knowledge Island 当前功能规格、兼容能力、研究结论和复用模板
> Related：`../requirements/functional-modules.md`、`../design/api-spec.md`、`feature-template.md`

每份功能文档只承担一个模块或一条行为链路。`Active` 表示文档当前有效，不代表其中每个历史阶段、研究方向或后续切片均已实现；正文必须分别标明“当前实现 / 兼容 / 研究 / 后续”。

## 1. v2 主闭环

| 文档 | 当前职责 |
|------|----------|
| [`project-knowledge-coach.md`](project-knowledge-coach.md) | 项目分析、知识点、技能映射、覆盖评估和学习计划 |
| [`frontend-engineering.md`](frontend-engineering.md) | Vue 工程、当前页面入口、状态管理、单测与构建 |
| [`notion-obsidian-sync.md`](notion-obsidian-sync.md) | Notion ZIP/Obsidian Vault 导入与桌面插件桥接、受控发布 |
| [`desktop-packaging.md`](desktop-packaging.md) | Tauri sidecar、平台 bundle 和发布验证边界 |
| [`first-run-wizard.md`](first-run-wizard.md) | 首次运行向导的当前编排与限制 |

## 2. 导入、资料和检索

| 文档 | 当前职责 |
|------|----------|
| [`project-space-ingestion.md`](project-space-ingestion.md) | 项目目录同步、文件处理和来源边界 |
| [`knowledge-base-management.md`](knowledge-base-management.md) | 文档、集合、预览、删除和导入批次管理 |
| [`github-repo-import.md`](github-repo-import.md) | GitHub 仓库浅克隆导入及安全限制 |
| [`concurrent-indexing.md`](concurrent-indexing.md) | 跨项目并发、同项目串行的进程内队列 |
| [`qdrant-vector-store.md`](qdrant-vector-store.md) | 可选 Qdrant local mode 与 SQLite 回退 |
| [`graph-enhanced-retrieval.md`](graph-enhanced-retrieval.md) | 仅在旧图表存在时启用的一跳候选扩展 |
| [`web-crawling-research.md`](web-crawling-research.md) | 抓取研究和已落地的受控单 URL 最小切片 |

## 3. 问答、会话与工具

| 文档 | 当前职责 |
|------|----------|
| [`chat-branching.md`](chat-branching.md) | 父消息分支、历史问题编辑重发和取消 |
| [`multi-model-comparison.md`](multi-model-comparison.md) | 多 Profile 对比回答 |
| [`result-export.md`](result-export.md) | 问答 Markdown/PDF 本地导出 |
| [`agent-tooling-mcp-research.md`](agent-tooling-mcp-research.md) | MCP/插件研究；当前 Agent 仍只有两个只读白名单工具 |

## 4. 平台、接口与运维

| 文档 | 当前职责 |
|------|----------|
| [`fastapi-runtime.md`](fastapi-runtime.md) | FastAPI/Uvicorn 运行时和兼容分发 |
| [`authentication.md`](authentication.md) | 默认关闭的共享 API Key + JWT 保护；不是多用户系统 |
| [`openapi-swagger-docs.md`](openapi-swagger-docs.md) | 94 个操作的 OpenAPI 清单；字段级契约仍以 api-spec 为准 |
| [`ops-maintenance.md`](ops-maintenance.md) | 备份、清理和索引重建脚本；当前路径漂移见 BACKLOG 已知问题 |
| [`team-workspace-research.md`](team-workspace-research.md) | 多用户/团队空间研究；不代表已经实现团队能力 |

## 5. 当前 UI 可达边界

- 主入口为 `教练 / 学习地图 / 学习计划 / 资料 / 设置`。
- 资料使用 `LibraryModal`；未挂载的 `LibraryView` 不能作为当前可达 UI 事实。
- 评估使用 `CoachAssessmentOverlay`；未挂载的 `AssessmentView` 只保留兼容代码。
- 后端已实现的导入/管理接口多于当前主资料弹窗可达能力。
- 可见但未接线的控件、URL 摘录参数缺口和 Tauri 动态连通性风险统一记录在 `../BACKLOG.md § 6`，功能文档不得用控件存在替代端到端验收。

## 6. 新增功能文档

1. 复制 [`feature-template.md`](feature-template.md) 并改为功能名。
2. 替换所有模板占位符。
3. 填写状态、Owner、日期、Scope、Related 和必要 ADR。
4. 写清用户、前置条件、主流程、边界、错误、接口/数据影响和验收。
5. 将文件加入本索引；涉及目录或 pack 时同步 `../README.md` 与 `../../template-mapping.md`。

[`feature-template.md`](feature-template.md) 是复用模板，不属于已实现功能。
