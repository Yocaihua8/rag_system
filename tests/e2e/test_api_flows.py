from __future__ import annotations

import requests


def test_health(live_server):
    response = requests.get(f"{live_server}/api/health", timeout=5)

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_project_and_import_and_search(live_server, tmp_path):
    response = requests.post(
        f"{live_server}/api/projects",
        json={"name": "e2e-test", "path": str(tmp_path)},
        timeout=5,
    )
    assert response.status_code == 201
    project_id = response.json()["project"]["id"]

    response = requests.post(
        f"{live_server}/api/import/note",
        json={
            "project_id": project_id,
            "title": "RAG 基础",
            "content": "向量检索是 RAG 的核心步骤，用于从知识库中召回相关片段。",
        },
        timeout=5,
    )
    assert response.status_code == 200

    response = requests.post(
        f"{live_server}/api/search",
        json={"project_id": project_id, "query": "向量检索", "top_k": 3},
        timeout=5,
    )
    assert response.status_code == 200
    assert response.json().get("hits"), "检索无结果"


def test_quality_summary_endpoint(live_server, tmp_path):
    response = requests.post(
        f"{live_server}/api/projects",
        json={"name": "quality-test", "path": str(tmp_path)},
        timeout=5,
    )
    assert response.status_code == 201
    project_id = response.json()["project"]["id"]

    response = requests.get(f"{live_server}/api/projects/quality-summary?project_id={project_id}", timeout=5)

    assert response.status_code == 200
    data = response.json()
    assert "total_questions" in data
    assert "has_sources_rate" in data


def test_chat_branch(live_server, tmp_path):
    response = requests.post(
        f"{live_server}/api/projects",
        json={"name": "branch-test", "path": str(tmp_path)},
        timeout=5,
    )
    assert response.status_code == 201
    project_id = response.json()["project"]["id"]
    response = requests.post(
        f"{live_server}/api/chat/sessions",
        json={"project_id": project_id, "title": "test"},
        timeout=5,
    )
    assert response.status_code == 200
    session_id = response.json()["session"]["id"]

    response = requests.post(
        f"{live_server}/api/chat/messages/branch",
        json={"session_id": session_id, "parent_message_id": "nonexistent", "question": "重新问"},
        timeout=5,
    )

    assert response.status_code == 404


def test_admin_stats(live_server):
    response = requests.get(f"{live_server}/api/admin/stats", timeout=5)

    assert response.status_code == 200
    assert "chunk_count" in response.json()
