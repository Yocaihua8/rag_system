# 功能文档说明

> 状态：Active
> Owner：RAG 团队
> Last Updated：2026-06-30

本目录用于存放各个功能模块的详细说明。每个功能应尽量独立成文，避免把多个模块混写在一个文件里。

## 1. 适用场景

适合写入这里的内容：

- 单个功能模块的行为规则
- 页面与接口之间的联动逻辑
- 状态变更规则
- 边界条件与异常处理

不适合写入这里的内容：

- 长期规划
- 项目背景
- 全局架构决策
- 发布记录

## 2. 建议命名

- `project-space-ingestion.md`
- `rag-retrieval.md`
- `chat-sessions.md`
- `agent-tools.md`
- `document-collections.md`
- `model-profiles.md`

## 3. 推荐做法

新增功能文档时，优先复制 `feature-template.md`。

若功能涉及**三层架构**中的层职责变化（如业务规则下沉至 `storage.py`、接口职责外溢），或**六边形架构**中的端口 / 适配器变化（如 `src/` 新增适配器），**必须**填写 `feature-template.md § 7 "架构落点"`，并按需关联 `../design/architecture-overview.md` 与对应 ADR。

## 现有功能文档

- `authentication.md`：B-140 API Key + JWT 认证中间件
- `agent-tooling-mcp-research.md`：B-117 MCP / 插件能力研究结论（不代表已实现 MCP 接入）
- `concurrent-indexing.md`：B-08 多工作区并发索引
- `fastapi-runtime.md`：B-139 FastAPI + Uvicorn 运行时迁移边界
- `frontend-engineering.md`：B-141 Vue 3 + Vite 前端工程化迁移边界
- `github-repo-import.md`：B-133 GitHub 仓库整体导入
- `graph-enhanced-retrieval.md`：B-126 知识图谱候选扩展接入检索流程
- `knowledge-base-management.md`：B-42 知识库辅助管理页
- `multi-model-comparison.md`：B-135 多模型并排对比
- `notion-obsidian-sync.md`：B-137 Notion / Obsidian 本地导出同步
- `openapi-swagger-docs.md`：B-136 OpenAPI / Swagger 接口文档
- `ops-maintenance.md`：B-06 本地维护脚本与索引重建管理入口
- `project-space-ingestion.md`：项目空间与摄入流程（扫描、增量、删除清理）
- `qdrant-vector-store.md`：B-134 Qdrant 本地向量存储替换 SQLite 全扫描
- `result-export.md`：B-07 生成结果导出为 Markdown / PDF
- `team-workspace-research.md`：B-118 多用户 / 团队空间研究结论（不代表已实现多用户或团队空间）
