# v3 文档内容迁移矩阵

> 状态：Active
> Owner：RAG 团队
> Last Updated：2026-08-02
> Scope：旧文档有效事实的吸收、归并、删除和历史回流规则
> Related：`../README.md`、`../features/README.md`、`../devlog/README.md`、`../../CHANGELOG.md`

## 1. 迁移原则

- 不直接运行 docs-template 初始化器，不复制示例项目、占位符或模板仓库状态文件。
- 先以当前源码、配置、Schema 和测试校准事实，再按需求、设计、功能、ADR、指南、BACKLOG、CHANGELOG 和 DevLog 的职责落位。
- 旧文档只有在有效事实已被目标文档吸收、所有索引和源码引用同步、文档门禁通过后才删除。
- 旧决策保留为 ADR 历史；被替代时标记 `Superseded`，不删除或改写当时背景。
- 过程性取舍和清理原因进入当日 DevLog；使用者可感知的完成事实进入 CHANGELOG。

## 2. 功能文档吸收矩阵

| 旧文档 | v3 目标职责 | 处理时机 |
|--------|-------------|----------|
| `chat-branching.md` | Agent 任务、消息和运行 | v3 任务 API 与 UI 闭环后归并删除 |
| `project-space-ingestion.md`、`knowledge-base-management.md`、`github-integration.md` | Projects、Sources 与 Connectors | v3 项目/资料接口和原型合同生效后归并删除 |
| `retrieval-and-question-answering.md` | Retrieval 与 Evidence | v3 检索和事件来源合同生效后归并删除 |
| `project-knowledge-coach.md` | Project Insights | 洞察 API 与新页面验收后归并；保留有效评估规则 |
| `result-export.md`、`obsidian-integration.md` | Actions、Approvals 与 Artifacts | 统一产物和审批链验收后归并；插件特有边界仍可独立保留 |
| `model-profile-settings.md`、`prompt-preset-settings.md`、`multi-model-comparison.md` | Models、Prompts 与 Compare | v3 Settings 和双模型合同验收后归并删除 |
| `authentication.md`、`desktop-app.md`、`first-run-wizard.md` | Desktop、Storage 与 Security | v3 sidecar、启动和认证边界验收后归并；平台专有事实保留 |

## 3. 现有任务处理

| 项目 | v3 处理 |
|------|---------|
| ISSUE-005 | 与 v3 无直接冲突，继续保留并独立处理 GitHub Action runtime |
| ISSUE-007 | 吸收到最终 Desktop 安装与跨平台验收，完成前保留 |
| ISSUE-008 | 由 React 页面替换和真实 API 联调吸收；旧 Vue 不再单独修复 |
| ISSUE-009 | 吸收到 v3 Retrieval 配置测试；不能在其他后端重构中顺带改变语义 |

删除 BACKLOG 项目前必须把仍未完成的验收要求转入新的 B-ID；不能因为旧 UI 即将删除就丢失真实缺口。

## 4. 不进入仓库的模板资产

- 模板工具状态文件和永久根级模板映射文件。
- `examples/`、`scaffold/`、commercial/team 专属文档和模板维护说明。
- 未替换的模板占位符、虚构命令、虚构接口或示例业务实体。
- readiness 快照、已验收 preview 归档和完成的执行 plan。

## 5. 删除门禁

每组旧文档删除前必须同时满足：

1. 目标文档状态为 Active，且内容由当前源码和测试校准。
2. 最近一级索引、Related、源码引用和测试引用已切换。
3. 当前实现与未来目标没有混写，未实现事项仍在 BACKLOG。
4. 占位符、链接和一致性检查全部通过。
5. 删除原因记录在当日 DevLog，使用者可见影响记录在 CHANGELOG。

本文件不是历史归档；全部迁移完成后可缩减为稳定的文档治理说明，但不能在尚有旧文档待吸收时删除。
