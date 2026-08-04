# v3 资料事实报告合同

> 状态：Active
> Owner：RAG 团队
> Last Updated：2026-08-03
> Scope：不调用模型的持久化资料事实报告
> Related：`v3-sources-contract.md`、`v3-project-insights-contract.md`、`agent-runtime-and-tool-contract.md`

## 1. 触发与持久化

React 项目页仅在当前项目已有 `ready` 资料快照时显示“生成资料事实报告”。它按固定 `project.source-facts.v1` 创建 Task 和 Run，首条消息、Run、Steps、Artifact 与 Agent 回答均使用既有 v3 持久化模型；不创建新表，也不触碰 v2。

固定 Run 仍有四个步骤：`trigger.manual → project.analyze → artifact.create → agent.respond`。其中 `project.analyze` 的 `analysis_kind=persisted_source_facts` 只能调用 v3 Store 的持久 Documents 快照，不得重新读取项目根、读取符号链接、执行代码或调用模型/provider。

## 2. 报告内容与证据

报告 Artifact 类型为 `project_source_facts`，状态为 `ready`，正文为确定性 JSON。它包含：

- `source_snapshot`：来源数、文档数、总字节数与按 `relative_path:checksum` 聚合的 SHA-256 指纹；
- 每份已持久文档的非空行数，以及 `document_id / source_id / relative_path / checksum` 证据；
- 最多 20 个 Markdown 标题及其行号和同一文档证据。

报告不包含 Documents 的完整正文、绝对路径、项目根、令牌、模型推断、技术栈/质量评分、学习/职业结论或外部连接器数据。Markdown 标题是为定位资料结构保留的最小正文派生事实。

## 3. 快照与陈旧状态

Artifact metadata 保存 `source_snapshot_fingerprint` 与 `stale=false`。后续 Sources 扫描若使当前资料指纹发生变化，Store 只更新已有事实报告的 metadata：设为 `stale=true` 并记录 `stale_against_fingerprint`；报告正文、checksum、Task、Run 和原始证据都不被改写。

重复扫描未改变快照时不标记为过期。生成新报告会固定新的快照，旧报告继续保留供审计，不被覆盖或删除。

## 4. 不在范围

本合同不开放正文预览、全文检索、向量化、模型总结、用户编辑报告、自动重跑、导出审批变化、通用工作流图或正式 Vue/Tauri/Docker 入口切换。
