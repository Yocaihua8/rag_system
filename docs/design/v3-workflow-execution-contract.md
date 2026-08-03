# v3 受限工作流执行合同

> 状态：Proposed
> Owner：RAG 团队
> Last Updated：2026-08-03
> Scope：已发布 v3 工作流的首个受限执行切片
> Related：`agent-runtime-and-tool-contract.md`、`api-spec.md`、`../features/agent-tasks-and-runs.md`

## 1. 首段目标

首段只允许用户以新建 Task 的不可变用户消息为输入，启动已绑定到该项目的已发布工作流版本。Run 必须保存 `workflow_version_id`、版本号和 checksum 快照；后续绑定、草稿或发布变化不得改写已创建 Run。

## 2. 准入规则

- 仅执行 `trigger.manual`、`project.analyze`、`artifact.create` 与 `agent.respond` 四类已有执行器节点，且图必须通过既有 DAG 校验并只有一个手动触发器和一个终端。
- `project.analyze` 仅允许现有 `sources` 分析，不读取未绑定路径、正文或 v2 数据；`artifact.create` 仅生成受控 SQLite Artifact；`agent.respond` 只基于该 Artifact 生成持久消息。
- `llm.*`、`source.*`、`insight.assess`、`learning.plan`、`approval.request`、`artifact.export`、`obsidian.publish`、分支和 join 节点均不在首段可执行白名单。命中时必须在创建 Run 前拒绝，而不是排队后失败或静默跳过。
- 每次创建仍要求 `Idempotency-Key` 与 `input_message_id`；写节点不因本切片开放。现有 Artifact 导出继续使用独立预览/确认合同，不成为工作流节点。

## 3. 调用与状态边界

调用方必须显式提交已发布 `workflow_version_id`，服务端验证它属于已绑定项目、Definition active、Binding enabled 且版本为 published。绑定不存在、已禁用、版本不匹配或图不在白名单时返回明确冲突/校验错误。

首段不做自动选择默认工作流、不复用旧 Run、不从浏览器状态推断发布版本，也不把工作流编辑界面提前写成可执行。React 只在服务端返回可执行绑定后显示启动入口。

## 4. 不在范围

本合同不开放通用自然语言规划、LLM/provider 调用、资料正文检索、持久洞察、审批等待后的写节点、用户自选目录、外部连接器、并行/分支图或正式 Vue/Tauri/Docker 入口切换。
