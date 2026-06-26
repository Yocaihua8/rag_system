# B-125 Reranker 重排序接入

> ⚠️ 创建此文件前，必须已完成以下操作（AI 自检）：
> - [x] `docs/BACKLOG.md` B-125 条目已存在，状态改为 `doing`
> - [x] 该 BACKLOG 条目"说明"列已填入本文件路径
> - [x] 下方"关联功能文档"和"关联设计文档"已填写

> 状态：Active
> 创建时间：2026-06-26
> 创建方：Claude Code
> 关联 BACKLOG：B-125
> 关联功能文档：docs/features/frontend-engineering.md（检索调试面板展示 reranker 信息）
> 关联设计文档：docs/design/new-architecture-design.md §5.1 §5.4 §16.3

## 1. 目标

在现有 BM25 + 向量混合检索之后，增加 **Cross-Encoder Reranker** 精排层，提升回答质量。

- 默认模型：`cross-encoder/ms-marco-MiniLM-L-6-v2`（~80MB，中英混合，CPU 可运行）
- **软依赖**：未安装 `sentence-transformers` 时，Reranker 自动跳过，检索结果不变
- 配置开关：`reranker.enabled = true`（`settings.toml`）
- 新代码放在 `backend/providers/reranker/`

**本任务不依赖 B-146 完成**，因为 `backend/` 目录由本任务在任务 1 中顺带建立（若 B-146 已完成则跳过建目录步骤）。

完成后效果：`/api/search` 和 `/api/answer/stream` 的结果经过 Cross-Encoder 精排，检索相关性显著提升；检索调试面板可见 `reranker_used` 字段。

## 2. 前置条件

- 读 `webapp/search.py`：理解现有 BM25 + 向量检索流程（`search_documents()` 函数）
- 读 `webapp/models.py`：`SearchHit` 结构，新增 `rerank_score` 字段
- 读 `docs/design/new-architecture-design.md §5.4`：RRF + Reranker 设计规范
- 读 `docs/design/new-architecture-design.md §16.3`：`SearchService` 接口（`_rerank()` 逻辑参考）
- 读 `docs/design/new-architecture-design.md §5.1`：`BaseReranker` ABC 接口定义
- `sentence-transformers` 包在本地未必已安装；测试时 mock，不要求真实模型

## 3. 任务拆解

每完成一项，立即执行：① 勾选此处 ② `git commit` ③ 更新 § 9 状态快照。

- [x] 任务 1：在 `backend/providers/reranker/` 建立目录（若 backend/ 不存在则同步创建骨架）
- [x] 任务 2：实现 `BaseReranker` ABC → `backend/providers/base.py`（或追加到已有 base.py）
- [x] 任务 3：实现 `CrossEncoderReranker` → `backend/providers/reranker/cross_encoder.py`
- [x] 任务 4：在 `webapp/search.py` 中接入 Reranker（在 RRF 融合之后，返回前调用）
- [x] 任务 5：`webapp/models.py` 的 `SearchHit` 新增 `rerank_score: float | None`
- [ ] 任务 6：API 响应的 `pipeline_trace` 新增 `reranker_used` 字段（`/api/answer/stream` done 事件）
- [ ] 任务 7：`settings.toml` / `AppSettings` 追加 `reranker.enabled` 和 `reranker.model` 字段
- [ ] 任务 8：写测试（MockReranker 验证接口；确认 disabled 时行为不变）
- [ ] 任务 9：同步文档，更新 BACKLOG B-125 为 done

## 4. 影响范围

| 类型 | 路径 / 模块 | 变更方向 |
|------|------------|---------|
| 代码（新建） | `backend/providers/reranker/__init__.py` | 新增 |
| 代码（新建） | `backend/providers/reranker/cross_encoder.py` | 新增：CrossEncoderReranker |
| 代码（新建/追加） | `backend/providers/base.py` | 新增 BaseReranker ABC |
| 代码（修改） | `webapp/search.py` | 修改：在 RRF 后接入 reranker |
| 代码（修改） | `webapp/models.py` | 修改：SearchHit 新增 rerank_score |
| 代码（修改） | `webapp/answers.py` 或路由层 | 修改：done 事件附加 pipeline_trace |
| 代码（修改） | `src/config/settings.py` 或 `settings.toml` | 修改：reranker 配置项 |
| 测试（新建） | `tests/test_backend/test_reranker.py` | 新增 |
| 测试（修改） | `tests/test_webapp/test_search.py`（若存在）| 修改：确认 reranker 跳过时测试通过 |
| 文档（修改） | `docs/BACKLOG.md` | B-125 → done |
| 文档（修改） | `docs/guides/setup.md` | 追加可选依赖 sentence-transformers 说明 |

**不改动**：
- `webapp/storage.py`（数据层）
- `webapp/server.py`（B-143 在改）
- `src/`（只读）

## 5. 依赖与冲突

### 5.1 依赖的其他 plan

| plan 文件 | 依赖原因 |
|-----------|---------|
| `docs/plans/B-146-port-ollama-to-backend.md` | 软依赖：若 B-146 已建 `backend/providers/base.py`，本任务追加 BaseReranker；若未完成则自行创建 `backend/` 骨架和 base.py |

### 5.2 与现有 plan 的重叠

| 冲突 plan | 重叠范围 | 解决方式 |
|-----------|---------|---------|
| `docs/plans/B-143-remove-legacy-static-fallback.md` | 均可能改 `webapp/` 下的文件，但 B-143 只改 `server.py` 和 `static/`，B-125 改 `search.py` 和 `models.py` | 分区：无实质冲突 |
| `docs/plans/B-146-port-ollama-to-backend.md` | 均在 `backend/providers/base.py` 中新增 ABC 类 | 协调：若并行执行，先到先写 base.py，后到追加；或等 B-146 合并后再开始 |

## 6. 完成标准

- [ ] `CrossEncoderReranker` 实现 `BaseReranker.rerank(query, candidates, top_n)`
- [ ] `reranker.enabled = false`（默认）时，搜索行为与现在完全一致（无回归）
- [ ] `reranker.enabled = true` 时，`/api/search` 返回的 hit 顺序经过精排
- [ ] `sentence-transformers` 未安装时，启动时打印 WARNING，reranker = None，不崩溃
- [ ] `SearchHit.rerank_score` 在精排后有值，未精排时为 `None`
- [ ] 测试：MockReranker 验证接口契约；`enabled=False` 时原有测试 100% 通过
- [ ] `.venv\Scripts\python.exe -m pytest tests/test_webapp tests/test_backend -q` 通过
- [ ] `docs/BACKLOG.md` B-125 状态更新为 `done`

## 7. 回流清单

| 内容 | 目标文档 | 是否完成 |
|------|----------|----------|
| Reranker 可选依赖安装说明（`pip install sentence-transformers`）| `docs/guides/setup.md` | [ ] |
| `reranker.enabled` / `reranker.model` 配置项 | `docs/design/new-architecture-design.md §18.2`（确认一致）| [ ] |
| `pipeline_trace.reranker_used` 字段加入 API 响应说明 | `docs/design/api-spec.md` | [ ] |

## 8. 执行记录

- 2026-06-26：创建 plan，B-125 进入 doing 状态。
- 2026-06-26：任务 1 完成；确认 B-146 已建立 `backend/` 与 `backend/providers/base.py`，本任务只新增 `backend/providers/reranker/__init__.py` 包入口；未重建既有 backend 骨架。
- 2026-06-26：任务 2 完成；先新增 `tests/test_backend/test_reranker.py` 验证 `BaseReranker` 导出与抽象方法，红灯为 import 失败；随后在 `backend/providers/base.py` 追加 `BaseReranker.rerank(query, candidates, top_n)`，测试转绿。
- 2026-06-26：任务 3 完成；先写 CrossEncoder provider 红灯测试，确认模块缺失；随后新增 `backend/providers/reranker/cross_encoder.py`，实现延迟加载、`predict()` 打分排序、`top_n` 截断和 ImportError WARNING 降级；采用 plan 中默认模型名 `cross-encoder/ms-marco-MiniLM-L-6-v2`，测试不下载模型。
- 2026-06-26：任务 4 完成；先写 `search_documents(..., reranker=...)` 红灯测试，确认原签名不支持；随后在 `webapp/search.py` 增加可选 `reranker` 参数，在现有 BM25+向量分数排序后取 `limit*3` 候选交给 reranker，默认 None 时仍走原排序截断。搜索测试 16 项与 backend reranker 测试 3 项通过。
- 2026-06-26：任务 5 完成；先新增 `tests/test_webapp/test_models.py` 红灯验证 `SearchHit(rerank_score=...)` 序列化，随后在 `webapp/models.py` 新增 `rerank_score: float | None = None` 并写入 `to_dict()`；模型与搜索测试 17 项通过。

## 9. 状态快照

- **最后更新**：2026-06-26 19:50
- **进度**：已完成 5 / 9 项（见 § 3 勾选状态）
- **最新 commit**：待提交 — 任务 5 SearchHit rerank_score
- **代码状态**：`SearchHit.to_dict()` 已包含 `rerank_score`
- **下一步**：任务 6 — API 响应 `pipeline_trace.reranker_used`
- **续任务须知**：
  - Cross-Encoder 模型首次加载需下载 ~80MB，测试时必须 mock，不要求联网
  - `rerank()` 入参是 `list[Chunk]`，内部拼接 `(query, chunk.content)` 对送入模型
  - 模型加载做延迟初始化（第一次 `rerank()` 调用时再 import），避免影响启动时间
  - `top_n=None` 时返回全部 candidates，按分数降序排列
