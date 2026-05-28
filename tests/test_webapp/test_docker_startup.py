from pathlib import Path


def test_dockerfile_runs_web_mvp_without_legacy_desktop_dependencies():
    dockerfile = Path("Dockerfile").read_text(encoding="utf-8")

    assert "python:3.11-slim" in dockerfile
    assert "node:20-slim AS frontend-build" in dockerfile
    assert "npm ci" in dockerfile
    assert "npm run build" in dockerfile
    assert "COPY backend ./backend" in dockerfile
    assert "COPY --from=frontend-build /app/backend/webapp/static_dist ./backend/webapp/static_dist" in dockerfile
    assert "EXPOSE 8765" in dockerfile
    assert "backend.webapp.server" in dockerfile
    assert "0.0.0.0" in dockerfile
    assert "fastapi" in dockerfile
    assert "uvicorn[standard]" in dockerfile
    assert "pip install -r requirements.txt" not in dockerfile


def test_compose_maps_port_runtime_workspace_and_deepseek_env():
    compose = Path("compose.yaml").read_text(encoding="utf-8")

    assert "knowledge-island-web" in compose
    assert "8765:8765" in compose
    assert "./runtime/docker:/app/runtime" in compose
    assert "${KNOWLEDGE_ISLAND_WORKSPACE:-./docker-workspace}:/workspace" in compose
    assert "DEEPSEEK_API_KEY" in compose
    assert "RAG_LLM_PROVIDER" in compose
    assert "RAG_EMBED_PROVIDER" in compose
    assert "RAG_EMBED_API_KEY" in compose
    assert "healthcheck:" in compose


def test_docker_one_click_script_injects_user_deepseek_key_without_printing_it():
    script = Path("scripts/docker_up.ps1").read_text(encoding="utf-8")

    assert "docker compose up --build -d" in script
    assert "GetEnvironmentVariable('DEEPSEEK_API_KEY', 'User')" in script
    assert "GetEnvironmentVariable('RAG_EMBED_API_KEY', 'User')" in script
    assert "docker-workspace" in script
    assert "DEEPSEEK_API_KEY=" not in script
    assert "RAG_EMBED_API_KEY=" not in script


def test_docker_stop_script_and_double_click_wrappers_exist():
    stop_script = Path("scripts/docker_down.ps1").read_text(encoding="utf-8")
    start_bat = Path("Start-KnowledgeIsland-Docker.bat").read_text(encoding="utf-8")
    stop_bat = Path("Stop-KnowledgeIsland-Docker.bat").read_text(encoding="utf-8")
    quickstart = Path("README-Docker-Quickstart.txt").read_text(encoding="utf-8")

    assert "docker compose down" in stop_script
    assert "docker_up.ps1" in start_bat
    assert "docker_down.ps1" in stop_bat
    assert "http://127.0.0.1:8765" in quickstart
    assert "/workspace" in quickstart
