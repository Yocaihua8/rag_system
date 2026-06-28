# BACKLOG

> 状态：Active
> Owner：RAG 团队
> Last Updated：2026-06-28（完成 B-142 Vue 工作台会话迁移与 B-128 对话分支）
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
| B-145 | feature | Tauri 桌面壳 — Windows 打包验证 | blocked | P1 | L | Tauri MVP 0 | RAG 团队 | docs/design/new-architecture-design.md §23, docs/features/desktop-packaging.md | 已完成 Tauri 壳、sidecar 脚本、测试和文档；`npm run sidecar:build` 可生成 backend exe；`npm run tauri:build:windows` 阻塞于本机缺 Rust/Cargo；plan：docs/plans/B-145-tauri-windows-packaging.md |
| B-148 | feature | First-Run Wizard（首次运行向导） | done | P1 | M | Tauri MVP 1 | RAG 团队 | docs/design/new-architecture-design.md §23.6, docs/features/first-run-wizard.md | 已完成：新增 Ollama 检测 `/api/ollama/status`、模型拉取 SSE `/api/ollama/pull`、Vue First-Run Wizard 和首个知识库创建入口；完成后删除 plan |
| B-147 | tech-debt | 归档 src/ 桌面遗留代码 | todo | P2 | XS | Tauri MVP 0 | RAG 团队 | docs/design/new-architecture-design.md §23.7 | B-146 已完成关键移植；归档前需再次确认 `src/` 无仍被 Web/Tauri 链路引用，再整体移至 `archive/src-desktop-legacy/`；不再接受 PR |
| B-144 | tech-debt | Docker 镜像内置 Vue 构建产物 | done | P1 | S | v0.11.0 | RAG 团队 | docs/features/frontend-engineering.md, docs/guides/setup.md | 已完成：Docker 镜像构建阶段执行 Vue/Vite 构建并复制 `webapp/static_dist/`，避免依赖宿主机预先运行 `npm run build`；完成后已删除 plan |
| B-42 | feature | 知识库辅助管理页 | todo | P2 | L | v0.11.0 | RAG 团队 | docs/design/ui-wireframes.md | 参考 SAS 后台式知识库，展示项目状态、文件列表、项目知识点、评估题库和最近结果 |
| B-125 | feature | Reranker 重排序接入 | done | P1 | L | v1.0.0 | RAG 团队 | docs/design/new-architecture-design.md §5.4, docs/guides/setup.md, docs/design/api-spec.md | 已完成：BM25 + 向量候选后可选接入本地 Cross-Encoder reranker；默认关闭；`sentence-transformers` 为软依赖；命中返回 `rerank_score`，回答返回 `pipeline_trace.reranker_used` |
| B-128 | feature | 对话分支与历史消息编辑重发 | done | P2 | M | v1.0.0 | RAG 团队 | docs/design/new-architecture-design.md §5.5.3, docs/features/chat-branching.md | 已完成：支持在历史消息上编辑并重发，写入 `parent_message_id` / `branch_index`；Vue 工作台提供编辑重发入口；完成后删除 plan |
| B-126 | feature | 知识图谱接入检索流程 | todo | P2 | L | v1.0.0 | RAG 团队 | docs/design/database-design.md | `graph_nodes` / `graph_edges` 已建表（B-48），当前检索未使用；补充 Graph-enhanced 检索，扩展关联节点提升多跳推理；预估 5 天 |
| B-06 | tech-debt | ops/ 运维脚本 | todo | P3 | S | backlog | RAG 团队 | — | `ops/scripts/` 目前是空框架，补充：备份 db、清理 runtime、一键重建索引 |
| B-07 | feature | 结果导出（Markdown / PDF） | todo | P3 | M | backlog | RAG 团队 | — | `data/outputs/` 预留了输出目录，支持将生成结果导出为 Markdown / PDF |
| B-08 | feature | 多工作区并发索引 | todo | P3 | L | backlog | RAG 团队 | docs/design/architecture-overview.md | 当前同一时间只允许一个工作区摄入任务，未来支持队列并发 |
| B-24 | feature | 跨平台打包 | todo | P3 | M | backlog | RAG 团队 | docs/guides/release-process.md | 使用 PyInstaller / Nuitka 打包为独立可执行文件，降低非技术用户使用门槛 |
| B-25 | test | 端到端 UI 自动化测试 | todo | P3 | M | backlog | RAG 团队 | docs/guides/testing.md | 目前测试全部在单元层面，缺少 Web UI 的自动化集成测试 |
| B-117 | research | MCP / 插件能力研究 | todo | P3 | S | backlog | RAG 团队 | — | 仅研究可控只读工具接入，不引入插件市场或任意命令执行 |
| B-118 | research | 多用户 / 团队空间研究 | todo | P3 | S | backlog | RAG 团队 | docs/design/permission-matrix.md | 当前仍是本地个人应用；多用户、权限和团队空间暂不进入实现 |
| B-119 | research | 网页自动抓取研究 | todo | P3 | S | backlog | RAG 团队 | docs/requirements/functional-modules.md | 当前 URL 来源只做人工粘贴正文；自动抓取涉及网络、权限和依赖，暂缓 |
| B-132 | feature | 网页自动爬取（可选依赖） | todo | P3 | XL | v1.0.0 | RAG 团队 | docs/requirements/functional-modules.md | 对接 `playwright` 或 `requests-html` 实现 URL 来源自动抓取；需解决动态页面、robots.txt 遵守和依赖隔离；B-119 的细化实现；预估 7 天 |
| B-133 | feature | GitHub 仓库整体导入 | todo | P3 | L | v1.0.0 | RAG 团队 | docs/requirements/functional-modules.md | 通过 GitHub API 或 `git clone` 一键导入仓库文件；开发者核心场景；预估 5 天 |
| B-134 | feature | Qdrant 替换 SQLite 向量存储 | todo | P3 | L | v1.0.0 | RAG 团队 | docs/design/architecture-overview.md | SQLite 全扫描在 > 5000 chunks 时性能下降（见 ISSUE-002）；Qdrant 本地单文件模式，无服务依赖，支持 HNSW；替代 B-67；预估 5 天 |
| B-135 | feature | 多模型并排对比 | todo | P3 | L | backlog | RAG 团队 | docs/design/api-spec.md | 同一问题同时发给 2 个不同 Profile 展示对比回答；预估 5 天 |
| B-136 | docs | OpenAPI / Swagger 接口文档 | todo | P3 | M | backlog | RAG 团队 | docs/design/api-spec.md | 为当前 61 个 API 端点生成 OpenAPI 3.0 规范文档，支持 Swagger UI；预估 2 天 |
| B-137 | feature | Notion / Obsidian 本地导出同步 | doing | P2 | L | v1.0.0 | RAG 团队 | docs/features/notion-obsidian-sync.md, docs/design/api-spec.md | 导入 Notion 导出的 Markdown zip 包和 Obsidian vault 目录；知识工作者核心 C端场景；plan：docs/plans/B-137-notion-obsidian-sync.md |
| B-23 | feature | Reranker 重排序（legacy） | wontfix | P3 | — | — | RAG 团队 | — | 已被 B-125 替代；原计划在 legacy 链路接入，Web MVP 由 B-125 统一覆盖 |
| B-67 | feature | Web 向量库与 Reranker 接入（legacy 规划） | wontfix | P3 | — | — | RAG 团队 | — | 已被 B-134（Qdrant）和 B-125（Reranker）拆分替代 |

---

## 6. 已知问题

### ISSUE-002 大规模 chunk 时向量检索响应变慢

- **现象**：项目 chunk 数量超过 5000 时，`/api/search` 响应耗时随 chunk 数线性增长，可达数秒
- **影响范围**：文件数量较多（> 200 个文件）的大型项目
- **复现条件**：导入大型代码仓库或文档库后提问，观察 `/api/search` 耗时
- **临时规避方案**：控制单个项目导入文件数量，或通过文档集合缩小检索范围
- **计划处理方式**：B-134（Qdrant 替换 SQLite 全扫描，v1.0.0）

### ISSUE-003 文档一致性脚本要求缺失的 docs/DEVLOG.md

- **现象**：运行 `.venv\Scripts\python.exe scripts\check_docs_consistency.py` 时失败，提示 `docs/DEVLOG.md` 不存在，无法校验聚合索引
- **影响范围**：文档一致性自动校验；不影响 Web MVP 启动、Docker 启动或 API 主流程
- **复现条件**：在当前仓库根目录运行 `.venv\Scripts\python.exe scripts\check_docs_consistency.py`
- **临时规避方案**：本次 Docker 修复验收以 `tests/test_webapp`、`docker compose config`、Docker 无缓存构建和容器健康检查为准
- **计划处理方式**：待确认是否补回 `docs/DEVLOG.md` 聚合索引，或调整脚本改为校验 `docs/devlog/` 目录结构
