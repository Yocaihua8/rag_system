# 企业化架构基线（阶段 1-2 历史记录）

> **状态**：Superseded（已被取代）
> **取代文档**：当前架构以 `docs/design/architecture-overview.md`（Web MVP）为准；中间历史版本见 `SYSTEM_ARCHITECTURE.md`（v3.0，2026-04，亦已 Superseded）
> **保留原因**：记录阶段 1-2 迁移决策，仅供历史参考，不反映当前代码结构

---

## 历史背景

本文档记录了 2026-04 之前完成的两阶段架构迁移：

**阶段 1（已执行）**：创建 `backend / frontend / desktop` 三分法骨架目录。

**阶段 2（已执行）**：
- `core → backend/core`
- `services/platform → backend/platform`
- `app/qt → desktop/`
- `desktop/api + routers/services/db/tasks → archive/legacy-20260407/desktop-api/`

**阶段 3（已由 v3.0 架构取代）**：
- 不再沿用 `backend/` 顶层结构
- 改为 `src/` 五层架构（config / domain / ports / adapters / application / desktop）
- 详见 `SYSTEM_ARCHITECTURE.md`

---

## 当前有效约束

以下约束在新架构中依然有效，但表述已更新：

| 旧约束 | 新约束（见 STRUCTURE_BASELINE.md） |
|--------|----------------------------------|
| 不在遗留目录新增业务功能 | 不在 `backend/`、`archive/` 新增代码 |
| 单次迁移只处理一个目录域 | 按实施顺序逐层推进（共 12 步） |
| 每次迁移后验证主链路 | 每步完成后运行 `scripts/migration_gate_check.py` |
