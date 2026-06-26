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


def test_reranker_settings_default_disabled_and_env_override():
    from backend.config.reranker import load_reranker_settings

    defaults = load_reranker_settings({})
    enabled = load_reranker_settings(
        {
            "RAG_RERANKER_ENABLED": "true",
            "RAG_RERANKER_MODEL": "BAAI/bge-reranker-base",
        }
    )

    assert defaults.enabled is False
    assert defaults.model == "cross-encoder/ms-marco-MiniLM-L-6-v2"
    assert enabled.enabled is True
    assert enabled.model == "BAAI/bge-reranker-base"


def test_build_reranker_returns_none_when_disabled_or_dependency_missing(capsys):
    from backend.config.reranker import RerankerSettings, build_reranker

    assert build_reranker(RerankerSettings(enabled=False, model="model")) is None

    missing = build_reranker(
        RerankerSettings(enabled=True, model="model"),
        dependency_available=lambda: False,
    )

    assert missing is None
    assert "WARNING: sentence-transformers is not installed; reranker disabled" in capsys.readouterr().err
