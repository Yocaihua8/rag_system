# 技术迁移状态与启用规则

> 状态：Active
> Owner：RAG 团队
> Last Updated：2026-07-30
> Scope：Knowledge Island 已完成技术迁移的事实边界，以及未来迁移任务的建档要求
> Related：`migration-guide-template.md`、`../design/architecture-overview.md`、`../design/database-design.md`、`../design/risk-register.md`、`../features/desktop-packaging.md`、`../BACKLOG.md`

当前没有活动中的技术迁移计划。本文件不虚构目标版本、排期或工时；它只记录已经完成并归档的迁移事实，以及未来启动迁移时必须遵循的流程。

历史迁移已完成或归档：

- B-139 后端入口迁移到 FastAPI + Uvicorn。
- B-141 / B-142 完成主要 Vue 3 + Vite Web UI 迁移。
- B-143 移除 legacy static fallback。
- B-145 建立 Tauri 2 Windows 打包验证链路。
- B-147 将旧 PySide6 / 六边形实现归档到 `archive/src-desktop-legacy/`，不再作为当前入口。
- B-155 将前端生产构建输出统一到 `backend/static_dist/`。
- B-161 将 v2 默认数据代际隔离到 `runtime/v2/`，不自动迁移或覆盖 1.x 数据。

`docs/release/MIGRATION_STATUS.md` 和 `docs/architecture/` 中的旧目录、旧边界描述仅是历史记录，不是当前实现规范。

## 1. 当前系统盘点

| 维度 | 当前状态 | 事实来源 / 备注 |
|------|----------|-----------------|
| 后端 | Python 3.10+、FastAPI、Uvicorn | `app.py` → `backend.api.server.run_server()` |
| 前端 | Vue 3 + Vite，根目录 `package.json` 管理依赖 | 生产构建输出到 `backend/static_dist/` |
| 桌面 | Tauri 2 + PyInstaller sidecar | Windows v2.0.0 NSIS 已发布但未签名；macOS / Linux v2 原生包未验证 |
| 数据 | SQLite 为唯一持久化入口，默认 `runtime/v2/app.db`；可选 Qdrant local | 1.x 数据保留且不自动迁移 |
| 当前关键模块 | `backend/api/`、`backend/routes/`、`backend/domain/`、`backend/storage/`、`frontend/`、`src-tauri/` | 旧 PySide6 只保留在 archive |
| 外部依赖 | 可选 LLM / Embedding Provider、可选 Ollama、可选 Qdrant local、Obsidian Bridge | 各集成有独立配置与安全边界 |
| 活动迁移 | N/A | 当前未发现已批准、处于 Active / Interrupted 状态的技术迁移 plan |

## 2. 当前目标方案

当前目标是维持已发布的 v2 架构，不进行新的技术栈替换。

| 维度 | 当前目标状态 | 原因 |
|------|--------------|------|
| 技术栈 | 保持 FastAPI + Vue 3 / Vite + Tauri 2 + SQLite | v2.0.0 已按该链路正式发布 |
| 架构边界 | API 编排、业务领域、存储入口分层；前端不承载业务规则 | 与 `AGENTS.md` 和架构文档一致 |
| 数据代际 | v2 只使用 `runtime/v2/` 或显式隔离的 `RAG_RUNTIME_DIR` | 防止误写 1.x 数据 |
| Legacy | `archive/src-desktop-legacy/` 只作历史参考 | 未经确认不得重新接入 |
| 新迁移目标 | N/A | 尚无已批准的迁移需求 |

## 3. 已完成组件映射

| 历史组件 / 边界 | 当前组件 / 边界 | 迁移结果 | 注意事项 |
|-----------------|-----------------|----------|----------|
| PySide6 / 六边形桌面入口 | FastAPI Web + Vue 前端 + Tauri 壳 | 已替换并归档 | archive 不承载新业务代码 |
| legacy static fallback | Vue/Vite 生产构建 `backend/static_dist/` | 已移除 | 不恢复双重前端入口 |
| 旧 Web / 路由组织 | `backend/api/` + `backend/routes/` | 已迁移 | 路由不得直接操作 SQLite |
| 多处数据路径 | v2 默认 `runtime/v2/app.db` 及派生目录 | 已隔离 | 旧数据不自动迁移、删除或覆盖 |
| 旧桌面打包链路 | Tauri 2 + Python sidecar | Windows 链路已落地 | macOS / Linux v2 原生包仍为未验证边界 |

## 4. 历史关键迁移点

| 迁移点 | 当前状态 | 遗留风险 | 现行处理 |
|--------|----------|----------|----------|
| 后端切换到 FastAPI / Uvicorn | 已完成 | 旧文档可能仍引用历史模块名 | 当前事实以 `backend/` 源码和 `docs/design/` 为准 |
| 前端切换到 Vue / Vite | 已完成 | 构建产物与源码职责混淆 | 只提交源码，不提交 `node_modules/` 或生产构建产物 |
| 桌面切换到 Tauri | Windows 已发布 | Windows 安装包未签名；其他平台 v2 未验证 | 保留发布说明边界，不宣称跨平台原生包已完成 |
| v2 数据代际隔离 | 已完成 | 把 `RAG_RUNTIME_DIR` 指向旧数据库会触发拒绝启动或污染风险 | 使用独立 v2 目录，旧数据按支持方式重新导入 |
| 运维备份路径 | 未完全对齐 | `ops/scripts/backup_db.sh` 默认仍指向旧 `runtime/webapp/knowledge_island.db` | 不把无参数脚本执行视为有效 v2 备份；另行建任务修复并验证恢复 |

## 5. 当前阶段计划

| 阶段 | 内容 | 开始时间 | 结束时间 | 验收标准 |
|------|------|----------|----------|----------|
| 当前活动迁移 | N/A | N/A | N/A | 当前无活动迁移 |
| 历史 v2 迁移 | 已完成并归档 | 见对应 BACKLOG、DevLog 和 readiness | 2026-07-30 正式发布 | `v2.0.0` Tag / Release 与发布证据已落地 |
| 未来迁移 | 尚未立项 | TBD | TBD | 必须按 § 10 建立独立迁移文档和 plan 后才能执行 |

## 6. 工时预估

当前无活动迁移，因此角色、工时和排期均为 N/A。未来迁移的工时必须基于实际影响范围评估，不能复用历史估算或在本文件预填数字。

## 7. 风险点

| 风险点 | 影响 | 触发信号 | 缓解措施 |
|--------|------|----------|----------|
| 将历史迁移文档当作当前架构 | 修改错误模块或恢复已退场入口 | 任务引用 `desktop/qt`、旧 `webapp/` 或 `backend/infra` 等历史路径 | 先以当前源码、`AGENTS.md` 和活动设计文档复核 |
| v2 指向 1.x 数据 | 启动拒绝或不可逆数据污染 | `RAG_RUNTIME_DIR` 指向含旧 schema 的非空目录 | 使用隔离 v2 目录，不自动迁移或覆盖 |
| 未建 plan 直接启动迁移 | 影响范围、回滚和文档回流不可追踪 | 出现框架替换、模块拆分或运行时升级改动但没有 B-ID / plan | 停止修改，按 § 10 建档并完成冲突扫描 |
| 误把发布完成等同于所有平台完成 | 对 macOS / Linux 或签名能力作错误承诺 | 文档宣称“全平台已发布”或“Windows 已签名” | 保留 v2.0.0 readiness 中的真实发布边界 |
| 备份脚本默认路径漂移 | 备份错误数据库，恢复时才发现数据缺失 | 无参数运行 `backup_db.sh` | 在脚本修复和恢复演练前禁止宣称其为安全 v2 备份 |

## 8. 回滚策略

当前没有活动迁移，因此没有待执行的迁移回滚步骤。

对于已完成的 v2 迁移：

| 项 | 当前边界 |
|----|----------|
| 源码回退 | 可从已知 Tag 建立隔离工作区重新构建；不要直接覆盖正在使用的工作区 |
| 数据回退 | 没有自动跨代回滚；1.x 与 v2 数据必须保持隔离 |
| 数据恢复 | 项目导出 / 恢复 API 不等同于整库灾备；运维备份脚本尚未完成 v2 默认路径与恢复演练 |
| 回滚触发条件 | 由具体未来迁移文档定义；当前为 N/A |
| 责任人 | 未来迁移 Owner；当前为 N/A |

## 9. 历史验证证据

- v2.0.0 正式发布状态以 `../release/V2_0_0_READINESS_2026-07-24.md` 和 `../../CHANGELOG.md` 为准。
- 当前架构与数据路径以 `../design/architecture-overview.md`、`../design/database-design.md` 和源码为准。
- Windows v2.0.0 原生构建已验证并发布未签名 NSIS。
- macOS / Linux v2 原生包未在本轮生成或验证。
- 历史迁移完成不代表未来框架、Schema 或依赖升级已经获得授权。

## 10. 未来迁移的启动规则

未来需要框架升级、UI 库替换、构建工具切换、模块拆分、运行时升级或数据迁移时：

1. 复制 `migration-guide-template.md` 为单独的实际迁移文档，命名需体现具体迁移对象。
2. 按 `AGENTS.md` 在 `docs/BACKLOG.md` 分配或关联 B-ID，并创建 `docs/plans/{B-ID}-{slug}.md`。
3. 在修改前完成活动 plan 冲突扫描，列出代码、接口、数据库、前端、测试、发布和文档影响。
4. 涉及数据库 Schema、公共 API、Agent 工具权限或 legacy 重新接入时，先取得用户确认。
5. 定义可执行的阶段、验收、回滚和数据保护方案；未知事项写 `TBD`，不从本历史状态文档复制结论。
6. 迁移完成后同步功能、设计、ADR、发布和 BACKLOG，并按 plan 生命周期清理实际 plan。
