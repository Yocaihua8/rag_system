# 贡献指南

感谢参与 Knowledge Island。提交前请先阅读 `README.md`、`AGENTS.md`、`docs/README.md` 和本任务涉及的规格；当前源码和测试优先于历史假设。

## 1. 环境

- Python 3.10+
- Node.js 20+ 与 npm
- Git
- 桌面构建另需 Rust/Cargo 和目标平台原生工具链

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r backend/requirements/dev.txt
npm ci
Copy-Item backend/.env.example backend/.env
```

本地开发使用两个终端：

```powershell
.\.venv\Scripts\python.exe -m backend
npm run frontend:dev
```

不要提交 `backend/.env`、API Key、Token、密码、运行数据库、`node_modules/`、`.venv/`、`frontend/dist/` 或临时产物。

## 2. 分支与提交

从最新目标分支创建短生命周期分支：

- `feat/<topic>`
- `fix/<topic>`
- `refactor/<topic>`
- `docs/<topic>`
- `test/<topic>`

提交信息使用简洁的 Conventional Commits 风格，例如：

```text
fix: 修复跨域 SSE 请求地址
refactor: 分离前后端运行时
docs: 更新 Docker 双服务说明
```

一次提交聚焦一个可验证阶段；不要混入无关格式化或重构。

## 3. 代码边界

### 后端

- Python 函数/变量使用 `snake_case`，类使用 `PascalCase`。
- `backend/api/` 和 `backend/routes/` 不直接操作 SQLite。
- `backend/storage/` 是 SQLite 唯一入口。
- 可选依赖使用隔离导入并提供明确降级。
- HTTP 方法、字段、响应结构和 Schema 变化必须说明兼容/迁移方案并同步文档。

### 前端

- JS 函数使用 `camelCase`，文件名使用 `kebab-case`。
- 前端只做展示、页面状态、输入校验和 API 调用，不复制后端业务规则。
- 所有 API 和 SSE URL 经 `VITE_API_BASE_URL` 统一生成。
- 生产产物只写入 `frontend/dist/`，不得提交构建产物。

### 桌面与插件

- Tauri 只承载窗口、托盘和 sidecar 生命周期，不复制业务逻辑。
- CSP 扩展、sidecar 权限或原生能力变化需说明安全影响。
- Obsidian 插件保持独立依赖和验证链，不加入根 npm workspace。
- 插件不能绕过应用侧发布确认、路径、托管标记、revision 或 hash 校验。

## 4. 测试

按改动范围运行最小相关集，合并前应覆盖完整相关矩阵：

```powershell
.\.venv\Scripts\python.exe -m pytest tests/backend tests/integration tests/repository -q
npm run frontend:test
npm run frontend:build
npm run frontend:e2e
```

桌面和插件按需追加：

```powershell
cargo check --manifest-path src-tauri/Cargo.toml
npm run desktop:build:windows
npm --prefix integrations/obsidian-plugin test
npm --prefix integrations/obsidian-plugin run typecheck
npm --prefix integrations/obsidian-plugin run build
```

依赖安全审计：

```powershell
npm audit --audit-level=high
.\.venv\Scripts\pip-audit.exe -r backend/requirements/base.txt --progress-spinner off
```

测试未运行或失败时，在 PR 中保留命令、原因和关键错误，不得写成通过。

## 5. 文档

行为变化必须同步当前文档：

- 产品背景、用例和版本边界：`docs/requirements/`
- 功能：`docs/features/`
- API、数据、权限、状态和 UI 契约：`docs/design/`
- 重大决策：`docs/adr/`
- 桌面/外部集成：对应功能规格及按操作目的归类的 `docs/guides/`
- 启动、测试、Docker、发布、安全：`docs/guides/`
- 未完成事项：`docs/BACKLOG.md`
- 已完成变更：`CHANGELOG.md`

不要创建 DevLog、readiness 快照或已验收 preview。文档元数据和写作规则见 `docs/style-guide.md`。

## 6. Pull Request

PR 至少说明：

- 改了什么与为什么；
- 影响的前端页面、后端接口、数据、桌面、插件或配置；
- 实际运行的命令和结果；
- 已知风险、未覆盖平台与回滚边界；
- 文档是否同步。

不要在 PR 中放凭证、真实用户数据、大体积构建产物或与任务无关的改动。

## 7. ADR

以下变化通常需要 ADR：跨模块技术选型、存储/认证/权限策略、状态机、破坏性契约、替代既有架构。使用 `docs/adr/ADR-000-template.md`，在 `docs/adr/README.md` 登记，并保持历史 ADR 不被静默改写。
