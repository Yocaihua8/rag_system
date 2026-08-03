# v3 Artifact 受控导出合同

> 状态：Active
> Owner：RAG 团队
> Last Updated：2026-08-03
> Scope：将已完成 v3 Artifact 写入受管 v3 导出目录的两阶段确认
> Related：`agent-runtime-and-tool-contract.md`、`permission-matrix.md`、`../features/agent-tasks-and-runs.md`

## 1. 两阶段 HTTP 合同

| 方法 | 路径 | 语义 |
|------|------|------|
| GET | `/api/v3/artifacts/{artifact_id}/export-preview` | 仅读取 ready Artifact，返回名称、hash、版本、大小和建议相对文件名；不创建文件或目录 |
| POST | `/api/v3/artifacts/{artifact_id}/export-confirm` | 用户明确确认后，核对 `expected_checksum` 与 `expected_version`，将固定快照独占写入受管 v3 导出目录 |

确认请求必须携带 `Idempotency-Key`。文件目标不接受调用方绝对路径或相对路径输入；服务端根据 Artifact ID、类型和受控扩展名生成文件名，并仅写入 `<KI_DATA_ROOT>/artifacts/exports/`。HTTP 响应只返回相对 `content_ref`、hash、大小和状态，不返回绝对目录。

## 2. 保护与状态

- 仅 `status=ready` 的 Artifact 可预览或确认导出；已导出、failed、draft 或版本/hash 变化时 fail closed。
- 预览不能构成授权。确认由 React 明确展示目标、不会修改的范围和不可自动撤销边界后发起；取消不写入任何状态或文件。
- 确认时把 Artifact 状态转为 `exported`、写入 `content_ref` 与 `exported_at`；已处理失败会清理本次创建的导出文件并保持原 Artifact 可读状态。
- 导出不读取项目根、Sources/Documents 正文、v2 数据根或环境凭据；只序列化 Artifact 已保存内容。

## 3. 不在范围

本合同不复用已完成 Run 的 Approval 行来伪造新的等待状态，也不开放任意本地路径、覆盖写、ZIP/PDF、多文件导出、浏览器下载、Obsidian 发布或外部网络写入。后续若把导出建模为工作流节点，必须单独增加新的 Run/Step/Approval 生命周期合同。
