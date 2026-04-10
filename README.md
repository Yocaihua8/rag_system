# RAG System Monorepo

本仓库采用 monorepo 结构，当前主维护范围为 `backend`、`desktop`、`frontend` 三端，并将文档、运维与脚本分离。

## 目录导航

- `backend/`：后端代码（`app/core/infra/tests`）
- `desktop/`：桌面壳（`main.py` + `app/ui/services/resources`）
- `frontend/`：前端代码（本轮未做内部重构）
- `docs/architecture/`：架构与结构基线文档
- `docs/release/`：发布与迁移状态文档
- `ops/`：运维说明与脚本
- `scripts/`：迁移守卫、启动检查、辅助脚本
- `runtime/`：运行时产物目录（数据库、缓存等）
- `archive/`：历史归档代码

## 快速启动

### Desktop

```powershell
py -3 desktop\main.py
```

### Backend（按模块导入验证）

```powershell
py -3 -c "import backend.app.main"
```

## 迁移说明

- 结构基线：`docs/architecture/STRUCTURE_BASELINE.md`
- 迁移状态：`docs/release/MIGRATION_STATUS.md`
- 发布检查：`docs/release/NON_TECH_RELEASE_CHECKLIST.md`
