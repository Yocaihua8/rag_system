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
    project_text = f"{doc.title}\n{doc.content[:4000]}".lower()
    points: List[ProjectKnowledgePoint] = []
    for name, keywords in _TECH_KEYWORDS.items():
        search_text = project_text if name == "pytest" else text
        if any(keyword.lower() in search_text for keyword in keywords):
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
    if path.name.lower() not in _CONFIG_FILENAMES:
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
        if any(word in heading.lower() for word in _FLOW_HEADING_WORDS):
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
