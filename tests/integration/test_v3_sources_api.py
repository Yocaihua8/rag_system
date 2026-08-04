from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from backend.api.server import create_app


def _headers(key: str) -> dict[str, str]:
    return {"Idempotency-Key": key}


def _create_project(client: TestClient, root: Path) -> str:
    response = client.post(
        "/api/v3/projects",
        headers=_headers("source-project"),
        json={"name": "Source project", "root_path": str(root)},
    )
    assert response.status_code == 201, response.text
    return response.json()["data"]["project"]["id"]


def test_v3_source_scan_is_idempotent_and_never_returns_content_or_absolute_paths(
    tmp_path: Path,
):
    root = tmp_path / "project"
    root.mkdir()
    (root / "README.md").write_text("# Safe project\n", encoding="utf-8")
    (root / "src").mkdir()
    (root / "src" / "main.py").write_text("print('secret body')\n", encoding="utf-8")
    (root / "node_modules").mkdir()
    (root / "node_modules" / "ignored.js").write_text("ignored", encoding="utf-8")

    app = create_app(db_path=tmp_path / "v2.db", v3_db_path=tmp_path / "v3" / "app.db")
    with TestClient(app) as client:
        project_id = _create_project(client, root)
        scanned = client.post(
            f"/api/v3/projects/{project_id}/sources/scan",
            headers=_headers("source-scan-1"),
        )
        assert scanned.status_code == 201, scanned.text
        data = scanned.json()["data"]
        assert data["replayed"] is False
        assert data["source"]["source_type"] == "project_root"
        assert data["summary"]["document_count"] == 2
        assert "locator" not in data["source"]
        assert str(root) not in scanned.text
        assert "secret body" not in scanned.text

        replay = client.post(
            f"/api/v3/projects/{project_id}/sources/scan",
            headers=_headers("source-scan-1"),
        )
        assert replay.status_code == 201, replay.text
        assert replay.json()["data"]["replayed"] is True

        sources = client.get(f"/api/v3/projects/{project_id}/sources")
        assert sources.status_code == 200, sources.text
        assert sources.json()["data"]["items"] == [data["source"]]

        documents = client.get(f"/api/v3/projects/{project_id}/documents")
        assert documents.status_code == 200, documents.text
        items = documents.json()["data"]["items"]
        assert [item["relative_path"] for item in items] == ["README.md", "src/main.py"]
        assert all("content" not in item and "source_path" not in item for item in items)
        assert str(root) not in documents.text
        assert "secret body" not in documents.text


def test_v3_source_scan_updates_changed_documents_and_removes_deleted_ones(tmp_path: Path):
    root = tmp_path / "project"
    root.mkdir()
    source_file = root / "app.py"
    source_file.write_text("print('one')\n", encoding="utf-8")

    app = create_app(db_path=tmp_path / "v2.db", v3_db_path=tmp_path / "v3" / "app.db")
    with TestClient(app) as client:
        project_id = _create_project(client, root)
        first = client.post(
            f"/api/v3/projects/{project_id}/sources/scan",
            headers=_headers("source-first"),
        )
        assert first.status_code == 201, first.text
        first_document = client.get(
            f"/api/v3/projects/{project_id}/documents"
        ).json()["data"]["items"][0]

        source_file.write_text("print('two')\n", encoding="utf-8")
        (root / "README.md").write_text("new\n", encoding="utf-8")
        updated = client.post(
            f"/api/v3/projects/{project_id}/sources/scan",
            headers=_headers("source-second"),
        )
        assert updated.status_code == 201, updated.text
        assert updated.json()["data"]["summary"]["updated"] == 1
        assert updated.json()["data"]["summary"]["inserted"] == 1

        source_file.unlink()
        removed = client.post(
            f"/api/v3/projects/{project_id}/sources/scan",
            headers=_headers("source-third"),
        )
        assert removed.status_code == 201, removed.text
        assert removed.json()["data"]["summary"]["deleted"] == 1
        items = client.get(f"/api/v3/projects/{project_id}/documents").json()["data"]["items"]
        assert [item["relative_path"] for item in items] == ["README.md"]
        assert first_document["id"] not in {item["id"] for item in items}


def test_v3_source_scan_reports_unavailable_project_root_and_rejects_foreign_source(
    tmp_path: Path,
):
    root = tmp_path / "project"
    root.mkdir()
    app = create_app(db_path=tmp_path / "v2.db", v3_db_path=tmp_path / "v3" / "app.db")
    with TestClient(app) as client:
        project_id = _create_project(client, root)
        root.rmdir()
        unavailable = client.post(
            f"/api/v3/projects/{project_id}/sources/scan",
            headers=_headers("source-unavailable"),
        )
        assert unavailable.status_code == 409
        assert unavailable.json()["error"]["code"] == "project_root_unavailable"

        missing_source = client.get(
            f"/api/v3/projects/{project_id}/documents",
            params={"source_id": "not-in-project"},
        )
        assert missing_source.status_code == 404
        assert missing_source.json()["error"]["code"] == "not_found"

        invalid_status = client.get(
            f"/api/v3/projects/{project_id}/sources",
            params={"status": "unknown"},
        )
        assert invalid_status.status_code == 422
        assert invalid_status.json()["error"]["code"] == "validation_error"
