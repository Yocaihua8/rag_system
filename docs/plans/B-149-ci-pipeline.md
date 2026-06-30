# B-149 CI 持续集成流水线

> 状态：Active
> 创建时间：2026-06-30
> 创建方：Claude（AI 助手）
> 关联 BACKLOG：B-149
> 关联功能文档：docs/guides/testing.md, docs/guides/release-process.md
> 关联设计文档：N/A（纯工程化配置，不涉及 API/数据库 schema 变更）

## 1. 目标

在 `.github/workflows/` 下新增 GitHub Actions CI 流水线，覆盖所有现有测试与构建检查，在 PR 合并前自动拦截失败。完成后系统状态：

- 任何推送到 `main` 或面向 `main` 的 PR 都会自动触发 CI
- `python-tests` job：运行 379 个 pytest（`tests/test_backend` + `tests/test_webapp`）+ 文档一致性检查
- `frontend-e2e` job：`npm run build`（Vue/Vite 构建）+ Playwright E2E
- 两个 job 并行跑，独立报告失败点
- pip 和 npm 依赖均有缓存，避免每次全量下载
- GitHub 分支保护规则可直接引用这两个 status check 作为合并门禁

## 2. 前置条件

- 已读 `docs/guides/testing.md`（了解实际测试命令与环境变量约定）
- 已知 E2E 通过 `tests/e2e/start-web-server.mjs` 自启动后端，无需手动 `python app.py`
- 已知 `playwright.config.js` 在 CI 环境（`process.env.CI`）下强制重启 server、单 worker、失败重试 1 次
- `.github/` 目录当前不存在，需新建

## 3. 任务拆解

每完成一项，立即执行：① 勾选此处 ② `git commit` 保存进度 ③ 更新 § 9 状态快照。

- [ ] **3.1** 新建 `.github/workflows/ci.yml`，实现 `python-tests` job（pytest + 文档一致性检查）
- [ ] **3.2** 在同一 workflow 中添加 `frontend-e2e` job（`npm run build` + Playwright）
- [ ] **3.3** 为两个 job 添加 pip 和 npm 缓存（`actions/cache`），验证缓存 key 正确
- [ ] **3.4** 本地用 `act`（或 push 到 fork）跑一遍完整 CI，确认两个 job 均 green
- [ ] **3.5** 更新 `docs/guides/testing.md`：补充 CI 触发条件、job 名称、缓存策略和 E2E 环境变量说明
- [ ] **3.6** 更新 `docs/guides/release-process.md`：补充 CI status check 作为 v1.0.0 合并门禁
- [ ] **3.7** BACKLOG B-149 状态置 `done`，删除本 plan 文件

## 4. 影响范围

| 类型 | 路径 / 模块 | 变更方向 |
|------|------------|---------|
| 代码 | `.github/workflows/ci.yml` | 新增 |
| 文档 | `docs/guides/testing.md` | 修改（补充 CI 说明） |
| 文档 | `docs/guides/release-process.md` | 修改（补充合并门禁） |

## 5. 依赖与冲突

### 5.1 依赖的其他 plan

| plan 文件 | 依赖原因 |
|-----------|---------|
| N/A | B-149 无前置 plan 依赖 |

### 5.2 与现有 plan 的重叠

| 冲突 plan | 重叠范围 | 解决方式 |
|-----------|---------|---------|
| N/A | N/A | N/A |

## 6. 完成标准

- [ ] `python-tests` job 在 GitHub Actions 上 green（pytest 379+ tests pass）
- [ ] `frontend-e2e` job 在 GitHub Actions 上 green（build 成功 + Playwright E2E pass）
- [ ] `docs/guides/testing.md` 已补充 CI 相关说明
- [ ] `docs/guides/release-process.md` 已补充合并门禁
- [ ] BACKLOG 条目 B-149 状态已更新为 `done`

## 7. 回流清单

| 内容 | 目标文档 | 是否完成 |
|------|----------|----------|
| CI 触发条件、job 结构、缓存策略 | `docs/guides/testing.md` | [ ] |
| CI status check 作为合并门禁 | `docs/guides/release-process.md` | [ ] |

> 本次无重大架构决策，不需要新建 ADR。

## 8. 执行记录

### CI workflow 设计决策

**两 job 并行而非单 job 串行**：pytest（379 个测试）和 Playwright E2E 是独立检查，并行运行可缩短总耗时约 40-50%，且失败点独立可见。

**job 划分**：
- `python-tests`：`python -m pytest tests/test_backend tests/test_webapp -q` + `python scripts/check_docs_consistency.py`。文档检查与 Python 测试合并在同一 job，因为都是纯 Python 依赖，共享同一 venv 缓存。
- `frontend-e2e`：`npm run build`（生成 `webapp/static_dist/`）→ `npx playwright install chromium` → `npx playwright test`。Playwright 通过 `playwright.config.js` 的 `webServer` 自动启动 `tests/e2e/start-web-server.mjs`（内部调用 `.venv/bin/python`），无需额外步骤。

**Python 可执行文件**：E2E server 脚本（`start-web-server.mjs`）自动检测 `.venv/bin/python`，CI 上只需先执行 `pip install` 进 `.venv` 即可。

**缓存 key**：
- pip：`requirements.txt` + `requirements-dev.txt` hash
- npm：`package-lock.json` hash

**E2E 环境变量**：`CI=true`（GitHub Actions 自动设置），触发 playwright 单 worker + 重启 server 策略；E2E 临时 DB 由 `start-web-server.mjs` 自动创建于系统临时目录。

### workflow 草稿

```yaml
# .github/workflows/ci.yml
name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  python-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Cache pip
        uses: actions/cache@v4
        with:
          path: .venv
          key: venv-${{ runner.os }}-${{ hashFiles('requirements.txt', 'requirements-dev.txt') }}

      - name: Install Python deps
        run: |
          python -m venv .venv
          .venv/bin/pip install -r requirements.txt -r requirements-dev.txt

      - name: Run pytest
        run: .venv/bin/python -m pytest tests/test_backend tests/test_webapp -q

      - name: Docs consistency check
        run: .venv/bin/python scripts/check_docs_consistency.py

  frontend-e2e:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-node@v4
        with:
          node-version: "20"

      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Cache npm
        uses: actions/cache@v4
        with:
          path: ~/.npm
          key: npm-${{ runner.os }}-${{ hashFiles('package-lock.json') }}

      - name: Cache pip (for E2E server)
        uses: actions/cache@v4
        with:
          path: .venv
          key: venv-${{ runner.os }}-${{ hashFiles('requirements.txt', 'requirements-dev.txt') }}

      - name: Install Node deps
        run: npm ci

      - name: Install Python deps
        run: |
          python -m venv .venv
          .venv/bin/pip install -r requirements.txt -r requirements-dev.txt

      - name: Build frontend
        run: npm run build

      - name: Install Playwright browsers
        run: npx playwright install chromium --with-deps

      - name: Run E2E tests
        run: npx playwright test
```

> 注：`npm run test:e2e` 内含 `npm run build`（双重构建），直接调 `npx playwright test` 避免重复构建。

## 9. 状态快照

- **最后更新**：2026-06-30 12:00
- **进度**：已完成 0 / 7 项（见 § 3 勾选状态）
- **最新 commit**：`07cb810` — docs: 设计 Phase 2 发布硬化任务集
- **代码状态**：`fix/b-08-concurrent-index`；工作区干净；plan 文件新建未提交
- **下一步**：3.1 — 新建 `.github/workflows/ci.yml`，实现 `python-tests` job
- **续任务须知**：workflow 草稿已在 § 8 中给出，可直接作为 3.1 起点；E2E job 需要 pip venv 也安装（供 start-web-server.mjs 调用），缓存 key 与 python-tests job 相同可命中同一缓存。
