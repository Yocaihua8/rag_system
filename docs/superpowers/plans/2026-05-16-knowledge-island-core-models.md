# Knowledge Island Core Models Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Recenter the first data-model slice around Knowledge Island by adding Project, Document, Chunk, Tag, DocumentTag, and Source domain models with tests and documentation.

**Architecture:** Keep the current PySide6 + Python hexagonal architecture. This slice changes only domain models, SQLite schema readiness, tests, and docs; application services and UI keep using the existing `Workspace` flow until a later migration task replaces it safely.

**Tech Stack:** Python dataclasses, sqlite3 schema DDL, pytest, existing `src/domain`, `src/adapters/storage`, and `docs` conventions.

---

## Files

- Modify: `tests/test_domain/test_models.py`
- Create: `src/domain/models/project.py`
- Modify: `src/domain/models/document.py`
- Modify: `src/domain/models/chunk.py`
- Create: `src/domain/models/tag.py`
- Create: `src/domain/models/source.py`
- Modify: `src/domain/models/__init__.py`
- Modify: `src/adapters/storage/db.py`
- Modify: `docs/BACKLOG.md`
- Modify: `docs/DEVLOG.md`
- Modify: `README.md`
- Create: `docs/architecture/DATA_MODEL.md`

## Task 1: Add Failing Core Model Tests

**Files:**
- Modify: `tests/test_domain/test_models.py`

- [ ] **Step 1: Write tests for Project, expanded Document, expanded Chunk, Tag, DocumentTag, and Source**

Add focused tests that express the required Knowledge Island fields:

```python
from src.domain.models.project import Project
from src.domain.models.tag import Tag, DocumentTag
from src.domain.models.source import Source


class TestProject:
    def test_create_project_space(self):
        project = Project.create("知识岛", "个人第二大脑桌面端", "E:/Code/rag_system")

        assert project.name == "知识岛"
        assert project.description == "个人第二大脑桌面端"
        assert project.root_path == "E:/Code/rag_system"
        assert project.created_at
        assert project.updated_at


class TestKnowledgeIslandDocument:
    def test_create_document_with_normalized_formats(self):
        doc = Document.create(
            project_id="project-1",
            title="README",
            source_type="markdown",
            source_path="E:/Code/rag_system/README.md",
            raw_content="# 标题\n\n正文",
            normalized_markdown="# 标题\n\n正文",
            plain_text="标题\n\n正文",
            rendered_html="<h1>标题</h1><p>正文</p>",
        )

        assert doc.project_id == "project-1"
        assert doc.source_type == "markdown"
        assert doc.raw_content.startswith("# 标题")
        assert doc.normalized_markdown.startswith("# 标题")
        assert doc.plain_text == "标题\n\n正文"
        assert "<script" not in doc.rendered_html.lower()
        assert doc.updated_at


class TestKnowledgeIslandChunk:
    def test_create_chunk_with_heading_path_and_plain_text(self):
        chunk = Chunk.create(
            document_id="doc-1",
            project_id="project-1",
            chunk_index=0,
            heading_path=["README", "架构"],
            chunk_markdown="## 架构\n\n内容",
            chunk_plain_text="架构\n\n内容",
            token_count=12,
            embedding_id="emb-1",
        )

        assert chunk.project_id == "project-1"
        assert chunk.chunk_index == 0
        assert chunk.heading_path == ["README", "架构"]
        assert chunk.chunk_markdown.startswith("## 架构")
        assert chunk.chunk_plain_text == "架构\n\n内容"
        assert chunk.token_count == 12
        assert chunk.embedding_id == "emb-1"


class TestTagAndSource:
    def test_create_tag_and_document_tag(self):
        tag = Tag.create("RAG", "#3366cc")
        link = DocumentTag.create("doc-1", tag.id)

        assert tag.name == "RAG"
        assert tag.color == "#3366cc"
        assert link.document_id == "doc-1"
        assert link.tag_id == tag.id

    def test_create_source_with_checksum(self):
        source = Source.create(
            document_id="doc-1",
            source_type="markdown",
            source_path="E:/Code/rag_system/README.md",
            checksum="abc123",
        )

        assert source.document_id == "doc-1"
        assert source.source_type == "markdown"
        assert source.checksum == "abc123"
        assert source.imported_at
```

- [ ] **Step 2: Run tests and verify failure**

Run:

```powershell
.venv\Scripts\python.exe -m pytest tests\test_domain\test_models.py -q
```

Expected: FAIL because `Project`, `Tag`, and `Source` models do not exist and existing `Document` / `Chunk` signatures do not support the new fields.

## Task 2: Implement Domain Models

**Files:**
- Create: `src/domain/models/project.py`
- Modify: `src/domain/models/document.py`
- Modify: `src/domain/models/chunk.py`
- Create: `src/domain/models/tag.py`
- Create: `src/domain/models/source.py`
- Modify: `src/domain/models/__init__.py`

- [ ] **Step 1: Implement minimal immutable dataclasses**

Use `@dataclass(frozen=True)`, UTC ISO timestamps, `create()`, `to_dict()`, and `from_dict()` where useful. Keep compatibility fields on `Document` and `Chunk` so existing application tests continue to pass while the new Knowledge Island fields are introduced.

- [ ] **Step 2: Run domain tests**

Run:

```powershell
.venv\Scripts\python.exe -m pytest tests\test_domain\test_models.py -q
```

Expected: PASS.

## Task 3: Prepare SQLite Schema For The New Models

**Files:**
- Modify: `src/adapters/storage/db.py`

- [ ] **Step 1: Extend schema without deleting old tables**

Add idempotent tables:

- `projects`
- additional nullable columns on `documents`
- additional nullable columns on `chunks`
- `tags`
- `document_tags`
- `sources`

Do not remove `workspaces`, `workspace_id`, `domain`, or `content` in this slice. Existing stores still depend on them.

- [ ] **Step 2: Run adapter tests**

Run:

```powershell
.venv\Scripts\python.exe -m pytest tests\test_adapters\test_storage.py -q
```

Expected: PASS.

## Task 4: Sync Documentation

**Files:**
- Modify: `README.md`
- Modify: `docs/BACKLOG.md`
- Modify: `docs/DEVLOG.md`
- Create: `docs/architecture/DATA_MODEL.md`

- [ ] **Step 1: Update product positioning**

State clearly that the formal project name is Knowledge Island / 知识岛 and that the current implementation is still a PySide6 local-first desktop app.

- [ ] **Step 2: Add data model documentation**

Document the first-slice model fields and explicitly mark knowledge mastery, graph, PDF/Word/OCR, and full Markdown-to-HTML as later slices.

- [ ] **Step 3: Update backlog and devlog**

Add a new 2026-05-16 section for this slice and convert old project-knowledge-only backlog direction into Knowledge Island work items.

## Task 5: Final Verification

**Files:**
- All touched files

- [ ] **Step 1: Run focused tests**

```powershell
.venv\Scripts\python.exe -m pytest tests\test_domain\test_models.py tests\test_adapters\test_storage.py -q
```

- [ ] **Step 2: Run full tests**

```powershell
.venv\Scripts\python.exe -m pytest tests -q
```

- [ ] **Step 3: Run import boundary check**

```powershell
.venv\Scripts\python.exe scripts\check_import_paths.py
```

- [ ] **Step 4: Run whitespace check**

```powershell
git diff --check
```

Expected: all commands pass. If any command fails, fix only failures caused by this slice.

## Self-Review

- This plan intentionally does not implement Knowledge Mastery, GraphNode/GraphEdge, Markdown rendering, PDF/DOCX parsing, OCR, or UI redesign yet.
- The existing `Workspace` model remains until a later compatibility migration can replace user-facing workspace wording with `Project`.
- No automatic commit is included because the repository rules say not to commit unless explicitly requested.
