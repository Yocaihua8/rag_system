from __future__ import annotations

from scripts.check_npm_audit import (
    ALLOWED_ADVISORY,
    _find_rsc_markers,
    _is_allowed_router_exception,
)


def _allowed_report() -> dict:
    return {
        "vulnerabilities": {
            "react-router": {
                "severity": "high",
                "isDirect": False,
                "via": [{"url": ALLOWED_ADVISORY}],
            },
            "react-router-dom": {
                "severity": "high",
                "isDirect": True,
                "via": ["react-router"],
            },
        },
        "metadata": {"vulnerabilities": {"high": 2, "total": 2}},
    }


def test_router_rsc_advisory_is_the_only_allowed_npm_audit_exception() -> None:
    assert _is_allowed_router_exception(_allowed_report()) is True

    report = _allowed_report()
    report["vulnerabilities"]["another-package"] = {
        "severity": "high",
        "isDirect": True,
        "via": [{"url": "https://example.invalid/another-advisory"}],
    }
    report["metadata"]["vulnerabilities"] = {"high": 3, "total": 3}
    assert _is_allowed_router_exception(report) is False


def test_frontend_v3_has_no_rsc_or_server_router_entrypoint() -> None:
    assert _find_rsc_markers() == []
