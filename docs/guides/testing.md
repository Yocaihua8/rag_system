# 测试指南

> 状态：Active
> Owner：RAG 团队
> Last Updated：2026-08-01
> Scope：后端、前端、E2E、Docker、桌面、插件和文档验证
> Related：`setup.md`、`../design/api-spec.md`、`../features/desktop-app.md`

## 1. 基础矩阵

```powershell
.\.venv\Scripts\python.exe -m pytest tests/backend tests/integration tests/repository -q
npm run frontend:test
npm run frontend:build
npm run frontend:e2e
git diff --check
```

E2E 使用 4173 前端和隔离的 18765 后端，覆盖真实跨域导入、问答/SSE、学习计划和 Obsidian 用户侧流程。

## 2. 关键契约

| 改动 | 至少验证 |
|------|----------|
| FastAPI/CORS | 根路由 404、允许/拒绝 Origin、OPTIONS、认证头、SSE |
| API/领域 | 对应后端和集成测试；方法、字段、错误保持兼容 |
| 存储 | 当前 Schema、迁移、CRUD 与 v2 数据代际 |
| 前端 API | `fetch` 与 `EventSource` 都断言绝对 API URL |
| 前端页面 | 相关 Vitest、构建和 Playwright 主流程 |
| 仓库/文档 | `tests/repository/`、根 allowlist、源码派生契约、链接与占位符 |

## 3. 依赖审计

```powershell
npm audit --audit-level=high
.\.venv\Scripts\pip-audit.exe -r backend/requirements/base.txt --progress-spinner off
npm --prefix integrations/obsidian-plugin audit --audit-level=high
```

生产 Python 审计使用 `base.txt`；`dev.txt` 还包含测试和打包工具，不能代替生产依赖范围。只记录本次实际输出。

## 4. Docker

```powershell
docker compose --project-directory ops/docker -f ops/docker/compose.yaml config
docker compose --project-directory ops/docker -f ops/docker/compose.yaml build
ops\docker\start.ps1 -NoOpen
docker compose --project-directory ops/docker -f ops/docker/compose.yaml ps
ops\docker\stop.ps1
```

两个服务各自健康后，从 4173 页面完成对 8765 API 的真实 REST/SSE 冒烟。停止时不传 `-RemoveVolumes`，除非用户明确授权删除准确 volume。

## 5. 桌面

```powershell
.\.venv\Scripts\python.exe -m pytest tests/repository -k tauri -q
cargo check --manifest-path src-tauri/Cargo.toml
npm run desktop:build:windows
```

结构测试、Cargo、sidecar、bundle 和安装后动态连通性是不同门禁；目标平台结果不能互相替代。

## 6. Obsidian 插件

插件在自身目录独立并串行验证：

```powershell
Push-Location integrations/obsidian-plugin
npm test
npm run typecheck
npm run build
Pop-Location
```

## 7. 文档

```powershell
pwsh -NoProfile -File scripts/check-placeholders.ps1
pwsh -NoProfile -File scripts/check-doc-links.ps1
.\.venv\Scripts\python.exe scripts/check_docs_consistency.py
```

文档门禁还应检查 API 路径/操作数量、SQLite 表与关键字段、包/脚本命令、源码内文档路径、最近一级索引引用、旧目录引用和活动文档占位符。

## 8. CI 覆盖边界

当前 GitHub Actions 会运行 npm audit、前端构建与单测、Python 依赖审计、后端/集成/仓库测试、文档一致性和 Playwright E2E。默认 CI **不运行** Docker 镜像/健康检查、Cargo/Tauri bundle 或 Obsidian 插件 test/typecheck/build；发布前必须另外执行并记录这些门禁。

## 9. 记录要求

只记录实际运行的命令、commit、环境、通过/失败数量和未覆盖边界。未运行、被环境阻断或只完成静态检查时，不得写成完整通过。
