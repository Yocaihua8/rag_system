# B-146 移植 Ollama LLM + 平台路径到 backend/

> ⚠️ 创建此文件前，必须已完成以下操作（AI 自检）：
> - [x] `docs/BACKLOG.md` B-146 条目已存在，状态改为 `doing`
> - [x] 该 BACKLOG 条目"说明"列已填入本文件路径
> - [x] 下方"关联功能文档"和"关联设计文档"已填写

> 状态：Active
> 创建时间：2026-06-26
> 创建方：Claude Code
> 关联 BACKLOG：B-146
> 关联功能文档：N/A（基础设施，无独立功能文档）
> 关联设计文档：docs/design/new-architecture-design.md §23.7（D-11 细节）

## 1. 目标

将 `src/` 中两个对 C 端发行至关重要的模块移植到 `backend/`，同时搭建 `backend/` 目录骨架：

1. **Ollama LLM Provider**（`src/adapters/llm/ollama_adapter.py`）→ `backend/providers/llm/ollama.py`，实现设计文档中的 `BaseLLM` 接口，使 Web MVP 可以使用本地 Ollama 作为 LLM。
2. **平台感知路径**（`src/config/settings.py` 中的 `_app_data_dir()`）→ `backend/config/paths.py`，使 C 端应用在 Windows/macOS/Linux 各自写入正确的用户数据目录。

完成后，`backend/` 具备最小骨架，Ollama 可在 Web MVP 设置界面作为 LLM 选项使用。这是 B-145（Tauri 壳）的先行条件。

## 2. 前置条件

- 读 `src/adapters/llm/ollama_adapter.py`：理解现有 `OllamaAdapter` 实现
- 读 `src/adapters/embedding/ollama_embedder.py`：一并移植 Ollama Embedder
- 读 `src/config/settings.py`：提取 `_app_data_dir()`、`save_setting()` 逻辑
- 读 `webapp/llm.py`：理解现有 `OpenAICompatibleChatClient`，`BaseLLM` 接口对齐它
- 读 `docs/design/new-architecture-design.md §5.1`：Provider ABC 接口规范
- `docs/BACKLOG.md` B-143 仍是 `doing`；本任务不改 `webapp/server.py` 或 `webapp/static/`

## 3. 任务拆解

每完成一项，立即执行：① 勾选此处 ② `git commit` ③ 更新 § 9 状态快照。

- [x] 任务 1：建立 `backend/` 目录骨架
- [x] 任务 2：实现 `backend/providers/base.py`（BaseLLM / BaseEmbedder ABC）
- [x] 任务 3：移植 `OllamaLLM` → `backend/providers/llm/ollama.py`
- [x] 任务 4：移植 `OllamaEmbedder` → `backend/providers/embedder/ollama.py`
- [x] 任务 5：移植平台路径 → `backend/config/paths.py`
- [ ] 任务 6：在 Web MVP 设置接口中注册 Ollama 为可选 LLM provider
- [ ] 任务 7：写测试（mock Ollama HTTP，验证 BaseLLM 接口实现）
- [ ] 任务 8：同步文档，更新 BACKLOG B-146 为 done

## 4. 影响范围

| 类型 | 路径 / 模块 | 变更方向 |
|------|------------|---------|
| 代码（新建） | `backend/__init__.py` | 新增 |
| 代码（新建） | `backend/providers/__init__.py` | 新增 |
| 代码（新建） | `backend/providers/base.py` | 新增：BaseLLM / BaseEmbedder ABC |
| 代码（新建） | `backend/providers/llm/__init__.py` | 新增 |
| 代码（新建） | `backend/providers/llm/ollama.py` | 新增：移植自 src/adapters/llm/ |
| 代码（新建） | `backend/providers/embedder/__init__.py` | 新增 |
| 代码（新建） | `backend/providers/embedder/ollama.py` | 新增：移植自 src/adapters/embedding/ |
| 代码（新建） | `backend/config/__init__.py` | 新增 |
| 代码（新建） | `backend/config/paths.py` | 新增：平台感知路径，移植自 src/config/settings.py |
| 代码（修改） | `webapp/routes/settings.py`（或同等路由文件）| 修改：注册 Ollama 为 LLM 选项 |
| 测试（新建） | `tests/test_backend/test_ollama_llm.py` | 新增 |
| 文档（修改） | `docs/BACKLOG.md` | B-146 → done；B-147 说明追加依赖注记 |
| 文档（修改） | `AGENTS.md` § 3 | 确认 backend/ 已出现在目录速查（已更新） |

**不改动**：
- `src/` 目录（只读参考，归档在 B-147）
- `webapp/storage.py`（数据层过渡期不动）
- `webapp/server.py`（B-143 在改）

## 5. 依赖与冲突

### 5.1 依赖的其他 plan

| plan 文件 | 依赖原因 |
|-----------|---------|
| N/A | B-146 是 Tauri 链的起点，无前置 plan |

### 5.2 与现有 plan 的重叠

| 冲突 plan | 重叠范围 | 解决方式 |
|-----------|---------|---------|
| `docs/plans/B-143-remove-legacy-static-fallback.md` | 均可能改 `webapp/server.py`，但 B-143 改静态服务，B-146 改 LLM 路由 | 分区：B-146 不碰 `webapp/server.py` 的 StaticFiles 挂载逻辑 |

## 6. 完成标准

- [ ] `backend/providers/llm/ollama.py` 实现 `BaseLLM.generate()` 和 `BaseLLM.stream()`
- [ ] `backend/providers/embedder/ollama.py` 实现 `BaseEmbedder.embed()`
- [ ] `backend/config/paths.py` 在 Windows/macOS/Linux 均返回正确的 `app_data_dir`
- [ ] Ollama 在 Web MVP 设置界面可选（`llm.provider = "ollama"` 时生效）
- [ ] `ollama.is_available()` 检测失败时给出友好提示，不阻断启动
- [ ] 测试：mock Ollama HTTP，`generate()` / `stream()` 返回符合接口契约
- [ ] `.venv\Scripts\python.exe -m pytest tests/test_webapp tests/test_backend -q` 通过
- [ ] `docs/BACKLOG.md` B-146 状态更新为 `done`

## 7. 回流清单

| 内容 | 目标文档 | 是否完成 |
|------|----------|----------|
| backend/ 目录骨架说明 | `AGENTS.md § 3` | [ ] |
| Ollama 作为 LLM 选项的配置方法 | `docs/guides/setup.md` | [ ] |
| BaseLLM / BaseEmbedder ABC 接口（与设计文档对齐） | `docs/design/new-architecture-design.md §16.2`（确认一致即可）| [ ] |

## 8. 执行记录

- 2026-06-26：创建 plan，B-146 进入 doing 状态。
- 2026-06-26：任务 1 完成；新增 `backend/`、`backend/config/`、`backend/providers/`、`backend/providers/llm/`、`backend/providers/embedder/` 包骨架；`.venv\Scripts\python.exe -c "import backend, backend.providers, backend.config, backend.providers.llm, backend.providers.embedder"` 通过。
- 2026-06-26：任务 2 完成；新增 `backend/providers/base.py`，定义 `BaseLLM.generate()`、`BaseLLM.stream()`、`BaseLLM.is_available()`、`BaseEmbedder.embed()`、`BaseEmbedder.is_available()` 及 `LLMMessage`/`LLMResult`；确认 `new-architecture-design.md §5.1` 当前未包含 BaseLLM/BaseEmbedder 明确定义，因此按 plan 目标和 Web LLM 结构建立最小 ABC；PowerShell here-string 导入/抽象方法检查通过。
- 2026-06-26：任务 3 完成；新增 `backend/providers/llm/ollama.py`，使用标准库 HTTP 调用 Ollama `/api/chat` 与 `/api/tags`，实现 `BaseLLM.generate()`、`stream()`、`is_available()`、`list_models()`；`is_available()` 检测失败时打印 `WARNING` 并返回 `False`，不阻断启动；`py_compile` 与导入检查通过。
- 2026-06-26：任务 4 完成；新增 `backend/providers/embedder/ollama.py`，使用标准库 HTTP 调用 Ollama `/api/embeddings` 与 `/api/tags`，实现 `BaseEmbedder.embed()`、`is_available()` 和 `dimension/model/provider` 属性；`py_compile` 与导入检查通过。
- 2026-06-26：任务 5 完成；新增 `backend/config/paths.py`，移植平台感知 `app_data_dir()`，并提供 `ensure_app_data_dir()` 与 `app_env_file()`；通过注入 `system/environ/home` 模拟 Windows/macOS/Linux 路径验证。

## 9. 状态快照

- **最后更新**：2026-06-26 19:08
- **进度**：已完成 5 / 8 项（见 § 3 勾选状态）
- **最新 commit**：待提交 — 任务 5 平台路径
- **代码状态**：`backend/` 目录骨架已新增；`src/` 保持只读
- **下一步**：任务 6 — 在 Web MVP 设置接口中注册 Ollama 为可选 LLM provider
- **续任务须知**：`docs/design/new-architecture-design.md §5.1` 未实际包含 BaseLLM/BaseEmbedder 定义；后续实现继续按 `backend/providers/base.py` 的最小 ABC 对齐，不直接复制 src/ 的旧 request/response 签名。
