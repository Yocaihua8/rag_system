from __future__ import annotations

from dataclasses import dataclass


def test_base_reranker_declares_rerank_contract():
    from backend.providers.base import BaseReranker

    assert BaseReranker.__abstractmethods__ == frozenset({"rerank"})


@dataclass(frozen=True)
class _Candidate:
    content: str


class _FakeCrossEncoder:
    def __init__(self, scores: list[float]) -> None:
        self.scores = scores
        self.pairs = []

    def predict(self, pairs):
        self.pairs.append(list(pairs))
        return self.scores


def test_cross_encoder_reranker_loads_model_lazily_and_orders_by_score():
    from backend.providers.reranker.cross_encoder import CrossEncoderReranker

    created_models = []
    fake_model = _FakeCrossEncoder([0.2, 0.9, 0.5])

    def factory(model_name: str):
        created_models.append(model_name)
        return fake_model

    candidates = [_Candidate("alpha"), _Candidate("beta"), _Candidate("gamma")]
    reranker = CrossEncoderReranker(model_factory=factory)

    assert created_models == []

    ranked = reranker.rerank("query", candidates, top_n=2)

    assert created_models == ["cross-encoder/ms-marco-MiniLM-L-6-v2"]
    assert fake_model.pairs == [[("query", "alpha"), ("query", "beta"), ("query", "gamma")]]
    assert ranked == [candidates[1], candidates[2]]


def test_cross_encoder_reranker_dependency_failure_warns_and_skips(capsys):
    from backend.providers.reranker.cross_encoder import CrossEncoderReranker

    candidates = [_Candidate("alpha"), _Candidate("beta")]

    def factory(model_name: str):
        raise ImportError("sentence-transformers missing")

    reranker = CrossEncoderReranker(model_factory=factory)

    assert reranker.rerank("query", candidates) == candidates
    assert "WARNING: sentence-transformers is not installed; reranker disabled" in capsys.readouterr().err
