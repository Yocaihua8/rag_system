from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def _read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def test_backend_image_is_api_only_and_uses_base_requirements():
    dockerfile = _read("backend/Dockerfile")
    entrypoint = _read("backend/entrypoint.sh")
    requirements = _read("backend/requirements/base.txt")

    assert "FROM python:3.11-slim" in dockerfile
    assert "backend/requirements/base.txt" in dockerfile
    assert "USER appuser" in dockerfile
    assert "HEALTHCHECK" in dockerfile
    assert "EXPOSE 8765" in dockerfile
    assert "node" not in dockerfile.lower()
    assert "python -m backend" in entrypoint
    assert "fastapi" in requirements
    assert "uvicorn" in requirements


def test_frontend_image_builds_workspace_and_serves_static_assets_only():
    dockerfile = _read("frontend/Dockerfile")
    nginx = _read("frontend/nginx.conf")

    assert "FROM node:24-alpine AS build" in dockerfile
    assert "FROM nginx:1.27-alpine AS runtime" in dockerfile
    assert "npm run frontend:build" in dockerfile
    assert "VITE_API_BASE_URL" in dockerfile
    assert "/app/frontend/dist" in dockerfile
    assert "try_files $uri $uri/ /index.html" in nginx
    assert "proxy_pass" not in nginx
    assert "/api" not in nginx


def test_compose_has_two_images_ports_and_health_checks():
    compose = _read("ops/docker/compose.yaml")

    assert "  backend:" in compose
    assert "  frontend:" in compose
    assert "backend/Dockerfile" in compose
    assert "frontend/Dockerfile" in compose
    assert '${KI_API_PORT:-8765}:8765' in compose
    assert '${KI_WEB_PORT:-4173}:80' in compose
    assert "KI_CORS_ORIGINS" in compose
    assert "VITE_API_BASE_URL" in compose
    assert compose.count("healthcheck:") == 2
    assert "proxy_pass" not in compose


def test_docker_scripts_and_environment_example_are_ops_local():
    env_example = _read("ops/docker/.env.example")
    scripts = [
        _read("ops/docker/start.ps1"),
        _read("ops/docker/stop.ps1"),
        _read("ops/docker/start.sh"),
        _read("ops/docker/stop.sh"),
    ]

    assert "KI_API_PORT=8765" in env_example
    assert "KI_WEB_PORT=4173" in env_example
    assert "KI_PUBLIC_API_URL=http://127.0.0.1:8765" in env_example
    assert "RAG_LLM_API_KEY=" in env_example
    for script in scripts:
        assert "ops/docker" not in script or "compose.yaml" in script
        assert "compose" in script


def test_root_docker_compatibility_files_are_removed():
    for relative in (
        "Dockerfile",
        "compose.yaml",
        "entrypoint.sh",
        ".env.docker.example",
        "README-Docker-Quickstart.txt",
        "Start-KnowledgeIsland-Docker.bat",
        "Stop-KnowledgeIsland-Docker.bat",
    ):
        assert not (ROOT / relative).exists()
