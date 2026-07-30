# 发布流程

> 状态：Active
> Owner：RAG 团队
> Last Updated：2026-07-30（补充本地等价 CI 例外与 Windows NSIS 候选证据）
> Scope：Knowledge Island 版本发布检查与步骤
> Related：docs/release/V1_0_0_READINESS_2026-07-01.md, docs/release/V2_0_0_READINESS_2026-07-24.md, docs/guides/testing.md, docs/guides/branch-conventions.md, CHANGELOG.md

## 1. 发布前检查

- [ ] 若发布 v1.0.0，先完成 `docs/release/V1_0_0_READINESS_2026-07-01.md` 的 go/no-go 门禁、自动化回归和手工主流程冒烟
- [ ] 若发布 v2.0.0，先复核 `docs/release/V2_0_0_READINESS_2026-07-24.md` 的本地候选证据，并为未执行的远端 CI、目标平台原生包、Tag 和 Release 单独补证
- [ ] **CI green**：面向 `main` 的最后一个 PR 的 `python-tests` 和 `frontend-e2e` 两个 status check 均通过；若 GitHub Actions 额度已用尽，只能按 §2.1 的一次性可审计例外处理，不得把本地结果标记为远端 green
- [ ] 主流程可运行：启动 `python app.py`，访问 `http://127.0.0.1:8765` 正常
- [ ] 健康检查通过：`GET /api/health` 返回 `{"status": "ok"}`
- [ ] 最小验收完成：导入目录成功 → 问答返回含来源的回答
- [ ] v2 主闭环完成：导入项目 → 分析 → 同步/流式问答 → 定向评估 → 覆盖/差距 → 编辑并确认学习计划 → Obsidian 预览/确认/插件结果回传
- [ ] 文档同步完成：`requirements/*` / `design/*` / `BACKLOG.md` 与实现一致
- [ ] `CHANGELOG.md` 已整理当前版本变更条目
- [ ] Docker 启动验证：`docker compose up --build -d` 服务启动正常（若有 Docker 变更）

## 2. CI 合并门禁

B-149 起，`.github/workflows/ci.yml` 定义两个必须通过的 status check：

| Status Check | 内容 |
|---|---|
| `python-tests` | Vue/Vite 构建（供 Web server 测试导入静态目录）+ pytest（`tests/test_backend` + `tests/test_webapp`）+ 文档一致性检查 |
| `frontend-e2e` | Vitest 前端单元测试 + Vue/Vite 构建（`npm run build`）+ Playwright E2E |

在 GitHub 仓库设置中为 `main` 分支启用 **Branch protection rule**，勾选 "Require status checks to pass before merging"，将上述两个 check 设为 Required，即可实现自动合并门禁。任一 check 失败，PR 无法合并。

### 2.1 GitHub Actions 额度耗尽时的可审计例外

GitHub-hosted CI 额度耗尽不等于 CI 已通过。仅在仓库负责人明确确认额度不足、当前候选无法获得 hosted runner 结果时，才可启用以下一次性例外：

1. 在 plan、readiness 和 PR 中记录额度阻塞、确认时间及“远端 status check 未执行”，不得使用 `CI green` 表述。
2. 固定待合并 commit SHA，确认工作区干净，并记录操作系统、Node、npm、Python、Rust 和原生工具链版本。Windows 路径若经过 Junction，同时记录入口路径和 `Resolve-Path` / Junction target 得到的真实路径。
3. 在同一候选提交上执行 `.github/workflows/ci.yml` 对应的完整本地矩阵：`npm ci`、npm / pip 安全审计、Python 全量测试、文档一致性、Vue 单测与构建、Obsidian 插件测试 / typecheck / build、Playwright；桌面发布还需执行目标平台原生构建。
4. 在 PR 与 readiness 中逐项记录命令、退出码、用例数量、产物路径 / 哈希和未覆盖边界，由发布负责人复核后明确批准例外。
5. 若 required checks 阻止合并，只能使用仓库已有的授权 bypass 完成此次合并并记录操作者、时间和原因；不得永久关闭或删除 `main` 的 required checks。
6. 额度恢复后立即恢复常规 hosted checks；本地例外不能追溯宣称 GitHub Actions 曾通过，也不能替代后续版本的正常门禁。

## 3. 发布步骤

1. 确认所有发布前检查通过（§1 的 CI green，或经发布负责人明确批准并完整留证的 §2.1 例外；v1.0.0 / v2.0.0 还需完成各自 readiness）
2. 更新 `CHANGELOG.md`，将 Unreleased 段改为具体版本号和日期
3. 在 `docs/devlog/` 下添加当日日志条目
4. 提交：`git commit -m "chore: release vX.Y.Z"`
5. 打 Tag：`git tag vX.Y.Z`
6. 若有桌面打包需求，执行 Tauri 打包链路（见 §5）

## 4. 回滚方案

- **回滚条件**：启动失败、导入或问答核心链路出现阻断性错误
- **回滚步骤**：`git checkout <上一个 tag>`，重新启动 `python app.py`
- **数据回滚**：2.0 发布前备份 `runtime/v2/` 或显式 `RAG_RUNTIME_DIR`；Docker 按实际 volume 备份。旧 `runtime/app.db`、`runtime/webapp/knowledge_island.db` 和旧向量目录不得被 2.0 回滚覆盖；当前无自动回滚或跨代迁移机制

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

2026-07-30 的 v2.0.0 本地候选已在 Windows 原生工具链上完成 `cargo check --manifest-path src-tauri/Cargo.toml` 与 `npm run tauri:build:windows`，生成：

- 文件：`src-tauri\target\release\bundle\nsis\Knowledge Island_2.0.0_x64-setup.exe`
- 大小：48,948,957 字节
- SHA-256：`BD68D8FD29C53231595E164867910425A5403809A80A933A891D8EF83878C98B`
- 签名状态：未签名，仅作为本地候选验证产物

该产物证明 Windows NSIS 构建链在本机可完成，不代表安装包已经上传或 v2.0.0 已正式发布。

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

## 7. 本地发布候选记录

| 版本 | 日期 | 状态 | 边界 |
|------|------|------|------|
| v2.0.0 | 2026-07-24 | 本地源码与自动化候选就绪 | 未创建 Tag、未推送远端、未合并 `main`、未创建 GitHub Release；本机缺少 MSVC `link.exe`，未生成 Windows installer，详见 v2 readiness |
| v2.0.0 | 2026-07-30 | 本地等价 CI 与 Windows NSIS 候选就绪 | GitHub Actions 额度已用尽，hosted checks 未执行；NSIS 未签名；PR、`main` 合并、`v2.0.0` Tag 和 GitHub Release 仍为 Pending |
