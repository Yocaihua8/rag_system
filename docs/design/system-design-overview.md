# 系统设计总览

> 状态：Active
> Owner：RAG 团队
> Last Updated：2026-08-01
> Scope：Knowledge Island 的系统组成、运行形态和主要数据流
> Related：`architecture-overview.md`、`api-spec.md`、`database-design.md`、`../adr/README.md`

Knowledge Island 由 Vue 表现层、FastAPI HTTP 适配层、Python 领域能力、SQLite/Qdrant 存储、Tauri 桌面壳和 Obsidian 插件组成。Web、桌面和 Docker 使用相同 HTTP API，不复制业务规则或数据库写入逻辑。

| 组成 | 主要职责 | 依赖边界 |
|------|----------|----------|
| Vue 应用 | 当前工作台、资料、Coach、学习计划和设置交互 | 仅通过绝对 HTTP/SSE URL 调用后端 |
| FastAPI | CORS、可选认证、参数校验、OpenAPI 和 SSE 适配 | 业务操作经 routes/domain/storage 完成 |
| 领域与存储 | 导入、检索、回答、Coach、发布队列和 SQLite 持久化 | SQLite 只由 `backend/storage/` 访问 |
| Tauri | 窗口、托盘、sidecar 生命周期和安装包 | 打包前端产物，sidecar 仅承载后端 |
| Obsidian 插件 | 增量 Markdown 事件和经确认的发布写回 | 仅连接本机 API，冲突时不覆盖文件 |
| Docker | 分别承载前端静态站点与后端 API | 两个镜像、两个健康检查，前端不代理 API |

详细依赖方向见 [`architecture-overview.md`](architecture-overview.md)。
