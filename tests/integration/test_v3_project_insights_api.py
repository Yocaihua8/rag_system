from __future__ import annotations

import time
from pathlib import Path

from fastapi.testclient import TestClient

from backend.api.server import create_app


def _headers(key: str) -> dict[str, str]:
    return {"Idempotency-Key": key}


def test_v3_project_insight_is_source_traceable_and_does_not_return_content(tmp_path: Path):
    root = tmp_path / "project"
    root.mkdir()
    (root / "package.json").write_text('{"name":"demo"}', encoding="utf-8")
    (root / "src").mkdir()
    (root / "src" / "main.py").write_text("print('secret source')", encoding="utf-8")
    app = create_app(db_path=tmp_path / "v2.db", v3_db_path=tmp_path / "v3" / "app.db")

    with TestClient(app) as client:
        project = client.post(
            "/api/v3/projects",
            headers=_headers("insight-project"),
            json={"name": "Insight project", "root_path": str(root)},
        )
        project_id = project.json()["data"]["project"]["id"]

        empty = client.get(f"/api/v3/projects/{project_id}/insights/overview")
        assert empty.status_code == 200, empty.text
        assert empty.json()["data"]["overview"]["status"] == "source_required"

        scanned = client.post(
            f"/api/v3/projects/{project_id}/sources/scan",
            headers=_headers("insight-scan"),
        )
        assert scanned.status_code == 201, scanned.text

        response = client.get(f"/api/v3/projects/{project_id}/insights/overview")
        assert response.status_code == 200, response.text
        overview = response.json()["data"]["overview"]
        assert overview["status"] == "ready"
        assert overview["source_snapshot"]["document_count"] == 2
        assert overview["source_snapshot"]["fingerprint"]
        assert overview["manifest_paths"] == ["package.json"]
        assert [item["relative_path"] for item in overview["evidence"]] == [
            "package.json",
            "src/main.py",
        ]
        assert str(root) not in response.text
        assert "secret source" not in response.text
        assert "content" not in overview["evidence"][0]


def test_v3_source_fact_report_uses_persisted_documents_and_becomes_stale_on_rescan(tmp_path: Path):
    root = tmp_path / "project"
    root.mkdir()
    readme = root / "README.md"
    readme.write_text("# Persisted heading\n\noriginal content\n", encoding="utf-8")
    app = create_app(db_path=tmp_path / "v2.db", v3_db_path=tmp_path / "v3" / "app.db")

    with TestClient(app) as client:
        project = client.post(
            "/api/v3/projects",
            headers=_headers("report-project"),
            json={"name": "Report project", "root_path": str(root)},
        ).json()["data"]["project"]
        client.post(
            f"/api/v3/projects/{project['id']}/sources/scan",
            headers=_headers("report-source-scan"),
        )
        readme.write_text("# Changed after scan\n\nnew content\n", encoding="utf-8")
        task = client.post(
            "/api/v3/tasks",
            headers=_headers("report-task"),
            json={
                "project_id": project["id"],
                "title": "资料事实报告",
                "message": "生成资料事实报告",
            },
        ).json()["data"]
        created = client.post(
            f"/api/v3/tasks/{task['task']['id']}/runs",
            headers=_headers("report-run"),
            json={
                "workflow_key": "project.source-facts.v1",
                "depth": "standard",
                "input_message_id": task["initial_message"]["id"],
            },
        )
        assert created.status_code == 202, created.text
        run = created.json()["data"]["run"]
        for _ in range(80):
            current = client.get(f"/api/v3/runs/{run['id']}").json()["data"]["run"]
            if current["status"] == "completed":
                break
            time.sleep(0.05)
        assert current["status"] == "completed"

        artifact = client.get(
            "/api/v3/artifacts",
            params={"run_id": run["id"]},
        ).json()["data"]["items"][0]
        assert artifact["artifact_type"] == "project_source_facts"
        assert artifact["metadata"]["stale"] is False
        assert "Persisted heading" in artifact["content"]
        assert "Changed after scan" not in artifact["content"]
        original_fingerprint = artifact["metadata"]["source_snapshot_fingerprint"]

        rescanned = client.post(
            f"/api/v3/projects/{project['id']}/sources/scan",
            headers=_headers("report-source-rescan"),
        )
        assert rescanned.status_code == 201, rescanned.text
        stale = client.get(f"/api/v3/artifacts/{artifact['id']}").json()["data"]["artifact"]
        assert stale["content"] == artifact["content"]
        assert stale["metadata"]["stale"] is True
        assert stale["metadata"]["source_snapshot_fingerprint"] == original_fingerprint
        assert stale["metadata"]["stale_against_fingerprint"] != original_fingerprint
