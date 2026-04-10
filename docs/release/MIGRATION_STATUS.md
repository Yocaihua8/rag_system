# 三分法迁移状态

更新时间：2026-04-07

## 已完成

1. 根目录收口为：`backend/`、`frontend/`、`desktop/`、`docs/`、`ops/`、`scripts/`、`runtime/`、`data/`、`archive/`。
2. 文档归档完成：
   - `docs/architecture/STRUCTURE_BASELINE.md`
   - `docs/architecture/ARCHITECTURE_ENTERPRISE_BASELINE.md`
   - `docs/release/MIGRATION_STATUS.md`
   - `docs/release/NON_TECH_RELEASE_CHECKLIST.md`
3. 业务主路径切换为：`desktop -> backend.app -> backend.infra`。
4. `backend/platform` 已退场，能力已归并至 `backend/infra`。
5. `desktop/qt` 已退场，桌面壳采用 `desktop/app + desktop/ui`。
6. 导入守卫脚本已更新到新路径。

## 待完成

1. 完整功能回归（桌面 UI、索引、问答、生成）
2. 打包链路回归（PyInstaller 全流程）

## 执行约束

1. 新增业务代码必须写入 `backend/` 或 `desktop/`。
2. `archive/` 仅作历史参考，不承载新增功能。
3. frontend 本轮不做内部结构重构。
