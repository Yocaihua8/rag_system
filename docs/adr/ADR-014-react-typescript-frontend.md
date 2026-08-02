# ADR-014 v3 前端采用 React 与 TypeScript

> 状态：Accepted
> Date：2026-08-02
> Owner：RAG 团队
> Scope：v3 Web/Tauri 前端框架、状态边界、工作流画布和迁移方式
> Related：`../design/ui-prototype-brief-v3.md`、`ADR-006-vue-vite-frontend.md`、`ADR-010-runtime-separation.md`

## 1. 背景

当前 Vue 3/JavaScript 前端由大型 `App.vue` 统一编排，页面状态和高级能力逐步堆叠。v3 需要多面板任务工作台、类型化 SSE 事件、审批卡和 DAG 编辑器，继续在现有 Vue 页面渐进扩展会保留当前结构性问题。

## 2. 决策结论

P2 原型明确批准后，在独立 `frontend-v3/` 建立：

- React 19、TypeScript 6 和 Vite 8；使用 Hash Router 让同一构建产物适配 Web 静态服务与 Tauri。
- TanStack Query 管理后端权威数据；Zustand 只管理临时 UI、布局和工作流草稿。
- React Flow 与 ELK.js Worker 提供类型化 DAG 画布和自动布局。
- Tailwind CSS、CSS Variables、Radix Primitives 和 Lucide 构成内部 UI 层。
- React Hook Form 与 Zod 管理表单；OpenAPI 生成 TypeScript 类型并由 `openapi-fetch` 调用。
- Vitest、React Testing Library 和 Playwright 覆盖组件与真实后端流程。

现有 Vue 前端在 React 完整验收前保持可运行；不在同一运行时混合 Vue 与 React。最终切换后再删除 Vue 代码和依赖。

## 3. 决策原因

1. React Flow 的类型和工作流生态更适合本产品最复杂的 DAG 编辑场景。
2. TypeScript discriminated union 能静态覆盖运行、步骤、事件、审批和产物状态。
3. Query 与 UI 草稿状态分离可避免再次形成大型中央状态对象。
4. 平行替换允许当前 v2 在迁移期间继续验证和回滚。

## 4. 备选方案

### 4.1 Vue 3 + TypeScript 增量重构

- 优点：可以复用更多组件和测试，迁移成本较低。
- 缺点：工作流生态较小，仍需要拆除现有集中编排。
- 未采用原因：长期产品质量和 DAG 能力优先于最低迁移成本。

### 4.2 Next.js 或 Electron

- 优点：分别提供服务端框架或 Node 桌面运行时。
- 缺点：本产品不需要 SSR/RSC，也没有必须依赖 Electron/Node 的桌面能力。
- 未采用原因：增加无必要运行时和打包复杂度。

## 5. 影响

### 5.1 正面影响

- API 与事件类型由 OpenAPI 统一生成。
- 页面、面板、工作流和测试边界更容易拆分。

### 5.2 负面影响

- 现有 Vue UI 实现大部分需要重写。
- 迁移期间需要维护两个独立前端目录和验证入口。

### 5.3 对现有系统的改动点

- 根 npm workspace 在 P2 后暂时加入 `frontend-v3`。
- 最终切换 Tauri、Docker 和根脚本到 React 产物。
- ADR-006 的 Vue 框架结论被本 ADR 取代；ADR-010 的运行时分离继续有效。

## 6. 后续动作

### 6.1 实施计划

| 项目 | 内容 |
|------|------|
| 实施开始日期 | P2 明确批准后 |
| 实施结束日期 | TBD |
| 实施负责人 | RAG 团队 / Codex |
| 里程碑 | 应用壳、任务时间线、工作流、项目洞察、设置、切换 |

### 6.2 回滚策略

| 项目 | 内容 |
|------|------|
| 回滚触发条件 | React 真实后端 E2E 或 Desktop 验收不通过 |
| 回滚步骤 | 保持 Tauri/Docker/根脚本继续指向现有 Vue；移除未切换的 `frontend-v3` |
| 数据回滚说明 | N/A，前端替换不迁移业务数据 |
| 回滚责任人 | RAG 团队 |
| 不可回滚的点 | N/A，切换前 Vue 保持完整 |

### 6.3 验证方式

- P1/P2 均获得明确批准。
- 生成类型、单测、构建和连接真实 v3 后端的 E2E 通过。
- Tauri 与 Web 使用同一构建产物且路由可直接打开。

### 6.4 待办项

- P2 前禁止创建 `frontend-v3/` 或修改 Vue 页面。
