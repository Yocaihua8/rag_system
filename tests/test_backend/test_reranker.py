from __future__ import annotations


def test_base_reranker_declares_rerank_contract():
    from backend.providers.base import BaseReranker

    assert BaseReranker.__abstractmethods__ == frozenset({"rerank"})
