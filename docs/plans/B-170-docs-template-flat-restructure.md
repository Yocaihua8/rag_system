# B-170 docs-template 扁平化文档重构

> 状态：Active
> 创建时间：2026-08-01
> 创建方：Codex
> 关联 BACKLOG：B-170
> 关联功能文档：`docs/features/README.md`
> 关联设计文档：`docs/design/architecture-overview.md`

## 1. 目标

以 `E:/Dev/Projects/docs-template@6cbb9e0` 的 1.0.0 脚手架为职责标准，将当前文档重构为 `requirements`、`design`、`features`、`adr`、`guides`、`plans` 六个扁平一级目录。迁移过程中以当前源码、测试和配置为事实来源，回流仍有效的信息后删除旧专题目录，不保留兼容副本、DevLog、模板状态或模板映射。

## 2. 前置条件

- 基线为 `refactor/repository-structure@905e7c2`，工作区干净。
- 用户已明确批准删除旧文档目录和 `tools/docs/`，并批准新增 ADR-010 的新路径归档；不得借机修改 HTTP API、SQLite Schema、Agent 白名单或运行时行为。
- 模板参考骨架只在系统临时目录生成，不在当前仓库运行初始化器。

## 3. 任务拆解

每完成一项，立即执行：① 勾选此处 ② `git commit` 保存进度 ③ 更新 § 9 状态快照。

- [x] 创建分支、登记 B-170、完成冲突扫描并生成隔离模板参考骨架。
- [x] 建立标准扁平目录和索引，原子迁移活动 plan 与可直接映射的文档。
- [x] 重写 requirements、design 与 ADR 索引，校准 API、Schema、安全和状态事实。
- [ ] 重构功能规格与 guides，回流 Desktop、GitHub、Obsidian、Docker 和维护事实后删除旧专题目录。
- [ ] 更新根 README、AGENTS、CONTRIBUTING、CHANGELOG、文档脚本、CI 与仓库契约测试。
- [ ] 运行全部文档门禁和相关契约测试，确认无行为漂移，移除 B-170 并删除本 plan。

## 4. 影响范围

| 类型 | 路径 / 模块 | 变更方向 |
|------|-------------|----------|
| 文档 | `docs/product/`、`docs/architecture/`、`docs/integrations/`、`docs/operations/`、`docs/governance/` | 事实回流后删除 |
| 文档 | `docs/requirements/`、`docs/design/`、`docs/features/`、`docs/adr/`、`docs/guides/`、`docs/plans/` | 新建、迁移、重写 |
| 文档 | `README.md`、`AGENTS.md`、`CONTRIBUTING.md`、`CHANGELOG.md` | 同步新路径与维护规则 |
| 工具 | `tools/docs/`、`scripts/`、`.github/workflows/ci.yml` | 迁移并更新调用路径 |
| 测试 | `tests/repository/` | 更新目录契约并增加源码派生文档检查 |
| 源码 | `backend/api/openapi_schema.py` | 仅在迁移后引用仍失效时修正文档路径，不改变行为 |

## 5. 依赖与冲突

### 5.1 依赖的其他 plan

| plan 文件 | 依赖原因 |
|-----------|---------|
| N/A | 当前基线没有其他活动或中断 plan。 |

### 5.2 与现有 plan 的重叠

| 冲突 plan | 重叠范围（文件 / 模块 / 接口） | 解决方式 |
|-----------|-------------------------------|---------|
| N/A | N/A | N/A |

冲突扫描覆盖 `docs/governance/plans/` 及仓库内其他 plan 目录；只发现计划生命周期说明，没有状态为 Active 或 Interrupted 的任务 plan。

## 6. 完成标准

- [ ] 文档目录与模板职责一致，且目录内部保持扁平。
- [ ] API 文档与当前 86 个路径、94 个 GET/POST 操作及 SSE 事件一致。
- [ ] 数据文档与当前 37 张 SQLite 表及关键字段一致。
- [ ] 功能规格区分可达、不可达、部分接线和未实现状态。
- [ ] 文档索引、链接、占位符、元数据、旧路径与源码引用检查通过。
- [ ] 相关 OpenAPI 与 repository 测试通过，`git diff --check` 通过。
- [ ] 业务源码、HTTP API、SQLite Schema 和 Agent 权限没有行为变化。
- [ ] B-170 从 BACKLOG 移除，本 plan 已删除，工作区干净。

## 7. 回流清单

| 内容 | 目标文档 | 是否完成 |
|------|----------|----------|
| 产品背景、目标用户、功能边界、用例和维护版本范围 | `docs/requirements/` | [ ] |
| 完整系统、API、数据、安全、权限、状态和 UI 契约 | `docs/design/` | [ ] |
| 当前用户可感知能力及可达性边界 | `docs/features/` | [ ] |
| Desktop、GitHub、Obsidian、Docker、维护与排障操作 | `docs/features/`、`docs/guides/` | [ ] |
| 新目录、命令、治理流程和发布可见变更 | 根文档、`docs/README.md`、`CHANGELOG.md` | [ ] |

## 8. 执行记录

- 2026-08-01：确认模板仓库为 `6cbb9e0`、脚手架版本 1.0.0；在系统临时目录成功生成 open-source 全栈参考骨架。生成结果只用于职责和文件集合对照，未复制 `.docs-template/`、DevLog、模板仓库测试或维护文件。
- 2026-08-01：本任务保留逐功能规格，但不建立前端、后端、集成、运维或技术组件专题子目录。

## 9. 状态快照

- **最后更新**：2026-08-01
- **进度**：已完成 3 / 6 项（见 § 3 勾选状态）
- **最新 commit**：`0eae2ba` — `docs: 建立扁平标准文档目录`
- **代码状态**：`docs/template-canonical-restructure`；标准目录、索引和可直接映射文档已提交，复杂专题仍留在旧目录等待内容回流。
- **下一步**：重构功能规格与 guides，完成旧专题事实回流并删除旧目录。
- **续任务须知**：模板参考目录位于系统临时目录；目标仓库不得运行初始化器或恢复模板状态目录。
