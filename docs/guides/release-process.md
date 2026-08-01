# 发布流程

> 状态：Active
> Owner：RAG 团队
> Last Updated：2026-08-01
> Scope：Web、Docker、Tauri 和 Obsidian 插件发布门禁
> Related：`testing.md`、`../features/desktop-app.md`、`../../CHANGELOG.md`

## 1. 发布前

- 工作区无不明改动，目标 commit 与待发布分支一致。
- API、Schema、CORS、前端 API base、Docker、桌面和插件变化已同步文档。
- 相关测试、依赖审计和目标平台构建已在目标 commit 上实际运行；失败或未覆盖项明确记录。
- 用户数据、`.env`、Key、Token、数据库和临时产物未进入提交或制品。
- `CHANGELOG.md` 的 `[Unreleased]` 只含真实变更；应用、桌面和插件版本按实际范围对齐。
- 当前仓库没有 LICENSE；在许可证决策完成前，不得把源码公开准备态描述为已授权发布。

仓库不创建 readiness 快照。发布证据保存在 CI、PR、Release 和可复现命令输出中。

## 2. 发布候选门禁

基础矩阵见 [`testing.md`](testing.md)，并另外完成：

- Docker：双镜像构建、双健康检查和 4173 页面到 8765 API 的 REST/SSE 流程。
- Tauri：目标平台 Cargo、sidecar、bundle、安装、API/SSE 连通性和签名状态。
- Obsidian：独立 test/typecheck/build，以及配对、离线重放和发布冲突流程。
- 文档：链接、占位符、一致性、源码派生事实、已删除路径和根 allowlist。

GitHub Actions 默认不覆盖 Docker、Tauri 或 Obsidian 插件门禁；CI 绿色不能替代上述验证。Windows 结果不替代 macOS/Linux，历史制品不替代当前 commit。

## 3. 版本提交与外部动作

1. 把 `[Unreleased]` 迁为 `[vX.Y.Z] - YYYY-MM-DD`，只写实际完成内容。
2. 提交 `chore: release vX.Y.Z`。
3. 推送分支并走正常 PR/required checks。
4. 在正式合并 commit 创建签名或带注释 Tag。
5. 创建 GitHub Release，附制品、平台、签名状态、SHA-256 和未覆盖边界。

推送、PR、合并、Tag、Release 和公开发布都需要用户明确授权。

## 4. 回滚

- 保留当前数据并确认实际 `RAG_RUNTIME_DIR`；不要用源码回退自动替换数据库。
- 使用已知 Tag 在隔离环境重建前端、后端和目标平台包。
- API/Schema 兼容性未证明时，不复用现有数据库。
- 撤回 Release、移动/删除 Tag 或删除制品属于外部破坏性操作，必须单独授权。
