# Knowledge Island Agent Rules

> 状态：Active
> Owner：RAG 团队
> Last Updated：2026-05-20

## 当前技术栈边界

- 默认可执行入口是本地 Web MVP：`app.py` -> `webapp.server.run_server()`。
- Web MVP 使用 Python 标准库 HTTP 服务、SQLite、原生 HTML/CSS/JavaScript，不新增运行时依赖。
- 旧 PySide6 桌面端代码暂时保留在 `src/desktop/`，作为 legacy 参考和后续迁移来源；不要在未确认迁移完成前批量删除。

## 文件拆分规则

- 一个文件只承载一个清晰职责，不把 API、存储、检索、导入、回答生成和 UI 脚本写在同一个文件内。
- 新 Web 栈按以下边界维护：
  - `webapp/server.py`：HTTP server 与静态文件服务。
  - `webapp/api.py`：API 路由分发，不直接写 SQLite。
  - `webapp/storage.py`：SQLite schema 与读写。
  - `webapp/ingestion.py`：目录导入。
  - `webapp/import_rules.py`：导入后缀、排除目录、文件大小上限。
  - `webapp/search.py`：关键词检索与排序。
  - `webapp/answers.py`：基于检索片段生成回答文本。
  - `webapp/static/js/*.js`：前端按 API、状态、项目、问答、渲染拆分。

## 修改流程

- 修改默认入口、接口行为、存储字段、启动方式时，必须同步 `README.md`、`docs/guides/setup.md`、`docs/guides/testing.md`、`docs/BACKLOG.md`、`docs/DEVLOG.md` 和 `CHANGELOG.md` 中相关内容。
- 涉及代码行为变化时，先补或更新测试，再改实现。
- 当前仓库已有大量未提交改动；不要清空项目、批量删除 legacy 目录或覆盖不相关文件。

## 验证命令

```powershell
.venv\Scripts\python.exe -m pytest tests\test_webapp -q
.venv\Scripts\python.exe -m pytest tests\test_application tests\test_domain tests\test_adapters -q
```

第二条用于确认旧业务层没有被新 Web 入口改坏；如本机缺依赖导致失败，必须记录失败原因。
