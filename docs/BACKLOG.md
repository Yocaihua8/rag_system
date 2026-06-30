# BACKLOG

> 状态：Active
> Owner：RAG 团队
> Last Updated：2026-06-30（启动 Phase 2「发布硬化 + 精选功能并行」：新增硬化主线 B-149 CI、B-150 backend 测试、B-151 前端 Vitest、B-152 macOS/Linux 打包验证、B-153 v1.0.0 发布门禁、B-154 依赖安全审计；功能并行轨 B-132 网页爬取提至 P2，目标里程碑统一 v1.0.0）
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
| B-139 | tech-debt | FastAPI 替代 stdlib HTTP | done | P1 | L | v1.0.0 | RAG 团队 | docs/adr/ADR-001-fastapi-migration.md | 已完成：路由层迁移至 FastAPI + Uvicorn；storage.py 不变；SSE 改为 StreamingResponse；见 ADR-001 |
| B-140 | feature | 认证中间件（JWT / API Key） | done | P1 | M | v1.0.0 | RAG 团队 | docs/adr/ADR-005-remote-auth.md | 已完成：可选启用 API Key + 短期 JWT；保护 `/api/*`、`/docs`、`/redoc`、`/openapi.json`；不改数据库 schema |
| B-141 | feature | Vue 3 + Vite 前端工程化 | done | P1 | XL | v1.0.0 | RAG 团队 | docs/features/frontend-engineering.md | 已完成：Vue/Vite 工程骨架和 B-141A-Z 页面级迁移薄片已收口，覆盖资料库、设置、评估、工作台非流式问答、回答反馈、检索调试、项目级检索默认值、检索复盘、Agent 只读工具和工具来源上下文；`webapp/static/` 继续保留为未迁移高级交互 fallback；已按 plan 生命周期删除 B-141 临时计划文件 |
| B-142 | feature | Vue 工作台 SSE 与会话历史迁移 | done | P2 | M | v0.11.0 | RAG 团队 | docs/features/frontend-engineering.md, docs/design/api-spec.md | 已完成：Vue 工作台接入 `/api/answer/stream` EventSource 流式输出、取消当前请求、`/api/chat/sessions*` 与 `/api/chat/messages` 会话列表、历史恢复和消息管理 |
| B-143 | tech-debt | 移除 legacy 静态前端 fallback | done | P2 | M | v0.12.0 | RAG 团队 | docs/features/frontend-engineering.md, docs/guides/setup.md, docs/guides/testing.md | 已完成：删除 `webapp/static/` legacy 原生前端；`webapp/server.py` 只服务 `static_dist/`；缺失构建时提示先执行 `npm run build`；清理 legacy 静态测试断言 |
| B-146 | tech-debt | 移植 Ollama + 平台路径到 backend/ | done | P1 | S | Tauri MVP 0 | RAG 团队 | docs/design/new-architecture-design.md §23.7, docs/guides/setup.md | 已完成：`src/adapters/llm/ollama_adapter.py` → `backend/providers/llm/ollama.py`；`src/adapters/embedding/ollama_embedder.py` → `backend/providers/embedder/ollama.py`；`_app_data_dir()` → `backend/config/paths.py`；Web MVP 设置接口支持 `provider=ollama` |
| B-145 | feature | Tauri 桌面壳 — Windows 打包验证 | done | P1 | L | Tauri MVP 0 | RAG 团队 | docs/design/new-architecture-design.md §23, docs/features/desktop-packaging.md | 已完成：Tauri 壳、Windows sidecar、Windows icon、测试和文档；`cargo check --manifest-path src-tauri\Cargo.toml`、`npm run sidecar:build`、`npm run tauri:build:windows` 均通过，生成 NSIS installer：`src-tauri/target/release/bundle/nsis/Knowledge Island_0.1.0_x64-setup.exe`；完成后删除 plan |
| B-148 | feature | First-Run Wizard（首次运行向导） | done | P1 | M | Tauri MVP 1 | RAG 团队 | docs/design/new-architecture-design.md §23.6, docs/features/first-run-wizard.md | 已完成：新增 Ollama 检测 `/api/ollama/status`、模型拉取 SSE `/api/ollama/pull`、Vue First-Run Wizard 和首个知识库创建入口；完成后删除 plan |
| B-147 | tech-debt | 归档 src/ 桌面遗留代码 | done | P2 | XS | Tauri MVP 0 | RAG 团队 | docs/design/architecture-overview.md | 已完成：Web/Tauri/Docker 活动链路不再引用 `src/`；配置入口迁移到 `backend/config/`；旧 PySide6 / 六边形代码、legacy 测试和旧桌面脚本已归档到 `archive/src-desktop-legacy/`；不再接受 legacy PR |
| B-144 | tech-debt | Docker 镜像内置 Vue 构建产物 | done | P1 | S | v0.11.0 | RAG 团队 | docs/features/frontend-engineering.md, docs/guides/setup.md | 已完成：Docker 镜像构建阶段执行 Vue/Vite 构建并复制 `webapp/static_dist/`，避免依赖宿主机预先运行 `npm run build`；完成后已删除 plan |
| B-42 | feature | 知识库辅助管理页 | done | P2 | L | v1.0.0 | RAG 团队 | docs/design/ui-wireframes.md, docs/features/knowledge-base-management.md | 已完成：资料库页顶部新增知识库辅助管理概览，展示项目状态、文件列表、摄入进度、评估题库和最近结果；新增只读 `/api/assessment/library` 和项目摘要评估计数字段；完成后删除 plan |
| B-125 | feature | Reranker 重排序接入 | done | P1 | L | v1.0.0 | RAG 团队 | docs/design/new-architecture-design.md §5.4, docs/guides/setup.md, docs/design/api-spec.md | 已完成：BM25 + 向量候选后可选接入本地 Cross-Encoder reranker；默认关闭；`sentence-transformers` 为软依赖；命中返回 `rerank_score`，回答返回 `pipeline_trace.reranker_used` |
| B-128 | feature | 对话分支与历史消息编辑重发 | done | P2 | M | v1.0.0 | RAG 团队 | docs/design/new-architecture-design.md §5.5.3, docs/features/chat-branching.md | 已完成：支持在历史消息上编辑并重发，写入 `parent_message_id` / `branch_index`；Vue 工作台提供编辑重发入口；完成后删除 plan |
| B-126 | feature | 知识图谱接入检索流程 | done | P2 | L | v1.0.0 | RAG 团队 | docs/design/database-design.md, docs/features/graph-enhanced-retrieval.md, docs/design/api-spec.md | 已完成：在 Web MVP 检索中只读兼容 legacy `graph_nodes` / `graph_edges`；当图谱表存在且可映射到当前项目 chunk 时，一跳相邻来源会以 `graph_score` / `graph_depth` 并入候选池；表不存在时保持原检索行为；不修改 SQLite schema |
| B-06 | tech-debt | ops/ 运维脚本 | done | P3 | S | backlog | RAG 团队 | ops/README.md §维护脚本；docs/features/ops-maintenance.md；docs/design/api-spec.md | 已完成：新增 `ops/scripts/backup_db.sh`、`cleanup_runtime.sh`、`rebuild_index.sh`；新增 `POST /api/admin/rebuild-index` 本地维护端点；支持按项目或全量重建 chunk/vector 索引；不修改 SQLite schema；完成后删除 plan |
| B-07 | feature | 结果导出（Markdown / PDF） | done | P3 | M | backlog | RAG 团队 | docs/features/result-export.md, docs/design/api-spec.md | 已完成：新增 `POST /api/export/result`，支持按 `project_id` + `message_id` 将已生成问答结果导出为 Markdown / PDF 文件，默认写入 `data/outputs/`；导出内容包含问题、回答和来源快照；不修改 SQLite schema；完成后删除 plan |
| B-08 | feature | 多工作区并发索引 | done | P3 | L | backlog | RAG 团队 | docs/design/architecture-overview.md, docs/features/concurrent-indexing.md | 已完成：新增进程内项目级摄入协调器；FastAPI `/api/*` 同步分发移入线程池；写入型导入入口同项目串行、跨项目可并发；SQLite 连接设置 busy timeout；不修改 SQLite schema；完成后删除 plan |
| B-24 | feature | Tauri 跨平台桌面打包（macOS / Linux） | done | P3 | M | backlog | RAG 团队 | docs/features/desktop-packaging.md | 已完成：沿用 B-145 Tauri sidecar 链路新增 macOS/Linux 本机打包入口；新增 Unix sidecar 脚本和 `npm run tauri:build:macos` / `npm run tauri:build:linux`，分别调用 `--bundles dmg` / `--bundles appimage`；Windows NSIS 默认目标保持不变；Windows 环境已完成静态契约、`npm run build` 与 `npx tauri info` 验证，macOS/Linux 原生包需在对应系统构建。 |
| B-25 | test | 端到端 UI 自动化测试 | done | P3 | M | backlog | RAG 团队 | docs/guides/testing.md | 已接入 Playwright E2E；覆盖项目空间创建、文本笔记导入、工作台问答主流程；命令见 docs/guides/testing.md |
| B-117 | research | MCP / 插件能力研究 | done | P3 | S | backlog | RAG 团队 | docs/features/agent-tooling-mcp-research.md | 已完成研究：当前不接入 MCP 插件市场或任意 MCP server；后续仅可按显式 allowlist、只读、用户手动触发、审计记录方式评估最小适配层 |
| B-118 | research | 多用户 / 团队空间研究 | done | P3 | S | backlog | RAG 团队 | docs/features/team-workspace-research.md, docs/design/permission-matrix.md | 已完成研究：当前继续本地单用户定位；团队空间不进入当前实现，未来需先拆分身份、租户、RBAC、审计和迁移设计 |
| B-119 | research | 网页自动抓取研究 | done | P3 | S | backlog | RAG 团队 | docs/features/web-crawling-research.md, docs/requirements/functional-modules.md | 已完成研究：当前继续保持手动 URL 摘录，不实现自动抓取；B-132 若进入实现需先满足 robots.txt、SSRF 防护、内容净化、大小/超时限制和可选依赖隔离 |
| B-132 | feature | 网页自动爬取（可选依赖） | todo | P2 | XL | v1.0.0 | RAG 团队 | docs/requirements/functional-modules.md, docs/features/web-crawling-research.md | Phase 2 功能并行轨：对接 `playwright` 或 `requests-html` 实现 URL 来源自动抓取；按 B-119 准入门槛先落地 robots.txt 遵守、SSRF 防护、内容净化、大小/超时限制和可选依赖隔离；B-119 的细化实现；预估 7 天 |
| B-133 | feature | GitHub 仓库整体导入 | done | P2 | L | v1.0.0 | RAG 团队 | docs/features/github-repo-import.md, docs/design/api-spec.md, docs/requirements/functional-modules.md | 已完成：通过本机 `git clone --depth 1` 导入 GitHub 仓库并创建项目空间；新增 `/api/import/github-repo`、Vue 资料库入口和 `github_repo` 导入批次记录；不接入 GitHub API，不保存凭据 |
| B-134 | feature | Qdrant 替换 SQLite 向量存储 | done | P3 | L | v1.0.0 | RAG 团队 | docs/features/qdrant-vector-store.md, docs/design/architecture-overview.md, docs/design/database-design.md, docs/design/api-spec.md, docs/adr/ADR-007-qdrant-vector-store.md | 已完成：新增 Qdrant local mode provider、配置开关、文档向量同步和搜索候选接入；默认关闭，Qdrant 不可用时回退 SQLite `chunk_vectors`；不改 API 契约或 SQLite schema |
| B-135 | feature | 多模型并排对比 | done | P3 | L | backlog | RAG 团队 | docs/features/multi-model-comparison.md, docs/design/api-spec.md | 已完成：新增 `/api/answer/compare`，同一问题可选择 2 个不同 Model Profile 并排生成回答；Vue 工作台提供对比入口；复用检索、Prompt 预设和工具来源上下文；不写入聊天消息 |
| B-136 | docs | OpenAPI / Swagger 接口文档 | done | P3 | M | backlog | RAG 团队 | docs/features/openapi-swagger-docs.md, docs/design/api-spec.md | 已完成：`/openapi.json` 返回显式 Web MVP API OpenAPI 3.0 schema；`/docs` Swagger UI 和 `/redoc` 保留；认证开启时继续保护文档入口；schema 覆盖 `/api/answer/compare` |
| B-137 | feature | Notion / Obsidian 本地导出同步 | done | P2 | L | v1.0.0 | RAG 团队 | docs/features/notion-obsidian-sync.md, docs/design/api-spec.md | 已完成：新增 Notion Markdown zip 与 Obsidian vault 本地导入 API、Vue 资料库入口、导入批次记录和文档契约；不接入 Notion API，不修改 SQLite schema |
| B-149 | infra | CI 持续集成流水线 | todo | P1 | M | v1.0.0 | RAG 团队 | docs/guides/testing.md, docs/guides/release-process.md | Phase 2 硬化主线：新增 GitHub Actions（仓库当前无 `.github/workflows/`），PR 门禁串联 `pytest`（backend+webapp+e2e）、`npm run build`、Playwright E2E 与 `scripts/check_docs_consistency.py`；缓存 pip/npm 依赖；失败即拦截合并 |
| B-150 | test | backend/ 单元测试补齐 | todo | P1 | M | v1.0.0 | RAG 团队 | docs/guides/testing.md | Phase 2 硬化主线：当前 `tests/test_backend/` 仅 3 个测试，与 webapp 28 个失衡；补齐 `backend/providers/llm`、`backend/providers/embedder`、`backend/config/paths`、`backend/config/settings` 与 Qdrant provider 降级路径覆盖 |
| B-151 | test | 前端 Vitest 单元测试 | todo | P2 | M | v1.0.0 | RAG 团队 | docs/guides/testing.md, docs/features/frontend-engineering.md | Phase 2 硬化主线：引入 Vitest，覆盖 `frontend/src/api/*` helper 的请求/错误归一化与关键组件状态；与 Playwright E2E 分层，单测跑纯逻辑、E2E 跑主流程 |
| B-152 | test | macOS/Linux Tauri 打包原生验证 | todo | P2 | M | v1.0.0 | RAG 团队 | docs/features/desktop-packaging.md | Phase 2 硬化主线：在 macOS/Linux 原生系统实测 B-24 的 `tauri:build:macos`（dmg）/`tauri:build:linux`（appimage）链路，补齐 Unix sidecar 与图标，记录平台差异与已知限制 |
| B-153 | docs | v1.0.0 发布门禁与回归清单 | todo | P1 | M | v1.0.0 | RAG 团队 | docs/release/, docs/guides/release-process.md | Phase 2 硬化主线：制定 v1.0.0 发布 readiness 清单与回归脚本，覆盖导入/检索/问答/导出/打包主流程，明确 go/no-go 门禁；沿用既有 `docs/release/*READINESS*` 模板 |
| B-154 | tech-debt | 依赖与安全审计基线 | todo | P2 | S | v1.0.0 | RAG 团队 | SECURITY.md, docs/guides/setup.md | Phase 2 硬化主线：引入 `pip-audit` / `npm audit` 基线与可选依赖矩阵验证（pymupdf / qdrant-client / sentence-transformers / ollama 缺失时降级路径），纳入 B-149 CI |
| B-23 | feature | Reranker 重排序（legacy） | wontfix | P3 | — | — | RAG 团队 | — | 已被 B-125 替代；原计划在 legacy 链路接入，Web MVP 由 B-125 统一覆盖 |
| B-67 | feature | Web 向量库与 Reranker 接入（legacy 规划） | wontfix | P3 | — | — | RAG 团队 | — | 已被 B-134（Qdrant）和 B-125（Reranker）拆分替代 |

---

## 6. 已知问题

_当前无未决已知问题。_

> ISSUE-003（文档一致性脚本要求缺失的 `docs/DEVLOG.md`）已于 2026-06-29 处理：确认仓库不维护 `docs/DEVLOG.md` 聚合索引，`scripts/check_docs_consistency.py` 改为在该文件缺失时跳过聚合索引校验（存在时仍校验）。
