# 项目洞察（Project Insights）

> 状态：Active
> Owner：RAG 团队
> Last Updated：2026-08-03
> Scope：v3 项目资料快照的可追溯概览
> Related：`project-sources.md`、`agent-tasks-and-runs.md`、`../design/v3-project-insights-contract.md`

## 1. 用户能力

用户可以查看当前 v3 项目资料的概览，包括来源数、文件数、总大小、可识别文件类型、常见项目清单和资料快照 hash。每项文件证据只引用受管文档 ID 与相对路径，不显示正文或绝对目录。

## 2. 首段边界

- 概览只基于当前 v3 Sources/Documents 动态计算，不读取 v2 Coach、旧项目数据或文件系统。
- 没有已索引 Documents 时，服务端返回明确的 `source_required` 状态，不伪造技术栈、质量或健康评分。
- 首段不执行 LLM、不生成知识点、评估、学习计划或职业能力结论，也不持久化洞察运行。
- 后续持久化分析、来源搜索和评估必须以明确的资料快照 hash 作为输入，不能覆盖或重写已完成 Run/Artifact。

## 3. 资料事实报告

项目页已开放“生成资料事实报告”：仅当资料快照 ready 时，固定工作流会读取已持久化的 v3 Documents 内容，创建 Task、Run、Artifact 和可恢复的回答。报告记录逐文档非空行数、有限 Markdown 标题、证据和快照 hash；不会再次读取项目根、调用模型、生成评分或替代人工判断。

资料重新扫描并改变 hash 时，旧报告会保留正文和原始证据，但 metadata 标记为过期；新报告必须显式由用户再次触发。详细合同见 [`v3-source-fact-report-contract.md`](../design/v3-source-fact-report-contract.md)。

## 4. 当前实现状态

React 项目页已经通过 `GET /api/v3/projects/{project_id}/insights/overview` 展示当前扫描快照：未扫描时提示先扫描，已扫描时展示文件数、总大小、类型汇总和已识别清单。页面不合成评分或技术栈结论；响应 `evidence` 留给后续可追溯展示，当前不显示正文。持久资料事实报告按本文件第 3 节的独立固定工作流开放。
