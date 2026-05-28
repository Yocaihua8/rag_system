# 发布流程

> 状态：Active
> Owner：RAG 团队
> Last Updated：2026-05-28
> Scope：Knowledge Island 版本发布检查与步骤
> Related：docs/guides/testing.md, docs/guides/branch-conventions.md, CHANGELOG.md

## 1. 发布前检查

- [ ] 主流程可运行：启动 `python backend/app.py`，访问 `http://127.0.0.1:8765` 正常
- [ ] 健康检查通过：`GET /api/health` 返回 `{"status": "ok"}`
- [ ] 测试套件通过：`.venv\Scripts\python.exe -m pytest tests/backend tests/frontend -q`
- [ ] 最小验收完成：导入目录成功 → 问答返回含来源的回答
- [ ] 文档同步完成：`requirements/*` / `design/*` / `BACKLOG.md` 与实现一致
- [ ] `CHANGELOG.md` 已整理当前版本变更条目
- [ ] Docker 启动验证：`docker compose --project-directory . -f ops/docker/compose.yaml up --build -d` 服务启动正常（若有 Docker 变更）

## 2. 发布步骤

1. 确认所有发布前检查通过
2. 更新 `CHANGELOG.md`，将 Unreleased 段改为具体版本号和日期
3. 在 `docs/devlog/` 下添加当日日志条目
4. 提交：`git commit -m "chore: release vX.Y.Z"`
5. 打 Tag：`git tag vX.Y.Z`
6. 若有 Windows 打包需求，执行打包脚本（见下方）

## 3. 回滚方案

- **回滚条件**：启动失败、导入或问答核心链路出现阻断性错误
- **回滚步骤**：`git checkout <上一个 tag>`，重新启动 `python backend/app.py`
- **数据回滚**：SQLite 数据库文件（`runtime/docker/knowledge.db`）可手动备份和替换；无自动回滚机制

## 4. Windows 打包（可选）

```powershell
# 首次执行，自动安装 PyInstaller
powershell -ExecutionPolicy Bypass -File scripts\release_windows.ps1 -SkipCheck -InstallPyInstaller

# 已安装 PyInstaller 时直接打包
powershell -ExecutionPolicy Bypass -File scripts\release_windows.ps1 -SkipCheck
```

输出目录：`release\dist\KnowledgeIsland\KnowledgeIsland.exe`

同目录还会生成 `Run_KnowledgeIsland.bat`，双击即可启动。脚本将 PyInstaller 缓存写入仓库内 `release-cache/`，不污染系统目录。

## 5. 发布记录

| 版本 | 日期 | 说明 |
|------|------|------|
| v0.9.0 | 2026-05-25 | 文档集合分组 + 导入批次历史 + 模型 Profile 多配置 |
| v0.8.0 | 2026-05-23 | 多会话聊天 + 检索复盘 + Agent 工具面板 + 备份导出 |
| v0.7.0 | 2026-05-21 | Web MVP 首版：RAG 检索 + 问答 + 聊天记录 + Docker |
