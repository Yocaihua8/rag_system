# B-161 项目分析、知识点与通用技能映射

> ⚠️ 创建此文件前，必须已完成以下操作（AI 自检）：
> - [x] `docs/BACKLOG.md` 中 B-161 状态为 `doing`
> - [x] B-161 说明列已填入本文件路径
> - [x] 关联功能文档和设计文档已按实际范围填写

> 状态：Active
> 创建时间：2026-07-23
> 创建方：Codex
> 关联 BACKLOG：B-161
> 关联功能文档：docs/features/project-knowledge-coach.md
> 关联设计文档：docs/design/architecture-overview.md, docs/design/database-design.md, docs/design/api-spec.md

## 1. 目标

建立 Knowledge Island 2.0 的独立运行数据根、项目分析运行、稳定知识点、来源和版本化通用技能映射，并通过新增 Coach API 提供有来源的项目概览。旧 1.x 数据与 API 保持不变且不迁移。

## 2. 前置条件

- B-160 已完成，ADR-008/ADR-009 为本任务边界
- 分支为 `feature/project-knowledge-coach-v2`
- 当前全量 Python 基线为 427 passed / 2 个既有静态断言失败，失败项在 B-165 收口

## 3. 任务拆解

- [x] 切换默认运行数据根到 `runtime/v2/`，新增 Coach 基础实体、schema 与存储方法
- [ ] 实现确定性项目分析器、稳定 ID、真实来源、技能树映射与来源陈旧判定
- [ ] 接入 Coach analyze/overview/knowledge-points/skills API，同步 OpenAPI、正式文档并完成回归

## 4. 影响范围

| 类型 | 路径 / 模块 | 变更方向 |
|------|------------|---------|
| 代码 | `backend/config/` | 默认运行路径切换到独立 v2 代际 |
| 代码 | `backend/domain/models.py`, `backend/domain/project_analysis.py` | 新增 Coach 基础实体与规则分析 |
| 代码 | `backend/storage/knowledge_store.py` | 新增项目分析、知识点、来源、技能树 schema 与读写 |
| 代码 | `backend/routes/coach.py`, `backend/routes/__init__.py` | 新增四个 Coach 基础接口 |
| 代码 | `backend/api/openapi_schema.py` | 新增公开 operation |
| 测试 | `tests/test_backend/`, `tests/test_webapp/` | 路径、存储、分析器和 API 契约回归 |
| 文档 | `docs/design/api-spec.md`, `docs/design/database-design.md`, `docs/features/project-knowledge-coach.md` | 将 B-161 已实现行为回流为当前事实 |

## 5. 依赖与冲突

### 5.1 依赖的其他 plan

| plan 文件 | 依赖原因 |
|-----------|---------|
| N/A | B-160 已完成并删除其 plan |

### 5.2 与现有 plan 的重叠

| 冲突 plan | 重叠范围（文件 / 模块 / 接口） | 解决方式 |
|-----------|-------------------------------|---------|
| N/A | N/A | N/A |

> 扫描 `docs/plans/` 与 `docs/superpowers/plans/` 后未发现其他 `Active` 或 `Interrupted` 任务 plan；`docs/plans/README.md` 的 `Active` 是规则文档状态。

## 6. 完成标准

- [ ] 功能行为符合 `docs/features/project-knowledge-coach.md` 的 B-161 业务规则
- [ ] B-161 相关单元、API、OpenAPI 和回归测试通过
- [ ] 相关文档已同步（见下方回流清单）
- [ ] BACKLOG B-161 状态已更新为 `done`

## 7. 回流清单

| 内容 | 目标文档 | 是否完成 |
|------|----------|----------|
| v2 默认路径与 Coach schema | `docs/design/database-design.md`, `docs/guides/setup.md` | [ ] |
| 项目分析、来源、技能映射行为 | `docs/features/project-knowledge-coach.md` | [ ] |
| Coach 基础 API | `docs/design/api-spec.md` | [ ] |

## 8. 执行记录

- 2026-07-23：冲突扫描无重叠；现有 `/api/assessment/*` 和 1.x 数据不在本任务中迁移或删除。
- 2026-07-23：默认 Web 数据库实际位于 `runtime/webapp/knowledge_island.db`，早期文档中的 `runtime/app.db` 不是当前启动入口；实现与验收同时保护两类旧路径。
- 2026-07-23：生产 `create_app` 在 DDL、回填和向量初始化前执行 v2 marker 校验；底层存储保留非严格兼容模式供既有 1.x 补列回归。
- 2026-07-23：Coach 分析、知识点、来源、技能树和映射六表已落地；来源删除后保留路径、哈希、摘录和定位快照。

## 9. 状态快照

- **最后更新**：2026-07-23
- **进度**：已完成 1 / 3 项
- **最新 commit**：`2cd0759` — docs: 启动项目分析与技能映射计划
- **代码状态**：`feature/project-knowledge-coach-v2`；v2 路径、代际保护与 Coach 基础存储待提交，分析器/API 并行改动未暂存
- **下一步**：实现确定性项目分析器、稳定 ID、真实来源、技能树映射与来源陈旧判定
- **续任务须知**：旧 `runtime/` 数据不得迁移、删除或覆盖；测试必须显式使用临时路径
