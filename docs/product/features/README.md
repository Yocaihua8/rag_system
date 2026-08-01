# 功能规格索引

> 状态：Active
> Owner：RAG 团队
> Last Updated：2026-08-01
> Scope：当前已实现功能及明确的兼容/可达边界
> Related：`../modules.md`、`../../architecture/backend/api.md`、`../../BACKLOG.md`

| 功能 | 规格 |
|------|------|
| 项目知识教练、评估与学习计划 | [`project-knowledge-coach.md`](project-knowledge-coach.md) |
| 项目空间与导入 | [`project-space-ingestion.md`](project-space-ingestion.md) |
| 资料管理 | [`knowledge-base-management.md`](knowledge-base-management.md) |
| 首次引导 | [`first-run-wizard.md`](first-run-wizard.md) |
| 对话分支 | [`chat-branching.md`](chat-branching.md) |
| 多模型比较 | [`multi-model-comparison.md`](multi-model-comparison.md) |
| 结果导出 | [`result-export.md`](result-export.md) |
| 并发索引 | [`concurrent-indexing.md`](concurrent-indexing.md) |
| Graph-enhanced 检索 | [`graph-enhanced-retrieval.md`](graph-enhanced-retrieval.md) |
| Qdrant 向量存储 | [`qdrant-vector-store.md`](qdrant-vector-store.md) |
| 可选认证 | [`authentication.md`](authentication.md) |
| FastAPI API-only 运行时 | [`fastapi-runtime.md`](fastapi-runtime.md) |
| Vue 前端工程 | [`frontend-engineering.md`](frontend-engineering.md) |
| OpenAPI/Swagger | [`openapi-swagger-docs.md`](openapi-swagger-docs.md) |

跨模块集成不在本目录重复维护：桌面、Obsidian 和 GitHub 分别见 [`../../integrations/`](../../integrations/)。

### 可达性原则

- 后端存在接口不等于当前主导航已提供完整入口。
- 未挂载的兼容组件不作为用户主流程能力。
- 可见但未接线的控件以 [`../../BACKLOG.md`](../../BACKLOG.md) 为准，不得描述为已交付闭环。
- 完成的新行为更新本索引和对应规格；未完成设想只进入 BACKLOG。

新功能文档使用 [`../../governance/templates/feature-template.md`](../../governance/templates/feature-template.md)。
