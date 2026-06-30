# 发布流程

> 状态：Active
> Owner：RAG 团队
> Last Updated：2026-06-30（补充 Tauri 原生打包手动验证 workflow）
> Scope：Knowledge Island 版本发布检查与步骤
> Related：docs/guides/testing.md, docs/guides/branch-conventions.md, CHANGELOG.md

## 1. 发布前检查

- [ ] **CI green**：面向 `main` 的最后一个 PR 的 `python-tests` 和 `frontend-e2e` 两个 status check 均通过（见 §2）
- [ ] 主流程可运行：启动 `python app.py`，访问 `http://127.0.0.1:8765` 正常
- [ ] 健康检查通过：`GET /api/health` 返回 `{"status": "ok"}`
- [ ] 最小验收完成：导入目录成功 → 问答返回含来源的回答
- [ ] 文档同步完成：`requirements/*` / `design/*` / `BACKLOG.md` 与实现一致
- [ ] `CHANGELOG.md` 已整理当前版本变更条目
- [ ] Docker 启动验证：`docker compose up --build -d` 服务启动正常（若有 Docker 变更）

## 2. CI 合并门禁

B-149 起，`.github/workflows/ci.yml` 定义两个必须通过的 status check：

| Status Check | 内容 |
|---|---|
| `python-tests` | pytest（`tests/test_backend` + `tests/test_webapp`）+ 文档一致性检查 |
| `frontend-e2e` | Vue/Vite 构建（`npm run build`）+ Playwright E2E |

在 GitHub 仓库设置中为 `main` 分支启用 **Branch protection rule**，勾选 "Require status checks to pass before merging"，将上述两个 check 设为 Required，即可实现自动合并门禁。任一 check 失败，PR 无法合并。

## 3. 发布步骤

1. 确认所有发布前检查通过（§1 CI green 为首项）
2. 更新 `CHANGELOG.md`，将 Unreleased 段改为具体版本号和日期
3. 在 `docs/devlog/` 下添加当日日志条目
4. 提交：`git commit -m "chore: release vX.Y.Z"`
5. 打 Tag：`git tag vX.Y.Z`
6. 若有桌面打包需求，执行 Tauri 打包链路（见 §5）

## 4. 回滚方案

- **回滚条件**：启动失败、导入或问答核心链路出现阻断性错误
- **回滚步骤**：`git checkout <上一个 tag>`，重新启动 `python app.py`
- **数据回滚**：SQLite 数据库文件（`runtime/docker/knowledge.db`）可手动备份和替换；无自动回滚机制

## 5. 桌面打包（可选）

桌面发行走 **Tauri 桌面壳 + PyInstaller sidecar** 链路，详见 `docs/features/desktop-packaging.md`。前置：目标平台本机已安装 Node.js / npm、Python 依赖、`requirements-dev.txt`、Rust / Cargo / rustup，并可用 `npx tauri info` 确认环境缺口。

### 4.1 Windows NSIS

```powershell
# 1. 生成 Vue/Vite 生产构建产物
npm run build

# 2. 用 PyInstaller 打包 app.py 为后端 sidecar，并复制到 src-tauri/binaries/
powershell -ExecutionPolicy Bypass -File scripts\build-backend-sidecar.ps1

# 3. 构建 Windows 桌面包（内部会先确保 sidecar 已生成）
npm run tauri:build:windows
```

输出：`src-tauri\target\release\bundle\nsis\Knowledge Island_<version>_x64-setup.exe`（NSIS installer）。

### 4.2 macOS `.dmg`

macOS 原生桌面包需要在 macOS 本机执行：

```bash
# 1. 安装依赖后生成 Vue/Vite 生产构建产物和 Unix sidecar
bash scripts/build-backend-sidecar.sh

# 2. 构建 macOS dmg 包（内部会先确保 Unix sidecar 已生成）
npm run tauri:build:macos
```

输出：`src-tauri/target/release/bundle/dmg/*.dmg`。

### 4.3 Linux `.AppImage`

Linux 原生桌面包需要在 Linux 本机执行：

```bash
# 1. 安装依赖后生成 Vue/Vite 生产构建产物和 Unix sidecar
bash scripts/build-backend-sidecar.sh

# 2. 构建 Linux AppImage 包（内部会先确保 Unix sidecar 已生成）
npm run tauri:build:linux
```

输出：`src-tauri/target/release/bundle/appimage/*.AppImage`。

> 本仓库当前不从 Windows 交叉生成 macOS `.dmg` / Linux `.AppImage`。跨平台“一键启动”仍由 Docker（`docker compose up`）覆盖；原生桌面包用于需要系统级桌面分发的场景。

没有本地 macOS / Linux 机器时，可在 GitHub Actions 手动触发 `Tauri Packaging` workflow（`.github/workflows/tauri-packaging.yml`），用 `macos-latest` / `ubuntu-latest` runner 生成并下载 `.dmg` / `.AppImage` 作为发布前桌面包验证证据。该 workflow 不替代 §2 的常规合并门禁。

## 6. 发布记录

| 版本 | 日期 | 说明 |
|------|------|------|
| v0.9.0 | 2026-05-25 | 文档集合分组 + 导入批次历史 + 模型 Profile 多配置 |
| v0.8.0 | 2026-05-23 | 多会话聊天 + 检索复盘 + Agent 工具面板 + 备份导出 |
| v0.7.0 | 2026-05-21 | Web MVP 首版：RAG 检索 + 问答 + 聊天记录 + Docker |
