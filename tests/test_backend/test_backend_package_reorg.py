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


def test_root_launcher_uses_backend_api_server():
    source = (PROJECT_ROOT / "app.py").read_text(encoding="utf-8")

    assert "from backend.api.server import app, run_server" in source
    assert "webapp" not in source


def test_vite_outputs_to_backend_static_dist_without_touching_frontend_source():
    source = (PROJECT_ROOT / "frontend/vite.config.js").read_text(encoding="utf-8")

    assert 'outDir: path.resolve(__dirname, "../backend/static_dist")' in source
    assert "../webapp/static_dist" not in source


def test_active_python_imports_use_backend_namespace():
    legacy_package = "web" + "app"
    blocked_markers = (
        f"from {legacy_package}",
        f"import {legacy_package}",
        f"{legacy_package}.",
    )
    scan_roots = [
        PROJECT_ROOT / "app.py",
        PROJECT_ROOT / "entrypoint.sh",
        PROJECT_ROOT / "backend",
        PROJECT_ROOT / "scripts",
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
