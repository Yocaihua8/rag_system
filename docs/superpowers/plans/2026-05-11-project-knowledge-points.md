# Project Knowledge Points Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the first backend slice for a project knowledge base: persist project knowledge points and extract them from indexed project documents with deterministic rules.

**Architecture:** Add a small domain model, a port, and a SQLite adapter that match the existing `Document` / `Chunk` storage style. Add a rule-based application use case that reads existing indexed `Document` records and writes `ProjectKnowledgePoint` records without introducing LLM calls, UI changes, automatic questions, or scoring.

**Tech Stack:** Python dataclasses, sqlite3, pytest, existing hexagonal architecture under `src/domain`, `src/ports`, `src/adapters/storage`, and `src/application`.

---

## Scope

This plan implements only B-36 and B-37 from `docs/BACKLOG.md`.

In scope:
- `ProjectKnowledgePoint` domain model.
- `IProjectKnowledgeStore` port.
- SQLite table, indexes, adapter, and container wiring.
- Rule-based `ProjectAnalysisUseCase` that extracts points from existing documents.
- Tests and docs synchronization.

Out of scope:
- `AssessmentQuestion`, `AssessmentAnswer`, and `AssessmentResult`.
- Automatic question generation.
- Answer grading.
- Ability gap reports.
- Desktop UI integration.

---

## File Structure

- Create `src/domain/models/project_knowledge.py`
  - Holds the immutable `ProjectKnowledgePoint` model.
- Create `src/ports/project_knowledge_store.py`
  - Defines the persistence interface used by application code.
- Modify `src/adapters/storage/db.py`
  - Adds the `project_knowledge_points` table and indexes.
- Create `src/adapters/storage/sqlite_project_knowledge_store.py`
  - Implements `IProjectKnowledgeStore` with SQLite.
- Modify `src/application/container.py`
  - Adds `project_knowledge_store` to `AppContainer.build()` and `build_for_testing()`.
- Create `src/application/project_analysis_usecases.py`
  - Extracts knowledge points from stored documents.
- Modify `tests/test_domain/test_models.py`
  - Covers the new domain model.
- Modify `tests/test_adapters/test_storage.py`
  - Covers SQLite persistence and workspace cascade deletion.
- Create `tests/test_application/test_project_analysis_usecases.py`
  - Covers extraction rules and workspace-not-found behavior.
- Modify `docs/BACKLOG.md`
  - Mark B-36 and B-37 as completed after tests pass.
- Modify `docs/DEVLOG.md`
  - Record what changed, why, verification, and known boundary.

---

### Task 1: Add ProjectKnowledgePoint Model And Port

**Files:**
- Create: `src/domain/models/project_knowledge.py`
- Create: `src/ports/project_knowledge_store.py`
- Modify: `tests/test_domain/test_models.py`

- [ ] **Step 1: Write the failing domain tests**

Append this test class to `tests/test_domain/test_models.py`:

```python
from src.domain.models.project_knowledge import ProjectKnowledgePoint


class TestProjectKnowledgePoint:

    def test_create_defaults(self):
        point = ProjectKnowledgePoint.create(
            workspace_id="ws-1",
            name="FastAPI",
            kind="tech_stack",
            summary="项目使用 FastAPI 提供后端接口。",
            source_path="/repo/README.md",
            evidence="后端采用 FastAPI 构建 API",
            confidence=0.8,
        )

        assert point.workspace_id == "ws-1"
        assert point.name == "FastAPI"
        assert point.kind == "tech_stack"
        assert point.source_path == "/repo/README.md"
        assert point.confidence == 0.8
        assert point.id
        assert point.created_at

    def test_to_dict_and_from_dict_roundtrip(self):
        point = ProjectKnowledgePoint.create(
            workspace_id="ws-1",
            name="索引流程",
            kind="flow",
            summary="项目包含扫描、分块、索引流程。",
            source_path="/repo/docs/rag.md",
            evidence="扫描文件 -> 分块 -> 建立索引",
            confidence=0.7,
        )

        restored = ProjectKnowledgePoint.from_dict(point.to_dict())

        assert restored == point
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```powershell
.venv\Scripts\python.exe -m pytest tests\test_domain\test_models.py::TestProjectKnowledgePoint -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'src.domain.models.project_knowledge'`.

- [ ] **Step 3: Add the domain model**

Create `src/domain/models/project_knowledge.py`:

```python
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import uuid


@dataclass(frozen=True)
class ProjectKnowledgePoint:
    """从项目文档和代码中提炼出的可追溯知识点。"""

    id: str
    workspace_id: str
    name: str
    kind: str
    summary: str
    source_path: str
    evidence: str
    confidence: float
    created_at: str

    @classmethod
    def create(
        cls,
        workspace_id: str,
        name: str,
        kind: str,
        summary: str,
        source_path: str,
        evidence: str,
        confidence: float = 0.6,
    ) -> "ProjectKnowledgePoint":
        return cls(
            id=str(uuid.uuid4()),
            workspace_id=workspace_id,
            name=name.strip(),
            kind=kind.strip(),
            summary=summary.strip(),
            source_path=source_path,
            evidence=evidence.strip(),
            confidence=max(0.0, min(1.0, confidence)),
            created_at=datetime.now(timezone.utc).isoformat(),
        )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "workspace_id": self.workspace_id,
            "name": self.name,
            "kind": self.kind,
            "summary": self.summary,
            "source_path": self.source_path,
            "evidence": self.evidence,
            "confidence": self.confidence,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ProjectKnowledgePoint":
        return cls(
            id=data["id"],
            workspace_id=data["workspace_id"],
            name=data["name"],
            kind=data["kind"],
            summary=data["summary"],
            source_path=data["source_path"],
            evidence=data["evidence"],
            confidence=float(data.get("confidence", 0.6)),
            created_at=data["created_at"],
        )
```

- [ ] **Step 4: Add the store port**

Create `src/ports/project_knowledge_store.py`:

```python
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List

from src.domain.models.project_knowledge import ProjectKnowledgePoint


class IProjectKnowledgeStore(ABC):

    @abstractmethod
    def save_batch(self, points: List[ProjectKnowledgePoint]) -> None:
        raise NotImplementedError

    @abstractmethod
    def list_by_workspace(self, workspace_id: str) -> List[ProjectKnowledgePoint]:
        raise NotImplementedError

    @abstractmethod
    def delete_by_workspace(self, workspace_id: str) -> None:
        raise NotImplementedError

    @abstractmethod
    def count_by_workspace(self, workspace_id: str) -> int:
        raise NotImplementedError
```

- [ ] **Step 5: Run domain test to verify it passes**

Run:

```powershell
.venv\Scripts\python.exe -m pytest tests\test_domain\test_models.py::TestProjectKnowledgePoint -v
```

Expected: PASS.

- [ ] **Step 6: Commit**

Stage only the files from this task:

```powershell
git add src\domain\models\project_knowledge.py src\ports\project_knowledge_store.py tests\test_domain\test_models.py
git commit -m "feat: 新增项目知识点领域模型"
```

If the local worktree contains unrelated unstaged migration changes, do not stage them.

---

### Task 2: Add SQLite Persistence

**Files:**
- Modify: `src/adapters/storage/db.py`
- Create: `src/adapters/storage/sqlite_project_knowledge_store.py`
- Modify: `tests/test_adapters/test_storage.py`

- [ ] **Step 1: Write failing storage tests**

In `tests/test_adapters/test_storage.py`, add these imports:

```python
from src.adapters.storage.sqlite_project_knowledge_store import SqliteProjectKnowledgeStore
from src.domain.models.project_knowledge import ProjectKnowledgePoint
```

Add the new store to the `stores` fixture:

```python
        "pkp":   SqliteProjectKnowledgeStore(conn),
```

Append this test class:

```python
class TestProjectKnowledgeStore:

    def _make_ws(self, stores) -> str:
        ws = Workspace.create("project", "/repo")
        stores["ws"].save(ws)
        return ws.id

    def test_save_batch_and_list_by_workspace(self, stores):
        ws_id = self._make_ws(stores)
        points = [
            ProjectKnowledgePoint.create(
                workspace_id=ws_id,
                name="FastAPI",
                kind="tech_stack",
                summary="后端 API 技术栈。",
                source_path="/repo/README.md",
                evidence="FastAPI",
                confidence=0.8,
            ),
            ProjectKnowledgePoint.create(
                workspace_id=ws_id,
                name="tests",
                kind="test",
                summary="项目包含测试目录。",
                source_path="/repo/tests/test_app.py",
                evidence="tests/test_app.py",
                confidence=0.7,
            ),
        ]

        stores["pkp"].save_batch(points)
        result = stores["pkp"].list_by_workspace(ws_id)

        assert [p.name for p in result] == ["FastAPI", "tests"]
        assert stores["pkp"].count_by_workspace(ws_id) == 2

    def test_delete_by_workspace(self, stores):
        ws_id = self._make_ws(stores)
        point = ProjectKnowledgePoint.create(
            workspace_id=ws_id,
            name="README",
            kind="concept",
            summary="README 描述项目入口。",
            source_path="/repo/README.md",
            evidence="# Project",
            confidence=0.6,
        )
        stores["pkp"].save_batch([point])

        stores["pkp"].delete_by_workspace(ws_id)

        assert stores["pkp"].list_by_workspace(ws_id) == []
        assert stores["pkp"].count_by_workspace(ws_id) == 0
```

Add this assertion to `TestCascadeDelete.test_cascade_on_workspace_delete` after the conversation is saved:

```python
        stores["pkp"].save_batch([
            ProjectKnowledgePoint.create(
                workspace_id=ws.id,
                name="FastAPI",
                kind="tech_stack",
                summary="后端 API 技术栈。",
                source_path="/p",
                evidence="FastAPI",
                confidence=0.8,
            )
        ])
```

Add this assertion after `stores["ws"].delete(ws.id)`:

```python
        assert stores["pkp"].count_by_workspace(ws.id) == 0
```

- [ ] **Step 2: Run storage tests to verify they fail**

Run:

```powershell
.venv\Scripts\python.exe -m pytest tests\test_adapters\test_storage.py::TestProjectKnowledgeStore -v
```

Expected: FAIL with missing adapter or missing table.

- [ ] **Step 3: Add SQLite schema**

In `src/adapters/storage/db.py`, add this table creation inside `init_schema(conn)` after the `chunks` table and before task/conversation tables:

```python
    conn.execute("""
    CREATE TABLE IF NOT EXISTS project_knowledge_points (
        id TEXT PRIMARY KEY,
        workspace_id TEXT NOT NULL,
        name TEXT NOT NULL,
        kind TEXT NOT NULL,
        summary TEXT NOT NULL,
        source_path TEXT NOT NULL,
        evidence TEXT NOT NULL,
        confidence REAL NOT NULL,
        created_at TEXT NOT NULL,
        FOREIGN KEY(workspace_id) REFERENCES workspaces(id) ON DELETE CASCADE
    )
    """)
```

Add these indexes inside `_ensure_indexes(conn)`:

```python
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_pkp_workspace "
        "ON project_knowledge_points(workspace_id)"
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_pkp_workspace_kind "
        "ON project_knowledge_points(workspace_id, kind)"
    )
```

- [ ] **Step 4: Add SQLite adapter**

Create `src/adapters/storage/sqlite_project_knowledge_store.py`:

```python
from __future__ import annotations

import sqlite3
from typing import List

from src.domain.models.project_knowledge import ProjectKnowledgePoint
from src.ports.project_knowledge_store import IProjectKnowledgeStore


class SqliteProjectKnowledgeStore(IProjectKnowledgeStore):

    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def save_batch(self, points: List[ProjectKnowledgePoint]) -> None:
        self._conn.executemany(
            """
            INSERT OR REPLACE INTO project_knowledge_points
                (id, workspace_id, name, kind, summary, source_path, evidence, confidence, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    p.id,
                    p.workspace_id,
                    p.name,
                    p.kind,
                    p.summary,
                    p.source_path,
                    p.evidence,
                    p.confidence,
                    p.created_at,
                )
                for p in points
            ],
        )
        self._conn.commit()

    def list_by_workspace(self, workspace_id: str) -> List[ProjectKnowledgePoint]:
        rows = self._conn.execute(
            """
            SELECT * FROM project_knowledge_points
            WHERE workspace_id = ?
            ORDER BY kind ASC, name ASC, created_at ASC
            """,
            (workspace_id,),
        ).fetchall()
        return [_row_to_point(row) for row in rows]

    def delete_by_workspace(self, workspace_id: str) -> None:
        self._conn.execute(
            "DELETE FROM project_knowledge_points WHERE workspace_id = ?",
            (workspace_id,),
        )
        self._conn.commit()

    def count_by_workspace(self, workspace_id: str) -> int:
        row = self._conn.execute(
            "SELECT COUNT(*) FROM project_knowledge_points WHERE workspace_id = ?",
            (workspace_id,),
        ).fetchone()
        return row[0] if row else 0


def _row_to_point(row: sqlite3.Row) -> ProjectKnowledgePoint:
    return ProjectKnowledgePoint(
        id=row["id"],
        workspace_id=row["workspace_id"],
        name=row["name"],
        kind=row["kind"],
        summary=row["summary"],
        source_path=row["source_path"],
        evidence=row["evidence"],
        confidence=row["confidence"],
        created_at=row["created_at"],
    )
```

- [ ] **Step 5: Run storage tests to verify they pass**

Run:

```powershell
.venv\Scripts\python.exe -m pytest tests\test_adapters\test_storage.py::TestProjectKnowledgeStore tests\test_adapters\test_storage.py::TestCascadeDelete::test_cascade_on_workspace_delete -v
```

Expected: PASS.

- [ ] **Step 6: Commit**

```powershell
git add src\adapters\storage\db.py src\adapters\storage\sqlite_project_knowledge_store.py tests\test_adapters\test_storage.py
git commit -m "feat: 新增项目知识点 SQLite 存储"
```

If the current checkout is intentionally dirty, keep the commit scoped to these files only or skip committing and report the exact reason.

---

### Task 3: Wire Store Into AppContainer

**Files:**
- Modify: `src/application/container.py`
- Modify: `tests/test_application/test_project_analysis_usecases.py`

- [ ] **Step 1: Create a failing container wiring test**

Create `tests/test_application/test_project_analysis_usecases.py` with this initial content:

```python
from __future__ import annotations

import dataclasses
from pathlib import Path

from src.application.container import AppContainer
from src.config.settings import load_settings


def _build_container(tmp_path) -> AppContainer:
    settings = load_settings(override_env={
        "RAG_KB_ROOT": str(tmp_path / "kb"),
        "RAG_RUNTIME_DIR": str(tmp_path / "runtime"),
        "RAG_RETRIEVER_KIND": "keyword",
        "RAG_EMBED_PROVIDER": "none",
    })
    settings = dataclasses.replace(settings, db_path=Path(":memory:"))
    return AppContainer.build_for_testing(settings)


def test_container_exposes_project_knowledge_store(tmp_path):
    container = _build_container(tmp_path)

    assert container.project_knowledge_store is not None
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```powershell
.venv\Scripts\python.exe -m pytest tests\test_application\test_project_analysis_usecases.py::test_container_exposes_project_knowledge_store -v
```

Expected: FAIL with `AttributeError` or dataclass constructor error.

- [ ] **Step 3: Wire the store in AppContainer**

In `src/application/container.py`, add the port import:

```python
from src.ports.project_knowledge_store import IProjectKnowledgeStore
```

Add this dataclass field after `conversation_store`:

```python
    project_knowledge_store: IProjectKnowledgeStore
```

In both `build()` and `build_for_testing()`, add the adapter import near other storage imports:

```python
        from src.adapters.storage.sqlite_project_knowledge_store import SqliteProjectKnowledgeStore
```

In `build()`, create the store after `conv_store`:

```python
        project_knowledge_store = SqliteProjectKnowledgeStore(conn)
```

Add it to the returned `cls(...)`:

```python
            project_knowledge_store=project_knowledge_store,
```

In `build_for_testing()`, add this returned argument:

```python
            project_knowledge_store=SqliteProjectKnowledgeStore(conn),
```

- [ ] **Step 4: Run container wiring test to verify it passes**

Run:

```powershell
.venv\Scripts\python.exe -m pytest tests\test_application\test_project_analysis_usecases.py::test_container_exposes_project_knowledge_store -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```powershell
git add src\application\container.py tests\test_application\test_project_analysis_usecases.py
git commit -m "feat: 接入项目知识点存储容器"
```

---

### Task 4: Add Rule-Based Project Analysis Use Case

**Files:**
- Create: `src/application/project_analysis_usecases.py`
- Modify: `tests/test_application/test_project_analysis_usecases.py`

- [ ] **Step 1: Extend failing use case tests**

Replace `tests/test_application/test_project_analysis_usecases.py` with this content:

```python
from __future__ import annotations

import dataclasses
from pathlib import Path

import pytest

from src.application.container import AppContainer
from src.application.project_analysis_usecases import ProjectAnalysisUseCase
from src.application.workspace_usecases import WorkspaceUseCases
from src.config.settings import load_settings
from src.domain.errors import NotFoundError
from src.domain.models.document import Document


def _build_container(tmp_path) -> AppContainer:
    settings = load_settings(override_env={
        "RAG_KB_ROOT": str(tmp_path / "kb"),
        "RAG_RUNTIME_DIR": str(tmp_path / "runtime"),
        "RAG_RETRIEVER_KIND": "keyword",
        "RAG_EMBED_PROVIDER": "none",
    })
    settings = dataclasses.replace(settings, db_path=Path(":memory:"))
    return AppContainer.build_for_testing(settings)


def test_container_exposes_project_knowledge_store(tmp_path):
    container = _build_container(tmp_path)

    assert container.project_knowledge_store is not None


class TestProjectAnalysisUseCase:

    def test_extracts_knowledge_points_from_project_documents(self, tmp_path):
        container = _build_container(tmp_path)
        workspace = WorkspaceUseCases(container.workspace_store).create(
            "project", str(tmp_path / "repo")
        )
        docs = [
            Document.create(
                workspace_id=workspace.id,
                title="README",
                source_path=str(tmp_path / "repo" / "README.md"),
                content="# RAG 系统\n\n使用 FastAPI、SQLite 和 PySide6 构建项目知识库。\n\n## 索引流程\n扫描文件后分块并建立索引。",
                domain="general",
                tags=["Python"],
            ),
            Document.create(
                workspace_id=workspace.id,
                title="pyproject",
                source_path=str(tmp_path / "repo" / "pyproject.toml"),
                content="[project]\ndependencies = ['pytest']",
                domain="general",
                tags=[],
            ),
            Document.create(
                workspace_id=workspace.id,
                title="test_app",
                source_path=str(tmp_path / "repo" / "tests" / "test_app.py"),
                content="def test_app():\n    assert True",
                domain="general",
                tags=[],
            ),
        ]
        container.document_store.save_batch(docs)

        result = ProjectAnalysisUseCase(
            workspace_store=container.workspace_store,
            document_store=container.document_store,
            project_knowledge_store=container.project_knowledge_store,
        ).analyze(workspace.id)

        names = {point.name for point in result.points}
        kinds = {point.kind for point in result.points}

        assert result.total_documents == 3
        assert result.total_points == len(result.points)
        assert "FastAPI" in names
        assert "SQLite" in names
        assert "PySide6" in names
        assert "索引流程" in names
        assert "测试目录" in names
        assert "tech_stack" in kinds
        assert "flow" in kinds
        assert "test" in kinds
        assert all(point.source_path for point in result.points)
        assert container.project_knowledge_store.count_by_workspace(workspace.id) == len(result.points)

    def test_analyze_replaces_old_points_for_workspace(self, tmp_path):
        container = _build_container(tmp_path)
        workspace = WorkspaceUseCases(container.workspace_store).create(
            "project", str(tmp_path / "repo")
        )
        first_doc = Document.create(
            workspace_id=workspace.id,
            title="README",
            source_path=str(tmp_path / "repo" / "README.md"),
            content="FastAPI",
            domain="general",
            tags=[],
        )
        container.document_store.save_batch([first_doc])
        usecase = ProjectAnalysisUseCase(
            workspace_store=container.workspace_store,
            document_store=container.document_store,
            project_knowledge_store=container.project_knowledge_store,
        )
        usecase.analyze(workspace.id)
        first_count = container.project_knowledge_store.count_by_workspace(workspace.id)

        container.document_store.delete(first_doc.id)
        second_doc = Document.create(
            workspace_id=workspace.id,
            title="README",
            source_path=str(tmp_path / "repo" / "README.md"),
            content="SQLite",
            domain="general",
            tags=[],
        )
        container.document_store.save_batch([second_doc])
        result = usecase.analyze(workspace.id)

        assert first_count > 0
        assert {point.name for point in result.points} == {"SQLite"}
        assert container.project_knowledge_store.count_by_workspace(workspace.id) == 1

    def test_empty_workspace_returns_empty_result(self, tmp_path):
        container = _build_container(tmp_path)
        workspace = WorkspaceUseCases(container.workspace_store).create(
            "empty", str(tmp_path / "empty")
        )

        result = ProjectAnalysisUseCase(
            workspace_store=container.workspace_store,
            document_store=container.document_store,
            project_knowledge_store=container.project_knowledge_store,
        ).analyze(workspace.id)

        assert result.total_documents == 0
        assert result.total_points == 0
        assert result.points == []

    def test_nonexistent_workspace_raises(self, tmp_path):
        container = _build_container(tmp_path)

        with pytest.raises(NotFoundError):
            ProjectAnalysisUseCase(
                workspace_store=container.workspace_store,
                document_store=container.document_store,
                project_knowledge_store=container.project_knowledge_store,
            ).analyze("no-such-workspace")
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```powershell
.venv\Scripts\python.exe -m pytest tests\test_application\test_project_analysis_usecases.py -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'src.application.project_analysis_usecases'`.

- [ ] **Step 3: Add project analysis use case**

Create `src/application/project_analysis_usecases.py`:

```python
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List

from src.domain.errors import NotFoundError
from src.domain.models.document import Document
from src.domain.models.project_knowledge import ProjectKnowledgePoint
from src.ports.document_store import IDocumentStore
from src.ports.project_knowledge_store import IProjectKnowledgeStore
from src.ports.workspace_store import IWorkspaceStore


@dataclass(frozen=True)
class ProjectAnalysisResult:
    workspace_id: str
    total_documents: int
    total_points: int
    points: List[ProjectKnowledgePoint]


class ProjectAnalysisUseCase:

    def __init__(
        self,
        workspace_store: IWorkspaceStore,
        document_store: IDocumentStore,
        project_knowledge_store: IProjectKnowledgeStore,
    ) -> None:
        self._workspace_store = workspace_store
        self._document_store = document_store
        self._project_knowledge_store = project_knowledge_store

    def analyze(self, workspace_id: str) -> ProjectAnalysisResult:
        workspace = self._workspace_store.get(workspace_id)
        if workspace is None:
            raise NotFoundError("Workspace", workspace_id)

        documents = self._document_store.list_by_workspace(workspace_id)
        points = _dedupe_points(_extract_points(documents))
        self._project_knowledge_store.delete_by_workspace(workspace_id)
        if points:
            self._project_knowledge_store.save_batch(points)

        return ProjectAnalysisResult(
            workspace_id=workspace_id,
            total_documents=len(documents),
            total_points=len(points),
            points=points,
        )


_TECH_KEYWORDS = {
    "FastAPI": ["fastapi"],
    "SQLite": ["sqlite"],
    "PySide6": ["pyside6", "qt"],
    "ChromaDB": ["chromadb", "chroma"],
    "Ollama": ["ollama"],
    "pytest": ["pytest"],
    "Docker": ["docker", "docker-compose"],
    "React": ["react"],
    "Vue": ["vue"],
    "TypeScript": ["typescript", ".ts"],
    "Python": ["python", ".py"],
}

_CONFIG_FILENAMES = {
    "pyproject.toml",
    "requirements.txt",
    "package.json",
    "docker-compose.yml",
    "docker-compose.yaml",
    ".env.example",
}

_FLOW_HEADING_WORDS = ("流程", "pipeline", "工作流", "索引", "检索", "部署")
_MD_HEADING = re.compile(r"^(#{1,6})\s+(.+)$", re.MULTILINE)


def _extract_points(documents: Iterable[Document]) -> List[ProjectKnowledgePoint]:
    points: List[ProjectKnowledgePoint] = []
    for doc in documents:
        points.extend(_extract_tech_stack_points(doc))
        points.extend(_extract_config_points(doc))
        points.extend(_extract_test_points(doc))
        points.extend(_extract_flow_points(doc))
    return points


def _extract_tech_stack_points(doc: Document) -> List[ProjectKnowledgePoint]:
    text = f"{doc.source_path}\n{doc.title}\n{doc.content[:4000]}".lower()
    points: List[ProjectKnowledgePoint] = []
    for name, keywords in _TECH_KEYWORDS.items():
        if any(keyword.lower() in text for keyword in keywords):
            points.append(ProjectKnowledgePoint.create(
                workspace_id=doc.workspace_id,
                name=name,
                kind="tech_stack",
                summary=f"项目中出现 {name} 相关技术线索。",
                source_path=doc.source_path,
                evidence=_evidence(doc.content, name),
                confidence=0.75,
            ))
    return points


def _extract_config_points(doc: Document) -> List[ProjectKnowledgePoint]:
    path = Path(doc.source_path)
    filename = path.name.lower()
    if filename not in _CONFIG_FILENAMES:
        return []
    return [ProjectKnowledgePoint.create(
        workspace_id=doc.workspace_id,
        name=path.name,
        kind="config",
        summary=f"项目包含配置文件 {path.name}。",
        source_path=doc.source_path,
        evidence=_first_non_empty_line(doc.content) or path.name,
        confidence=0.7,
    )]


def _extract_test_points(doc: Document) -> List[ProjectKnowledgePoint]:
    normalized_path = doc.source_path.replace("\\", "/").lower()
    path = Path(doc.source_path)
    if "/tests/" not in normalized_path and not path.name.lower().startswith("test_"):
        return []
    return [ProjectKnowledgePoint.create(
        workspace_id=doc.workspace_id,
        name="测试目录",
        kind="test",
        summary="项目包含测试文件，可作为验证入口。",
        source_path=doc.source_path,
        evidence=path.name,
        confidence=0.7,
    )]


def _extract_flow_points(doc: Document) -> List[ProjectKnowledgePoint]:
    points: List[ProjectKnowledgePoint] = []
    for match in _MD_HEADING.finditer(doc.content):
        heading = match.group(2).strip()
        heading_lower = heading.lower()
        if any(word in heading_lower for word in _FLOW_HEADING_WORDS):
            points.append(ProjectKnowledgePoint.create(
                workspace_id=doc.workspace_id,
                name=heading,
                kind="flow",
                summary=f"项目文档描述了 {heading}。",
                source_path=doc.source_path,
                evidence=match.group(0).strip(),
                confidence=0.65,
            ))
    return points


def _dedupe_points(points: List[ProjectKnowledgePoint]) -> List[ProjectKnowledgePoint]:
    result: List[ProjectKnowledgePoint] = []
    seen: set[tuple[str, str]] = set()
    for point in points:
        key = (point.kind, point.name.lower())
        if key in seen:
            continue
        seen.add(key)
        result.append(point)
    return result


def _evidence(content: str, name: str) -> str:
    for line in content.splitlines():
        if name.lower() in line.lower():
            return line.strip()[:200]
    return name


def _first_non_empty_line(content: str) -> str:
    for line in content.splitlines():
        stripped = line.strip()
        if stripped:
            return stripped[:200]
    return ""
```

- [ ] **Step 4: Run use case tests to verify they pass**

Run:

```powershell
.venv\Scripts\python.exe -m pytest tests\test_application\test_project_analysis_usecases.py -v
```

Expected: PASS.

- [ ] **Step 5: Run nearby regression tests**

Run:

```powershell
.venv\Scripts\python.exe -m pytest tests\test_domain tests\test_adapters\test_storage.py tests\test_application\test_project_analysis_usecases.py tests\test_application\test_ingestion_usecases.py -v
```

Expected: PASS.

- [ ] **Step 6: Commit**

```powershell
git add src\application\project_analysis_usecases.py tests\test_application\test_project_analysis_usecases.py
git commit -m "feat: 新增项目知识点提炼用例"
```

---

### Task 5: Sync Documentation

**Files:**
- Modify: `docs/BACKLOG.md`
- Modify: `docs/DEVLOG.md`

- [ ] **Step 1: Update BACKLOG**

In `docs/BACKLOG.md`, move B-36 and B-37 from the active task list to the completed area using the existing document style. The completed wording should be:

```markdown
| B-36 | 已完成 | 新增 `ProjectKnowledgePoint`、`IProjectKnowledgeStore` 与 SQLite Store，知识点保留来源文件和证据片段 |
| B-37 | 已完成 | 新增规则式项目知识点提炼用例，基于 README、docs、路径、配置文件、测试目录和技术关键词生成知识点 |
```

Keep B-38 to B-42 active because assessment question, scoring, gap report, and admin page are not implemented by this plan.

- [ ] **Step 2: Update DEVLOG**

Append this entry to `docs/DEVLOG.md`:

```markdown
## 2026-05-11 - 项目知识点模型与提炼用例

### 变更内容
- 新增 `ProjectKnowledgePoint` 领域模型，记录知识点名称、类型、摘要、来源文件、证据片段和置信度。
- 新增 `IProjectKnowledgeStore` 与 SQLite 实现，支持按工作区保存、查询、清空和计数。
- 新增 `ProjectAnalysisUseCase`，从已入库文档中按规则提炼技术栈、配置文件、测试入口和流程类知识点。

### 修改原因
- 为“项目知识库”提供可追溯的中间层数据。
- 为后续评估题、掌握评估和差距报告提供稳定输入。

### 验证
- `.venv\Scripts\python.exe -m pytest tests\test_domain tests\test_adapters\test_storage.py tests\test_application\test_project_analysis_usecases.py tests\test_application\test_ingestion_usecases.py -v`

### 边界
- 本次未实现自动出题、回答评分、差距报告和桌面端展示。
- 本次提炼规则是确定性规则，不调用 LLM。
```

- [ ] **Step 3: Run docs diff check for touched files**

Run:

```powershell
git diff --check -- docs\BACKLOG.md docs\DEVLOG.md
```

Expected: exit code 0.

- [ ] **Step 4: Commit**

```powershell
git add docs\BACKLOG.md docs\DEVLOG.md
git commit -m "docs: 记录项目知识点提炼进展"
```

---

### Task 6: Final Verification

**Files:**
- Verify all files touched by Tasks 1-5.

- [ ] **Step 1: Run focused test suite**

Run:

```powershell
.venv\Scripts\python.exe -m pytest tests\test_domain tests\test_adapters\test_storage.py tests\test_application\test_project_analysis_usecases.py tests\test_application\test_ingestion_usecases.py -v
```

Expected: PASS.

- [ ] **Step 2: Run full test suite**

Run:

```powershell
.venv\Scripts\python.exe -m pytest tests -q
```

Expected: PASS.

- [ ] **Step 3: Run scoped whitespace check**

Run:

```powershell
git diff --check -- src\domain\models\project_knowledge.py src\ports\project_knowledge_store.py src\adapters\storage\db.py src\adapters\storage\sqlite_project_knowledge_store.py src\application\container.py src\application\project_analysis_usecases.py tests\test_domain\test_models.py tests\test_adapters\test_storage.py tests\test_application\test_project_analysis_usecases.py docs\BACKLOG.md docs\DEVLOG.md
```

Expected: exit code 0.

- [ ] **Step 4: Inspect final changed files**

Run:

```powershell
git status --short
git diff -- src\domain\models\project_knowledge.py src\ports\project_knowledge_store.py src\adapters\storage\db.py src\adapters\storage\sqlite_project_knowledge_store.py src\application\container.py src\application\project_analysis_usecases.py tests\test_domain\test_models.py tests\test_adapters\test_storage.py tests\test_application\test_project_analysis_usecases.py docs\BACKLOG.md docs\DEVLOG.md
```

Expected: only files from this plan contain the B-36/B-37 changes.

---

## Self-Review

- Spec coverage: B-36 is covered by Tasks 1-3. B-37 is covered by Task 4. Documentation sync is covered by Task 5. Verification is covered by Task 6.
- Boundary check: The plan does not implement B-38 to B-42. It stores extracted knowledge points but does not generate questions, grade answers, produce reports, or add desktop UI.
- Type consistency: `ProjectKnowledgePoint`, `IProjectKnowledgeStore`, `SqliteProjectKnowledgeStore`, and `ProjectAnalysisUseCase` use the same field names and method names across model, port, adapter, container, and tests.
- Existing architecture fit: The plan follows the existing `Document` / `Chunk` model style, SQLite adapter style, `AppContainer` composition root rule, and pytest layout.
