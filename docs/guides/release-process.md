# 发布流程

> 状态：Active
> Owner：RAG 团队
> Last Updated：2026-05-16

## 1. 发布前检查

- 需求确认：更新 `docs/requirements/*` 或 `BACKLOG.md`。
- 设计核对：更新 `docs/design/*`。
- 过程记录：在 `docs/devlog` 添加当日/当周日志条目。
- 对外变更：更新 `CHANGELOG.md` 的对应版本。

## 2. 文档一致性

- `docs/README.md` 中的目录说明必须与实际文件一致。
- `CHANGELOG.md`、`BACKLOG.md` 与 `docs/devlog` 的记录不应互相冲突。
- 若涉及 `architecture` 迁移，补充 `design/architecture-overview.md` 或相应 ADR。
- 可直接运行：

```bash
.venv\Scripts\python.exe scripts\check_docs_consistency.py
```

## 3. 最小验收

1. 安装与启动完成
2. 导入至少一个目录成功
3. 一个问答返回含来源信息
4. 关键文档（README/CHNAGELOG/DEVLOG）更新完整

## 4. Windows 打包与一键启动（可选）

```bash
# 先自动补齐 PyInstaller（首次执行）
powershell -ExecutionPolicy Bypass -File scripts\release_windows.ps1 -SkipCheck -InstallPyInstaller

# 仅打包（你已自行安装 PyInstaller）
powershell -ExecutionPolicy Bypass -File scripts\release_windows.ps1 -SkipCheck
```

成功后输出目录为：

`release\dist\KnowledgeIsland\KnowledgeIsland.exe`

同目录还会生成：

`release\dist\KnowledgeIsland\Run_KnowledgeIsland.bat`

双击 `.bat` 可启动应用。

说明：脚本会将 PyInstaller 相关缓存写入仓库内 `release-cache/`（不再写 `C:\Users\...` 的默认缓存目录）。
`Run_KnowledgeIsland.bat` 会把 `RAG_RUNTIME_DIR` 指向当前 exe 目录下的 `runtime`，避免运行时目录因工作目录异常导致初始化失败。
脚本也会显式收集 `chromadb` 与 `chromadb_rust_bindings`，避免 ChromaDB 动态导入模块在冻结包中缺失。
