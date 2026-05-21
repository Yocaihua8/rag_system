from pathlib import Path


def test_dockerfile_runs_web_mvp_without_legacy_desktop_dependencies():
    dockerfile = Path("Dockerfile").read_text(encoding="utf-8")

    assert "python:3.11-slim" in dockerfile
    assert "EXPOSE 8765" in dockerfile
    assert "webapp.server" in dockerfile
    assert "0.0.0.0" in dockerfile
    assert "pip install -r requirements.txt" not in dockerfile


def test_compose_maps_port_runtime_workspace_and_deepseek_env():
    compose = Path("compose.yaml").read_text(encoding="utf-8")

    assert "knowledge-island-web" in compose
    assert "8765:8765" in compose
    assert "./runtime/docker:/app/runtime" in compose
    assert "${KNOWLEDGE_ISLAND_WORKSPACE:-./docker-workspace}:/workspace" in compose
    assert "DEEPSEEK_API_KEY" in compose
    assert "RAG_LLM_PROVIDER" in compose
    assert "healthcheck:" in compose


def test_docker_one_click_script_injects_user_deepseek_key_without_printing_it():
    script = Path("scripts/docker_up.ps1").read_text(encoding="utf-8")

    assert "docker compose up --build -d" in script
    assert "GetEnvironmentVariable('DEEPSEEK_API_KEY', 'User')" in script
    assert "docker-workspace" in script
    assert "DEEPSEEK_API_KEY=" not in script
