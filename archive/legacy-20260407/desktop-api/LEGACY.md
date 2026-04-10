# LEGACY 目录说明

本目录包含历史阶段的桌面 API / WebView 链路代码（FastAPI + 前端壳）。

当前重构后的主路径为：

- `desktop/qt/`
- `backend/core/`
- `backend/platform/`

统一调用方向：

`desktop.qt -> backend.core -> backend.platform`

## 使用约束

1. 本目录默认不再承接新增功能开发。
2. 允许用于历史实现参考与迁移对照。
3. 如需修复线上阻断问题，可做最小修复，但应同步规划迁移到主路径。

## 当前入口说明

- `desktop/main.py` 仅作为启动兼容转发入口，实际启动逻辑在 `desktop.qt.app`。
