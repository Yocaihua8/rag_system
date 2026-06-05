"""
test_query_usecases.py — QueryKnowledgeBaseUseCase 测试。

覆盖：
  - 基本问答（execute）返回 QueryResponse
  - 答案内容来自 FakeLLM
  - 问答历史被保存并可检索
  - 空知识库下仍能返回结果（无 chunk）
  - 流式问答（execute_streaming）合并 token 并保存历史
  - get_history 分页 / limit
  - 多轮对话历史顺序
"""
from __future__ import annotations

import pytest

from legacy.desktop.application.container import AppContainer
from legacy.desktop.application.workspace_usecases import WorkspaceUseCases
from legacy.desktop.application.ingestion_usecases import IngestWorkspaceUseCase
from legacy.desktop.application.query_usecases import QueryKnowledgeBaseUseCase, QueryRequest
from legacy.desktop.domain.models.conversation import ConversationRecord
from legacy.desktop.ports.llm_client import LLMResponse


# ── Fixtures ──────────────────────────────────────────────────────────────────

class CapturingLLM:
    def __init__(self):
        self.prompts: list[str] = []

    def generate(self, request):
        self.prompts.append(request.prompt)
        return LLMResponse(content="[captured answer]", model="captured")

    def stream(self, request):
        self.prompts.append(request.prompt)
        yield "[captured answer]"

    def is_available(self):
        return True

    def list_models(self):
        return ["captured"]


@pytest.fixture
def setup(tmp_path, container: AppContainer):
    """
    为每个测试提供：
      - ws_uc   : WorkspaceUseCases
      - query_uc: QueryKnowledgeBaseUseCase
      - ws_id   : 已创建的工作区 ID
      - container
    同时预置一个带索引数据的工作区（kb_dir 含 2 个 .md 文件）。
    """
    # 准备知识库文件
    kb = tmp_path / "kb"
    (kb / "resume").mkdir(parents=True)
    (kb / "jds").mkdir(parents=True)
    (kb / "resume" / "profile.md").write_text(
        "# 个人简介\n\n## 技能\nPython FastAPI RAG 向量检索\n\n## 经历\n参与过多个 RAG 系统搭建。",
        encoding="utf-8",
    )
    (kb / "jds" / "jd_001.md").write_text(
        "# JD-001 后端工程师\n\n要求：Python FastAPI 高并发 微服务",
        encoding="utf-8",
    )

    ws_uc = WorkspaceUseCases(container.workspace_store)
    ws = ws_uc.create("测试工作区", str(kb))

    # 先索引，让 KeywordRetriever 有数据
    ingest_uc = IngestWorkspaceUseCase(
        workspace_store=container.workspace_store,
        document_store=container.document_store,
        chunk_store=container.chunk_store,
        task_store=container.task_store,
        retriever=container.retriever,
        settings=container.settings,
    )
    for _ in ingest_uc.execute(ws.id):
        pass  # 消费生成器，完成索引

    query_uc = QueryKnowledgeBaseUseCase(
        retriever=container.retriever,
        llm_client=container.llm_client,
        conversation_store=container.conversation_store,
    )

    return {"ws_uc": ws_uc, "query_uc": query_uc, "ws_id": ws.id, "container": container}


# ── execute 基本测试 ──────────────────────────────────────────────────────────

class TestQueryExecute:

    def test_returns_query_response(self, setup):
        """execute 应返回 QueryResponse，包含 answer / sources / scores / model_used。"""
        query_uc = setup["query_uc"]
        ws_id = setup["ws_id"]

        req = QueryRequest(workspace_id=ws_id, question="Python 技能")
        resp = query_uc.execute(req)

        assert resp.answer  # 非空
        assert isinstance(resp.sources, list)
        assert isinstance(resp.scores, list)
        assert resp.model_used  # FakeLLM 返回 "fake"

    def test_fake_llm_answer_content(self, setup):
        """FakeLLM 固定返回 '[test answer]'，验证 answer 即为该内容。"""
        req = QueryRequest(workspace_id=setup["ws_id"], question="随便问")
        resp = setup["query_uc"].execute(req)
        assert resp.answer == "[test answer]"

    def test_model_name_is_fake(self, setup):
        req = QueryRequest(workspace_id=setup["ws_id"], question="问题")
        resp = setup["query_uc"].execute(req)
        assert resp.model_used == "fake"

    def test_sources_returned_when_chunks_exist(self, setup):
        """已索引工作区查询 Python 相关问题，应返回至少 1 个 source chunk。"""
        req = QueryRequest(workspace_id=setup["ws_id"], question="Python", top_k=5)
        resp = setup["query_uc"].execute(req)
        assert len(resp.sources) >= 1

    def test_sources_and_scores_same_length(self, setup):
        req = QueryRequest(workspace_id=setup["ws_id"], question="Python FastAPI")
        resp = setup["query_uc"].execute(req)
        assert len(resp.sources) == len(resp.scores)

    def test_empty_kb_returns_answer_without_chunks(self, container: AppContainer):
        """空工作区（无索引数据）：sources 为空，但 answer 仍然存在。"""
        ws_uc = WorkspaceUseCases(container.workspace_store)
        ws = ws_uc.create("空工作区", "/nonexistent")

        query_uc = QueryKnowledgeBaseUseCase(
            retriever=container.retriever,
            llm_client=container.llm_client,
            conversation_store=container.conversation_store,
        )
        req = QueryRequest(workspace_id=ws.id, question="什么都没有")
        resp = query_uc.execute(req)

        assert resp.answer  # FakeLLM 仍返回内容
        assert resp.sources == []


# ── 历史记录测试 ──────────────────────────────────────────────────────────────

class TestQueryHistory:

    def test_execute_saves_to_history(self, setup):
        """execute 之后，对话历史应包含该条记录。"""
        query_uc = setup["query_uc"]
        ws_id = setup["ws_id"]

        req = QueryRequest(workspace_id=ws_id, question="什么是 RAG？")
        query_uc.execute(req)

        history = query_uc.get_history(ws_id)
        assert len(history) >= 1
        assert any(r.question == "什么是 RAG？" for r in history)

    def test_history_answer_matches_response(self, setup):
        """历史记录的 answer 应与 execute 返回的 answer 一致。"""
        query_uc = setup["query_uc"]
        ws_id = setup["ws_id"]

        req = QueryRequest(workspace_id=ws_id, question="测试答案一致性")
        resp = query_uc.execute(req)

        history = query_uc.get_history(ws_id)
        matching = [r for r in history if r.question == "测试答案一致性"]
        assert len(matching) == 1
        assert matching[0].answer == resp.answer

    def test_multiple_queries_accumulate_history(self, setup):
        """多次 execute 应累积历史记录。"""
        query_uc = setup["query_uc"]
        ws_id = setup["ws_id"]

        questions = ["问题一", "问题二", "问题三"]
        for q in questions:
            query_uc.execute(QueryRequest(workspace_id=ws_id, question=q))

        history = query_uc.get_history(ws_id)
        asked = {r.question for r in history}
        for q in questions:
            assert q in asked

    def test_history_limit(self, setup):
        """get_history(limit=2) 不应返回超过 2 条记录。"""
        query_uc = setup["query_uc"]
        ws_id = setup["ws_id"]

        for i in range(5):
            query_uc.execute(QueryRequest(workspace_id=ws_id, question=f"限制测试 {i}"))

        history = query_uc.get_history(ws_id, limit=2)
        assert len(history) <= 2

    def test_history_isolated_per_workspace(self, setup, container: AppContainer):
        """不同工作区的历史互不干扰。"""
        query_uc = setup["query_uc"]
        ws_id_a = setup["ws_id"]

        # 创建第二个工作区
        ws_uc = WorkspaceUseCases(container.workspace_store)
        ws_b = ws_uc.create("工作区B", "/tmp/b")

        query_uc.execute(QueryRequest(workspace_id=ws_id_a, question="工作区A的问题"))
        query_uc.execute(QueryRequest(workspace_id=ws_b.id, question="工作区B的问题"))

        history_a = query_uc.get_history(ws_id_a)
        history_b = query_uc.get_history(ws_b.id)

        a_questions = {r.question for r in history_a}
        b_questions = {r.question for r in history_b}

        assert "工作区A的问题" in a_questions
        assert "工作区B的问题" not in a_questions
        assert "工作区B的问题" in b_questions
        assert "工作区A的问题" not in b_questions

    def test_execute_injects_only_current_session_recent_history(self, setup):
        container = setup["container"]
        ws_id = setup["ws_id"]
        llm = CapturingLLM()
        query_uc = QueryKnowledgeBaseUseCase(
            retriever=container.retriever,
            llm_client=llm,
            conversation_store=container.conversation_store,
        )
        container.conversation_store.save(
            ConversationRecord.create(
                ws_id,
                "会话旧问题",
                "会话旧回答",
                session_id="session-a",
            )
        )
        container.conversation_store.save(
            ConversationRecord.create(
                ws_id,
                "其他会话问题",
                "其他会话回答",
                session_id="session-b",
            )
        )

        query_uc.execute(
            QueryRequest(
                workspace_id=ws_id,
                question="继续说明",
                session_id="session-a",
            )
        )

        prompt = llm.prompts[-1]
        assert "最近对话" in prompt
        assert "用户：会话旧问题" in prompt
        assert "助手：会话旧回答" in prompt
        assert "其他会话问题" not in prompt

    def test_execute_saves_history_with_session_id(self, setup):
        query_uc = setup["query_uc"]
        ws_id = setup["ws_id"]

        query_uc.execute(
            QueryRequest(
                workspace_id=ws_id,
                question="保存会话问题",
                session_id="session-save",
            )
        )

        history = query_uc.get_history(ws_id, session_id="session-save")
        assert any(record.question == "保存会话问题" for record in history)
        assert all(record.session_id == "session-save" for record in history)

    def test_streaming_saves_history_with_session_id(self, setup):
        query_uc = setup["query_uc"]
        ws_id = setup["ws_id"]

        query_uc.execute_streaming(
            QueryRequest(
                workspace_id=ws_id,
                question="流式会话问题",
                session_id="session-stream",
            ),
            on_token=lambda token: None,
        )

        history = query_uc.get_history(ws_id, session_id="session-stream")
        assert any(record.question == "流式会话问题" for record in history)


# ── execute_streaming 测试 ────────────────────────────────────────────────────

class TestQueryStreaming:

    def test_streaming_collects_tokens(self, setup):
        """execute_streaming 收集 token，answer 为拼接结果。"""
        query_uc = setup["query_uc"]
        ws_id = setup["ws_id"]

        tokens: list[str] = []
        resp = query_uc.execute_streaming(
            QueryRequest(workspace_id=ws_id, question="流式测试"),
            on_token=tokens.append,
        )

        assert len(tokens) >= 1
        assert resp.answer == "".join(tokens)

    def test_streaming_answer_matches_fake_llm(self, setup):
        """FakeLLM.stream() 只 yield '[test answer]'，所以 answer 应为该值。"""
        query_uc = setup["query_uc"]
        ws_id = setup["ws_id"]

        resp = query_uc.execute_streaming(
            QueryRequest(workspace_id=ws_id, question="流式内容"),
            on_token=lambda t: None,
        )
        assert resp.answer == "[test answer]"

    def test_streaming_saves_to_history(self, setup):
        """execute_streaming 完成后，对话历史应包含该条记录。"""
        query_uc = setup["query_uc"]
        ws_id = setup["ws_id"]

        query_uc.execute_streaming(
            QueryRequest(workspace_id=ws_id, question="流式历史测试"),
            on_token=lambda t: None,
        )

        history = query_uc.get_history(ws_id)
        assert any(r.question == "流式历史测试" for r in history)

    def test_streaming_sources_returned(self, setup):
        """execute_streaming 同样返回 sources，与 execute 行为一致。"""
        query_uc = setup["query_uc"]
        ws_id = setup["ws_id"]

        resp = query_uc.execute_streaming(
            QueryRequest(workspace_id=ws_id, question="Python 技能"),
            on_token=lambda t: None,
        )
        assert isinstance(resp.sources, list)
        assert len(resp.sources) == len(resp.scores)


# ── 内部 _build_prompt 测试 ───────────────────────────────────────────────────

class TestBuildPrompt:

    def test_empty_chunks_returns_no_content_message(self):
        prompt = QueryKnowledgeBaseUseCase._build_prompt("测试问题", [])
        assert "测试问题" in prompt
        assert "暂无" in prompt

    def test_chunks_included_in_prompt(self):
        from legacy.desktop.domain.models.chunk import Chunk
        # Chunk.create(document_id, workspace_id, content, order, domain)
        chunk = Chunk.create(
            document_id="doc1",
            workspace_id="ws1",
            content="Python 是一门编程语言",
            order=0,
            domain="resume",
        )
        prompt = QueryKnowledgeBaseUseCase._build_prompt("编程语言", [chunk])
        assert "Python 是一门编程语言" in prompt
        assert "编程语言" in prompt
        assert "来源 1" in prompt

    def test_multiple_chunks_numbered_sequentially(self):
        from legacy.desktop.domain.models.chunk import Chunk
        chunks = [
            Chunk.create(
                document_id="doc1",
                workspace_id="ws1",
                content=f"内容 {i}",
                order=i,
                domain="resume",
            )
            for i in range(3)
        ]
        prompt = QueryKnowledgeBaseUseCase._build_prompt("问题", chunks)
        assert "来源 1" in prompt
        assert "来源 2" in prompt
        assert "来源 3" in prompt

    def test_history_is_included_after_sources_before_question(self):
        from legacy.desktop.domain.models.chunk import Chunk
        chunk = Chunk.create(
            document_id="doc1",
            workspace_id="ws1",
            content="资料片段",
            order=0,
            domain="notes",
        )
        history = [
            ConversationRecord.create("ws1", "旧问题", "旧回答", session_id="s1")
        ]

        prompt = QueryKnowledgeBaseUseCase._build_prompt(
            "新问题",
            [chunk],
            history=history,
        )

        assert "参考资料" in prompt
        assert "资料片段" in prompt
        assert "最近对话" in prompt
        assert "用户：旧问题" in prompt
        assert "助手：旧回答" in prompt
        assert (
            prompt.index("资料片段")
            < prompt.index("最近对话")
            < prompt.index("问题：新问题")
        )
