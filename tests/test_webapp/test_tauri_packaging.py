import json
from pathlib import Path


def test_tauri_config_bundles_vue_build_and_backend_sidecar():
    config_path = Path("src-tauri/tauri.conf.json")

    assert config_path.exists(), "B-145 must add a Tauri 2 configuration"
    config = json.loads(config_path.read_text(encoding="utf-8"))

    assert config["productName"] == "Knowledge Island"
    assert config["identifier"] == "local.knowledge-island.app"
    assert config["build"]["beforeBuildCommand"] == "npm run build"
    assert config["build"]["frontendDist"] == "../webapp/static_dist"
    assert config["bundle"]["active"] is True
    assert config["bundle"]["externalBin"] == ["binaries/knowledge-island-backend"]


def test_tauri_windows_icon_exists_for_resource_generation():
    icon_path = Path("src-tauri/icons/icon.ico")

    assert icon_path.exists(), "Tauri Windows builds require src-tauri/icons/icon.ico"
    assert icon_path.stat().st_size > 0


def test_tauri_rust_entry_starts_sidecar_and_minimizes_to_tray():
    main_rs = Path("src-tauri/src/main.rs")

    assert main_rs.exists(), "B-145 must add the Tauri Rust entrypoint"
    source = main_rs.read_text(encoding="utf-8")

    assert "tauri_plugin_shell::init()" in source
    assert 'sidecar("binaries/knowledge-island-backend")' in source
    assert "TrayIconBuilder" in source
    assert "MenuItem" in source
    assert "CloseRequested" in source
    assert "prevent_close" in source
    assert ".hide()" in source
    assert "kill_backend_sidecar" in source
    assert "guard.take()" in source


def test_windows_sidecar_script_builds_pyinstaller_binary_for_tauri_triple():
    script_path = Path("scripts/build-backend-sidecar.ps1")

    assert script_path.exists(), "B-145 must add a Windows sidecar build script"
    script = script_path.read_text(encoding="utf-8")

    assert "npm run build" in script
    assert "-m PyInstaller" in script
    assert "--onefile" in script
    assert "--name" in script
    assert "knowledge-island-backend" in script
    assert "webapp/static_dist" in script
    assert "src-tauri/binaries" in script
    assert "knowledge-island-backend-x86_64-pc-windows-msvc.exe" in script


def test_package_json_exposes_tauri_windows_packaging_scripts():
    package_data = json.loads(Path("package.json").read_text(encoding="utf-8"))

    assert package_data["scripts"]["sidecar:build"] == (
        "powershell -ExecutionPolicy Bypass -File scripts/build-backend-sidecar.ps1"
    )
    assert package_data["scripts"]["tauri:dev"] == "tauri dev"
    assert package_data["scripts"]["tauri:build"] == "tauri build"
    assert package_data["scripts"]["tauri:build:windows"] == (
        "npm run sidecar:build && tauri build"
    )
    assert package_data["devDependencies"]["@tauri-apps/cli"]


def test_desktop_packaging_docs_describe_windows_validation_commands():
    setup = Path("docs/guides/setup.md").read_text(encoding="utf-8")
    testing = Path("docs/guides/testing.md").read_text(encoding="utf-8")
    feature = Path("docs/features/desktop-packaging.md").read_text(encoding="utf-8")

    assert "npm run tauri:build:windows" in setup
    assert "scripts/build-backend-sidecar.ps1" in setup
    assert "npm run tauri:build:windows" in testing
    assert "tests/test_webapp/test_tauri_packaging.py" in testing
    assert "Tauri MVP 0" in feature
    assert "src-tauri/binaries/knowledge-island-backend-*-windows-msvc.exe" in feature
