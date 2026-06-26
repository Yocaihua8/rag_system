# B-143 Remove Legacy Static Fallback Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remove the legacy `webapp/static/` vanilla frontend fallback so the Web MVP serves only the Vue/Vite production build.

**Architecture:** Keep FastAPI, API routes, SQLite schema, and Vue source contracts unchanged. B-143 only changes the static frontend delivery boundary: `webapp/server.py` must mount `webapp/static_dist/` and fail clearly when the Vue build output is missing, instead of falling back to `webapp/static/`.

**Tech Stack:** FastAPI `StaticFiles`, Vue 3 + Vite build output, pytest, npm.

> 状态：Active
> 创建时间：2026-06-26
> 创建方：Codex
> 关联 BACKLOG：B-143
> 关联功能文档：docs/features/frontend-engineering.md
> 关联设计文档：docs/design/architecture-overview.md, docs/design/system-design-overview.md, docs/guides/setup.md, docs/guides/testing.md

## 1. 目标

完成 B-143 后，仓库不再保留或服务 legacy 原生静态前端：

- 删除 `webapp/static/` 下的 vanilla HTML/CSS/JS。
- `webapp/server.py` 只服务 `webapp/static_dist/`。
- Vue 构建产物缺失时，启动阶段给出明确错误，不再静默回退旧 UI。
- 删除 `tests/test_webapp/test_frontend_static.py` 中仅针对 legacy 静态源码的断言。
- 保留 Vue 源码契约、FastAPI、API、数据库和 Agent 只读权限不变。

## 2. 前置条件

- B-142 已完成，Vue 工作台已覆盖 SSE、取消、会话历史和消息管理。
- 当前工作区包含未提交的 B-142 改动；B-143 执行时应在当前状态上继续，不回滚这些改动。
- `docs/design/new-architecture-design.md` 当前为未跟踪文件，来源未确认；B-143 不修改它。
- 仓库规则存在冲突：`AGENTS.md § 9.4` 要求每个子任务 commit，`AGENTS.md § 8` 又要求未明确要求时不要自动提交。本计划执行时默认不自动提交，除非用户明确要求。

## 3. 任务拆解

- [x] 任务 1：写 B-143 红灯测试，锁定“只服务 `static_dist`、缺失构建不回退 legacy”的服务边界。
- [x] 任务 2：修改 `webapp/server.py`，移除 `STATIC_LEGACY_DIR` / `STATIC_DIR` / fallback 逻辑。
- [x] 任务 3：删除 `webapp/static/` legacy 原生前端文件。
- [ ] 任务 4：删除或替换 `tests/test_webapp/test_frontend_static.py`，确保 legacy 静态源码断言不再参与回归。
- [ ] 任务 5：同步正式文档，说明生产前端唯一来源是 Vue/Vite 构建产物。
- [ ] 任务 6：运行 B-143 验收命令，确认全量 Web MVP 测试和前端构建通过。

## 4. 影响范围

| 类型 | 路径 / 模块 | 变更方向 |
|------|------------|---------|
| 代码 | `webapp/server.py` | 移除 legacy 静态 fallback，只挂载 `webapp/static_dist/` |
| 代码 | `webapp/static/` | 删除 legacy 原生前端文件 |
| 测试 | `tests/test_webapp/test_frontend_build.py` | 更新 FastAPI 静态托管契约测试 |
| 测试 | `tests/test_webapp/test_frontend_static.py` | 删除 legacy 静态源码测试或迁移剩余价值到 Vue 测试 |
| 测试 | `tests/test_webapp/test_frontend_vue_app.py` | 如发现缺口，只补 Vue 源码契约断言 |
| 文档 | `docs/features/frontend-engineering.md` | 更新 B-143 后前端交付边界 |
| 文档 | `docs/design/architecture-overview.md` | 更新展示层和静态服务边界 |
| 文档 | `docs/design/system-design-overview.md` | 更新逻辑组成中的前端来源 |
| 文档 | `docs/guides/setup.md` | 更新本地启动前端构建要求 |
| 文档 | `docs/guides/testing.md` | 更新 B-143 后测试要求 |
| 文档 | `docs/BACKLOG.md` | 状态流转与完成记录 |

## 5. 依赖与冲突

### 5.1 依赖的其他 plan

| plan 文件 | 依赖原因 |
|-----------|---------|
| N/A | B-142 已完成并删除 plan；B-143 可开始 |

### 5.2 与现有 plan 的重叠

扫描到的历史 plan：

| 冲突 plan | 重叠范围（文件 / 模块 / 接口） | 解决方式 |
|-----------|-------------------------------|---------|
| `docs/superpowers/plans/2026-05-11-project-knowledge-base-ui-skeleton.md` | 旧 PySide6 桌面 UI，不覆盖 Web 静态服务 | 分区：B-143 只处理 Web MVP 静态前端 |
| `docs/superpowers/plans/2026-05-11-project-knowledge-points.md` | 后端知识点模型，不覆盖 Web 静态服务 | 分区：B-143 不改数据模型 |
| `docs/superpowers/plans/2026-05-16-knowledge-island-core-models.md` | legacy/core models，不覆盖 Web 静态服务 | 分区：B-143 不改 `src/` 或 schema |

## 6. 完成标准

- [ ] `webapp/server.py` 不再出现 `STATIC_LEGACY_DIR`、`STATIC_DIR` 或返回 `webapp/static/` 的 fallback。
- [ ] `webapp/static/` legacy 原生前端文件已删除。
- [ ] `tests/test_webapp/test_frontend_static.py` 已删除，或其剩余断言已迁移到 Vue 源码/构建测试。
- [ ] `tests/test_webapp/test_frontend_build.py` 覆盖 `static_dist` 存在时首页可服务、缺失时不回退 legacy。
- [ ] `npm run build` 通过。
- [ ] `.venv\Scripts\python.exe -m pytest tests/test_webapp -q` 通过。
- [ ] `git diff --check` 通过。
- [ ] 相关正式文档已同步。
- [ ] BACKLOG B-143 状态改为 `done`，本 plan 删除。

## 7. 回流清单

| 内容 | 目标文档 | 是否完成 |
|------|----------|----------|
| B-143 后生产前端唯一来源为 `webapp/static_dist/` | `docs/features/frontend-engineering.md` | [ ] |
| 展示层不再包含 legacy Vanilla SPA fallback | `docs/design/architecture-overview.md` | [ ] |
| 系统组成中的静态前端改为 Vue/Vite 构建产物 | `docs/design/system-design-overview.md` | [ ] |
| 本地启动前需先生成 Vue 构建产物 | `docs/guides/setup.md` | [ ] |
| 删除 legacy 静态测试后的验证命令 | `docs/guides/testing.md` | [ ] |
| B-143 完成记录 | `docs/BACKLOG.md` | [ ] |

## 8. 执行记录

- 2026-06-26：启动 B-143 文档与计划准备；确认当前工作区包含未提交 B-142 改动，本任务不回滚这些改动。
- 2026-06-26：确认 B-143 不改后端 API、SQLite schema、Agent 工具权限或 `src/` legacy 桌面代码。
- 2026-06-26：确认 `tests/test_webapp/test_frontend_static.py` 基本全部依赖 `webapp/static/`，实现阶段应整体删除或把少量仍有价值的断言迁移到 Vue 源码契约测试。
- 2026-06-26：任务 1 完成；`tests/test_webapp/test_frontend_build.py` 已新增缺失 Vue 构建时抛错和 server 源码无 legacy fallback 的红灯测试；`.venv\Scripts\python.exe -m pytest tests\test_webapp\test_frontend_build.py -q` 预期失败 2 项，分别指向现有 fallback 未抛 `RuntimeError` 和 `STATIC_LEGACY_DIR`/`STATIC_DIR` 仍存在。
- 2026-06-26：任务 2 完成；`webapp/server.py` 已移除 `STATIC_LEGACY_DIR`/`STATIC_DIR` 和 fallback 分支，`_frontend_static_dir()` 在 `static_dist/index.html` 缺失时抛出包含 `npm run build` 的 `RuntimeError`；`.venv\Scripts\python.exe -m pytest tests\test_webapp\test_frontend_build.py -q` 通过 5 项。
- 2026-06-26：任务 3 完成；已删除 `webapp/static/` 下 legacy 原生前端 HTML/CSS/JS 文件，PowerShell 确认剩余文件数为 0；`.venv\Scripts\python.exe -m pytest tests\test_webapp\test_frontend_build.py -q` 通过 5 项。

## 9. 状态快照

- **最后更新**：2026-06-26 18:44
- **进度**：已完成 3 / 6 项（见 § 3 勾选状态）
- **最新 commit**：待提交 — 任务 3 删除 legacy 原生静态文件
- **代码状态**：有未提交 B-142 改动；B-143 plan 已建档；未跟踪 `docs/design/new-architecture-design.md` 不属于本任务
- **下一步**：任务 4：删除或替换 `tests/test_webapp/test_frontend_static.py`
- **续任务须知**：任务 3 已删除 legacy 静态文件；下一步清理 legacy 静态源码断言，不触碰 Vue 源码、后端 API、数据库、`backend/` 或 `webapp/search.py`。

## 10. 实施细节草案

### 10.1 服务边界目标

`webapp/server.py` 目标形态：

```python
STATIC_DIST_DIR = WEBAPP_DIR / "static_dist"


def _frontend_static_dir() -> Path:
    if not (STATIC_DIST_DIR / "index.html").exists():
        raise RuntimeError("Vue build output missing. Run `npm run build` before starting Knowledge Island.")
    return STATIC_DIST_DIR
```

`create_app()` 继续使用：

```python
app.mount("/", StaticFiles(directory=_frontend_static_dir(), html=True), name="static")
```

### 10.2 测试目标

`tests/test_webapp/test_frontend_build.py` 应保留 `static_dist` 正常服务测试，并把 fallback 测试改为缺失构建时明确失败：

```python
def test_fastapi_requires_vite_build_output(tmp_path, monkeypatch):
    dist_dir = tmp_path / "missing_dist"
    monkeypatch.setattr(server, "STATIC_DIST_DIR", dist_dir, raising=False)

    with pytest.raises(RuntimeError, match="npm run build"):
        server.create_app(db_path=tmp_path / "app.db")
```

同时增加源码守卫：

```python
def test_fastapi_static_server_has_no_legacy_fallback():
    source = Path("webapp/server.py").read_text(encoding="utf-8")

    assert "STATIC_LEGACY_DIR" not in source
    assert "STATIC_DIR" not in source
    assert "webapp/static" not in source
```

### 10.3 验收命令

```powershell
.venv\Scripts\python.exe -m pytest tests\test_webapp\test_frontend_build.py -q
.venv\Scripts\python.exe -m pytest tests\test_webapp\test_frontend_vue_app.py -q
npm run build
.venv\Scripts\python.exe -m pytest tests\test_webapp -q
git diff --check
```
