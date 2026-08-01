# 版本范围

> 状态：Active
> Owner：RAG 团队
> Last Updated：2026-08-01
> Scope：v2.0.0 发布后的维护边界与 1.x 兼容基线
> Related：`project-background-and-scope.md`、`functional-modules.md`、`../BACKLOG.md`、`../../CHANGELOG.md`

## 当前维护范围

- 当前发布基线为 v2.0.0，项目处于维护与增量迭代阶段。
- 默认入口是本地 Web 应用；Tauri 提供桌面承载，Obsidian 插件提供受控发布集成。
- 1.x 的项目导入、聊天和基础评估能力作为兼容基线保留，但旧 PySide6 桌面实现不再维护。
- HTTP API 字段、SQLite Schema 和 Agent 只读权限边界以当前源码、测试和 Accepted ADR 为准。

## 不在当前范围

- 多租户 SaaS、云端托管和面向公网的默认部署。
- 恢复旧 PySide6 桌面端或旧静态托管运行时。
- 未经验证的平台安装包、已知未接线前端控件和未来规划；这些内容只记录在 [`../BACKLOG.md`](../BACKLOG.md)。

版本发布事实进入 [`../../CHANGELOG.md`](../../CHANGELOG.md)，本文件不保存阶段验收快照。
