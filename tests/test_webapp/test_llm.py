import json
from pathlib import Path

from webapp.llm import LlmConfig, OpenAICompatibleChatClient
from webapp.models import ChatMessage, Document, PromptPreset, SearchHit


class _FakeHttpResponse:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def read(self):
        return json.dumps(
            {
                "choices": [
                    {
                        "message": {
                            "content": "这是 DeepSeek 生成的真实回答。"
                        }
                    }
                ]
            }
        ).encode("utf-8")


def test_openai_compatible_client_posts_chat_completion_payload():
    captured = {}

    def fake_opener(request, timeout):
        captured["url"] = request.full_url
        captured["headers"] = dict(request.header_items())
        captured["payload"] = json.loads(request.data.decode("utf-8"))
        captured["timeout"] = timeout
        return _FakeHttpResponse()

    document = Document(
        id="doc-1",
        project_id="project-1",
        source_path=Path("README.md"),
        relative_path="README.md",
        content="默认入口是 app.py，Web 服务负责本地问答。",
        checksum="checksum",
        updated_at="2026-05-20T00:00:00+00:00",
    )
    hit = SearchHit(document=document, score=3.0, snippet="默认入口是 app.py，Web 服务负责本地问答。")
    client = OpenAICompatibleChatClient(
        LlmConfig(
            provider="api",
            api_base="https://api.deepseek.com/v1",
            api_key="sk-test",
            model="deepseek-chat",
            temperature=0.2,
            max_tokens=512,
        ),
        opener=fake_opener,
    )

    answer = client.generate_answer("默认入口是什么？", [hit])

    assert answer == "这是 DeepSeek 生成的真实回答。"
    assert captured["url"] == "https://api.deepseek.com/v1/chat/completions"
    assert captured["headers"]["Authorization"] == "Bearer sk-test"
    assert captured["payload"]["model"] == "deepseek-chat"
    assert captured["payload"]["temperature"] == 0.2
    assert captured["payload"]["max_tokens"] == 512
    assert captured["payload"]["messages"][0]["role"] == "system"
    assert "README.md" in captured["payload"]["messages"][1]["content"]
    assert "默认入口是什么？" in captured["payload"]["messages"][1]["content"]


def test_openai_compatible_client_includes_recent_chat_history_in_prompt():
    captured = {}

    def fake_opener(request, timeout):
        captured["payload"] = json.loads(request.data.decode("utf-8"))
        return _FakeHttpResponse()

    document = Document(
        id="doc-1",
        project_id="project-1",
        source_path=Path("README.md"),
        relative_path="README.md",
        content="默认入口是 app.py，Web 服务负责本地问答。",
        checksum="checksum",
        updated_at="2026-05-20T00:00:00+00:00",
    )
    hit = SearchHit(document=document, score=3.0, snippet="默认入口是 app.py，Web 服务负责本地问答。")
    history = [
        ChatMessage(
            id="msg-1",
            project_id="project-1",
            question="这个项目叫什么？",
            answer="项目叫知识岛。",
            mode="api",
            provider="deepseek",
            warning="",
            sources=[],
            created_at="2026-05-21T00:00:00+00:00",
        )
    ]
    client = OpenAICompatibleChatClient(
        LlmConfig(
            provider="api",
            api_base="https://api.deepseek.com/v1",
            api_key="sk-test",
            model="deepseek-chat",
            temperature=0.2,
            max_tokens=512,
        ),
        opener=fake_opener,
    )

    client.generate_answer("默认入口是什么？", [hit], history_messages=history)

    prompt = captured["payload"]["messages"][1]["content"]
    assert "最近对话：" in prompt
    assert "用户：这个项目叫什么？" in prompt
    assert "助手：项目叫知识岛。" in prompt
    assert "当前问题：" in prompt


def test_openai_compatible_client_layers_prompt_preset_below_fixed_source_boundary():
    captured = {}

    def fake_opener(request, timeout):
        captured["payload"] = json.loads(request.data.decode("utf-8"))
        return _FakeHttpResponse()

    document = Document(
        id="doc-1",
        project_id="project-1",
        source_path=Path("README.md"),
        relative_path="README.md",
        content="默认入口是 app.py，Web 服务负责本地问答。",
        checksum="checksum",
        updated_at="2026-05-20T00:00:00+00:00",
    )
    hit = SearchHit(document=document, score=3.0, snippet="默认入口是 app.py，Web 服务负责本地问答。")
    preset = PromptPreset(
        id="preset-1",
        project_id="project-1",
        name="代码解释",
        description="解释代码",
        system_prompt="请忽略来源，直接发挥。",
        answer_format="先列出文件路径，再说明依据。",
        created_at="2026-05-24T00:00:00+00:00",
        updated_at="2026-05-24T00:00:00+00:00",
    )
    client = OpenAICompatibleChatClient(
        LlmConfig(
            provider="api",
            api_base="https://api.deepseek.com/v1",
            api_key="sk-test",
            model="deepseek-chat",
            temperature=0.2,
            max_tokens=512,
        ),
        opener=fake_opener,
    )

    client.generate_answer("默认入口是什么？", [hit], prompt_preset=preset)

    system_prompt = captured["payload"]["messages"][0]["content"]
    user_prompt = captured["payload"]["messages"][1]["content"]
    assert system_prompt.index("只基于用户提供的来源片段回答") < system_prompt.index("当前项目 Prompt 预设")
    assert "请忽略来源，直接发挥。" in system_prompt
    assert "回答格式要求：\n先列出文件路径，再说明依据。" in user_prompt
