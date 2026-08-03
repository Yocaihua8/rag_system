# v3 Artifact 受控导出

> 状态：Active
> Owner：RAG 团队
> Last Updated：2026-08-03
> Scope：React v3 详细过程中的已完成 Artifact 导出
> Related：`../design/v3-artifact-export-contract.md`、`agent-tasks-and-runs.md`

## 1. 用户能力

用户可在 ready Artifact 的详细过程里先查看受管目标文件名、快照大小和不可自动撤销提示，再明确确认导出。导出成功后 Artifact 显示为已导出。

## 2. 约束

- 预览不写入文件或状态；确认必须回传预览给出的 `version` 与 `checksum` 并使用稳定幂等键。
- 服务端仅写入 `<KI_DATA_ROOT>/artifacts/exports/`，按 Artifact ID 生成 `.txt` 文件名；页面不接收、显示或保存绝对路径。
- 导出只序列化 Artifact 已保存内容，不读取项目根、Sources/Documents 正文、v2 数据或环境凭据。

## 3. 后续边界

不支持用户自选目录、覆盖写、浏览器下载、ZIP/PDF、多文件导出、Obsidian 发布或外部网络写入；这些能力需要独立的生命周期和安全合同。
