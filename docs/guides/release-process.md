# 发布流程

> 状态：Active
> Owner：RAG 团队
> Last Updated：2026-08-01
> Scope：Web、Docker、Tauri 与插件发布前后的当前流程
> Related：`testing.md`、`../integrations/desktop.md`、`../../CHANGELOG.md`

## 1. 发布前

- 工作区无不明改动，目标 commit 固定且与待发布分支一致。
- API、Schema、CORS、前端 API base、Docker、Tauri 和插件变更已同步文档。
- 完整相关测试、依赖审计和目标平台构建已实际运行；失败或未覆盖项如实记录。
- 用户数据、`.env`、Key、Token、数据库和临时产物未进入提交/制品。
- `CHANGELOG.md` 的 `[Unreleased]` 有真实变更；版本号与应用/桌面/插件清单按实际范围对齐。

仓库不再创建 readiness 快照。发布证据保存在 CI、PR、Release 和可复现命令输出中。

## 2. 验证

基础矩阵见 [`testing.md`](testing.md)。发布候选还需：

- Docker：双镜像、双健康检查和 4173→8765 浏览器主流程。
- Tauri：目标平台 `cargo check`、sidecar、bundle、安装、API/SSE 连通性；未签名状态明确标注。
- Obsidian：独立 test/typecheck/build 和受控发布冲突流程。
- 文档：链接、占位符、一致性、已删除路径和根 allowlist。

Windows 结果不替代 macOS/Linux；历史版本的产物不替代当前 commit。

## 3. 发布提交与 Tag

1. 把 `[Unreleased]` 迁为 `[vX.Y.Z] - YYYY-MM-DD`，只写实际完成内容。
2. 提交 `chore: release vX.Y.Z`。
3. 推送分支并走正常 PR/检查链路；禁止绕过 required checks。
4. 在正式合并 commit 上创建签名或带注释 Tag（按仓库当前权限）。
5. 创建 GitHub Release，附制品、平台、签名状态、SHA-256 和未覆盖边界。

这些外部动作只有在用户明确授权后执行。

## 4. 回滚

- 保留当前数据并确认实际运行目录；不要用源码回退自动替换数据库。
- 使用已知 Tag 在隔离环境重建前端、后端和目标平台包。
- API/Schema 兼容性未证明时，不复用现有数据库。
- 发布撤回、Tag 改动或 Release 删除属于外部破坏性操作，必须单独授权。
