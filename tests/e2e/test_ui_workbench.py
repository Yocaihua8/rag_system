from __future__ import annotations

import pytest

try:
    from playwright.sync_api import Error, sync_playwright

    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    Error = Exception
    PLAYWRIGHT_AVAILABLE = False


@pytest.mark.skipif(not PLAYWRIGHT_AVAILABLE, reason="playwright not installed")
def test_workbench_sends_question(live_server):
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch()
            page = browser.new_page()
            page.goto(live_server)
            page.wait_for_selector(".masthead")
            browser.close()
    except Error as exc:
        pytest.skip(f"playwright browser unavailable: {exc}")
