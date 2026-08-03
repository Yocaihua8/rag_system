from __future__ import annotations

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
