# 架构总览

> 状态：Active
> Owner：RAG 团队
> Last Updated：2026-08-01
> Scope：Knowledge Island v2.0 当前源码、运行时与集成边界
> Related：`backend/api/server.py`、`backend/storage/knowledge_store.py`、`../product/overview.md`、`backend/api.md`、`decisions/ADR-010-runtime-separation.md`

Knowledge Island 是本地优先的项目知识教练。当前系统由独立 Vue 前端、FastAPI 后端、SQLite 数据层、Tauri 桌面壳和独立 Obsidian 插件组成。前后端通过 HTTP/SSE 通信，不共享依赖或构建产物。

## 1. 运行时拓扑

```text
浏览器 / Tauri WebView
  frontend/dist（dev 5173，preview/Docker 4173）
              │ VITE_API_BASE_URL；REST + SSE
              ▼
FastAPI API（127.0.0.1:8765）
  backend/api + backend/routes
              │ 用例编排
              ▼
领域服务（backend/domain）
  导入、检索、回答、Coach、Obsidian、只读 Agent 工具
              │ 唯一持久化入口
              ▼
SQLite + 可选 Qdrant local mode
  runtime/v2/app.db + runtime/v2/vectors
```

- `python -m backend` 启动 API；FastAPI 不托管前端，`GET /` 返回 404。
- `frontend/` 拥有 Vue、Vite、Vitest 和 Playwright；生产构建只写入 `frontend/dist/`。
- `src-tauri/` 只承载窗口、托盘和 sidecar 生命周期；它打包 `frontend/dist/`，sidecar 只包含后端。
- `integrations/obsidian-plugin/` 是独立 desktop-only 工程，不进入根 npm workspace。
- Docker 由 `ops/docker/compose.yaml` 启动两个独立服务；前端不反向代理 API。

端口和跨域决策见 [ADR-010](decisions/ADR-010-runtime-separation.md)。

## 2. 后端分层

| 层 | 路径 | 职责 |
|----|------|------|
| 入口 | `backend/__main__.py` | 加载配置并启动 Uvicorn |
| HTTP | `backend/api/`、`backend/routes/` | 鉴权、参数校验、响应映射、SSE；不得直接操作 SQLite |
| 领域 | `backend/domain/` | 导入、检索、回答、评估、计划、Agent 与 Obsidian 用例 |
| 存储 | `backend/storage/` | Schema 初始化与全部 SQLite 读写 |
| 配置/provider | `backend/config/`、`backend/providers/` | 路径、环境变量、LLM、Embedding 与向量 provider |

后端继续保持既有 HTTP 方法、路径、请求/响应字段和 SQLite Schema。API 字段级契约见 [`backend/api.md`](backend/api.md)，数据结构见 [`backend/data.md`](backend/data.md)。

## 3. 前端边界

- Vue 只负责页面状态、展示、输入校验和 API 调用，不在浏览器实现业务规则。
- `frontend/src/api/` 统一经 API base 生成绝对 URL；`fetch` 与 `EventSource` 使用相同配置。
- 默认 API base 为 `http://127.0.0.1:8765`，部署时由 `VITE_API_BASE_URL` 在构建阶段显式覆盖。
- 用户主流程为教练、学习地图、学习计划、资料和设置；部分兼容组件仍存在但不代表主导航可达。
- 来源、覆盖、评估、计划冲突和 Obsidian 发布状态均以后端结果为准。

页面与组件约定见 [`frontend/`](frontend/)，前后端契约对照见 [`contracts/frontend-backend.md`](contracts/frontend-backend.md)。

## 4. 数据与模型

- v2 默认数据根为 `runtime/v2/`；正式启动在写入前检查数据代际。
- v2 不自动迁移、删除或覆盖 1.x 数据。需要旧资料时通过支持的重新导入或项目导出/恢复流程处理。
- SQLite 是关系数据和向量兼容副本的唯一权威入口；可选 Qdrant local mode 只承担向量候选，失败时回退 SQLite。
- LLM 和 OpenAI-compatible Embedding 均为可选；不可用时分别回退来源片段组合回答和本地 hashing 向量。
- API Key 只保存 `env:*` / `saved:*` 引用；接口不得回显明文。

## 5. 安全与权限

- Agent 工具白名单硬编码，当前只允许只读操作，不执行 shell 或写入。
- 可选共享 API Key + HS256 JWT 认证默认关闭；它不是多用户、租户或 RBAC 系统。
- CORS 使用精确 Origin allowlist，不启用通配符和 cookie credentials。
- Obsidian 发布必须经过预览、用户确认、插件领取、受管文件校验和结果回传；冲突不覆盖。

权限矩阵见 [`contracts/permissions.md`](contracts/permissions.md)，安全操作见 [`../operations/security.md`](../operations/security.md)。

## 6. 产品与发布边界

- `v2.0.0` 已发布；Windows x64 NSIS 已验证并发布但未签名。
- macOS/Linux 的历史 1.x 产物不能作为当前 v2 原生包通过证据；目标平台构建需按当前源码重新验证。
- `/api/health` 是进程活性检查，不证明 SQLite、外部模型、向量库或完整问答链路就绪。
- Tauri 静态配置和 bundle 成功不能替代安装后 WebView 到 sidecar 的动态 API 连通性验证。
- 未完成事项只记录在 [`../BACKLOG.md`](../BACKLOG.md)；已完成事实进入 `CHANGELOG.md` 和 Git 历史，不再建立 readiness 快照、DevLog 或已验收 preview。

## 7. 不允许的耦合

- FastAPI 不读取或托管 `frontend/dist/`。
- 前端不直连 SQLite，不复制后端业务状态机，不持有 Obsidian 插件令牌。
- `backend/api/` 和 `backend/routes/` 不写 SQL。
- Tauri 不复制业务逻辑；Obsidian 插件不绕过应用侧确认流程。
- Docker 前端不反向代理 API；外部访问地址必须通过构建配置明确传入。
