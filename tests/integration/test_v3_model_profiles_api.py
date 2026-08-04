from __future__ import annotations

from fastapi.testclient import TestClient

from backend.api.server import create_app


def _headers(key: str) -> dict[str, str]:
    return {"Idempotency-Key": key}


def _profile(
    *,
    name: str = "Primary API",
    status: str = "active",
    is_default: bool = False,
) -> dict[str, object]:
    return {
        "name": name,
        "provider": "api",
        "api_base": "https://example.invalid/v1",
        "model": "demo-model",
        "temperature": 0.4,
        "max_tokens": 4096,
        "api_key_ref": "env:RAG_LLM_API_KEY",
        "status": status,
        "is_default": is_default,
    }


def test_v3_model_profiles_are_isolated_idempotent_and_never_return_key_values(tmp_path):
    app = create_app(db_path=tmp_path / "v2.db", v3_db_path=tmp_path / "v3" / "app.db")

    with TestClient(app) as client:
        created = client.post(
            "/api/v3/model-profiles",
            headers=_headers("profile-create"),
            json=_profile(is_default=True),
        )
        assert created.status_code == 201, created.text
        profile = created.json()["data"]["profile"]
        assert profile["is_default"] is True
        assert profile["api_key_ref"] == "env:RAG_LLM_API_KEY"
        assert "has_api_key" not in profile
        assert "api_key" not in {key for key in profile if key != "api_key_ref"}

        replay = client.post(
            "/api/v3/model-profiles",
            headers=_headers("profile-create"),
            json=_profile(is_default=True),
        )
        assert replay.status_code == 201, replay.text
        assert replay.json()["data"]["replayed"] is True

        disabled = client.post(
            "/api/v3/model-profiles",
            headers=_headers("profile-disabled"),
            json=_profile(name="Disabled local", status="disabled"),
        )
        assert disabled.status_code == 201, disabled.text
        disabled_id = disabled.json()["data"]["profile"]["id"]

        rejected_default = client.post(
            f"/api/v3/model-profiles/{disabled_id}/default",
            headers=_headers("profile-disabled-default"),
        )
        assert rejected_default.status_code == 409
        assert rejected_default.json()["error"]["code"] == "state_conflict"

        updated = client.post(
            f"/api/v3/model-profiles/{disabled_id}/update",
            headers=_headers("profile-update"),
            json=_profile(name="Enabled local", is_default=True),
        )
        assert updated.status_code == 200, updated.text
        assert updated.json()["data"]["profile"]["is_default"] is True

        profiles = client.get("/api/v3/model-profiles")
        assert profiles.status_code == 200, profiles.text
        items = profiles.json()["data"]["items"]
        assert [item["name"] for item in items] == ["Enabled local", "Primary API"]
        assert sum(item["is_default"] for item in items) == 1

        deleted = client.post(
            f"/api/v3/model-profiles/{disabled_id}/delete",
            headers=_headers("profile-delete"),
        )
        assert deleted.status_code == 200, deleted.text
        assert deleted.json()["data"] == {
            "deleted": True,
            "profile_id": disabled_id,
            "replayed": False,
        }
