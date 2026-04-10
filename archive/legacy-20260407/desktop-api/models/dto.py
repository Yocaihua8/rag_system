from typing import Any, Dict, List

from pydantic import BaseModel, Field


class IngestRequest(BaseModel):
    paths: List[str] = Field(default_factory=list)


class IngestResponse(BaseModel):
    task_id: str
    paths: List[str]
    result: Dict[str, Any]


class BuildResponse(BaseModel):
    task_id: str


class QueryRequest(BaseModel):
    question: str = ""
    top_k: int = Field(default=5, ge=1, le=20)


class TaskStatus(BaseModel):
    id: str
    status: str
    progress: int
    message: str


class QueryResponse(BaseModel):
    answer: str
    hits: List[str] = Field(default_factory=list)


class HistoryItem(BaseModel):
    id: str
    question: str
    answer: str
    created_at: str


class HistoryResponse(BaseModel):
    items: List[HistoryItem] = Field(default_factory=list)
