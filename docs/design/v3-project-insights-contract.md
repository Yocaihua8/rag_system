# v3 Project Insights 合同

> 状态：Active
> Owner：RAG 团队
> Last Updated：2026-08-03
> Scope：v3 文档快照的只读、可追溯项目概览
> Related：`v3-sources-contract.md`、`agent-runtime-and-tool-contract.md`、`../features/project-insights.md`

## 1. 首段 HTTP 合同

| 方法 | 路径 | 成功 | 失败 |
|------|------|------|------|
| GET | `/api/v3/projects/{project_id}/insights/overview` | `200`，返回当前资料快照概览 | `404 project not found` |

响应 `ProjectInsightOverview` 包含：`project_id`、`status=ready|source_required`、`source_snapshot`、`file_types`、`manifest_paths` 和 `evidence`。`source_snapshot` 包含来源数、文档数、总大小与稳定 `fingerprint`；`evidence` 仅包含 `document_id / source_id / relative_path / checksum`。

## 2. 计算与安全边界

- 使用 Store 读取当前 v3 Documents 的元数据；不读取 `content`、`source_path`、v2 SQLite 或项目根。
- `fingerprint` 对按相对路径排序的 `relative_path:checksum` SHA-256 聚合；同一资料快照稳定，资料变化必然改变 hash。
- 文件类型按相对路径后缀归一化；常见 manifest 仅由文件名识别。结论必须可由 `evidence` 解析，不引入模型推断。
- 没有已索引 Documents 时返回 `status=source_required`：`document_count` 和 `total_bytes` 为零，类型、清单与证据数组为空；已登记但尚未产生文档的 Source 数仍如实计入 `source_count`。不以 HTTP 错误或虚构洞察掩盖资料缺口。
- 响应不包含正文、绝对路径、内部 source locator/config、令牌或错误栈。
