import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def _json(relative: str) -> dict:
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


def test_tauri_packages_frontend_dist_and_api_only_sidecar():
    config = _json("src-tauri/tauri.conf.json")
    capability = _json("src-tauri/capabilities/default.json")

    assert config["build"]["frontendDist"] == "../frontend/dist"
    assert config["bundle"]["externalBin"] == ["binaries/knowledge-island-backend"]
    assert config["build"]["beforeBuildCommand"] == "npm --prefix .. run frontend:build"
    assert "http://127.0.0.1:8765" in config["app"]["security"]["csp"]
    assert "connect-src" in config["app"]["security"]["csp"]
    assert "*" not in config["app"]["security"]["csp"]
    assert capability["windows"] == ["main"]
    assert capability["permissions"] == []


def test_secure_sidecar_runtime_is_opt_in_and_keeps_bootstrap_in_rust_state():
    source = (ROOT / "src-tauri/src/main.rs").read_text(encoding="utf-8")

    for marker in (
        'std::env::var("KI_TAURI_SECURE_RUNTIME")',
        'TcpListener::bind((Ipv4Addr::LOCALHOST, 0))',
        "getrandom::fill(&mut bytes)",
        '.env("KI_DESKTOP_MODE", "1")',
        '.env("KI_API_HOST", "127.0.0.1")',
        '.env("KI_API_PORT", port.to_string())',
        '.env("KI_DESKTOP_STARTUP_TOKEN", token)',
        "Mutex<Option<BackendBootstrap>>",
        'window.label() != "main"',
    ):
        assert marker in source

    assert "shell:allow-execute" not in json.dumps(
        _json("src-tauri/capabilities/default.json")
    )


def test_tauri_workspace_owns_cli_and_sidecar_build_commands():
    package = _json("src-tauri/package.json")

    assert "@tauri-apps/cli" in package["devDependencies"]
    assert package["scripts"]["dev"].endswith("tauri dev")
    assert "prepare-sidecar.mjs" in package["scripts"]["dev"]
    assert "sidecar:build:windows" in package["scripts"]["build:windows"]
    assert "sidecar:build:unix" in package["scripts"]["build:macos"]
    assert "sidecar:build:unix" in package["scripts"]["build:linux"]


def test_sidecar_scripts_build_backend_module_without_frontend_payload():
    windows = (ROOT / "src-tauri/scripts/build-backend-sidecar.ps1").read_text(encoding="utf-8")
    unix = (ROOT / "src-tauri/scripts/build-backend-sidecar.sh").read_text(encoding="utf-8")

    for source in (windows, unix):
        assert "backend/__main__.py" in source
        assert "PyInstaller" in source
        assert "--add-data" in source
        assert "backend/alembic.ini" in source.replace("\\", "/")
        assert "backend/storage/v3/migrations" in source.replace("\\", "/")
        assert "frontend/dist" not in source
        assert "backend/static_dist" not in source
        assert "build/sidecar" in source or "build\\sidecar" in source
    assert '"x86_64-pc-windows-msvc"' in windows
    assert '"$BackendName-$TargetTriple.exe"' in windows
    assert "KI_TAURI_TARGET_TRIPLE" in unix


def test_version_is_consistent_across_workspaces_and_tauri():
    expected = "2.0.0"
    root_package = _json("package.json")
    frontend_package = _json("frontend/package.json")
    desktop_package = _json("src-tauri/package.json")
    lock = _json("package-lock.json")
    config = _json("src-tauri/tauri.conf.json")

    assert root_package["version"] == expected
    assert frontend_package["version"] == expected
    assert desktop_package["version"] == expected
    assert lock["packages"][""]["version"] == expected
    assert config["version"] == expected


def test_native_packaging_workflow_uses_workspace_and_backend_dev_requirements():
    source = (ROOT / ".github/workflows/tauri-packaging.yml").read_text(encoding="utf-8")

    assert "npm --workspace src-tauri run build:macos" in source
    assert "npm --workspace src-tauri run build:linux" in source
    assert "backend/requirements/dev.txt" in source
    assert "requirements-dev.txt" not in source


def test_cross_platform_bundle_icons_exist():
    config = _json("src-tauri/tauri.conf.json")
    for icon in config["bundle"]["icon"]:
        icon_path = ROOT / "src-tauri" / icon
        assert icon_path.is_file()
        assert icon_path.stat().st_size > 0
