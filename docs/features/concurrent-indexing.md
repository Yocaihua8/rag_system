# 多工作区并发索引

> 状态：Draft
> Owner：RAG 团队
> Last Updated：2026-06-29
> Scope：B-08 进程内轻量队列，支持跨项目摄入并发与同项目串行保护
> Related：docs/design/architecture-overview.md, docs/design/api-spec.md, docs/design/import-batches-design.md

## 1. 背景

Web MVP 当前导入入口直接在请求路径内执行目录扫描、文档入库、分块和向量同步。资料库页一次只能等待当前导入请求结束，且 FastAPI `/api/*` 兼容分发会同步执行业务逻辑。

B-08 目标是在不引入外部消息队列、不修改 SQLite schema 的前提下，补齐本地单进程内的轻量并发索引能力。

## 2. 第一片范围

- 跨项目空间的导入任务可以在进程内并发执行。
- 同一项目空间的导入任务必须串行，避免目录同步删除清理与其他写入互相覆盖。
- 保留既有 `/api/import*` 同步响应契约，导入完成后仍返回 `result / batch / documents`。
- 导入批次历史继续记录完成态结果；第一片不新增持久化 job 表。

## 3. 非目标

- 不新增外部消息队列、后台服务或多进程 worker。
- 不修改 SQLite 表结构。
- 不提供重启后恢复排队任务。
- 不提供批次取消、重试、回滚或跨项目批次总览。
- 不改变 Agent 工具权限。

## 4. 验收要点

- 同一 `project_id` 的两个目录同步请求不会同时进入实际导入执行段。
- 不同 `project_id` 的目录同步请求可在不同线程中重叠执行。
- FastAPI `/api/*` 兼容分发不在事件循环中直接执行同步业务逻辑。
