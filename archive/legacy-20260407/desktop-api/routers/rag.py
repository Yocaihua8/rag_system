from fastapi import APIRouter, HTTPException, Query

from desktop.db.history import add_history, list_history
from desktop.models.dto import (
    BuildResponse,
    HistoryResponse,
    IngestRequest,
    IngestResponse,
    QueryRequest,
    QueryResponse,
    TaskStatus,
)
from desktop.services.ingest_service import IngestService
from desktop.tasks.task_manager import TaskManager
from desktop.services.rag_service import RagService

router = APIRouter()
service = RagService()
ingest_service = IngestService()
manager = TaskManager()


@router.get("/health")
def health():
    return {"status": "ok"}


@router.post("/ingest", response_model=IngestResponse)
def ingest(payload: IngestRequest):
    paths = payload.paths
    if not paths:
        raise HTTPException(status_code=400, detail="paths cannot be empty")

    task_id = manager.create(message="ingest started")
    try:
        manager.update(task_id, "running", 20, "collecting files")
        result = ingest_service.import_paths(paths)
        if result["error_count"] > 0:
            manager.update(task_id, "failed", 100, f"ingest failed, errors={result['error_count']}")
            raise HTTPException(
                status_code=500,
                detail={
                    "message": "ingest failed",
                    "task_id": task_id,
                    "result": result,
                },
            )
        else:
            manager.update(task_id, "done", 100, f"ingest completed, imported={result['imported_count']}")
        return {"task_id": task_id, "paths": paths, "result": result}
    except HTTPException:
        raise
    except Exception as ex:
        manager.update(task_id, "failed", 100, f"ingest exception: {ex}")
        raise HTTPException(
            status_code=500,
            detail={
                "message": "ingest exception",
                "task_id": task_id,
                "error": str(ex),
            },
        )


@router.post("/build", response_model=BuildResponse)
def build():
    task_id = manager.create(message="build started")
    try:
        manager.update(task_id, "running", 20, "loading documents")
        service.load()
        manager.update(task_id, "done", 100, "build completed")
    except HTTPException:
        raise
    except Exception as ex:
        manager.update(task_id, "failed", 100, f"build exception: {ex}")
        raise HTTPException(
            status_code=500,
            detail={
                "message": "build exception",
                "task_id": task_id,
                "error": str(ex),
            },
        )
    return {"task_id": task_id}


@router.get("/task/{task_id}", response_model=TaskStatus)
def task_status(task_id: str):
    return manager.get(task_id)


@router.post("/query", response_model=QueryResponse)
def query(payload: QueryRequest):
    question = payload.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="question cannot be empty")

    top_k = payload.top_k
    try:
        result = service.query(question, top_k=top_k)
        add_history(question, result.get("answer", ""))
        return result
    except Exception as ex:
        raise HTTPException(status_code=500, detail=f"query failed: {ex}")


@router.get("/history", response_model=HistoryResponse)
def history(limit: int = Query(default=50, ge=1, le=200)):
    return {"items": list_history(limit)}
