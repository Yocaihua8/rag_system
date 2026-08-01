# 系统设计总览

> 状态：Active
> Owner：RAG 团队
> Last Updated：2026-08-01
> Scope：Knowledge Island 的系统组成、运行形态和主要数据流
> Related：`architecture-overview.md`、`api-spec.md`、`database-design.md`、`permission-matrix.md`、`../adr/README.md`

Knowledge Island 是一个本地优先的完整系统。Vue、FastAPI、SQLite、Tauri、Docker 和 Obsidian 插件是不同运行职责，不是彼此独立的产品或文档专题。

## 1. 系统组成

| 组成 | 当前职责 | 不承担 |
|------|----------|--------|
| Vue 应用 | 工作区导航、教练、学习地图、学习计划、资料弹窗、设置和评估/逐点学习覆盖层 | 业务状态机、数据库访问、重试/评分/计划完成判定、Agent 权限判断 |
| FastAPI | HTTP/SSE、CORS、可选认证、参数校验、OpenAPI 和用例分发 | 托管前端静态文件、直接在 HTTP 层写 SQL |
| 领域与存储 | 导入、检索、回答、Coach 分析/评估/逐点学习、SQL 练习评分、发布和 SQLite 持久化 | 页面布局或浏览器状态 |
| SQLite | 当前关系数据、来源、向量兼容副本、审计和状态 | 多租户隔离或远端共享数据库承诺 |
| Qdrant local mode | 启用时提供向量候选 | 替代 SQLite 权威数据或保存业务状态 |
| Tauri | 窗口、托盘、sidecar 生命周期和安装包 | 复制后端业务逻辑 |
| Obsidian 插件 | Markdown 变更事件、排队发布领取、Vault 写入和结果回传 | 绕过用户确认或直接访问 SQLite |
| Docker | 分别运行静态前端和 API 服务 | 前端反向代理 API |

## 2. 运行形态

| 形态 | 用户入口 | API | 关键约束 |
|------|----------|-----|----------|
| 本地开发 | `127.0.0.1:5173` | `127.0.0.1:8765` | 通过 `VITE_API_BASE_URL` 使用绝对 URL |
| 前端预览 / Docker | `127.0.0.1:4173` | `127.0.0.1:8765` | 两个服务、两个健康检查，Nginx 不代理 API |
| Tauri | 本地 WebView | sidecar `127.0.0.1:8765` | 打包 `frontend/dist`，CSP 只开放所需连接 |
| Obsidian | Vault 内插件界面 | 本机 `127.0.0.1:8765` | 插件专用 Bearer 令牌和受控输出根 |

FastAPI 根路由不提供产品首页，`GET /` 返回 404；接口文档位于 `/docs`、`/redoc` 和 `/openapi.json`。

## 3. 主要数据流

```text
用户选择来源
  -> 导入适配与校验
  -> documents / document_chunks / chunk_vectors
  -> BM25 + 向量检索（可选 Qdrant）
  -> 来源约束回答、项目分析、评估或逐点学习
  -> 聊天、评估/attempt 证据、覆盖、计划与审计记录
  -> 用户预览并确认
  -> Obsidian 插件写入受管 Markdown 并回传结果
```

- 导入时分块实现当前固定使用 700 字符上限和 80 字符重叠；配置对象虽加载 `RAG_CHUNK_SIZE` / `RAG_CHUNK_OVERLAP`，当前 Web 入库链路没有把它们传给分块函数。
- 问答 SSE 使用 `GET /api/answer/stream`，按 `token`、`done`、`answer_error` 事件推进；Ollama 拉取是另一条 `POST /api/ollama/pull` SSE 流。
- 来源变化会影响检索，并使相关 Coach 分析进入 `stale`；历史结果可以追溯但不能冒充当前结果。
- 逐点学习一次只公开当前步骤和 exercise；有效 attempt 可进入当前覆盖投影，从确认计划任务启动时还可单调推进该任务进度。
- SQL 题由来源中的可解析 SQLite Schema 证据生成，学习者查询只在结构化 fixture 创建的临时只读数据库中执行，不连接正式业务 SQLite。
- 发布确认只把任务推进到 `queued`；只有插件回传结果后才进入 `applied`、`conflict` 或 `failed`。

## 4. 依赖真实状态

| 依赖 | 安装状态 | 当前使用状态 |
|------|----------|--------------|
| `qdrant-client` | `backend/requirements/base.txt` | 可选启用 Qdrant local mode；失败回退 SQLite |
| `jieba` | `backend/requirements/base.txt` | 中文分词与检索链路使用 |
| `pinia` | `frontend/package.json` | 已声明但当前应用未创建或使用 Pinia store；状态由 `App.vue` 与响应式单例管理 |
| `pymupdf` | 不在 base/dev requirements | 可选 PDF 抽取；缺失时跳过 PDF 并报告原因 |
| `sentence-transformers` | 不在 base/dev requirements | 可选 Cross-Encoder rerank；默认关闭，缺失时保持原排序 |

依赖声明不等于功能默认启用；可选依赖和降级必须在响应或日志中保持可辨识。

## 5. 权威源

- 方法、路径和字段：[`api-spec.md`](api-spec.md) 与 routes/dispatch 测试。
- 当前 43 张表和字段：[`database-design.md`](database-design.md) 与 `backend/storage/`。
- 可达页面和接线状态：[`page-module-contract.md`](page-module-contract.md) 与 `frontend/src/App.vue`。
- 认证、CORS、Key 和工具边界：[`permission-matrix.md`](permission-matrix.md)。
- 决策原因和取代关系：[`../adr/README.md`](../adr/README.md)。
