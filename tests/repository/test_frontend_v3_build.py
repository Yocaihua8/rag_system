from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
FRONTEND_V3 = ROOT / "frontend-v3"


def _json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_frontend_v3_is_an_independent_locked_workspace() -> None:
    root_package = _json(ROOT / "package.json")
    package = _json(FRONTEND_V3 / "package.json")

    assert "frontend-v3" in root_package["workspaces"]
    assert "tools/openapi-codegen" in root_package["workspaces"]
    assert package["version"] == "3.0.0-alpha.2"
    assert package["engines"]["node"] == "^20.19.0 || ^22.13.0 || >=24.0.0"
    assert package["dependencies"]["react"] == "19.2.8"
    assert package["devDependencies"]["typescript"] == "6.0.3"
    assert package["devDependencies"]["vite"] == "8.2.0"
    assert package["scripts"]["dev"] == "vite --host 127.0.0.1 --port 5174"
    assert package["scripts"]["preview"] == "vite preview --host 127.0.0.1 --port 4174"


def test_v3_openapi_generation_is_versioned_and_exposes_run_recovery() -> None:
    schema = _json(FRONTEND_V3 / "src" / "api" / "generated" / "openapi-v3.json")
    codegen = _json(ROOT / "tools" / "openapi-codegen" / "package.json")

    assert schema["info"]["version"] == "3.0.0-alpha.2"
    assert schema["components"]["schemas"]["AgentEvent"]["discriminator"][
        "propertyName"
    ] == "event_type"
    assert "get" in schema["paths"]["/tasks/{task_id}/runs"]
    assert codegen["devDependencies"] == {
        "openapi-typescript": "7.13.0",
        "typescript": "5.9.3",
    }


def test_frontend_v3_does_not_enable_react_server_or_rsc_paths() -> None:
    forbidden = (
        "unstable_rsc",
        "routerscserverrequest",
        "rschydratedrouter",
        "serverrouter",
        "react-server",
        "@react-router/dev",
        "@react-router/node",
        "@react-router/serve",
    )
    sources = [
        path
        for path in (FRONTEND_V3 / "src").rglob("*")
        if path.suffix in {".ts", ".tsx"} and ".test." not in path.name
    ]
    combined = "\n".join(path.read_text(encoding="utf-8").lower() for path in sources)

    assert not any(marker in combined for marker in forbidden)
    assert "/api/v2" not in combined


def test_v3_uses_workflow_name_and_keeps_vue_as_the_production_entry() -> None:
    sources = "\n".join(
        path.read_text(encoding="utf-8")
        for path in (FRONTEND_V3 / "src").rglob("*.tsx")
        if ".test." not in path.name
    )
    tauri = _json(ROOT / "src-tauri" / "tauri.conf.json")
    compose = (ROOT / "ops" / "docker" / "compose.yaml").read_text(encoding="utf-8")

    assert "工作流" in sources
    assert "常用做法" not in sources
    assert tauri["build"]["frontendDist"] == "../frontend/dist"
    assert tauri["build"]["devUrl"] == "http://127.0.0.1:5173"
    assert "dockerfile: frontend/Dockerfile" in compose
