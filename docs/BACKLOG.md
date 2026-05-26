# BACKLOG

> 状态：Active
> Owner：RAG 团队
> Last Updated：2026-05-26（新增 B-139/B-140/B-141 技术栈迁移；B-138 已完成归档）
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
| B-141 | feature | Vue 3 + Vite 前端工程化 | doing | P1 | XL | v1.0.0 | RAG 团队 | docs/design/architecture-overview.md | 前后端分离：新建 frontend/ 目录，迁移 webapp/static/；B-139/B-140 已完成；ADR-006 代码实施；plans: docs/plans/B-141-vue-vite-foundation.md, docs/plans/B-141-vue-api-layout.md, docs/plans/B-141-vue-project-space.md, docs/plans/B-141-vue-workbench-answer-entry.md, docs/plans/B-141-vue-document-list-preview.md, docs/plans/B-141-vue-text-url-import.md, docs/plans/B-141-vue-import-batch-history.md, docs/plans/B-141-vue-file-upload-import.md, docs/plans/B-141-vue-browser-folder-import.md |
| B-42 | feature | 知识库辅助管理页 | todo | P2 | L | v0.11.0 | RAG 团队 | docs/design/ui-wireframes.md | 参考 SAS 后台式知识库，展示项目状态、文件列表、项目知识点、评估题库和最近结果 |
| B-125 | feature | Reranker 重排序接入 | todo | P2 | L | v0.11.0 | RAG 团队 | docs/design/architecture-overview.md | 向量检索 top_k 候选后增加 Cross-Encoder reranker；优先对接 Cohere Rerank API（可选依赖），本地 cross-encoder 作为后备；预估 5 天 |
| B-128 | feature | 对话分支与历史消息编辑重发 | todo | P2 | M | v0.11.0 | RAG 团队 | docs/design/api-spec.md | 支持在某条历史消息上编辑并重发，派生新对话分支；Claude.ai / ChatGPT 标配交互；预估 3 天 |
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
| B-137 | feature | Notion / Obsidian 本地导出同步 | todo | P3 | L | v1.0.0 | RAG 团队 | docs/requirements/functional-modules.md | 支持导入 Notion 导出的 Markdown zip 包和 Obsidian vault 目录；预估 4 天 |
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
