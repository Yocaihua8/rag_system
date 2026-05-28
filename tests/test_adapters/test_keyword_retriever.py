from src.adapters.retrieval.keyword_retriever import KeywordRetriever
from src.domain.models.chunk import Chunk
from src.ports.retriever import RetrievalQuery


def test_keyword_retriever_matches_chinese_compound_terms():
    retriever = KeywordRetriever()
    workspace_id = "ws-cn"
    matching = Chunk.create(
        document_id="doc-entry",
        workspace_id=workspace_id,
        content="默认入口通过 app.py 启动本地 Web MVP。",
        order=0,
        domain="general",
    )
    unrelated = Chunk.create(
        document_id="doc-model",
        workspace_id=workspace_id,
        content="模型设置页面用于保存 API Key。",
        order=1,
        domain="general",
    )
    retriever.index([unrelated, matching])

    result = retriever.search(
        RetrievalQuery(question="默认入口是什么", workspace_id=workspace_id, top_k=2)
    )

    assert result.chunks
    assert result.chunks[0].id == matching.id
    assert result.scores[0] > 0
