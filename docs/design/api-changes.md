# API 变更记录

> 状态：Active
> Owner：RAG 团队
> Last Updated：2026-07-30
> Scope：Knowledge Island 本地 HTTP API 的破坏性变更记录与迁移要求
> Related：`api-spec.md`、`architecture-overview.md`、`../guides/release-process.md`

当前项目未对外发布 HTTP API，未形成对外接口版本契约。

| 日期 | 变更 | 影响范围 | 风险 |
|------|------|---------|------|
| 2026-05-16 | 文档模型与用例接口扩展（Markdown 安全链路、增量删除） | `src/application` 与 `src/domain` 数据形态 | 行为兼容层通过 `Workspace` 兼容 |
