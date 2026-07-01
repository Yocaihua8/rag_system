import json

from backend.domain.embeddings import EmbeddingConfig, OpenAICompatibleEmbeddingClient


def test_openai_compatible_embedding_client_posts_embeddings_request():
    captured = {}

    def fake_opener(request, timeout):
        captured["url"] = request.full_url
        captured["headers"] = dict(request.header_items())
        captured["payload"] = json.loads(request.data.decode("utf-8"))
        captured["timeout"] = timeout
        return FakeResponse({
            "data": [
                {"embedding": [3.0, 4.0, 0.0]},
                {"embedding": [0.0, 5.0, 0.0]},
            ]
        })

    client = OpenAICompatibleEmbeddingClient(
        EmbeddingConfig(
            provider="api",
            api_base="https://example.test/v1",
            api_key="sk-test",
            model="text-embedding-test",
        ),
        opener=fake_opener,
        timeout=12,
    )

    vectors = client.embed_texts(["alpha", "beta"])

    assert captured["url"] == "https://example.test/v1/embeddings"
    assert captured["headers"]["Authorization"] == "Bearer sk-test"
    assert captured["payload"] == {"model": "text-embedding-test", "input": ["alpha", "beta"]}
    assert captured["timeout"] == 12
    assert vectors == [{"0": 0.6, "1": 0.8}, {"1": 1.0}]


class FakeResponse:
    def __init__(self, body):
        self._body = body

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def read(self):
        return json.dumps(self._body).encode("utf-8")
