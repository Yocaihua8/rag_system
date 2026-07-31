# BACKLOG

> 状态：Active
> Owner：RAG 团队
> Last Updated：2026-07-31（完成 docs-template 1.0.0 文档体系重构）
> Related：docs/requirements/functional-modules.md, docs/design/api-spec.md, docs/adr/ADR-001-fastapi-migration.md

用于记录尚未完成、待验证、待决策、已知问题和技术债。**这里允许写规划内容**，但应保持可执行和可追踪。

---

## 1. 使用规则

- 已经上线 / 已确定的内容不要留在 BACKLOG
- 每条记录必须有状态和优先级
- 大而空的愿景不写，尽量拆成可执行事项

### 1.1 待办清单 vs 已知问题

两类记录用途不同，不要写串：

| 类型 | 位置 | 关注 | 典型形态 |
|------|------|------|----------|
| 待办清单（§ 5） | `B-xxx` 表格行 | **要做的事**（可执行事项） | "流式输出接入 SSE" / "api.py 按领域拆分" |
| 已知问题（§ 6） | `ISSUE-xxx` 条目 | **已发现但尚未修复的现象** | "Markdown 符号以原始文本显示" |

**流转规则**：

- 一旦决定修复某个已知问题，**必须**在 § 5 新建对应 `B-xxx` 条目，并在原 `ISSUE-xxx` 的"计划处理方式"中引用该 ID
- 待办完成并验证后**可以**从 § 5 移除；已知问题在修复发布后**应该**从 § 6 移除并记入 `CHANGELOG.md`

---

## 2. 状态定义

- `todo`：待开始
- `doing`：进行中
- `blocked`：被阻塞
- `done`：已完成，待归档
- `wontfix`：暂不处理

---

## 3. 优先级定义

- `P0`：必须尽快处理，影响主流程
- `P1`：重要，影响使用体验或质量
- `P2`：常规优化
- `P3`：长期想法或低优先级改进

---

## 4. 规模估算定义

- `XS`：< 半天
- `S`：< 1 天
- `M`：< 3 天
- `L`：< 1 周
- `XL`：> 1 周

---

## 5. 待办清单

| ID | 类型 | 标题 | 状态 | 优先级 | 规模 | 里程碑 | 负责人 | 关联文档 | 说明 |
|----|------|------|------|--------|------|--------|--------|----------|------|
| B-150 | test | backend/ 单元测试补齐 | done | P1 | M | v1.0.0 | RAG 团队 | docs/guides/testing.md | Phase 2 硬化主线：已补齐 `backend/providers/llm`、`backend/providers/embedder`、`backend/config/paths`、`backend/config/settings` 与 Qdrant provider 降级路径单元测试，并在 `docs/guides/testing.md` 记录 backend/provider 验证命令 |
| B-151 | test | 前端 Vitest 单元测试 | done | P2 | M | v1.0.0 | RAG 团队 | docs/guides/testing.md, docs/features/frontend-engineering.md | Phase 2 硬化主线：已引入 Vitest + jsdom，覆盖 `frontend/src/api/*` helper 的请求/错误归一化、SSE/上传 payload 与 `AnswerPanel`、`ProjectSpacePanel`、`QuestionComposer` 关键状态；CI 已在 Playwright E2E 前执行 `npm run test:unit` |
| B-152 | test | macOS/Linux Tauri 打包原生验证 | done | P2 | M | v1.0.0 | RAG 团队 | docs/features/desktop-packaging.md | Phase 2 硬化主线：已补齐 Tauri 桌面 bundle 图标、修正 macOS/Linux `tauri build --bundles ...` 命令、修复 Unix sidecar target 检测 pipefail 退出码，并通过 GitHub Actions `macos-latest` / `ubuntu-latest` 原生 runner 生成 `.dmg` 与 `.AppImage` artifact |
| B-153 | docs | v1.0.0 发布门禁与回归清单 | done | P1 | M | v1.0.0 | RAG 团队 | docs/release/V1_0_0_READINESS_2026-07-01.md, docs/guides/release-process.md | Phase 2 硬化主线：已新增 v1.0.0 readiness 清单与回归脚本，覆盖导入/检索/问答/导出/打包主流程，明确 go/no-go 门禁，并在发布流程中设为 v1.0.0 发布前检查入口 |
| B-154 | tech-debt | 依赖与安全审计基线 | done | P2 | S | v1.0.0 | RAG 团队 | SECURITY.md, docs/guides/setup.md | Phase 2 硬化主线：引入 `pip-audit` / `npm audit` 基线与可选依赖矩阵验证（pymupdf / qdrant-client / sentence-transformers / ollama 缺失时降级路径），纳入 B-149 CI 与 v1.0.0 readiness |
| B-155 | tech-debt | webapp/ 全量重组至 backend/ | done | P2 | XL | v1.1.0 | RAG 团队 | docs/design/architecture-overview.md | v1.0.0 后执行：已废弃受控 `webapp/` 源码目录，按职责重组至 `backend/api/`、`backend/storage/`、`backend/domain/`、`backend/routes/` 等子包；已迁移 Python import 路径、测试和文档引用；不改 API 契约、不改 SQLite schema，不改 `frontend/src` 或前端交互，仅调整 Vite 构建输出到 `backend/static_dist/` |
| B-156 | feature | 第二阶段前端简洁化重设计 | done | P1 | XL | v1.1.0 | RAG 团队 | docs/features/frontend-engineering.md, docs/design/ui-wireframes.md, docs/superpowers/specs/2026-07-02-frontend-phase-2-redesign.md | 已将 Vue 前端从迁移期四视图收束为“聊 / 库 / 设”简洁主线：默认聊天工作台，工作区和线程统一在侧栏，库改为资料管理弹窗并支持先加入库、再按资料夹和资料列表选择资料，设改为全屏设置；独立评估入口收进聊天工具，主色调整为黑白灰中性方案。 |
| B-157 | feature | 全局资料库与工作区连接接口 | wontfix | P3 | L | future | RAG 团队 | docs/design/api-spec.md, docs/design/database-design.md | Knowledge Island 2.0 已转向单项目知识教练；当前继续保持 `project_id` 资料边界，不实现跨工作区全局资料库。若未来重新启动，需作为新的产品决策重新评估。 |
| B-158 | docs | Codex 工作区会话与资料导入 HTML 预览 | done | P1 | S | v1.1.0 | RAG 团队 | docs/design/codex-workspace-chat-import-design.md, docs/previews/codex-anythingllm-workspace-preview/index.html | 已基于 In Review 设计新增单文件可交互 HTML 预览，用于验证默认会话首页、添加资料五步流程、依据抽屉、设置全屏页和练习入口；预览不修改正式 Vue 代码，不伪装后端未支持的跨工作区资料、文件级问答范围或实时导入进度。 |
| B-159 | docs | Codex 风格视觉规范与术语收口 | done | P1 | S | v1.1.0 | RAG 团队 | docs/design/codex-ui-visual-system.md, docs/design/codex-workspace-chat-import-design.md, docs/design/ui-wireframes.md, docs/style-guide.md | 新增视觉令牌、组件状态、动效和无障碍规范；明确 B-156 已落地的页面方向与 B-157 未实现的全局资料库边界；将用户界面“工作区”、内部 `project_id` 与历史“项目空间”的语境写清。本次仅更新文档，不改 Vue、API 或数据库。 |
| B-160 | docs | 项目知识教练方向与 v2 数据代际冻结 | done | P0 | M | v2.0.0 | RAG 团队 | docs/features/project-knowledge-coach.md, docs/adr/ADR-008-project-knowledge-coach-v2.md, docs/adr/ADR-009-obsidian-plugin-bridge.md | 已冻结个人开发学习场景、项目知识覆盖 + 通用技能树边界、全新 `runtime/v2/` 数据代际和 Obsidian 插件桥方案；相关能力已由 B-161～B-165 分片实现并完成本地候选验收。 |
| B-161 | feature | 项目分析、知识点与通用技能映射 | done | P0 | XL | v2.0.0 | RAG 团队 | docs/features/project-knowledge-coach.md, docs/design/api-spec.md, docs/design/database-design.md | 已完成独立 v2 数据根、确定性项目分析、稳定知识点、真实来源、版本化技能映射及四个 Coach 基础 API；默认模型 Profile 可选增强概览，失败回退规则结果。 |
| B-162 | feature | 持久评估、双层差距与学习计划 | done | P0 | XL | v2.0.0 | RAG 团队 | docs/features/project-knowledge-coach.md, docs/design/api-spec.md, docs/design/database-design.md | 已完成知识点/技能定向评估、来源约束评分、项目覆盖与技能聚合，以及可编辑、确认、保留历史来源的版本化学习计划；旧 `/api/assessment/*` 契约保持兼容。 |
| B-163 | feature | Obsidian 插件桥与受控双向同步 | done | P0 | XL | v2.0.0 | RAG 团队 | docs/features/notion-obsidian-sync.md, docs/design/api-spec.md, docs/design/database-design.md | 已实现桌面插件配对、Markdown 幂等事件同步、受控发布、冲突阻断、不可变修订与九个 Obsidian API；保留原单向手动导入。 |
| B-164 | feature | Vue 项目知识教练闭环 | done | P0 | XL | v2.0.0 | RAG 团队 | docs/features/frontend-engineering.md, docs/design/ui-wireframes.md | 已在现有 Codex 风格外壳中接通教练、学习地图、学习计划、评估覆盖层和 Obsidian 连接/受控发布交互；浏览器只使用应用侧路由，确认发布后明确显示 `queued` 等待插件执行。 |
| B-165 | release | Knowledge Island 2.0 发布验收 | done | P0 | L | v2.0.0 | RAG 团队 | docs/guides/testing.md, CHANGELOG.md, docs/release/V2_0_0_READINESS_2026-07-24.md | 已完成 OpenAPI、文档、533 项后端/Web 测试、Vue、插件、Web E2E、Tauri 静态回归和旧运行时哈希复核，形成 v2.0.0 本地发布候选；正式 Tag、远端发布和原生安装包未执行。 |
| B-166 | release | v2.0.0 依赖安全修复与正式发布 | done | P0 | L | v2.0.0 | RAG 团队 | docs/features/frontend-engineering.md, docs/features/desktop-packaging.md, docs/guides/testing.md, docs/guides/release-process.md, CHANGELOG.md, docs/release/V2_0_0_READINESS_2026-07-24.md | 依赖 high 漏洞已完成兼容修复，在线 npm/pip 审计、本地完整矩阵、PR #4 两项 GitHub Actions 检查、`main` 合并和 Windows v2 NSIS 构建均通过；`v2.0.0` Tag 与 GitHub Release 已发布同一提交，并附带 SHA-256 已核验的未签名 Windows x64 安装包。 |
| B-167 | docs | 基于 docs-template 1.0.0 重构文档体系 | done | P1 | XL | maintenance | RAG 团队 | docs/README.md, template-mapping.md | 已按 `open-source` profile 与 20 个适用 pack 完成 64 个模板 destination 的语义迁移与状态追踪，以当前 v2.0.0 源码校准正式文档，归档 19 份 DevLog，并激活跨平台占位符、链接、索引和元数据门禁。 |

---

## 6. 已知问题

### ISSUE-008：当前主资料/聊天界面存在未接线或参数不完整的可见控件

- **发现时间**：2026-07-30
- **现象**：活动 `LibraryModal` 的“网页摘录”只提交 URL，但 API helper 同时要求非空 title/content；“选择资料”没有进入问答 payload；侧栏线程搜索和问题框部分工具按钮没有有效 handler。未挂载的 `LibraryView` / `AssessmentView` 仍在源码中，但不能作为当前可达页面。
- **影响范围**：`frontend/src/components/LibraryModal.vue`、`WorkspaceSidebar.vue`、`QuestionComposer.vue`、`WorkbenchView.vue`、`frontend/src/App.vue`。
- **计划处理方式**：分别建立最小前端/联调任务，先冻结交互与现有 API 契约，再补参数、事件和 E2E；在修复前，入口文档不得把这些控件描述为已交付能力。

### ISSUE-007：Tauri 打包配置未动态证明 WebView 到 sidecar 的 API 连通性

- **发现时间**：2026-07-30
- **现象**：桌面壳会启动监听 `127.0.0.1:8765` 的后端 sidecar，前端 API 使用同源 `/api/*`；Vite 开发服务器提供 8765 proxy，但当前 Tauri 生产配置没有等价代理或显式 API base。已有静态回归只断言配置/字符串，未覆盖安装包内实际请求。
- **影响范围**：`src-tauri/`、`frontend/src/api/`、Windows/macOS/Linux 原生运行时。
- **计划处理方式**：在独立任务中先对已构建安装包执行真实主流程连通性验证；若复现，明确采用 sidecar origin 或 Tauri bridge 的最小方案，并同步 API/桌面文档与原生 E2E。未验证前不以打包成功替代运行可用。

### ISSUE-006：v2 运行路径与部分配置/脚本存在漂移

- **发现时间**：2026-07-30
- **现象**：正式 Web 默认数据库为 `runtime/v2/app.db`，但 `ops/scripts/backup_db.sh` 仍默认旧 `runtime/webapp/knowledge_island.db`；结果导出仍写 `data/outputs/`，未使用配置层 `runtime/v2/outputs`；若干已加载的 chunk/retriever/top-k 配置未进入活动链路，实际分块固定为 700/80。
- **影响范围**：备份恢复可信度、运行目录说明、配置可预期性和运维指南。
- **计划处理方式**：代码修复前，runbook 将备份脚本标记为不可直接用于 v2；后续拆分路径修复与配置收口任务，补真实备份恢复/配置生效测试，不在本次文档重构中静默改业务代码。

### ISSUE-005：GitHub Actions 官方 Action 的 Node runtime 弃用警告

- **发现时间**：2026-07-30
- **现象**：PR #4 的 CI 两项 job 均通过，但 GitHub 对 `actions/cache@v4`、`actions/setup-node@v4`、`actions/setup-python@v5` 标注 Node 20 action runtime 已弃用，并由 runner 强制使用 Node 24 执行。
- **影响范围**：`.github/workflows/ci.yml` 的 Action 运行时；不影响项目通过 `setup-node` 配置的应用 Node 20 测试版本，也不阻断本次发布。
- **计划处理方式**：后续单独评估并升级到官方已迁移 Node 24 runtime 的 Action 版本，复跑 PR CI；不在 v2.0.0 发布提交中临时改写 workflow。

> ISSUE-004（v2.0.0 前端锁文件包含两个 high 漏洞）已于 2026-07-30 处理：锁文件将 `postcss` 升至 `8.5.22`，并以 `minimatch@9.0.8` 兼容覆盖解析到已修复的 `brace-expansion@5.0.9`；在线 `npm audit --audit-level=high` 与完整本地 CI 均通过，结果已回流 `CHANGELOG.md`。

> ISSUE-003（文档一致性脚本要求缺失的 `docs/DEVLOG.md`）已于 2026-06-29 处理：确认仓库不维护 `docs/DEVLOG.md` 聚合索引，`scripts/check_docs_consistency.py` 改为在该文件缺失时跳过聚合索引校验（存在时仍校验）。
