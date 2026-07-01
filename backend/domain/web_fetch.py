from __future__ import annotations

import hashlib
import html
import ipaddress
import re
import socket
from dataclasses import dataclass
from datetime import UTC, datetime
from html.parser import HTMLParser
from urllib import robotparser
from urllib.parse import ParseResult, urlparse, urlunparse
from urllib.request import HTTPRedirectHandler, Request, build_opener

DEFAULT_USER_AGENT = "KnowledgeIslandWebFetch/1.0"
DEFAULT_TIMEOUT_SECONDS = 10.0
DEFAULT_MAX_BYTES = 1_000_000
DEFAULT_MAX_REDIRECTS = 3
EXTRACTOR_VERSION = "static-html-v1"
ALLOWED_CONTENT_TYPES = {"text/html", "text/plain", "text/markdown", "text/x-markdown"}
SKIP_HTML_TAGS = {"script", "style", "form", "noscript", "template", "svg", "canvas"}


class WebFetchError(ValueError):
    pass


@dataclass(frozen=True)
class WebFetchPreview:
    url: str
    final_url: str
    title: str
    content: str
    content_length: int
    content_type: str
    fetched_at: str
    robots_allowed: bool
    status_code: int
    content_hash: str
    extractor_version: str = EXTRACTOR_VERSION

    def to_dict(self) -> dict[str, object]:
        return {
            "url": self.url,
            "final_url": self.final_url,
            "title": self.title,
            "content": self.content,
            "content_length": self.content_length,
            "content_type": self.content_type,
            "fetched_at": self.fetched_at,
            "robots_allowed": self.robots_allowed,
            "status_code": self.status_code,
            "content_hash": self.content_hash,
            "extractor_version": self.extractor_version,
        }


def validate_public_http_url(url: object, *, resolver=socket.getaddrinfo) -> str:
    if not isinstance(url, str) or not url.strip():
        raise WebFetchError("url is required")
    clean_url = url.strip()
    try:
        parsed = urlparse(clean_url)
        port = parsed.port
    except ValueError as exc:
        raise WebFetchError("url is invalid") from exc
    if parsed.scheme not in {"http", "https"}:
        raise WebFetchError("url must use http or https")
    if parsed.username or parsed.password:
        raise WebFetchError("URL credentials are not allowed")
    if not parsed.hostname:
        raise WebFetchError("url host is required")
    if port and port != _default_port(parsed.scheme):
        raise WebFetchError("non-standard ports are not allowed")
    hostname = parsed.hostname.strip().rstrip(".").casefold()
    if hostname == "localhost" or hostname.endswith(".localhost"):
        raise WebFetchError("url resolves to private or local network")
    _validate_resolved_addresses(hostname, port or _default_port(parsed.scheme), resolver)
    return clean_url


def fetch_web_preview(
    url: object,
    *,
    opener=None,
    resolver=socket.getaddrinfo,
    timeout: float = DEFAULT_TIMEOUT_SECONDS,
    max_bytes: int = DEFAULT_MAX_BYTES,
    user_agent: str = DEFAULT_USER_AGENT,
) -> WebFetchPreview:
    clean_url = validate_public_http_url(url, resolver=resolver)
    http_opener = opener or build_opener(_ValidatingRedirectHandler(resolver=resolver))
    robots_allowed = _robots_allows(clean_url, http_opener, timeout, user_agent)
    if not robots_allowed:
        raise WebFetchError("robots.txt disallows fetching this URL")

    request = Request(clean_url, headers={"User-Agent": user_agent})
    with http_opener.open(request, timeout=timeout) as response:
        status_code = int(getattr(response, "status", getattr(response, "code", 200)) or 200)
        if status_code >= 400:
            raise WebFetchError(f"web fetch failed with status {status_code}")
        final_url = validate_public_http_url(str(getattr(response, "url", clean_url)), resolver=resolver)
        content_type = response.headers.get_content_type()
        if content_type not in ALLOWED_CONTENT_TYPES:
            raise WebFetchError("unsupported content type")
        charset = response.headers.get_content_charset("utf-8") or "utf-8"
        body = _read_limited(response, max_bytes)

    title, content = extract_readable_text(content_type, body, charset)
    if not title:
        title = _fallback_title(final_url)
    content_bytes = content.encode("utf-8")
    return WebFetchPreview(
        url=clean_url,
        final_url=final_url,
        title=title,
        content=content,
        content_length=len(content_bytes),
        content_type=content_type,
        fetched_at=datetime.now(UTC).isoformat(),
        robots_allowed=True,
        status_code=status_code,
        content_hash=hashlib.sha256(content_bytes).hexdigest(),
    )


def extract_readable_text(content_type: str, body: bytes, charset: str) -> tuple[str, str]:
    text = body.decode(charset or "utf-8", errors="replace").strip()
    if content_type != "text/html":
        if not text:
            raise WebFetchError("no readable text")
        return "", text

    parser = _ReadableHTMLParser()
    parser.feed(text)
    parser.close()
    content = _normalize_html_text(parser.readable_text())
    if not content:
        raise WebFetchError("no readable text")
    return parser.title_text(), content


def _validate_resolved_addresses(hostname: str, port: int, resolver) -> None:
    try:
        records = resolver(hostname, port)
    except OSError as exc:
        raise WebFetchError("url host could not be resolved") from exc
    addresses = [record[4][0] for record in records if len(record) >= 5 and record[4]]
    if not addresses:
        raise WebFetchError("url host could not be resolved")
    for address in addresses:
        try:
            ip = ipaddress.ip_address(str(address).split("%", 1)[0])
        except ValueError as exc:
            raise WebFetchError("url host could not be resolved") from exc
        if not ip.is_global:
            raise WebFetchError("url resolves to private or local network")


def _robots_allows(url: str, opener, timeout: float, user_agent: str) -> bool:
    parsed = urlparse(url)
    robots_url = urlunparse((parsed.scheme, parsed.netloc, "/robots.txt", "", "", ""))
    request = Request(robots_url, headers={"User-Agent": user_agent})
    try:
        with opener.open(request, timeout=timeout) as response:
            status = int(getattr(response, "status", getattr(response, "code", 200)) or 200)
            if status >= 400:
                return True
            body = response.read(DEFAULT_MAX_BYTES + 1).decode("utf-8", errors="replace")
    except WebFetchError:
        raise
    except Exception as exc:
        raise WebFetchError("robots.txt could not be checked") from exc
    parser = robotparser.RobotFileParser()
    parser.set_url(robots_url)
    parser.parse(body.splitlines())
    return bool(parser.can_fetch(user_agent, url))


def _read_limited(response, max_bytes: int) -> bytes:
    body = response.read(max_bytes + 1)
    if len(body) > max_bytes:
        raise WebFetchError("response is too large")
    return body


def _default_port(scheme: str) -> int:
    return 443 if scheme == "https" else 80


def _fallback_title(url: str) -> str:
    parsed = urlparse(url)
    path = parsed.path.strip("/").split("/")[-1]
    return path or parsed.hostname or "web page"


def _normalize_html_text(text: str) -> str:
    lines = [re.sub(r"\s+", " ", line).strip() for line in text.splitlines()]
    return "\n".join(line for line in lines if line)


class _ReadableHTMLParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._skip_depth = 0
        self._in_title = False
        self._title_parts: list[str] = []
        self._parts: list[str] = []

    def handle_starttag(self, tag: str, attrs) -> None:
        normalized = tag.lower()
        if normalized in SKIP_HTML_TAGS:
            self._skip_depth += 1
        if normalized == "title":
            self._in_title = True
        if normalized in {"p", "div", "section", "article", "li", "br", "h1", "h2", "h3"}:
            self._parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        normalized = tag.lower()
        if normalized in SKIP_HTML_TAGS and self._skip_depth > 0:
            self._skip_depth -= 1
        if normalized == "title":
            self._in_title = False
        if normalized in {"p", "div", "section", "article", "li", "h1", "h2", "h3"}:
            self._parts.append("\n")

    def handle_data(self, data: str) -> None:
        clean_data = html.unescape(data)
        if self._in_title:
            self._title_parts.append(clean_data)
        if self._skip_depth == 0 and not self._in_title:
            self._parts.append(clean_data)

    def title_text(self) -> str:
        return re.sub(r"\s+", " ", " ".join(self._title_parts)).strip()

    def readable_text(self) -> str:
        return "".join(self._parts)


class _ValidatingRedirectHandler(HTTPRedirectHandler):
    def __init__(self, *, resolver=socket.getaddrinfo, max_redirects: int = DEFAULT_MAX_REDIRECTS) -> None:
        super().__init__()
        self._resolver = resolver
        self._max_redirects = max_redirects
        self._redirect_count = 0

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        self._redirect_count += 1
        if self._redirect_count > self._max_redirects:
            raise WebFetchError("too many redirects")
        validate_public_http_url(newurl, resolver=self._resolver)
        return super().redirect_request(req, fp, code, msg, headers, newurl)
