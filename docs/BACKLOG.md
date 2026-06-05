# BACKLOG

> 状态：Active
> Owner：RAG 团队
> Last Updated：2026-05-28（完成 B-146 根目录结构收敛）
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
| B-141 | feature | Vue 3 + Vite 前端工程化 | done | P1 | XL | v1.0.0 | RAG 团队 | docs/features/frontend-engineering.md | 已完成：Vue/Vite 工程骨架和 B-141A-Z 页面级迁移薄片已收口，覆盖资料库、设置、评估、工作台非流式问答、回答反馈、检索调试、项目级检索默认值、检索复盘、Agent 只读工具和工具来源上下文；B-143 后 legacy 静态 fallback 已移除；已按 plan 生命周期删除 B-141 临时计划文件 |
| B-142 | feature | Vue 工作台 SSE 与会话历史迁移 | done | P2 | M | v0.11.0 | RAG 团队 | docs/features/frontend-engineering.md, docs/design/api-spec.md | 已完成：Vue 工作台接入 `/api/answer/stream` EventSource 流式输出、取消当前请求、`/api/chat/sessions*` 与 `/api/chat/messages` 会话列表/历史恢复；未修改后端契约或数据库 schema |
| B-143 | tech-debt | 移除 legacy 静态前端 fallback | done | P2 | M | v0.12.0 | RAG 团队 | docs/features/frontend-engineering.md, docs/guides/setup.md, docs/guides/testing.md | 已完成：删除 `webapp/static/` legacy 原生前端；FastAPI 只服务 `backend/knowledge_island/static_dist/`，缺失构建产物时返回 503 构建提示；删除 legacy 静态前端测试断言并同步前端工程、启动和测试文档 |
| B-144 | tech-debt | 前后端目录结构解耦 | done | P2 | M | v0.12.0 | RAG 团队 | docs/features/fastapi-runtime.md, docs/features/frontend-engineering.md, docs/design/architecture-overview.md | 已完成：FastAPI 后端运行时代码聚合到 `backend/knowledge_island/`，默认启动入口为 `backend/app.py`；Vite 构建输出调整为 `backend/knowledge_island/static_dist/`；同步 Docker、测试 import 和正式文档 |
| B-145 | tech-debt | 目录命名与当前 Web MVP 阶段对齐 | done | P2 | M | v0.12.0 | RAG 团队 | docs/features/fastapi-runtime.md, docs/features/frontend-engineering.md, docs/design/architecture-overview.md | 已完成：后端包统一为 `backend/knowledge_island/`，Web 测试拆为 `tests/backend/` 与 `tests/frontend/`，legacy 桌面端归档为 `legacy/desktop/`，历史架构/发布文档归入 `docs/archive/`；已按 plan 生命周期删除 B-145 临时计划文件 |
| B-146 | tech-debt | 根目录结构收敛 | done | P2 | M | v0.12.0 | RAG 团队 | docs/features/fastapi-runtime.md, docs/features/frontend-engineering.md, docs/design/architecture-overview.md, docs/guides/setup.md, docs/guides/testing.md | 已完成：根目录不再保留前端 npm 配置、Vite shim、Dockerfile、Compose、Docker 双击脚本、Docker quickstart 和文档映射；前端 npm 配置归入 `frontend/`，Docker 入口归入 `ops/docker/`，文档映射归入 `docs/template-mapping.md`；已按 plan 生命周期删除 B-146 临时计划文件 |
| B-147 | tech-debt | 文档一致性检查对齐 devlog 目录结构 | done | P1 | S | v0.12.0 | RAG 团队 | docs/guides/testing.md, docs/README.md | 已完成：`scripts/check_docs_consistency.py` 改为校验当前 `docs/devlog/` 目录和日期日志文件；根 README 文档入口同步为 `docs/devlog/`；已按 plan 生命周期删除 B-147 临时计划文件 |
| B-148 | ux | Vue Web MVP 首屏体验收敛 | done | P1 | S | v0.12.0 | RAG 团队 | docs/features/frontend-engineering.md, docs/design/ui-wireframes.md | 已完成：修复体验审查发现的开发迁移文案外露、项目根目录展示字段不一致、云端模型调用提示不足；已按 plan 生命周期删除 B-148 临时计划文件 |
| B-149 | ux | Vue 海图志视觉重构 | done | P1 | L | v0.12.0 | RAG 团队 | docs/features/frontend-engineering.md, docs/design/ui-wireframes.md | 已完成：将 `知识岛/prototypes/D-atlas/atlas.css` 与 `atlas.jsx` 的海图志视觉语言迁移到 Vue 前端；首屏 masthead、工作台三列、资料库 dashboard/table、评估 frame、设置 frame 已落地；未修改 `frontend/src/api/`、`frontend/src/state/`、后端 API 或数据库 schema；已按 plan 生命周期删除 B-149 临时计划文件 |
| B-150 | ux | Vue 前端产品化收口 | done | P1 | M | v0.12.0 | RAG 团队 | docs/features/frontend-engineering.md, docs/design/ui-wireframes.md | 已完成：补齐顶部主题切换、资料库项目健康概览、集合创建入口与集合面板状态连接；验证 `tests/frontend`、`npm --prefix frontend run build` 和浏览器四主视图；未修改 `frontend/src/api/`、`frontend/src/state/`、后端 API 或数据库 schema；已按 plan 生命周期删除 B-150 临时计划文件 |
| B-151 | ux | Vue 工作台最终可用性修复 | done | P1 | S | v0.12.0 | RAG 团队 | docs/features/frontend-engineering.md, docs/design/ui-wireframes.md | 已完成：新增 `MarkdownBody.vue`，工作台回答正文支持安全 Markdown 渲染；`WorkbenchView.vue` 改为三列独立滚动组合；`styles.css` 末尾追加视口与列滚动 CSS；`QuestionPanel.vue` 提交后清空输入；验证 `tests/frontend` 与 `npm run build`；未修改 `frontend/src/api/`、`frontend/src/state/`；已按 plan 生命周期删除 B-151 临时计划文件 |
| B-152 | ux | Vue 工作台线性会话流收口 | done | P1 | S | v0.12.0 | RAG 团队 | docs/features/frontend-engineering.md, docs/design/ui-wireframes.md | 已完成：工作台中列改为历史轮次 / 流式回答 / 底部 composer 的线性会话流；清理会话面板历史块；masthead 增加项目选择器；空状态按钮可跳转资料库；验证 `tests/frontend`、`npm run build`、preview 浏览器冒烟；未修改 `frontend/src/api/`、`frontend/src/state/`；已按 plan 生命周期删除 B-152 临时计划文件 |
| B-42 | feature | 知识管理仪表盘（第五 Tab） | todo | P2 | L | v0.14.0 | RAG 团队 | docs/plans/phase-2-intelligence-v014.md, docs/design/ui-wireframes.md | 新增「知识库」导航 Tab；展示项目健康状态、掌握分布饼图、知识点列表（按掌握状态分组）、最近评估记录 |
| B-125 | feature | Reranker 重排序接入 | todo | P2 | L | v0.14.0 | RAG 团队 | docs/plans/phase-2-intelligence-v014.md, docs/design/architecture-overview.md | 向量检索 top_k 候选后增加 Cross-Encoder reranker；优先对接 Cohere Rerank API（可选依赖），本地 cross-encoder 作为后备；预估 5 天 |
| B-128 | feature | 对话分支与历史消息编辑重发 | done | P2 | M | v0.13.0 | RAG 团队 | docs/plans/phase-1-quality-v013.md, docs/design/api-spec.md, docs/design/database-design.md, docs/features/frontend-engineering.md | 已完成：chat_messages 追加 parent_message_id / branch_id / is_active；新增 branch_chat_message、GET include_branches 和 POST /api/chat/messages/branch；Workbench 历史用户消息支持内联编辑派生分支；验证 `pytest tests/backend/`、`pytest tests/ -x`、`npm --prefix frontend run build` |
| B-126 | feature | 知识图谱增强检索（Graph-RAG） | todo | P2 | L | v0.15.0 | RAG 团队 | docs/plans/phase-3-knowledge-v015.md, docs/design/database-design.md | `graph_nodes` / `graph_edges` 已建表（B-48），当前检索未使用；GraphBuilder 自动构建图谱；BFS 2 跳扩展 + Reranker 精排；预估 5 天 |
| B-06 | tech-debt | ops/ 运维脚本 | done | P2 | S | v0.13.0 | RAG 团队 | docs/plans/phase-1-quality-v013.md, docs/design/api-spec.md, ops/README.md | 已完成：新增 /api/admin/stats 与 /api/admin/rebuild-index；新增 backup_db.sh / rebuild_index.sh / cleanup_runtime.sh；验证 `pytest tests/backend/` 与 `pytest tests/ -x` |
| B-07 | feature | 结果导出（Markdown / PDF） | todo | P3 | M | backlog | RAG 团队 | — | `data/outputs/` 预留了输出目录，支持将生成结果导出为 Markdown / PDF |
| B-08 | feature | 多工作区并发索引 | todo | P3 | L | backlog | RAG 团队 | docs/design/architecture-overview.md | 当前同一时间只允许一个工作区摄入任务，未来支持队列并发 |
| B-24 | feature | 跨平台打包（macOS / Windows / Linux） | todo | P1 | XL | v1.0.0 | RAG 团队 | docs/plans/phase-4-production-v100.md, docs/guides/release-process.md | PyInstaller 三平台构建；双击启动无需 Python；GitHub Actions 矩阵 CI；预估 7 天 |
| B-25 | test | 端到端 UI 自动化测试 | doing | P2 | M | v0.13.0 | RAG 团队 | docs/plans/phase-1-quality-v013.md, docs/guides/testing.md | Playwright 驱动三条主流程 E2E（工作台问答 / 资料库导入 / 评估周期）；CI 集成；预估 3 天 |
| B-117 | feature | MCP 工具接口实现 | todo | P2 | L | v1.1.0 | RAG 团队 | docs/plans/phase-5-ecosystem-v11x.md | 实现 MCP Server（stdio 模式）；暴露 search_knowledge 和 get_project_overview 两个只读工具；设置页生成 Claude Desktop 配置 |
| B-118 | feature | 多用户 LAN 模式 Alpha | todo | P2 | XL | v1.1.0 | RAG 团队 | docs/plans/phase-5-ecosystem-v11x.md, docs/design/permission-matrix.md | users / project_members 表；邮箱+密码+JWT；owner/editor/viewer 权限；LAN 部署 Docker Compose；预估 7 天 |
| B-119 | research | 网页自动抓取研究 | todo | P3 | S | backlog | RAG 团队 | docs/requirements/functional-modules.md | 当前 URL 来源只做人工粘贴正文；自动抓取涉及网络、权限和依赖，暂缓 |
| B-132 | feature | 网页自动爬取（可选依赖） | todo | P3 | XL | v1.0.0 | RAG 团队 | docs/requirements/functional-modules.md | 对接 `playwright` 或 `requests-html` 实现 URL 来源自动抓取；需解决动态页面、robots.txt 遵守和依赖隔离；B-119 的细化实现；预估 7 天 |
| B-133 | feature | GitHub 仓库整体导入 | todo | P3 | L | v1.0.0 | RAG 团队 | docs/requirements/functional-modules.md | 通过 GitHub API 或 `git clone` 一键导入仓库文件；开发者核心场景；预估 5 天 |
| B-134 | feature | Qdrant 替换 SQLite 向量存储 | done | P2 | L | v0.13.0 | RAG 团队 | docs/plans/phase-1-quality-v013.md, docs/design/architecture-overview.md | 已完成：新增 VectorBackend 抽象、Qdrant local mode 与 SQLite fallback；检索改为通过后端候选融合；chunk 重建同步写入向量后端；新增迁移脚本；验证 qdrant/sqlite 相关后端测试、迁移脚本和 `pytest tests/ -x` |
| B-135 | feature | 多模型并排对比 | todo | P3 | L | backlog | RAG 团队 | docs/design/api-spec.md | 同一问题同时发给 2 个不同 Profile 展示对比回答；预估 5 天 |
| B-136 | docs | OpenAPI / Swagger 接口文档 | done | P3 | M | v0.13.0 | RAG 团队 | docs/plans/phase-1-quality-v013.md, docs/design/api-spec.md, docs/design/openapi.json | 已完成：FastAPI metadata 更新为 v0.13.0，schema endpoint 均补 summary/tags，生成 docs/design/openapi.json；当前 8765 被旧服务占用，已在 18766 验证当前分支 /docs 和 /openapi.json |
| B-137 | feature | Notion / Obsidian 本地导出同步 | todo | P3 | L | v1.0.0 | RAG 团队 | docs/requirements/functional-modules.md | 支持导入 Notion 导出的 Markdown zip 包和 Obsidian vault 目录；预估 4 天 |
| B-23 | feature | Reranker 重排序（legacy） | wontfix | P3 | — | — | RAG 团队 | — | 已被 B-125 替代；原计划在 legacy 链路接入，Web MVP 由 B-125 统一覆盖 |
| B-67 | feature | Web 向量库与 Reranker 接入（legacy 规划） | wontfix | P3 | — | — | RAG 团队 | — | 已被 B-134（Qdrant）和 B-125（Reranker）拆分替代 |
| B-153 | tech-debt | SQLite WAL 模式启用 | done | P2 | XS | v0.13.0 | RAG 团队 | docs/plans/phase-1-quality-v013.md | 已完成：在 storage.py 连接初始化时追加 WAL / synchronous=NORMAL / busy_timeout=5000；新增并发读写测试；验证 `pytest tests/backend/test_concurrent_access.py` 与 `pytest tests/ -x` |
| B-154 | feature | 回答质量指标存储 | done | P2 | S | v0.13.0 | RAG 团队 | docs/plans/phase-1-quality-v013.md, docs/design/database-design.md, docs/design/api-spec.md, docs/features/frontend-engineering.md | 已完成：chat_messages 追加 quality_metrics JSON 列；回答完成时计算 source_coverage / retrieval_top_score / has_sources / answer_length；新增 /api/projects/quality-summary；资料库 dashboard 展示回答有来源率；验证 `pytest tests/backend/`、`pytest tests/ -x`、`npm --prefix frontend run build` |
| B-155 | feature | HyDE 查询增强 | todo | P2 | M | v0.14.0 | RAG 团队 | docs/plans/phase-2-intelligence-v014.md | 先让 LLM 生成假设答案，用假设答案 embedding 做向量检索；retrieval_settings 可开关；预估 2 天 |
| B-156 | feature | 多路查询改写 | todo | P2 | M | v0.14.0 | RAG 团队 | docs/plans/phase-2-intelligence-v014.md | 将问题改写为 3 个语义等价变体并发检索，RRF 融合去重；retrieval_settings 可开关；预估 2 天 |
| B-157 | feature | 自动更新机制 | todo | P1 | M | v1.0.0 | RAG 团队 | docs/plans/phase-4-production-v100.md | 打包版本启动时后台检查 GitHub Releases 最新版本；masthead 显示更新提示；不自动安装，只引导下载 |
| B-158 | tech-debt | 安全审计与加固 | todo | P1 | M | v1.0.0 | RAG 团队 | docs/plans/phase-4-production-v100.md | API Key 迁移到系统 Keychain；pip-audit + npm audit；路径穿越扫描；认证 v1.0.0 起默认开启 |
| B-159 | feature | 浏览器扩展（Chrome/Firefox） | todo | P2 | L | v1.1.0 | RAG 团队 | docs/plans/phase-5-ecosystem-v11x.md | Manifest V3 扩展；侧边栏提问 + 一键存入；调用本地 127.0.0.1:8765；预估 5 天 |
| B-160 | feature | 后台定时任务（APScheduler） | todo | P2 | M | v1.1.0 | RAG 团队 | docs/plans/phase-5-ecosystem-v11x.md | 自动目录同步 + 自动备份；设置页可配置时间；应用重启后恢复；预估 3 天 |
| B-161 | feature | 插件 API | todo | P3 | XL | v2.0.0 | RAG 团队 | docs/plans/phase-6-platform-v20.md | DataSourcePlugin / AssessmentPlugin / RerankerPlugin 协议；插件沙箱（独立线程 + 超时）；三个官方参考插件 |
| B-162 | feature | 知识岛协议 KIP v2 | todo | P3 | L | v2.0.0 | RAG 团队 | docs/plans/phase-6-platform-v20.md | .kib 标准交换格式（documents / chunks / vectors / graph）；Python SDK；规范发布到 GitHub |
| B-163 | feature | 移动端只读伴侣 | todo | P3 | XL | v2.0.0 | RAG 团队 | docs/plans/phase-6-platform-v20.md | React Native + Expo；iOS + Android；局域网连接桌面服务；提问 / 历史 / 笔记存入；不支持文档管理 |

---

## 6. 已知问题

### ISSUE-002 大规模 chunk 时向量检索响应变慢

- **现象**：项目 chunk 数量超过 5000 时，`/api/search` 响应耗时随 chunk 数线性增长，可达数秒
- **影响范围**：文件数量较多（> 200 个文件）的大型项目
- **复现条件**：导入大型代码仓库或文档库后提问，观察 `/api/search` 耗时
- **临时规避方案**：控制单个项目导入文件数量，或通过文档集合缩小检索范围
- **计划处理方式**：B-134（Qdrant 替换 SQLite 全扫描，v1.0.0）
