# 测试指南

> 状态：Active
> Owner：RAG 团队
> Last Updated：2026-08-01
> Scope：后端、前端、E2E、Docker、Tauri、插件和文档验证
> Related：`setup.md`、`../architecture/backend/api.md`、`../integrations/desktop.md`

## 1. 基础矩阵

```powershell
# Python
.\.venv\Scripts\python.exe -m pytest tests/backend tests/integration tests/repository -q

# 前端
npm run frontend:test
npm run frontend:build
npm run frontend:e2e

# 最终文本检查
git diff --check
```

E2E 用例位于 `tests/e2e/`，同时启动 `4173` 前端和隔离的 `18765` 后端，必须覆盖真实跨域导入、问答/SSE、学习计划和 Obsidian 用户侧流程。

## 2. 关键契约

| 改动 | 至少验证 |
|------|----------|
| FastAPI/CORS | 根路由 404、允许/拒绝 Origin、OPTIONS、认证头、SSE |
| API/领域 | 对应 `tests/backend/` 与 `tests/integration/`；方法、字段和错误保持兼容 |
| 存储 | Schema 结构、迁移、CRUD 与 v2 数据代际；不得用空库单测替代迁移路径 |
| 前端 API | 单测断言绝对 API URL，包含 `fetch` 与 `EventSource` |
| 前端页面 | Vitest、构建、相关 Playwright 主流程 |
| 仓库结构 | `tests/repository/`、根 allowlist、已删除路径引用和文档门禁 |

## 3. 依赖审计

```powershell
npm audit --audit-level=high
.\.venv\Scripts\pip-audit.exe -r backend/requirements/dev.txt --progress-spinner off
```

插件在自身目录独立执行 `npm audit --audit-level=high`。只引用本次实际输出，不复用旧发布快照的数字。

## 4. Docker

```powershell
docker compose --project-directory ops/docker -f ops/docker/compose.yaml config
docker compose --project-directory ops/docker -f ops/docker/compose.yaml build
ops\docker\start.ps1
docker compose --project-directory ops/docker -f ops/docker/compose.yaml ps
ops\docker\stop.ps1
```

验证两个服务各自健康，并从 `http://127.0.0.1:4173` 的页面访问 `http://127.0.0.1:8765` API。停止时不要添加 `-v`，除非明确授权删除 volume 数据。

## 5. Tauri

```powershell
.\.venv\Scripts\python.exe -m pytest tests/repository -k tauri -q
cargo check --manifest-path src-tauri/Cargo.toml
npm run desktop:build:windows
```

按需追加 sidecar 独立构建和安装后动态主流程。不同平台结果不能互相替代；未签名状态必须如实记录。

## 6. Obsidian 插件

插件验证必须串行：

```powershell
npm --prefix integrations/obsidian-plugin test
npm --prefix integrations/obsidian-plugin run typecheck
npm --prefix integrations/obsidian-plugin run build
```

## 7. 文档

```powershell
pwsh -NoProfile -File tools/docs/check-placeholders.ps1
pwsh -NoProfile -File tools/docs/check-doc-links.ps1
.\.venv\Scripts\python.exe tools/docs/check_docs_consistency.py
```

必须确认活动文件不引用已删除的历史/归档目录、旧文档分类或旧根命令。

## 8. 结果记录

只记录实际运行的命令、commit、环境、通过/失败数量和未覆盖边界。命令未运行、被环境阻断或只完成静态检查时，不得写成完整通过。
