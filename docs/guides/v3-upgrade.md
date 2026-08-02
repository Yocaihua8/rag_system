# v3 工程迁移指南

> 状态：Active
> Owner：RAG 团队
> Last Updated：2026-08-02
> Scope：从当前 v2 基线迁移到 v3 通用项目 Agent 的实施、验证与回滚顺序
> Related：`../requirements/agent-product-v3.md`、`../design/v3-document-migration.md`、`../design/ui-prototype-brief-v3.md`、`../adr/ADR-015-v3-data-api-storage.md`

## 1. 当前与目标

- 当前可运行基线：Vue 3/Vite + FastAPI v2 API + `runtime/v2/app.db` + Tauri 2。
- 目标：React/TypeScript + `/api/v3` + 持久 Agent runtime + `runtime/v3/app.db` + Tauri sidecar 安全启动。
- 迁移期间 v2 与 v3 必须使用独立前端入口、API 语义和数据根，不能共享业务表或把目标能力描述为当前可用。

## 2. 执行顺序

1. 冻结产品、权限、数据、工作流和 UI 原型合同，建立每日 DevLog。
2. 在不修改 Vue 的前提下实现独立 v3 Schema、资源 API、持久执行器和真实只读垂直切片。
3. 实现随机环回端口、一次性启动令牌、存储预检、备份和恢复等非视觉 Desktop 能力。
4. 完成并确认 P1 信息架构；当前 Revision 3 已获得用户明确实施授权，门禁变更见 ADR-017。
5. 建立独立 React 前端，通过 OpenAPI 类型连接真实 v3 后端；原 P2 高保真要求并入 React 实现验收。
6. Web 与 Desktop E2E 通过后切换正式前端、Tauri 和镜像入口。
7. 最后删除旧 Vue、v2 路由和已安全吸收的旧文档。

## 3. 数据门禁

v3 启动只允许创建或打开带 `data_generation=v3` 标记的数据库。不得把 `KnowledgeStore` 或 v2 Schema 初始化到 v3 数据根。

删除旧数据库前：

1. 停止所有 Knowledge Island 进程。
2. 解析并确认准确目标是仓库内 `runtime/v2/app.db`。
3. 使用只读连接统计全部业务表，确认均为空。
4. 确认数据库没有未提交 WAL、锁或占用进程。
5. 任一检查失败立即停止，不删除数据库或相邻文件。

删除仅限已确认的 `app.db`；不删除其他 runtime 数据库、向量目录、输出、备份或用户数据。

## 4. 前端门禁

- P1 Revision 3 已由用户明确授权作为 React 实施基线；该例外由 ADR-017 冻结。
- React 实现必须确认三种主题、视觉 token、文案、键盘、响应式和危险动作，未通过时不得进入后续联调或最终切换。
- 当前授权只允许创建独立 React 目录；继续禁止修改 Vue UI、切换 Tauri/Docker/根正式入口或删除旧前端。
- 原型使用的演示内容不能复制到运行时、测试服务或错误回退。

## 5. 阶段验证

| 阶段 | 最低验证 |
|------|----------|
| 后端垂直切片 | Schema/generation、项目、任务、运行、事件续传、并发和恢复测试 |
| Desktop 基础设施 | sidecar 令牌、随机端口、存储预检、备份校验和恢复失败回滚 |
| React 基础 | 类型生成、typecheck、单测、构建、主题和路由 |
| 真实联调 | Playwright 连接本地后端完成任务、审批、工作流和产物 |
| 最终切换 | Python 测试、前端测试/build/E2E、Cargo、文档门禁和安装包冒烟 |

## 6. 回滚

- 最终切换前：继续让根脚本、Tauri 和 Docker 指向 v2/Vue，停用 v3 路由即可回滚。
- 最终切换后但尚未产生外部写入：恢复上一个提交和 v2 配置；v3 数据根保留供诊断。
- 已由用户批准的文件或外部系统写入不能通过数据库回滚撤销，必须使用对应产物审计和补偿操作。
- 回滚不得把 v3 数据反向写入 v2，也不得自动删除任何代际数据。
