# 前端工程化

> 状态：Active
> Owner：RAG 团队
> Last Updated：2026-08-01
> Scope：Vue 3 前端的源码、依赖、构建、API 与测试边界
> Related：`../../architecture/decisions/ADR-006-vue-vite-frontend.md`、`../../architecture/decisions/ADR-010-runtime-separation.md`、`../../architecture/frontend/pages.md`、`../../operations/testing.md`

## 当前实现

- `frontend/` 是独立 npm workspace，拥有 Vue、Vite、Vitest、Playwright、Nginx 和前端 Dockerfile。
- Vite 开发端口为 `5173`，preview/Docker 对外端口为 `4173`，生产输出为 `frontend/dist/`。
- FastAPI 不托管前端。前端通过 `VITE_API_BASE_URL` 生成 `fetch` 和 `EventSource` 的绝对地址；默认 `http://127.0.0.1:8765`。
- 根 `package.json` 只负责编排 frontend 与 src-tauri workspace，不持有 Vue/Vite/Playwright 依赖。

## 页面边界

当前一级入口为教练、学习地图、学习计划、资料和设置。Vue 只负责展示、页面状态和 API 调用：

- 项目分析、知识点、覆盖、评估和计划状态以后端 Coach API 为准。
- 来源统一来自服务端，不在浏览器拼造证据。
- Obsidian 用户侧只发起配对、查询/撤销连接、预览和确认；插件令牌与执行接口不可由浏览器调用。
- 兼容组件或后端能力若未挂入主导航，不描述为当前可达闭环。
- 当前未接线控件见 `docs/BACKLOG.md ISSUE-008`。

## API 客户端约束

- API base 去除末尾 `/` 后与 `/api/...` 路径拼接。
- `fetch` 和 `EventSource` 必须复用同一 URL helper。
- API base 是公开部署配置，不能包含凭证。
- 前端不能使用相对 `/api` 依赖反向代理或同源假设。
- API Key/JWT 只通过既有认证 header 发送，不启用 cookie credentials。

## 命令与验证

```powershell
npm run frontend:dev
npm run frontend:test
npm run frontend:build
npm run frontend:e2e
```

API client 单测必须断言绝对 URL；E2E 使用 4173 前端和 18765 隔离后端覆盖真实跨域、SSE 和核心用户流程。

## 不变边界

B-168 不修改 API 方法/字段/响应、SQLite Schema 或 Agent 权限。前端运行时分离只改变构建位置、访问地址和部署拓扑。
