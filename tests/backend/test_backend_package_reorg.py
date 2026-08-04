import subprocess
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _tracked_files(prefix: str) -> list[str]:
    result = subprocess.run(
        ["git", "ls-files", prefix],
        cwd=PROJECT_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return [line for line in result.stdout.splitlines() if line.strip()]


def test_webapp_package_is_removed_from_tracked_sources():
    assert _tracked_files("webapp") == []


def test_backend_module_is_the_only_python_service_entrypoint():
    source = (PROJECT_ROOT / "backend/__main__.py").read_text(encoding="utf-8")

    assert not (PROJECT_ROOT / "app.py").exists()
    assert "from backend.api.server import run_server" in source
    assert "load_desktop_settings" in source
    assert "load_server_binding" in source
    assert "host=binding.host" in source
    assert "port=binding.port" in source


def test_vite_outputs_to_frontend_dist_without_touching_backend_source():
    source = (PROJECT_ROOT / "frontend/vite.config.js").read_text(encoding="utf-8")

    assert "backend/static_dist" not in source
    assert "../backend" not in source
    assert not (PROJECT_ROOT / "backend/static_dist").exists()


def test_active_python_imports_use_backend_namespace():
    legacy_package = "web" + "app"
    blocked_markers = (
        f"from {legacy_package}",
        f"import {legacy_package}",
        f"{legacy_package}.",
    )
    scan_roots = [
        PROJECT_ROOT / "backend",
        PROJECT_ROOT / "tools",
        PROJECT_ROOT / "tests",
    ]
    offenders: list[str] = []

    for root in scan_roots:
        paths = [root] if root.is_file() else list(root.rglob("*.py"))
        for path in paths:
            if "__pycache__" in path.parts:
                continue
            text = path.read_text(encoding="utf-8", errors="ignore")
            for marker in blocked_markers:
                if marker in text:
                    offenders.append(f"{path.relative_to(PROJECT_ROOT)} contains {marker}")

    assert offenders == []
