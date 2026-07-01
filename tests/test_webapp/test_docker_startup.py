from pathlib import Path


def test_docker_requirements_are_container_runtime_only():
    requirements = Path("requirements-docker.txt").read_text(encoding="utf-8")

    assert "fastapi>=0.115.0" in requirements
    assert "uvicorn[standard]>=0.30.0" in requirements
    assert "qdrant-client>=1.10.0" in requirements
    assert "PySide6" not in requirements
    assert "chromadb" not in requirements
    assert "openai" not in requirements
    assert "ollama" not in requirements


def test_dockerignore_excludes_local_heavy_paths():
    dockerignore = Path(".dockerignore").read_text(encoding="utf-8")

    for ignored in (".venv/", "frontend/node_modules/", "node_modules/", "runtime/", "tests/", "docs/plans/"):
        assert ignored in dockerignore


def test_dockerfile_builds_frontend_and_runs_web_mvp_without_desktop_dependencies():
    dockerfile = Path("Dockerfile").read_text(encoding="utf-8")

    assert "FROM node:24-alpine AS frontend-build" in dockerfile
    assert "FROM python:3.11-slim AS runtime" in dockerfile
    assert "npm ci" in dockerfile
    assert "npm run build" in dockerfile
    assert "COPY requirements-docker.txt ./requirements-docker.txt" in dockerfile
    assert "pip install --no-cache-dir -r requirements-docker.txt" in dockerfile
    assert "COPY app.py ./app.py" in dockerfile
    assert "COPY backend ./backend" in dockerfile
    assert "COPY --from=frontend-build /app/backend/static_dist ./backend/static_dist" in dockerfile
    assert "COPY entrypoint.sh /entrypoint.sh" in dockerfile
    assert "useradd" in dockerfile
    assert "USER appuser" in dockerfile
    assert "HEALTHCHECK" in dockerfile
    assert "EXPOSE 8765" in dockerfile
    assert 'ENTRYPOINT ["/entrypoint.sh"]' in dockerfile
    assert "COPY src/" not in dockerfile
    assert "pip install -r requirements.txt" not in dockerfile


def test_entrypoint_starts_server_on_container_host():
    entrypoint = Path("entrypoint.sh").read_text(encoding="utf-8")

    assert entrypoint.startswith("#!/bin/sh")
    assert "mkdir -p /app/runtime/webapp" in entrypoint
    assert "from backend.api.server import run_server" in entrypoint
    assert "run_server(host='0.0.0.0', port=8765)" in entrypoint


def test_compose_maps_port_runtime_workspace_and_env():
    compose = Path("compose.yaml").read_text(encoding="utf-8")

    assert "knowledge-island-web" in compose
    assert "context: ." in compose
    assert "dockerfile: Dockerfile" in compose
    assert "${KI_PORT:-8765}:8765" in compose
    assert "ki-runtime:/app/runtime" in compose
    assert "${KNOWLEDGE_ISLAND_WORKSPACE:-./docker-workspace}:/workspace" in compose
    assert "RAG_RUNTIME_DIR" in compose
    assert "RAG_LLM_API_KEY" in compose
    assert "DEEPSEEK_API_KEY" in compose
    assert "RAG_LLM_PROVIDER" in compose
    assert "RAG_EMBED_PROVIDER" in compose
    assert "RAG_EMBED_API_KEY" in compose
    assert "RAG_AUTH_ENABLED" in compose
    assert "healthcheck:" in compose
    assert "ki-runtime:" in compose


def test_docker_env_example_documents_runtime_settings_without_secrets():
    env_example = Path(".env.docker.example").read_text(encoding="utf-8")

    assert "KI_PORT=8765" in env_example
    assert "KNOWLEDGE_ISLAND_WORKSPACE=./docker-workspace" in env_example
    assert "RAG_LLM_API_KEY=" in env_example
    assert "DEEPSEEK_API_KEY=" in env_example
    assert "RAG_AUTH_ENABLED=false" in env_example


def test_docker_scripts_cover_windows_and_linux_entrypoints_without_printing_keys():
    ps_script = Path("scripts/docker_up.ps1").read_text(encoding="utf-8")
    ps_stop = Path("scripts/docker_down.ps1").read_text(encoding="utf-8")
    sh_script = Path("scripts/docker_up.sh").read_text(encoding="utf-8")
    sh_stop = Path("scripts/docker_down.sh").read_text(encoding="utf-8")

    for script in (ps_script, ps_stop, sh_script, sh_stop):
        assert "docker compose --project-directory" in script
        assert "compose.yaml" in script

    assert "GetEnvironmentVariable('DEEPSEEK_API_KEY', 'User')" in ps_script
    assert "GetEnvironmentVariable('RAG_EMBED_API_KEY', 'User')" in ps_script
    assert "docker-workspace" in ps_script
    assert "DEEPSEEK_API_KEY=" not in ps_script
    assert "RAG_EMBED_API_KEY=" not in ps_script
    assert "docker-workspace" in sh_script
    assert "up --build -d" in sh_script
    assert "down" in sh_stop


def test_docker_stop_script_and_double_click_wrappers_exist():
    start_bat = Path("Start-KnowledgeIsland-Docker.bat").read_text(encoding="utf-8")
    stop_bat = Path("Stop-KnowledgeIsland-Docker.bat").read_text(encoding="utf-8")
    quickstart = Path("README-Docker-Quickstart.txt").read_text(encoding="utf-8")

    assert "docker_up.ps1" in start_bat
    assert "docker_down.ps1" in stop_bat
    assert "http://127.0.0.1:8765" in quickstart
    assert "/workspace" in quickstart
