from legacy.desktop.domain.models.document import Document
from legacy.desktop.domain.models.chunk import Chunk
from legacy.desktop.domain.models.project import Project
from legacy.desktop.domain.models.project_knowledge import (
    Evidence,
    KnowledgePoint,
    MasteryRecord,
    MasteryStatus,
    SkillArea,
)
from legacy.desktop.domain.models.source import Source
from legacy.desktop.domain.models.tag import DocumentTag, Tag
from legacy.desktop.domain.models.workspace import Workspace
from legacy.desktop.domain.models.graph import GraphEdge, GraphNode
from legacy.desktop.domain.models.task import Task, TaskStatus, TaskKind
from legacy.desktop.domain.models.conversation import ConversationRecord

__all__ = [
    "Document",
    "Chunk",
    "Project",
    "Evidence",
    "KnowledgePoint",
    "MasteryRecord",
    "MasteryStatus",
    "SkillArea",
    "Source",
    "Tag",
    "GraphNode",
    "GraphEdge",
    "DocumentTag",
    "Workspace",
    "Task",
    "TaskStatus",
    "TaskKind",
    "ConversationRecord",
]
