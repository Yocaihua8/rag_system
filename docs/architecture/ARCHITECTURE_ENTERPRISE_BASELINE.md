# 企业化架构基线（阶段 1）

本文档定义“目录先收口、代码后迁移”的执行标准。

## 1. 当前状态

当前仓库仍存在新旧链路并行：

- 主链路：`desktop/qt + backend/core + backend/platform`
- 遗留链路：`legacy/desktop-api + frontend(web legacy) + app/main(legacy cli)`

该状态可运行，但不利于企业化协作和长期维护。

## 2. 目标分层（三分法）

目标目录（企业化三分法）：

- `backend/`：核心业务与平台适配
- `frontend/`：Web 前端（Vite + Vue）
- `desktop/`：桌面端（Qt）
- `legacy/`：遗留冻结代码
- `ops/`：发布与运维脚本
- `docs/`：架构与流程文档

## 3. 阶段策略

### 阶段 1（已执行）

- 创建企业化骨架目录
- 保留旧路径运行能力

### 阶段 2（已执行）

- 代码迁移：
  - `core -> backend/core`（已迁移）
  - `services/platform -> backend/platform`（已迁移）
  - `app/qt -> desktop/qt`（已迁移）
  - `desktop/api + routers/services/db/tasks -> legacy/desktop-api`（已迁移）

### 阶段 3（待执行）

- 清理过渡目录与占位目录
- 统一文档口径与发布清单

## 4. 执行约束

1. 单次迁移只处理一个目录域。
2. 每次迁移后必须验证启动主链路。
3. 保留兼容入口直到迁移全部完成。
4. 不在遗留目录新增业务功能。
