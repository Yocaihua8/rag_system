# 结构性收口基线（2026-04）

本文档用于明确当前代码库重构后的主路径边界，避免继续混线开发。

## 1. 主路径（Active）

当前主路径采用目录级分层：

- `desktop/`：桌面壳（入口 + 启动 + UI）
- `backend/app/`：业务模块与应用服务
- `backend/core/`：系统核心能力（配置/日志/异常/生命周期）
- `backend/infra/`：基础设施适配（storage/model）
- `desktop/main.py`：桌面统一入口

### 主调用方向

`desktop -> backend.app -> backend.infra`

## 2. 遗留路径（Legacy, 冻结）

以下目录仅用于历史参考与迁移对照：

- `archive/legacy-20260407/desktop-api/`
- `frontend/`（本轮未做内部重构）

## 3. 新增代码约束

1. 新增桌面功能进入 `desktop/app` 与 `desktop/ui`。
2. 新增业务模块进入 `backend/app/modules`。
3. 新增基础设施适配进入 `backend/infra`。
4. 禁止新增 `backend/platform`、`desktop/qt` 路径。

## 4. 运行入口

推荐统一入口：

```powershell
py -3 desktop\main.py
```

后端模块导入检查：

```powershell
py -3 -c "import backend.app.main"
```
