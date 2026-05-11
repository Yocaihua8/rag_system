# Project Knowledge Base UI Skeleton Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reposition the current desktop app from Career Assistant to a project knowledge base assistant, with a first-pass UI skeleton for project Q&A, project management, knowledge base review, and mastery assessment.

**Architecture:** Keep the existing PySide6 desktop app and hexagonal architecture. This plan only changes product-facing docs, navigation labels, onboarding copy, and a placeholder assessment view; it does not add new database tables or assessment algorithms.

**Tech Stack:** Python 3.10+, PySide6, pytest, existing `src/desktop` views/controllers/workers, existing Markdown docs.

---

## Scope

This plan implements the first independently shippable slice from `docs/superpowers/specs/2026-05-11-project-knowledge-base-design.md`:

- B-32: Product positioning docs.
- B-33: First-use onboarding copy.
- B-34: Main navigation skeleton.
- B-35: Mastery assessment placeholder page.

The following items need separate plans after this one lands:

- B-36 to B-37: project knowledge point model and extraction.
- B-38 to B-41: assessment question, answer, grading, and report model/use cases.
- B-42: full knowledge base management page with file/knowledge/question tables.

## File Structure

Create:

- `src/desktop/views/assessment_view.py`
  Placeholder PySide6 page for the future mastery assessment flow.

- `tests/test_desktop/test_project_knowledge_ui.py`
  Lightweight UI import and text checks. Uses offscreen Qt.

Modify:

- `README.md`
  Product positioning: "项目知识库助手", with resume generation described as a later output tool rather than the main product goal.

- `docs/architecture/SYSTEM_ARCHITECTURE.md`
  Product positioning and desktop navigation description.

- `docs/architecture/RAG_PIPELINE.md`
  Add project knowledge base and mastery assessment flow as a planned extension over the existing RAG pipeline.

- `src/desktop/views/main_window.py`
  Navigation labels and stack wiring. Add `AssessmentView`; rename visible app title.

- `src/desktop/views/guide_view.py`
  Replace the six-step Career Assistant guide with a three-step project knowledge base guide.

- `src/desktop/views/query_view.py`
  Rename page to "项目问答"; add a visible "开始评估" action placeholder that emits a signal.

Do not modify:

- Storage schema.
- Domain models.
- Application use cases.
- LLM or retrieval adapters.
- Existing generation use cases.

---

### Task 1: Add UI Safety Tests

**Files:**
- Create: `tests/test_desktop/test_project_knowledge_ui.py`
- Test: `tests/test_desktop/test_project_knowledge_ui.py`

- [ ] **Step 1: Create desktop test directory**

Run:

```powershell
New-Item -ItemType Directory -Force tests\test_desktop | Out-Null
```

Expected: command exits with code 0.

- [ ] **Step 2: Write failing UI tests**

Create `tests/test_desktop/test_project_knowledge_ui.py`:

```python
from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QLabel, QPushButton

from src.desktop.views.assessment_view import AssessmentView
from src.desktop.views.guide_view import GuideView
from src.desktop.views.query_view import QueryView


def _app() -> QApplication:
    return QApplication.instance() or QApplication([])


def _label_texts(widget) -> list[str]:
    return [label.text() for label in widget.findChildren(QLabel)]


def _button_texts(widget) -> list[str]:
    return [button.text() for button in widget.findChildren(QPushButton)]


def test_query_view_uses_project_qa_language():
    _app()
    view = QueryView()

    labels = "\n".join(_label_texts(view))
    buttons = "\n".join(_button_texts(view))

    assert "项目问答" in labels
    assert "开始评估" in buttons
    assert "知识库问答" not in labels


def test_guide_view_uses_three_project_steps():
    _app()
    view = GuideView()
    labels = "\n".join(_label_texts(view))

    assert "欢迎使用项目知识库" in labels
    assert "导入项目" in labels
    assert "建立索引" in labels
    assert "开始使用" in labels
    assert "简历" not in labels


def test_assessment_view_placeholder_language():
    _app()
    view = AssessmentView()
    labels = "\n".join(_label_texts(view))

    assert "掌握评估" in labels
    assert "开始评估后，系统会围绕当前项目生成问题" in labels
    assert "第二大脑" not in labels
```

- [ ] **Step 3: Run tests and verify they fail**

Run:

```powershell
.venv\Scripts\python.exe -m pytest tests\test_desktop\test_project_knowledge_ui.py -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'src.desktop.views.assessment_view'` or missing expected UI text.

- [ ] **Step 4: Commit failing tests**

```powershell
git add tests\test_desktop\test_project_knowledge_ui.py
git commit -m "test: 增加项目知识库界面文案测试"
```

Expected: commit succeeds if the worktree has only intended staged files.

---

### Task 2: Add Assessment Placeholder View

**Files:**
- Create: `src/desktop/views/assessment_view.py`
- Test: `tests/test_desktop/test_project_knowledge_ui.py`

- [ ] **Step 1: Implement `AssessmentView`**

Create `src/desktop/views/assessment_view.py`:

```python
from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QLabel, QPushButton, QVBoxLayout, QWidget

from src.desktop.style import ACCENT, TEXT_SECONDARY


class AssessmentView(QWidget):
    """掌握评估页面占位。

    第一阶段只提供稳定页面骨架和文案。后续计划接入自动出题、
    回答评估和能力差距报告。
    """

    start_requested = Signal(str)  # workspace_id

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._workspace_id: str = ""
        self._build_ui()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 16)
        root.setSpacing(12)

        title = QLabel("掌握评估")
        title.setProperty("title", "true")
        root.addWidget(title)

        body = QWidget()
        body_layout = QVBoxLayout(body)
        body_layout.setAlignment(Qt.AlignCenter)
        body_layout.setSpacing(10)

        icon = QLabel("✓")
        icon.setAlignment(Qt.AlignCenter)
        icon.setStyleSheet(f"font-size: 42px; color: {ACCENT};")
        body_layout.addWidget(icon)

        headline = QLabel("评估你对当前项目的掌握情况")
        headline.setAlignment(Qt.AlignCenter)
        headline.setStyleSheet("font-size: 16px; font-weight: 600;")
        body_layout.addWidget(headline)

        description = QLabel(
            "开始评估后，系统会围绕当前项目生成问题，并根据你的回答给出掌握情况、"
            "漏掉的关键点和建议阅读文件。"
        )
        description.setAlignment(Qt.AlignCenter)
        description.setWordWrap(True)
        description.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 13px;")
        body_layout.addWidget(description)

        self._btn_start = QPushButton("开始评估")
        self._btn_start.setProperty("primary", "true")
        self._btn_start.setEnabled(False)
        self._btn_start.clicked.connect(self._emit_start)
        body_layout.addWidget(self._btn_start, alignment=Qt.AlignCenter)

        root.addWidget(body, 1)

    def set_workspace(self, workspace_id: str) -> None:
        self._workspace_id = workspace_id
        self._btn_start.setEnabled(bool(workspace_id))

    def _emit_start(self) -> None:
        if self._workspace_id:
            self.start_requested.emit(self._workspace_id)
```

- [ ] **Step 2: Run assessment view test**

Run:

```powershell
.venv\Scripts\python.exe -m pytest tests\test_desktop\test_project_knowledge_ui.py::test_assessment_view_placeholder_language -v
```

Expected: PASS.

- [ ] **Step 3: Commit assessment view**

```powershell
git add src\desktop\views\assessment_view.py tests\test_desktop\test_project_knowledge_ui.py
git commit -m "feat: 新增掌握评估页面占位"
```

Expected: commit succeeds.

---

### Task 3: Update Query View Copy and Add Assessment Action

**Files:**
- Modify: `src/desktop/views/query_view.py`
- Test: `tests/test_desktop/test_project_knowledge_ui.py`

- [ ] **Step 1: Add signal and button in `QueryView`**

In `src/desktop/views/query_view.py`, make these concrete edits:

1. Replace the signal block with:

```python
    query_submitted = Signal(str, str)    # (workspace_id, question)
    index_requested = Signal(str)         # workspace_id -> trigger indexing
    assessment_requested = Signal(str)    # workspace_id -> open assessment
```

2. Replace the title label text:

```python
        title = QLabel("项目问答")
```

3. Replace the question input placeholder:

```python
        self._question_input.setPlaceholderText("围绕当前项目提问，按 Enter 或点击发送...")
```

4. Replace the input row button construction with:

```python
        self._btn_assessment = QPushButton("开始评估")
        self._btn_assessment.setToolTip("围绕当前项目生成评估问题")
        self._btn_assessment.clicked.connect(
            lambda: self.assessment_requested.emit(self._workspace_id)
        )
        self._btn_send = QPushButton("发送")
        self._btn_send.clicked.connect(self._submit)
        input_row.addWidget(self._question_input)
        input_row.addWidget(self._btn_assessment)
        input_row.addWidget(self._btn_send)
```

5. In `on_query_started`, disable the assessment button:

```python
        self._btn_assessment.setEnabled(False)
```

6. In `on_query_finished`, enable the assessment button:

```python
        self._btn_assessment.setEnabled(True)
```

7. In `on_query_failed`, enable the assessment button:

```python
        self._btn_assessment.setEnabled(True)
```

- [ ] **Step 2: Run query view test**

Run:

```powershell
.venv\Scripts\python.exe -m pytest tests\test_desktop\test_project_knowledge_ui.py::test_query_view_uses_project_qa_language -v
```

Expected: PASS.

- [ ] **Step 3: Commit query view copy**

```powershell
git add src\desktop\views\query_view.py tests\test_desktop\test_project_knowledge_ui.py
git commit -m "feat: 调整项目问答入口文案"
```

Expected: commit succeeds.

---

### Task 4: Update Main Window Navigation

**Files:**
- Modify: `src/desktop/views/main_window.py`
- Test: `tests/test_desktop/test_project_knowledge_ui.py`

- [ ] **Step 1: Update imports and navigation items**

In `src/desktop/views/main_window.py`:

1. Add the import:

```python
from src.desktop.views.assessment_view import AssessmentView
```

2. Replace `_NAV_ITEMS` with:

```python
_NAV_ITEMS = [
    ("🔍", "项目问答"),
    ("📁", "我的项目"),
    ("📚", "知识库"),
    ("✓", "掌握评估"),
    ("⚙️", "设置"),
]
```

3. Replace the window title and app title:

```python
        self.setWindowTitle("项目知识库助手")
```

```python
        app_title = QLabel("项目知识库")
```

- [ ] **Step 2: Update stack order**

In `_build_ui`, replace view construction and stack setup with:

```python
        self._stack = QStackedWidget()
        self._query_view = QueryView()
        self._project_view = self._ws_view
        self._knowledge_view = IngestionView()
        self._assessment_view = AssessmentView()
        self._settings_view = SettingsView()

        self._stack.addWidget(self._query_view)      # 0 项目问答
        self._stack.addWidget(self._project_view)    # 1 我的项目
        self._stack.addWidget(self._knowledge_view)  # 2 知识库
        self._stack.addWidget(self._assessment_view) # 3 掌握评估
        self._stack.addWidget(self._settings_view)   # 4 设置
```

Because `WorkspaceView` is currently also embedded in the sidebar, do not use this exact block if it would reparent the same widget. If keeping the current sidebar workspace panel, use this safer block instead:

```python
        self._stack = QStackedWidget()
        self._query_view = QueryView()
        self._project_view = IngestionView()
        self._knowledge_view = IngestionView()
        self._assessment_view = AssessmentView()
        self._settings_view = SettingsView()

        self._stack.addWidget(self._query_view)       # 0 项目问答
        self._stack.addWidget(self._project_view)     # 1 我的项目，占位复用索引页
        self._stack.addWidget(self._knowledge_view)   # 2 知识库
        self._stack.addWidget(self._assessment_view)  # 3 掌握评估
        self._stack.addWidget(self._settings_view)    # 4 设置
```

Use the safer block for this first slice. It avoids moving the sidebar `WorkspaceView` out of the sidebar. A later plan can split "我的项目" into its own first-class page.

- [ ] **Step 3: Wire workspace and assessment signals**

In `_wire_controllers`, add:

```python
        self._query_view.assessment_requested.connect(
            lambda ws_id: self._open_assessment(ws_id)
        )
        self._assessment_view.start_requested.connect(
            lambda _: self._status_bar.show_message("掌握评估功能将在后续版本接入自动出题")
        )
```

Add this method near `_switch_page`:

```python
    def _open_assessment(self, workspace_id: str) -> None:
        self._assessment_view.set_workspace(workspace_id)
        self._switch_page(3)
```

In `_on_workspace_selected`, add:

```python
        self._assessment_view.set_workspace(workspace.id)
```

- [ ] **Step 4: Run import smoke test**

Run:

```powershell
.venv\Scripts\python.exe -c "from src.desktop.views.main_window import MainWindow; from src.desktop.views.assessment_view import AssessmentView; print('ok')"
```

Expected:

```text
ok
```

- [ ] **Step 5: Run desktop UI tests**

Run:

```powershell
.venv\Scripts\python.exe -m pytest tests\test_desktop\test_project_knowledge_ui.py -v
```

Expected: all tests PASS.

- [ ] **Step 6: Commit navigation skeleton**

```powershell
git add src\desktop\views\main_window.py src\desktop\views\assessment_view.py tests\test_desktop\test_project_knowledge_ui.py
git commit -m "feat: 调整项目知识库主导航"
```

Expected: commit succeeds.

---

### Task 5: Update Onboarding Guide

**Files:**
- Modify: `src/desktop/views/guide_view.py`
- Test: `tests/test_desktop/test_project_knowledge_ui.py`

- [ ] **Step 1: Replace guide steps**

In `src/desktop/views/guide_view.py`, replace `_STEPS` with:

```python
_STEPS = [
    {
        "icon": "①",
        "title": "导入项目",
        "tag": "开始",
        "tag_color": ACCENT,
        "desc": (
            "选择一个代码项目目录。系统会读取 README、docs、源码、配置文件和测试文件。\n\n"
            "建议优先选择一个你正在学习或准备复盘的项目。第一版会自动过滤 .git、"
            "node_modules、.venv、dist、build 等无关目录。"
        ),
    },
    {
        "icon": "②",
        "title": "建立索引",
        "tag": "知识库",
        "tag_color": WARNING,
        "desc": (
            "系统会整理项目文件、切分内容、建立检索索引，并提炼项目知识点。\n\n"
            "完成后，你可以在知识库页查看哪些文件已处理、哪些知识点被识别。"
        ),
    },
    {
        "icon": "③",
        "title": "开始使用",
        "tag": "问答与评估",
        "tag_color": SUCCESS,
        "desc": (
            "你可以围绕当前项目提问，也可以点击开始评估。\n\n"
            "评估功能会围绕项目生成问题，根据你的回答给出掌握情况、漏掉的关键点"
            "和建议阅读文件。"
        ),
    },
]
```

- [ ] **Step 2: Replace guide header text**

In `GuideView._build_ui`, replace the title and subtitle with:

```python
        title = QLabel("欢迎使用项目知识库")
```

```python
        subtitle = QLabel(
            "导入你的代码项目后，系统会建立索引，帮助你围绕项目提问，"
            "并通过评估题了解哪些内容已经掌握、哪些还需要补。"
        )
```

Replace the bottom tip with:

```python
        tip = QLabel("提示：随时可通过左侧底部的 ？ 按钮重新打开使用指引。")
```

- [ ] **Step 3: Run guide test**

Run:

```powershell
.venv\Scripts\python.exe -m pytest tests\test_desktop\test_project_knowledge_ui.py::test_guide_view_uses_three_project_steps -v
```

Expected: PASS.

- [ ] **Step 4: Commit onboarding copy**

```powershell
git add src\desktop\views\guide_view.py tests\test_desktop\test_project_knowledge_ui.py
git commit -m "feat: 简化项目知识库首次使用指引"
```

Expected: commit succeeds.

---

### Task 6: Update Product Positioning Docs

**Files:**
- Modify: `README.md`
- Modify: `docs/architecture/SYSTEM_ARCHITECTURE.md`
- Modify: `docs/architecture/RAG_PIPELINE.md`
- Test: docs diff checks

- [ ] **Step 1: Update README title and feature table**

In `README.md`, change the main title to:

```markdown
# 项目知识库助手
```

Replace the opening paragraph with:

```markdown
基于六边形架构（Hexagonal Architecture）的本地项目知识库桌面应用。
第一版目标是导入代码项目，建立可问答的项目知识库，并通过掌握评估帮助用户理解自己与项目要求之间的差距。
```

Replace the function table with:

```markdown
| 功能 | 说明 |
|------|------|
| **项目管理** | 创建多个项目工作区，每个工作区指向一个代码项目目录 |
| **项目导入** | 扫描 README、docs、源码、配置文件和测试文件，过滤常见无关目录 |
| **项目问答** | 基于向量检索或关键词检索回答项目问题，并展示来源片段 |
| **掌握评估** | 围绕项目知识点生成评估题，记录掌握情况和能力差距 |
| **知识库管理** | 查看项目状态、文件处理情况、项目知识点和评估题库 |
| **输出工具** | 简历、JD 匹配、面试脚本作为后续输出能力保留 |
```

- [ ] **Step 2: Update architecture product section**

In `docs/architecture/SYSTEM_ARCHITECTURE.md`, replace section `1. 产品定位` with:

```markdown
## 1. 产品定位

项目知识库助手是一款本地桌面 RAG 应用，第一版帮助用户基于自己的代码项目完成：

- 导入代码项目并建立本地知识库
- 围绕项目进行问答
- 提炼项目知识点
- 通过评估题判断掌握情况
- 输出能力差距和建议阅读文件

简历项目子弹点、JD 关键词匹配和面试脚本生成保留为后续输出工具，不作为第一版主线。
```

- [ ] **Step 3: Add RAG pipeline extension section**

Append this section to `docs/architecture/RAG_PIPELINE.md` before the final performance section or at the end:

````markdown
## 项目知识库与掌握评估扩展

项目知识库助手在标准 RAG 流程之上增加两条计划中的应用链路：

```text
项目导入 → 项目知识点提炼 → 项目问答
项目知识点 → 自动出题 → 用户回答 → 回答评估 → 能力差距报告
```

第一版评估链路必须保留来源：

- 每个项目知识点关联来源文件或来源片段。
- 每道评估题关联知识点和来源。
- 每次回答评估展示参考要点、判断原因和建议阅读文件。

这能避免评估结果变成不可追踪的 AI 结论。
````

- [ ] **Step 4: Run doc checks**

Run:

```powershell
git diff --check -- README.md docs\architecture\SYSTEM_ARCHITECTURE.md docs\architecture\RAG_PIPELINE.md
```

Expected: no output and exit code 0.

- [ ] **Step 5: Commit docs positioning**

```powershell
git add README.md docs\architecture\SYSTEM_ARCHITECTURE.md docs\architecture\RAG_PIPELINE.md
git commit -m "docs: 调整项目知识库助手产品定位"
```

Expected: commit succeeds.

---

### Task 7: Update Backlog and Devlog After Implementation

**Files:**
- Modify: `docs/BACKLOG.md`
- Modify: `docs/DEVLOG.md`
- Test: docs diff checks

- [ ] **Step 1: Mark implemented backlog items**

In `docs/BACKLOG.md`, move or mark B-32 to B-35 as completed after Tasks 2 to 6 have passed.

Use this completed table format:

```markdown
| B-32 | **产品定位调整为项目知识库助手** | 2026-05-11 |
| B-33 | **首次使用弹窗改为项目导入三步** | 2026-05-11 |
| B-34 | **主导航调整** | 2026-05-11 |
| B-35 | **新增掌握评估页面占位** | 2026-05-11 |
```

Keep B-36 to B-42 in the active product direction section.

- [ ] **Step 2: Add devlog implementation entry**

Add a new entry near the top of `docs/DEVLOG.md`:

````markdown
## 2026-05-11 | B-32~B-35 — 项目知识库界面骨架（完成）

### 目标

完成项目知识库助手第一阶段骨架：产品定位文档、主导航、首次使用指引和掌握评估页面占位。

### 变更文件

| 操作 | 路径 | 内容 |
|------|------|------|
| 更新 | `README.md` | 产品定位从 Career Assistant 调整为项目知识库助手 |
| 更新 | `docs/architecture/SYSTEM_ARCHITECTURE.md` | 更新产品定位和第一版主线 |
| 更新 | `docs/architecture/RAG_PIPELINE.md` | 补充项目知识库与掌握评估扩展链路 |
| 更新 | `src/desktop/views/main_window.py` | 主导航调整为项目问答 / 我的项目 / 知识库 / 掌握评估 / 设置 |
| 更新 | `src/desktop/views/query_view.py` | 页面文案调整为项目问答，并增加开始评估入口 |
| 更新 | `src/desktop/views/guide_view.py` | 首次使用指引改为导入项目 / 建立索引 / 开始使用三步 |
| 新增 | `src/desktop/views/assessment_view.py` | 新增掌握评估页面占位 |
| 新增 | `tests/test_desktop/test_project_knowledge_ui.py` | 增加 UI 文案和页面导入测试 |

### 测试结果

```text
.venv\Scripts\python.exe -m pytest tests\test_desktop\test_project_knowledge_ui.py -v
.venv\Scripts\python.exe -m pytest tests\test_application tests\test_domain tests\test_adapters -v
git diff --check
```

### 未涉及

- 未新增数据库表。
- 未实现自动出题。
- 未实现回答评估和能力差距报告。
- 简历、JD 匹配、面试脚本仍保留为后续输出能力。
````

- [ ] **Step 3: Run final verification**

Run:

```powershell
.venv\Scripts\python.exe -m pytest tests\test_desktop\test_project_knowledge_ui.py -v
.venv\Scripts\python.exe -m pytest tests\test_application tests\test_domain tests\test_adapters -v
git diff --check
```

Expected:

- Desktop UI tests PASS.
- Existing domain/application/adapter tests PASS.
- `git diff --check` exits 0.

- [ ] **Step 4: Commit docs sync**

```powershell
git add docs\BACKLOG.md docs\DEVLOG.md
git commit -m "docs: 同步项目知识库界面骨架进度"
```

Expected: commit succeeds.

---

## Self-Review

Spec coverage:

- Product positioning: Task 6.
- UI avoids “第二大脑”: Tasks 1, 3, 5, 6.
- Codex-style project Q&A as default: Tasks 3 and 4.
- SAS-style auxiliary knowledge base: Task 4 creates navigation slot; full management tables are deferred to B-42 by scope.
- First-use popup: Task 5.
- Mastery assessment placeholder: Task 2 and Task 4.
- No database/model changes: enforced by Scope and File Structure.

Plan limitations:

- This first slice intentionally does not implement B-36 to B-42.
- `我的项目` uses a safe placeholder in the stack because the current `WorkspaceView` already lives in the sidebar. A later plan should split a dedicated project management page.
- The plan includes commit steps, but execution should only commit intended files. If the worktree contains unrelated user changes, stage exact files only.
