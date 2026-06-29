from pathlib import Path

from webapp.api import dispatch
from webapp.storage import KnowledgeStore


def test_assessment_start_generates_questions_from_imported_documents(tmp_path: Path):
    project_dir = tmp_path / "notes"
    project_dir.mkdir()
    store = KnowledgeStore(tmp_path / "app.db")
    project = store.create_project("知识岛", project_dir)
    store.upsert_document(
        project.id,
        project_dir / "README.md",
        "README.md",
        "# 默认入口\n\napp.py 启动本地 Web 服务，SQLite 保存项目资料。",
    )

    response = dispatch(
        store,
        "POST",
        "/api/assessment/start",
        {"project_id": project.id},
    )

    assert response.status == 200
    assert response.body["session"]["project_id"] == project.id
    assert response.body["session"]["questions"][0]["source_path"] == "README.md"
    assert "README.md" in response.body["session"]["questions"][0]["prompt"]
    assert response.body["session"]["questions"][0]["expected_points"]


def test_assessment_start_generates_question_types_from_project_knowledge(tmp_path: Path):
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    store = KnowledgeStore(tmp_path / "app.db")
    project = store.create_project("知识岛", project_dir)
    store.upsert_document(
        project.id,
        project_dir / "webapp" / "assessment.py",
        "webapp/assessment.py",
        (
            "# 掌握评估\n\n"
            "## 自动出题流程\n\n"
            "create_assessment_session 读取项目文档，生成概念理解题、流程说明题和代码定位题。\n"
            "evaluate_assessment_answer 对照 expected_points 计算掌握状态。"
        ),
    )

    response = dispatch(
        store,
        "POST",
        "/api/assessment/start",
        {"project_id": project.id},
    )

    questions = response.body["session"]["questions"]
    question_types = {question["question_type"] for question in questions}
    assert {"concept", "flow", "code_location"}.issubset(question_types)
    assert all(question["knowledge_point"] for question in questions)
    assert all(question["source_path"] == "webapp/assessment.py" for question in questions)
    assert any("概念理解" in question["prompt"] for question in questions)
    assert any("流程" in question["prompt"] for question in questions)
    assert any("代码" in question["prompt"] for question in questions)


def test_assessment_start_persists_generated_questions(tmp_path: Path):
    project_dir = tmp_path / "notes"
    project_dir.mkdir()
    store = KnowledgeStore(tmp_path / "app.db")
    project = store.create_project("知识岛", project_dir)
    store.upsert_document(
        project.id,
        project_dir / "README.md",
        "README.md",
        "app.py 启动本地 Web 服务，SQLite 保存项目资料。",
    )

    response = dispatch(
        store,
        "POST",
        "/api/assessment/start",
        {"project_id": project.id},
    )

    questions = response.body["session"]["questions"]
    question = questions[0]
    persisted = store.list_assessment_questions(project.id)
    assert [item.id for item in persisted] == [item["id"] for item in questions]
    assert persisted[0].project_id == project.id
    assert persisted[0].source_path == "README.md"
    assert persisted[0].question_type == question["question_type"]
    assert persisted[0].knowledge_point == question["knowledge_point"]
    assert persisted[0].expected_points == question["expected_points"]
    assert persisted[0].reference_snippet == question["reference_snippet"]


def test_assessment_start_rejects_project_without_documents(tmp_path: Path):
    project_dir = tmp_path / "notes"
    project_dir.mkdir()
    store = KnowledgeStore(tmp_path / "app.db")
    project = store.create_project("知识岛", project_dir)

    response = dispatch(
        store,
        "POST",
        "/api/assessment/start",
        {"project_id": project.id},
    )

    assert response.status == 400
    assert response.body["error"] == "assessment requires imported documents"


def test_assessment_answer_returns_feedback_and_reading_source(tmp_path: Path):
    project_dir = tmp_path / "notes"
    project_dir.mkdir()
    store = KnowledgeStore(tmp_path / "app.db")
    project = store.create_project("知识岛", project_dir)
    store.upsert_document(
        project.id,
        project_dir / "README.md",
        "README.md",
        "app.py 启动本地 Web 服务，SQLite 保存项目资料。",
    )
    start = dispatch(store, "POST", "/api/assessment/start", {"project_id": project.id})
    question = start.body["session"]["questions"][0]

    response = dispatch(
        store,
        "POST",
        "/api/assessment/answer",
        {
            "project_id": project.id,
            "question": question,
            "answer": "app.py 启动 Web 服务，并使用 SQLite 保存项目资料。",
        },
    )

    assert response.status == 200
    assert response.body["result"]["status"] in {"已掌握", "基本理解", "需要补充", "暂未掌握"}
    assert response.body["result"]["source_path"] == "README.md"
    assert response.body["result"]["feedback"]


def test_assessment_answer_uses_persisted_question_points(tmp_path: Path):
    project_dir = tmp_path / "notes"
    project_dir.mkdir()
    store = KnowledgeStore(tmp_path / "app.db")
    project = store.create_project("知识岛", project_dir)
    store.upsert_document(
        project.id,
        project_dir / "README.md",
        "README.md",
        "# 默认入口\n\napp.py 启动本地 Web 服务，SQLite 保存项目资料。",
    )
    start = dispatch(store, "POST", "/api/assessment/start", {"project_id": project.id})
    question = dict(start.body["session"]["questions"][0])
    question["expected_points"] = ["伪造要点"]
    question["source_path"] = "fake.md"

    response = dispatch(
        store,
        "POST",
        "/api/assessment/answer",
        {
            "project_id": project.id,
            "question": question,
            "answer": "伪造要点",
        },
    )

    assert response.status == 200
    assert response.body["result"]["source_path"] == "README.md"
    assert response.body["result"]["matched_points"] == []
    assert "伪造要点" not in response.body["result"]["missing_points"]


def test_assessment_answer_returns_unmastered_when_no_reference_points_match(tmp_path: Path):
    project_dir = tmp_path / "notes"
    project_dir.mkdir()
    store = KnowledgeStore(tmp_path / "app.db")
    project = store.create_project("知识岛", project_dir)
    store.upsert_document(
        project.id,
        project_dir / "README.md",
        "README.md",
        "# 默认入口\n\napp.py 启动本地 Web 服务，SQLite 保存项目资料。",
    )
    start = dispatch(store, "POST", "/api/assessment/start", {"project_id": project.id})
    question = start.body["session"]["questions"][0]

    response = dispatch(
        store,
        "POST",
        "/api/assessment/answer",
        {
            "project_id": project.id,
            "question": question,
            "answer": "这段回答只描述番茄钟和日程安排。",
        },
    )

    assert response.status == 200
    assert response.body["result"]["status"] == "暂未掌握"
    assert response.body["result"]["score"] == 0
    assert response.body["result"]["matched_points"] == []


def test_assessment_answer_persists_answer_and_result(tmp_path: Path):
    project_dir = tmp_path / "notes"
    project_dir.mkdir()
    store = KnowledgeStore(tmp_path / "app.db")
    project = store.create_project("知识岛", project_dir)
    store.upsert_document(
        project.id,
        project_dir / "README.md",
        "README.md",
        "app.py 启动本地 Web 服务，SQLite 保存项目资料。",
    )
    start = dispatch(store, "POST", "/api/assessment/start", {"project_id": project.id})
    question = start.body["session"]["questions"][0]

    response = dispatch(
        store,
        "POST",
        "/api/assessment/answer",
        {
            "project_id": project.id,
            "question": question,
            "answer": "app.py 启动 Web 服务，并使用 SQLite 保存项目资料。",
        },
    )

    answers = store.list_assessment_answers(project.id)
    results = store.list_assessment_results(project.id)
    assert len(answers) == 1
    assert answers[0].question_id == question["id"]
    assert answers[0].answer.startswith("app.py 启动")
    assert len(results) == 1
    assert results[0].question_id == question["id"]
    assert results[0].answer_id == answers[0].id
    assert results[0].status == response.body["result"]["status"]
    assert results[0].score == response.body["result"]["score"]
    assert results[0].matched_points == response.body["result"]["matched_points"]


def test_assessment_library_api_returns_question_bank_and_recent_results(tmp_path: Path):
    project_dir = tmp_path / "notes"
    project_dir.mkdir()
    store = KnowledgeStore(tmp_path / "app.db")
    project = store.create_project("知识岛", project_dir)
    store.upsert_document(
        project.id,
        project_dir / "README.md",
        "README.md",
        "# 默认入口\n\napp.py 启动本地 Web 服务，SQLite 保存项目资料。",
    )
    start = dispatch(store, "POST", "/api/assessment/start", {"project_id": project.id})
    question = start.body["session"]["questions"][0]
    dispatch(
        store,
        "POST",
        "/api/assessment/answer",
        {
            "project_id": project.id,
            "question": question,
            "answer": "app.py 启动 Web 服务，并使用 SQLite 保存项目资料。",
        },
    )

    response = dispatch(store, "GET", f"/api/assessment/library?project_id={project.id}")

    assert response.status == 200
    library = response.body["library"]
    assert library["project_id"] == project.id
    assert library["question_count"] == len(start.body["session"]["questions"])
    assert library["result_count"] == 1
    assert library["question_type_counts"]["concept"] >= 1
    assert library["status_counts"]
    assert library["questions"][0]["id"] == question["id"]
    assert library["questions"][0]["knowledge_point"]
    assert library["recent_results"][0]["source_path"] == "README.md"
    assert library["recent_results"][0]["status"] in {"已掌握", "基本理解", "需要补充", "暂未掌握"}


def test_assessment_library_api_rejects_missing_or_unknown_project(tmp_path: Path):
    store = KnowledgeStore(tmp_path / "app.db")

    missing_id_response = dispatch(store, "GET", "/api/assessment/library")
    unknown_project_response = dispatch(store, "GET", "/api/assessment/library?project_id=missing")

    assert missing_id_response.status == 400
    assert missing_id_response.body["error"] == "project_id is required"
    assert unknown_project_response.status == 404
    assert unknown_project_response.body["error"] == "project not found"
