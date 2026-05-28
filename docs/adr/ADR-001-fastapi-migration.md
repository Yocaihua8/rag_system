# ADR-001 迁移至 FastAPI（替代 Python stdlib HTTP）

> 状态：Accepted
> Date：2026-05-26
> Owner：RAG 团队
> Related：`../design/architecture-overview.md`、`../design/api-spec.md`、`../../BACKLOG.md`

## 1. 背景

Web MVP（v0.7.0，2026-05-21）选择 Python stdlib `http.server` 作为 HTTP 服务层，核心理由是：

- 零运行时依赖，符合 MVP 阶段"不新增必需运行时依赖"的约束
- 快速出包，降低部署复杂度
- 团队规模小，功能迭代优先于框架完整性

随着项目演进至 v0.9.0，以下需求使 stdlib HTTP 的局限性成为**结构性阻力**：

1. **前后端分离**：计划将前端迁移为独立工程（Vue 3 + Vite），后端变为纯 API 服务。此时 CORS、认证中间件等 API 基础设施需求大幅增加，而 stdlib 缺乏标准挂载点。
2. **多客户端**：桌面端（Tauri）、移动端（PWA / Flutter）共享同一套 API，需要标准化的认证头、错误响应和 OpenAPI 文档。
3. **SSE 流式输出维护成本**：当前 `/api/answer` 的流式实现依赖手写 chunked response（约 40 行），每次修改容易引入协议错误。
4. **API 文档硬需求**：B-136 要求提供 OpenAPI/Swagger 文档，stdlib 下只能全量手写。

v0.9.0 完成了 `backend/knowledge_island/api.py` 的领域路由拆分（B-138），路由层与业务层边界已清晰，**迁移窗口已到，且当前 P1 BACKLOG 已清空**。

## 2. 决策结论

在前后端分离阶段，将 HTTP 服务层从 **Python stdlib `http.server`** 迁移至 **FastAPI + Uvicorn**。

**边界约定**：

- `backend/knowledge_island/storage.py` 保持不变
- `backend/knowledge_island/search.py`、`backend/knowledge_island/answers.py`、`backend/knowledge_island/ingestion.py` 等业务层保持不变
- 仅替换路由层（`backend/knowledge_island/routes/*.py`）与服务器启动逻辑（`backend/knowledge_island/server.py`、`backend/app.py`）
- B-143/B-145 后，FastAPI 只服务 `backend/knowledge_island/static_dist/` 构建产物

## 3. 决策原因

1. **与 storage.py 无缝兼容**：FastAPI 无 ORM，现有裸 SQLite 层零改动
2. **原生 async + SSE**：`async def` 路由 + `StreamingResponse` 替换手写 chunked，代码量减少约 60%
3. **路由迁移成本最低**：`backend/knowledge_island/routes/*` 已按领域拆分（B-138），一对一映射为 FastAPI Router
4. **OpenAPI 免费得到**：B-136（OpenAPI/Swagger 文档）迁移完成后自动实现，无需额外工作
5. **认证中间件标准化**：`Depends()` 注入模式支持统一 Auth 校验，无需每个路由手写

## 4. 备选方案

### 4.1 方案 A：Flask

- 优点：轻量，学习曲线低，Blueprint 结构与现有路由相近
- 缺点：同步优先（async 为后补），SSE 需手写，无自动 API 文档
- 未采用原因：SSE 和 API 文档是硬需求，Flask 需额外插件，不如 FastAPI 原生

### 4.2 方案 B：Django + DRF

- 优点：生态完整，有 Admin 后台
- 缺点：ORM 与 `storage.py` 形成反模式；SSE 需 Django Channels，引入 Redis/Daphne 部署依赖；项目结构强制重组
- 未采用原因：结构性冲突，迁移收益低于成本（详见会话讨论记录 2026-05-26）

### 4.3 方案 C：继续使用 stdlib HTTP

- 优点：零迁移成本
- 缺点：CORS 手写、认证中间件无挂载点、SSE 维护困难、OpenAPI 需全量手写，多客户端支持成本持续累积
- 未采用原因：前后端分离与多客户端目标下，技术债增速高于维护收益

## 5. 影响

### 5.1 正面影响

- CORS 中间件一行配置，不再散落各路由
- SSE 实现从约 40 行降至约 5 行（`StreamingResponse`）
- OpenAPI/Swagger 文档自动生成（`/docs` 路由）
- 认证中间件统一通过 `Depends()` 注入
- Uvicorn ASGI 吞吐量优于 stdlib HTTPServer，SSE 背压处理更稳定

### 5.2 负面影响

- 新增两个运行时依赖：`fastapi`、`uvicorn[standard]`（总约 10MB，无重型传递依赖）
- 现有 `app.py` 入口与 `webapp/server.py` 需重写
- Docker 镜像需重新验证构建与启动

### 5.3 对现有系统的改动点

| 模块 | 变更内容 |
|------|----------|
| `backend/knowledge_island/server.py` | 替换为 FastAPI `app` 实例 + Uvicorn 启动逻辑 |
| `backend/knowledge_island/api.py` | `dispatch()` 逻辑迁移为 FastAPI Router；`answer_stream_events` 改为 `StreamingResponse` |
| `backend/knowledge_island/routes/*.py` | 路由函数签名改为 `async def` + Pydantic 请求体 |
| `backend/app.py` | 入口改为 `backend.knowledge_island.server:app` |
| `requirements.txt` | 新增 `fastapi`、`uvicorn[standard]` |
| `backend/knowledge_island/static_dist/` | Vue/Vite 生产构建产物目录，由 FastAPI 静态服务托管 |

## 6. 后续动作

### 6.1 实施计划

| 项目 | 内容 |
|------|------|
| 实施开始日期 | 2026-05-27（估算）|
| 实施结束日期 | 2026-06-03（估算，约 1 周）|
| 实施负责人 | RAG 团队 |
| 里程碑 | v1.0.0 |
| 关联 BACKLOG | B-139 |

### 6.2 回滚策略

| 项目 | 内容 |
|------|------|
| 回滚触发条件 | 迁移后 `tests/backend/` 与 `tests/frontend/` 回归失败率 > 5%，或 `/api/answer` SSE 流式输出中断 |
| 回滚步骤 | `git revert` 迁移相关 commits；恢复 `backend/knowledge_island/server.py` 与 `backend/app.py` 原实现；回退 `requirements.txt` |
| 数据回滚说明 | N/A（`storage.py` 不变，无数据迁移） |
| 回滚责任人 | RAG 团队 |
| 不可回滚的点 | 若迁移中同步修改了 `storage.py`，该部分需单独评估 |

### 6.3 验证方式

- **验证指标**：`tests/backend/` 与 `tests/frontend/` 全量通过率、`/api/answer` SSE 流式输出可用性、`/docs` OpenAPI 页面可访问
- **观察窗口**：迁移完成后首次完整测试运行通过
- **验收标准**：全部现有测试通过；`/docs` 正常访问；SSE 流输出行为与迁移前一致；现有前端页面功能无回归

### 6.4 待办项

- [ ] B-139：FastAPI 替代 stdlib HTTP（本 ADR 的代码实施）
- [ ] B-140：认证中间件实现（ADR-005 前置，与 B-139 串行）
- [ ] B-141：Vue 3 + Vite 前端工程化（前后端分离的另一半，在 B-139 完成后开始）
