# B-167 基于 docs-template 1.0.0 重构文档体系

> 状态：Active
> 创建时间：2026-07-30
> 创建方：Codex
> 关联 BACKLOG：B-167
> 关联功能文档：`docs/features/README.md`
> 关联设计文档：`docs/design/architecture-overview.md`、`docs/design/api-spec.md`、`docs/design/database-design.md`

## 1. 目标

以 `E:\Code\docs-template` 的 `scaffold/VERSION=1.0.0` 为权威结构，按已确认的 `open-source` profile 和适用 packs 对 Knowledge Island 文档做语义迁移。迁移后，文档入口、元数据、索引、GitHub 协作资产、校验脚本和 DevLog 归档规则应一致，并且正文只描述当前 v2.0.0 源码、已发布事实和明确标注的规划。

## 2. 前置条件

- 已读取 `AGENTS.md`、`README.md`、`docs/README.md`、`docs/BACKLOG.md`、`docs/plans/README.md` 与 `template-mapping.md`
- 已核验模板仓库 `origin/main` 文件树和 `scaffold/VERSION=1.0.0`
- 用户已确认采用推荐方案，包括 GitHub 协作资产、文档 CI 和 DevLog 年月整理
- 当前工作区在 `main` 且无未提交改动

## 3. 任务拆解

每完成一项，立即执行：① 勾选此处 ② `git commit` 保存进度 ③ 更新 § 9 状态快照。
未完成项不得删除。

- [x] 建立模板消费与治理基线：记录 profile/packs/state，补齐根级规范、GitHub 协作资产和跨平台文档校验脚本
- [x] 重构正式文档入口、映射、需求、设计、功能、指南与 ADR 模板/索引，并用源码校准 v2.0.0 事实
- [x] 将 dated DevLog 迁入 `docs/devlog/YYYY/MM/`，修复全仓链接和索引，保留历史扩展目录
- [ ] 运行链接、占位符、元数据、文档一致性、测试与前端构建验证并修复发现的问题
- [ ] 完成回流审计，将 B-167 置为 `done` 并删除本 plan

## 4. 影响范围

| 类型 | 路径 / 模块 | 变更方向 |
|------|------------|---------|
| 配置 | `.docs-template/state.tsv`、`.editorconfig`、`.markdownlint.json` | 新增模板消费与格式基线 |
| GitHub | `.github/CODEOWNERS`、`.github/ISSUE_TEMPLATE/`、`.github/pull_request_template.md`、`.github/workflows/docs-checks.yml` | 新增开源协作与文档校验资产 |
| 根文档 | `README.md`、`AGENTS.md`、`CONTRIBUTING.md`、`SECURITY.md`、`CODE_OF_CONDUCT.md`、`CHANGELOG.md`、`template-mapping.md` | 按模板职责校准或补齐 |
| 正式文档 | `docs/README.md`、`docs/requirements/`、`docs/design/`、`docs/features/`、`docs/guides/`、`docs/adr/`、`docs/glossary.md` | 语义重构、补模板、补索引与元数据 |
| 过程文档 | `docs/devlog/` | dated DevLog 迁入年月目录并更新索引 |
| 历史扩展 | `docs/architecture/`、`docs/release/`、`docs/superpowers/`、`docs/previews/` | 保留内容，只修正必要入口和链接 |
| 校验脚本 | `scripts/check-doc-links.*`、`scripts/check-placeholders.*`、`scripts/check_docs_consistency.py` | 新增或强化文档治理校验 |

## 5. 依赖与冲突

### 5.1 依赖的其他 plan

| plan 文件 | 依赖原因 |
|-----------|---------|
| N/A | 当前无标记为 Active 或 Interrupted 的依赖 plan |

### 5.2 与现有 plan 的重叠

| 冲突 plan | 重叠范围（文件 / 模块 / 接口） | 解决方式 |
|-----------|-------------------------------|---------|
| N/A | `docs/superpowers/plans/` 三份无状态旧计划仅作为历史材料保留，不参与当前执行 | N/A |

## 6. 完成标准

- [ ] 文档结构和模板消费状态符合 `docs-template` 1.0.0 的已选 profile/packs
- [ ] 正式文档对产品定位、接口、数据、前端、桌面与插件边界的描述与当前源码一致
- [ ] 文档链接、模板占位符、元数据和既有文档一致性检查通过
- [ ] 相关测试与前端构建验证通过；未执行项有真实原因和本地复验方式
- [ ] 相关文档已同步（见下方“回流清单”）
- [ ] BACKLOG 条目 B-167 状态已更新为 `done`

## 7. 回流清单

| 内容 | 目标文档 | 是否完成 |
|------|----------|----------|
| 模板版本、profile、packs、项目扩展及迁移边界 | `template-mapping.md`、`.docs-template/state.tsv` | [ ] |
| 文档导航、职责、当前产品状态和事实来源 | `README.md`、`docs/README.md` | [x] |
| 需求、架构、API、数据、权限、前后端契约与功能索引 | `docs/requirements/`、`docs/design/`、`docs/features/` | [x] |
| 开发、运维、安全、支持、贡献、迁移与排障指南 | `docs/guides/`、`CONTRIBUTING.md`、`SECURITY.md` | [x] |
| ADR/功能/RFC/DevLog/Postmortem 等复用模板 | `docs/adr/`、`docs/features/`、`docs/design/`、`docs/devlog/` | [x] |
| DevLog 年月归档规则和历史入口 | `docs/devlog/README.md`、`docs/README.md` | [x] |
| GitHub 协作资产与自动化文档门禁 | `.github/`、`scripts/` | [ ] |

## 8. 执行记录

- 2026-07-30：确认模板源为 `E:\Code\docs-template`，模板版本 1.0.0。
- 2026-07-30：选择 `open-source` profile；packs 为 requirements、architecture、workflow、ai-planning、release-support、operations、api、data、frontend、frontend-api-contract、access-control、migration、glossary、github、github-ci。
- 2026-07-30：仓库公开但无 LICENSE；本任务不擅自选择许可证，许可证状态明确标记为待项目所有者决策。
- 2026-07-30：保留 `docs/architecture/`、`docs/release/`、`docs/superpowers/`、`docs/previews/` 等项目历史扩展，不做批量删除。
- 2026-07-30：已机械复用模板 1.0.0 中 32 个缺失 scaffold 文件，并以当前目标文件哈希生成 64 行 `.docs-template/state.tsv`；未覆盖任何既有文件。
- 2026-07-30：暂不创建 `.docs-template/strict-ci`。活动文档完成语义迁移且消费者占位符检查归零后再激活；本地 `.venv`、运行时副本和 GitHub Actions 表达式的误报留待校验切片修正。
- 2026-07-30：完成正式文档语义迁移。按当前后端、Vue/Tauri、Obsidian 插件和发布事实重写入口、治理、契约与运维文档，并将 37 张当前 SQLite 表、未挂载视图、URL 摘录参数缺口、v2 备份路径漂移和 Tauri 动态连通性风险明确写回正式文档与 BACKLOG。
- 2026-07-30：将 19 份 dated DevLog 原样迁入 `docs/devlog/2026/{04,05,07}/`，重建年月索引并更新活动路径引用；历史 superpowers plan 和 BACKLOG ISSUE-003 中的旧路径作为当时事实保留。
- 2026-07-30：强化 `scripts/check_docs_consistency.py`，新增递归 DevLog 归档/索引、功能索引、ADR 索引、核心目录和正式文档元数据检查，并补 3 项回归测试。

## 9. 状态快照

- **最后更新**：2026-07-30
- **进度**：已完成 2 / 5 项（见 § 3 勾选状态）
- **最新 commit**：`f6db3b6` — docs: 校准 v2 文档结构与实现事实
- **代码状态**：`main`；正式文档语义迁移已提交；状态快照为下一提交的计划更新
- **下一步**：将 dated DevLog 迁入 `docs/devlog/YYYY/MM/`，同步索引、路径引用和一致性脚本
- **续任务须知**：保留历史日志内容，只迁移 19 份 dated DevLog 并修复必要路径；严格占位符门禁尚未激活
