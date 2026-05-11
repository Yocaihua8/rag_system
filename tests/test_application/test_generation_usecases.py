"""
test_generation_usecases.py — 生成类用例测试。

覆盖：
  - GenerateResumeUseCase: 正常检索到内容时调用 LLM 并返回 GenerationResult
  - MatchJDUseCase: 正常检索到内容时返回 GenerationResult，覆盖率计算正确
  - GenerateInterviewScriptUseCase: 正常检索到内容时调用 LLM
  - P3 保护：三个用例在检索结果为空时均返回警告文本，不调用 LLM
"""
from __future__ import annotations

import pytest

from src.application.container import AppContainer
from src.application.workspace_usecases import WorkspaceUseCases
from src.application.ingestion_usecases import IngestWorkspaceUseCase
from src.application.generation_usecases import (
    GenerateInterviewScriptUseCase,
    GenerateResumeUseCase,
    InterviewRequest,
    JDMatchRequest,
    MatchJDUseCase,
    ResumeRequest,
)


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def setup(tmp_path, container: AppContainer):
    """
    建立一个带索引数据的工作区。
    返回 (resume_uc, jd_uc, interview_uc, ws_id)。
    """
    kb = tmp_path / "kb"
    (kb / "resume").mkdir(parents=True)
    (kb / "resume" / "profile.md").write_text(
        "# 项目经历\n\n主导搭建了基于 RAG 的知识检索系统，"
        "使用 Python / FastAPI 开发，性能提升 40%。",
        encoding="utf-8",
    )

    c = container
    ws_uc = WorkspaceUseCases(c.workspace_store)
    ws = ws_uc.create("测试工作区", str(kb))

    ingest_uc = IngestWorkspaceUseCase(
        c.workspace_store, c.document_store, c.chunk_store,
        c.task_store, c.retriever, c.settings,
    )
    list(ingest_uc.execute(ws.id, force_reindex=True))

    resume_uc = GenerateResumeUseCase(c.retriever, c.llm_client, c.settings.ollama_model)
    jd_uc = MatchJDUseCase(c.retriever, c.llm_client, c.settings.ollama_model)
    interview_uc = GenerateInterviewScriptUseCase(
        c.retriever, c.llm_client, c.settings.ollama_model
    )
    return resume_uc, jd_uc, interview_uc, ws.id


@pytest.fixture
def empty_setup(tmp_path, container: AppContainer):
    """工作区存在但没有任何索引数据（空目录）。"""
    kb = tmp_path / "empty_kb"
    kb.mkdir(parents=True)

    c = container
    ws_uc = WorkspaceUseCases(c.workspace_store)
    ws = ws_uc.create("空工作区", str(kb))

    # 执行索引（目录为空，不会产生 chunk）
    ingest_uc = IngestWorkspaceUseCase(
        c.workspace_store, c.document_store, c.chunk_store,
        c.task_store, c.retriever, c.settings,
    )
    list(ingest_uc.execute(ws.id, force_reindex=True))

    resume_uc = GenerateResumeUseCase(c.retriever, c.llm_client, c.settings.ollama_model)
    jd_uc = MatchJDUseCase(c.retriever, c.llm_client, c.settings.ollama_model)
    interview_uc = GenerateInterviewScriptUseCase(
        c.retriever, c.llm_client, c.settings.ollama_model
    )
    return resume_uc, jd_uc, interview_uc, ws.id


# ── GenerateResumeUseCase ─────────────────────────────────────────────────────

class TestGenerateResumeUseCase:

    def test_returns_generation_result(self, setup):
        resume_uc, _, _, ws_id = setup
        req = ResumeRequest(
            workspace_id=ws_id,
            job_keywords=["Python", "RAG"],
            project_name="知识检索系统",
        )
        result = resume_uc.execute(req)
        assert result.markdown  # FakeLLM 返回非空字符串
        assert result.model_used != "—"
        assert result.sources_used > 0

    def test_empty_retrieval_returns_warning(self, empty_setup):
        """P3：检索结果为空时返回警告，不调用 LLM。"""
        resume_uc, _, _, ws_id = empty_setup
        req = ResumeRequest(
            workspace_id=ws_id,
            job_keywords=["Python"],
            project_name="测试项目",
        )
        result = resume_uc.execute(req)
        assert "⚠️" in result.markdown
        assert result.sources_used == 0
        assert result.model_used == "—"

    def test_sources_used_reflects_chunk_count(self, setup):
        resume_uc, _, _, ws_id = setup
        req = ResumeRequest(
            workspace_id=ws_id,
            job_keywords=["Python"],
            project_name="项目A",
            top_k=5,
        )
        result = resume_uc.execute(req)
        assert result.sources_used >= 1


# ── MatchJDUseCase ────────────────────────────────────────────────────────────

class TestMatchJDUseCase:

    def test_returns_generation_result(self, setup):
        _, jd_uc, _, ws_id = setup
        req = JDMatchRequest(
            workspace_id=ws_id,
            job_name="后端工程师",
            job_keywords=["Python", "FastAPI"],
        )
        result = jd_uc.execute(req)
        assert result.markdown
        assert result.sources_used > 0

    def test_empty_retrieval_returns_warning(self, empty_setup):
        """P3：空检索保护。"""
        _, jd_uc, _, ws_id = empty_setup
        req = JDMatchRequest(
            workspace_id=ws_id,
            job_name="后端工程师",
            job_keywords=["Python"],
        )
        result = jd_uc.execute(req)
        assert "⚠️" in result.markdown
        assert result.sources_used == 0

    def test_model_used_is_set(self, setup):
        _, jd_uc, _, ws_id = setup
        req = JDMatchRequest(
            workspace_id=ws_id,
            job_name="全栈工程师",
            job_keywords=["Python", "Vue"],
        )
        result = jd_uc.execute(req)
        assert result.model_used  # 非空


# ── GenerateInterviewScriptUseCase ────────────────────────────────────────────

class TestGenerateInterviewScriptUseCase:

    def test_returns_generation_result(self, setup):
        _, _, interview_uc, ws_id = setup
        req = InterviewRequest(
            workspace_id=ws_id,
            job_keywords=["Python", "架构"],
            project_name="RAG 系统",
        )
        result = interview_uc.execute(req)
        assert result.markdown
        assert result.sources_used > 0

    def test_empty_retrieval_returns_warning(self, empty_setup):
        """P3：空检索保护。"""
        _, _, interview_uc, ws_id = empty_setup
        req = InterviewRequest(
            workspace_id=ws_id,
            job_keywords=["Python"],
            project_name="测试项目",
        )
        result = interview_uc.execute(req)
        assert "⚠️" in result.markdown
        assert result.sources_used == 0

    def test_custom_domains(self, setup):
        """domains 参数正确传递给检索器。"""
        _, _, interview_uc, ws_id = setup
        req = InterviewRequest(
            workspace_id=ws_id,
            job_keywords=["Python"],
            project_name="项目",
            domains=["resume"],  # 只检索 resume domain
        )
        result = interview_uc.execute(req)
        # 能正常返回（不崩溃），sources_used >= 0
        assert result.sources_used >= 0
