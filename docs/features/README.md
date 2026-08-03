# 功能规格索引

> 状态：Active
> Owner：RAG 团队
> Last Updated：2026-08-03
> Scope：当前用户能力、兼容能力与可达边界
> Related：`../requirements/functional-modules.md`、`../design/api-spec.md`、`../BACKLOG.md`

本目录按用户可感知能力组织，一份文档只描述一个能力。后端存在接口、源码中保留组件或测试覆盖，并不自动代表当前主界面已经接通。

v3 目标规格在实现前标记为 `Proposed`，不得与当前可达能力混写。

| 用户能力 | 规格 | 当前入口 |
|----------|------|----------|
| 项目资料导入 | [`project-space-ingestion.md`](project-space-ingestion.md) | 资料弹窗；部分高级入口只在未挂载视图中保留 |
| 资料浏览与分组 | [`knowledge-base-management.md`](knowledge-base-management.md) | 资料弹窗；集合写操作只在未挂载视图中保留 |
| 检索与有来源问答 | [`retrieval-and-question-answering.md`](retrieval-and-question-answering.md) | 教练工作台 |
| 对话分支 | [`chat-branching.md`](chat-branching.md) | 教练工作台 |
| 项目知识教练与逐点学习 | [`project-knowledge-coach.md`](project-knowledge-coach.md) | 教练、学习地图、学习计划及学习覆盖层 |
| 首次运行引导 | [`first-run-wizard.md`](first-run-wizard.md) | 教练工作台首次状态 |
| 多模型比较 | [`multi-model-comparison.md`](multi-model-comparison.md) | 教练工作台高级区域 |
| 模型配置（v2） | [`model-profile-settings.md`](model-profile-settings.md) | Vue 设置页 |
| Prompt 预设 | [`prompt-preset-settings.md`](prompt-preset-settings.md) | 设置页 |
| GitHub 仓库导入 | [`github-integration.md`](github-integration.md) | 资料弹窗 |
| Obsidian 同步与发布 | [`obsidian-integration.md`](obsidian-integration.md) | 资料、设置、学习计划与桌面插件 |
| 桌面应用 | [`desktop-app.md`](desktop-app.md) | Tauri 桌面包 |
| 结果导出 | [`result-export.md`](result-export.md) | 仅 API，主界面无导出按钮 |
| 可选 API 认证 | [`authentication.md`](authentication.md) | 后端部署配置；当前 Vue/SSE 未接凭证 |

## v3 目标规格

| 能力 | 规格 | 当前状态 |
|------|------|----------|
| Agent 任务、持久运行、审批与产物 | [`agent-tasks-and-runs.md`](agent-tasks-and-runs.md) | Proposed；后端实施中逐项校准 |
| 项目资料（Sources） | [`project-sources.md`](project-sources.md) | 项目根扫描已接入平行 React；外部资料和正文预览仍未实现 |
| 项目洞察（Project Insights） | [`project-insights.md`](project-insights.md) | Active；当前可查看基于已扫描 v3 文档元数据的资料快照概览 |
| 模型配置 | [`model-profile-settings-v3.md`](model-profile-settings-v3.md) | Active；平行 React 可管理独立 v3 Profile 元数据与默认选择 |
| Artifact 受控导出 | [`artifact-export-v3.md`](artifact-export-v3.md) | Active；ready Artifact 可预览并确认写入受管 v3 导出目录 |

状态用语：

- **当前可达**：从 `frontend/src/App.vue` 挂载的主入口可以完成。
- **部分接线**：界面可见但输入、状态或后续动作没有形成完整闭环。
- **源码保留但不可达**：后端或组件仍存在，但当前主导航没有挂载。
- **未实现**：不写入功能规格，统一记录在 [`../BACKLOG.md`](../BACKLOG.md)。

新功能规格使用 [`feature-template.md`](feature-template.md)。
