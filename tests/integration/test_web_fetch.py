from __future__ import annotations

import socket
from email.message import Message

import pytest

from backend.domain.web_fetch import (
    WebFetchError,
    extract_readable_text,
    fetch_web_preview,
    validate_public_http_url,
)


GLOBAL_IP = "93.184.216.34"


def global_resolver(host: str, port: int):
    return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", (GLOBAL_IP, port))]


def private_resolver(host: str, port: int):
    return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("127.0.0.1", port))]


def test_validate_public_http_url_rejects_unsafe_targets():
    with pytest.raises(WebFetchError, match="http or https"):
        validate_public_http_url("file:///etc/passwd", resolver=global_resolver)

    with pytest.raises(WebFetchError, match="URL credentials are not allowed"):
        validate_public_http_url("https://user:pass@example.com/doc", resolver=global_resolver)

    with pytest.raises(WebFetchError, match="non-standard ports are not allowed"):
        validate_public_http_url("https://example.com:8443/doc", resolver=global_resolver)

    with pytest.raises(WebFetchError, match="private or local network"):
        validate_public_http_url("https://example.com/doc", resolver=private_resolver)


def test_fetch_web_preview_respects_robots_and_does_not_fetch_page_when_disallowed():
    opener = FakeOpener({
        "https://example.com/robots.txt": FakeResponse(
            "https://example.com/robots.txt",
            "User-agent: *\nDisallow: /private\n",
            "text/plain",
        ),
        "https://example.com/private/page": FakeResponse(
            "https://example.com/private/page",
            "<html><body>blocked</body></html>",
            "text/html",
        ),
    })

    with pytest.raises(WebFetchError, match="robots.txt disallows fetching this URL"):
        fetch_web_preview("https://example.com/private/page", opener=opener, resolver=global_resolver)

    assert opener.opened_urls == ["https://example.com/robots.txt"]


def test_fetch_web_preview_extracts_safe_html_text_and_metadata():
    opener = FakeOpener({
        "https://example.com/robots.txt": FakeResponse(
            "https://example.com/robots.txt",
            "User-agent: *\nAllow: /\n",
            "text/plain",
        ),
        "https://example.com/article": FakeResponse(
            "https://example.com/article",
            """
            <html>
              <head>
                <title>Example Article</title>
                <style>.hidden { display: none; }</style>
                <script>secret()</script>
              </head>
              <body>
                <h1>Visible Heading</h1>
                <p>Visible paragraph with Knowledge Island.</p>
                <form><input value="password"></form>
              </body>
            </html>
            """,
            "text/html; charset=utf-8",
        ),
    })

    preview = fetch_web_preview("https://example.com/article", opener=opener, resolver=global_resolver)

    assert preview.url == "https://example.com/article"
    assert preview.final_url == "https://example.com/article"
    assert preview.title == "Example Article"
    assert preview.robots_allowed is True
    assert preview.status_code == 200
    assert preview.content_type == "text/html"
    assert preview.content_length == len(preview.content.encode("utf-8"))
    assert preview.content_hash
    assert preview.extractor_version == "static-html-v1"
    assert "Visible Heading" in preview.content
    assert "Knowledge Island" in preview.content
    assert "secret()" not in preview.content
    assert "display: none" not in preview.content
    assert "password" not in preview.content


def test_fetch_web_preview_rejects_unsupported_type_and_oversized_response():
    unsupported = FakeOpener({
        "https://example.com/robots.txt": FakeResponse("https://example.com/robots.txt", "", "text/plain", status=404),
        "https://example.com/image.png": FakeResponse("https://example.com/image.png", b"\x89PNG", "image/png"),
    })

    with pytest.raises(WebFetchError, match="unsupported content type"):
        fetch_web_preview("https://example.com/image.png", opener=unsupported, resolver=global_resolver)

    oversized = FakeOpener({
        "https://example.com/robots.txt": FakeResponse("https://example.com/robots.txt", "", "text/plain", status=404),
        "https://example.com/large": FakeResponse("https://example.com/large", "abcdef", "text/plain"),
    })

    with pytest.raises(WebFetchError, match="response is too large"):
        fetch_web_preview("https://example.com/large", opener=oversized, resolver=global_resolver, max_bytes=5)


def test_extract_readable_text_handles_plain_text_and_empty_html():
    assert extract_readable_text("text/plain", b"  hello\n\nworld  ", "utf-8") == ("", "hello\n\nworld")

    with pytest.raises(WebFetchError, match="no readable text"):
        extract_readable_text("text/html", b"<html><script>onlyScript()</script></html>", "utf-8")


class FakeResponse:
    def __init__(self, url: str, body: str | bytes, content_type: str, status: int = 200):
        self.url = url
        self.status = status
        self.headers = Message()
        self.headers["Content-Type"] = content_type
        self._body = body if isinstance(body, bytes) else body.encode("utf-8")

    def read(self, size: int = -1) -> bytes:
        if size is None or size < 0:
            return self._body
        return self._body[:size]

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class FakeOpener:
    def __init__(self, responses: dict[str, FakeResponse]):
        self.responses = responses
        self.opened_urls: list[str] = []

    def open(self, request, timeout: float):
        url = request.full_url if hasattr(request, "full_url") else str(request)
        self.opened_urls.append(url)
        try:
            return self.responses[url]
        except KeyError as exc:
            raise AssertionError(f"unexpected URL opened: {url}") from exc
