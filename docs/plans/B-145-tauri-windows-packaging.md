# B-145 Tauri Windows Packaging Plan

> 状态：Active
> 创建时间：2026-06-28
> 创建方：Codex
> 关联 BACKLOG：B-145
> 关联功能文档：docs/features/desktop-packaging.md
> 关联设计文档：docs/design/new-architecture-design.md §23

## 1. 目标

执行 B-145：新增 Tauri 2 桌面壳与 Windows 打包验证链路，使 Knowledge Island 可以以 Tauri WebView 加载 Vue/Vite 生产构建产物，并以 PyInstaller sidecar 方式启动 FastAPI 后端。

## 2. 前置条件

- 已阅读 `AGENTS.md`
- 已阅读 `docs/design/new-architecture-design.md §23`
- 已确认 B-143、B-146、B-125 当前 BACKLOG 状态为 `done`
- 已通过 ctx7 查询 Tauri 2 sidecar / externalBin / tray 当前文档：`/websites/v2_tauri_app`
- PyInstaller 文档 ID 已通过 ctx7 确认：`/websites/pyinstaller_en_stable`

## 3. 任务拆解

每完成一项，立即执行：① 勾选此处 ② `git commit` 保存进度 ③ 更新 § 9 状态快照。

- [x] 任务 1：写 B-145 红灯测试，覆盖 Tauri 配置、Windows sidecar 脚本、npm 脚本和桌面打包文档入口
- [x] 任务 2：建立 `src-tauri/` Tauri 2 最小壳，包含 sidecar 声明、Vue 构建产物加载、Rust 入口和托盘/关闭隐藏逻辑
- [x] 任务 3：新增 Windows sidecar 打包脚本与 npm/Tauri 构建脚本，接入 PyInstaller 和目标 triple 文件名
- [x] 任务 4：补齐测试通过所需的静态校验与最小构建验证，不引入后端 API、数据库 schema 或 Vue 源码改动
- [ ] 任务 5：同步正式文档，覆盖 setup/testing/frontend/new architecture 中的桌面打包入口和限制
- [ ] 任务 6：运行 B-145 验证清单，关闭 BACKLOG 状态并删除本 plan

## 4. 影响范围

| 类型 | 路径 / 模块 | 变更方向 |
|------|-------------|----------|
| 代码 | `src-tauri/` | 新增 Tauri 2 桌面壳 |
| 代码 | `scripts/build-backend-sidecar.ps1` | 新增 Windows sidecar 打包脚本 |
| 配置 | `package.json` | 新增 Tauri / sidecar npm scripts |
| 配置 | `requirements-dev.txt` | 新增 PyInstaller 开发打包依赖 |
| 测试 | `tests/test_webapp/test_tauri_packaging.py` | 新增 B-145 静态/配置测试 |
| 文档 | `docs/features/desktop-packaging.md` | 新增桌面打包功能文档 |
| 文档 | `docs/guides/setup.md` | 补充桌面打包准备与命令 |
| 文档 | `docs/guides/testing.md` | 补充 B-145 验证命令 |
| 文档 | `docs/features/frontend-engineering.md` | 说明 Tauri 与 Vue 构建产物关系 |
| 文档 | `docs/design/new-architecture-design.md §23` | 对齐实际 Windows 打包脚本和构建产物路径 |
| 文档 | `docs/BACKLOG.md` | B-145 状态流转与 plan 路径 |

## 5. 依赖与冲突

### 5.1 依赖的其他 plan

| plan 文件 | 依赖原因 |
|-----------|----------|
| N/A | B-143、B-146、B-125 在 BACKLOG 中已为 `done`；本任务不依赖未完成 plan |

### 5.2 与现有 plan 的重叠

| 冲突 plan | 重叠范围（文件 / 模块 / 接口） | 解决方式 |
|-----------|-------------------------------|----------|
| `docs/superpowers/plans/2026-05-11-project-knowledge-base-ui-skeleton.md` | 旧 UI/知识库计划，不涉及 `src-tauri/`、sidecar 脚本或桌面打包 | N/A |
| `docs/superpowers/plans/2026-05-11-project-knowledge-points.md` | 旧项目知识点后端计划，主要涉及 `src/` legacy 层和 BACKLOG | N/A |
| `docs/superpowers/plans/2026-05-16-knowledge-island-core-models.md` | 旧核心模型计划，不涉及 Tauri 桌面壳 | N/A |

## 6. 完成标准

- [ ] 功能行为符合 `docs/features/desktop-packaging.md` 的 B-145 边界
- [ ] `tests/test_webapp/test_tauri_packaging.py` 通过
- [ ] `npm run build` 通过并生成 Vue/Vite 生产构建产物
- [ ] 可执行时运行 Tauri/Rust 静态检查或构建命令；若本机缺 Rust/Tauri 依赖，记录阻塞原因和本地验证方式
- [ ] 相关文档已同步（见下方"回流清单"）
- [ ] BACKLOG 条目 B-145 状态已更新为 `done`

## 7. 回流清单

| 内容 | 目标文档 | 是否完成 |
|------|----------|----------|
| Tauri Windows 打包入口和范围 | `docs/features/desktop-packaging.md` | [ ] |
| 本地安装/构建命令 | `docs/guides/setup.md` | [ ] |
| 测试与打包验证命令 | `docs/guides/testing.md` | [ ] |
| Vue 构建产物与 Tauri WebView 关系 | `docs/features/frontend-engineering.md` | [ ] |
| §23 实际脚本名称、Windows triple、构建产物路径 | `docs/design/new-architecture-design.md` | [ ] |

## 8. 执行记录

- 2026-06-28：创建 plan。冲突扫描未发现涉及 `src-tauri/`、Windows sidecar 脚本或桌面打包链路的 Active/Interrupted plan。当前工作区已有多处用户改动，提交时需窄范围 staging。
- 2026-06-28：ctx7 Tauri 2 文档确认 `bundle.externalBin`、`build.beforeBuildCommand`、`TrayIconBuilder` 仍是当前可用入口；本任务采用 Tauri MVP 0，不实现自动更新和 First-Run Wizard。
- 2026-06-28：任务 1 红灯测试已运行：`.venv\Scripts\python.exe -m pytest tests\test_webapp\test_tauri_packaging.py -q`，结果 5 failed，失败点符合预期，集中在缺少 Tauri 配置、Rust 入口、sidecar 脚本、npm scripts 和 setup/testing 文档入口。
- 2026-06-28：任务 2 新增 `src-tauri/` 最小壳后复跑 B-145 测试，结果 2 passed / 3 failed；已转绿部分为 Tauri 配置和 Rust 入口，剩余失败对应任务 3/5。
- 2026-06-28：任务 3 新增 Windows sidecar 脚本、Tauri npm scripts、`@tauri-apps/cli` 和 PyInstaller 开发依赖；复跑 B-145 测试结果 4 passed / 1 failed，剩余失败为正式文档入口。
- 2026-06-28：任务 4 验证结果：`npm run build` 通过；首次 `npx tauri --version` 因 npm optional dependency 未安装 `@tauri-apps/cli-win32-x64-msvc` 失败，执行 `npm install --include=optional` 后 `npx tauri --version` 通过（2.11.3）；`npx tauri info` 可读取配置并显示 WebView2/MSVC 可用、`frontendDist` 正确，阻塞项为本机未安装 `rustc`/`cargo`/`rustup`；`cargo check --manifest-path src-tauri\Cargo.toml` 因 `cargo` 不存在无法运行。

## 9. 状态快照

- **最后更新**：2026-06-28 14:21
- **进度**：已完成 3 / 6 项（见 § 3 勾选状态）
- **最新 commit**：`7db0c66` — feat: 接入 Windows sidecar 打包脚本
- **代码状态**：`main` 分支；工作区仍存在与 B-145 无关的未提交改动；B-145 测试剩余失败对应 setup/testing 文档入口
- **下一步**：任务 4：补齐测试通过所需的静态校验与最小构建验证，不引入后端 API、数据库 schema 或 Vue 源码改动
- **续任务须知**：不要修改后端 API、数据库 schema 或 `frontend/src/`；B-145 只覆盖 Windows 打包验证，不包含 B-148/B-149/B-150
