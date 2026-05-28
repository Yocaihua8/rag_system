from pathlib import Path


def test_root_keeps_only_project_level_entrypoints_and_metadata():
    expected_root_files = {
        ".dockerignore",
        ".env.example",
        ".gitignore",
        "AGENTS.md",
        "CHANGELOG.md",
        "CONTRIBUTING.md",
        "README.md",
        "SECURITY.md",
        "requirements-dev.txt",
        "requirements.txt",
    }
    misplaced_root_files = {
        "Dockerfile",
        "README-Docker-Quickstart.txt",
        "Start-KnowledgeIsland-Docker.bat",
        "Stop-KnowledgeIsland-Docker.bat",
        "compose.yaml",
        "package-lock.json",
        "package.json",
        "template-mapping.md",
        "vite.config.js",
    }

    for file_name in expected_root_files:
        assert Path(file_name).is_file(), f"{file_name} should stay in the repository root"
    for file_name in misplaced_root_files:
        assert not Path(file_name).exists(), f"{file_name} should move out of the repository root"


def test_frontend_docker_and_docs_assets_live_under_their_own_directories():
    expected_files = {
        "frontend/package.json",
        "frontend/package-lock.json",
        "frontend/vite.config.js",
        "ops/docker/Dockerfile",
        "ops/docker/compose.yaml",
        "ops/docker/docker_up.ps1",
        "ops/docker/docker_down.ps1",
        "ops/docker/Start-KnowledgeIsland-Docker.bat",
        "ops/docker/Stop-KnowledgeIsland-Docker.bat",
        "docs/guides/docker-quickstart.txt",
        "docs/template-mapping.md",
    }

    for path in expected_files:
        assert Path(path).is_file(), f"{path} should exist after root directory cleanup"

    assert not Path("scripts/docker_up.ps1").exists()
    assert not Path("scripts/docker_down.ps1").exists()
