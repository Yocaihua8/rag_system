from __future__ import annotations

import pytest

from backend.config.desktop import (
    DesktopRuntimeSettings,
    load_desktop_settings,
    load_server_binding,
)


TOKEN = "ab" * 32


def test_desktop_mode_is_disabled_by_default_and_keeps_web_binding():
    desktop = load_desktop_settings({})
    binding = load_server_binding({}, desktop_settings=desktop)

    assert desktop == DesktopRuntimeSettings(enabled=False)
    assert binding.host == "127.0.0.1"
    assert binding.port == 8765


def test_desktop_mode_requires_explicit_port_and_strict_process_token():
    with pytest.raises(ValueError, match="KI_DESKTOP_STARTUP_TOKEN"):
        load_desktop_settings(
            {"KI_DESKTOP_MODE": "1", "KI_DESKTOP_STARTUP_TOKEN": "short"}
        )

    with pytest.raises(ValueError, match="KI_DESKTOP_STARTUP_TOKEN"):
        load_desktop_settings(
            {"KI_DESKTOP_MODE": "1", "KI_DESKTOP_STARTUP_TOKEN": TOKEN.upper()}
        )

    desktop = load_desktop_settings(
        {"KI_DESKTOP_MODE": "1", "KI_DESKTOP_STARTUP_TOKEN": TOKEN}
    )
    with pytest.raises(ValueError, match="KI_API_PORT is required"):
        load_server_binding({}, desktop_settings=desktop)


@pytest.mark.parametrize("host", ["0.0.0.0", "localhost", "::1", "192.168.1.20"])
def test_desktop_mode_rejects_every_non_exact_loopback_host(host):
    desktop = DesktopRuntimeSettings(enabled=True, startup_token=TOKEN)

    with pytest.raises(ValueError, match="bind exactly"):
        load_server_binding(
            {"KI_API_HOST": host, "KI_API_PORT": "49152"},
            desktop_settings=desktop,
        )


@pytest.mark.parametrize("port", ["0", "65536", "not-a-port"])
def test_server_binding_rejects_invalid_ports(port):
    desktop = DesktopRuntimeSettings(enabled=True, startup_token=TOKEN)

    with pytest.raises(ValueError, match="KI_API_PORT"):
        load_server_binding(
            {"KI_API_HOST": "127.0.0.1", "KI_API_PORT": port},
            desktop_settings=desktop,
        )


def test_desktop_mode_accepts_explicit_loopback_port():
    desktop = DesktopRuntimeSettings(enabled=True, startup_token=TOKEN)

    binding = load_server_binding(
        {"KI_API_HOST": "127.0.0.1", "KI_API_PORT": "49152"},
        desktop_settings=desktop,
    )

    assert binding.host == "127.0.0.1"
    assert binding.port == 49152
