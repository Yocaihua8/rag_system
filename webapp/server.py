from __future__ import annotations

import json
import mimetypes
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

from webapp.api import dispatch
from webapp.config import DEFAULT_HOST, DEFAULT_PORT, default_db_path
from webapp.storage import KnowledgeStore


STATIC_DIR = Path(__file__).resolve().parent / "static"


def run_server(
    host: str = DEFAULT_HOST,
    port: int = DEFAULT_PORT,
    db_path: Path | None = None,
) -> int:
    store = KnowledgeStore(db_path or default_db_path())
    handler = _build_handler(store)
    httpd = ThreadingHTTPServer((host, port), handler)
    print(f"Knowledge Island Web is running at http://{host}:{port}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")
    finally:
        httpd.server_close()
    return 0


def _build_handler(store: KnowledgeStore):
    class KnowledgeIslandHandler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            if self.path.startswith("/api/"):
                self._send_api("GET")
                return
            self._send_static()

        def do_POST(self) -> None:
            self._send_api("POST")

        def log_message(self, format: str, *args: Any) -> None:
            return

        def _send_api(self, method: str) -> None:
            response = dispatch(store, method, self.path, self._read_json())
            body = json.dumps(response.body, ensure_ascii=False).encode("utf-8")
            self.send_response(response.status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _send_static(self) -> None:
            rel_path = self.path.lstrip("/") or "index.html"
            target = (STATIC_DIR / rel_path).resolve()
            if not target.is_file() or STATIC_DIR not in target.parents:
                self.send_error(404)
                return
            content = target.read_bytes()
            content_type = mimetypes.guess_type(target.name)[0] or "application/octet-stream"
            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(content)))
            self.end_headers()
            self.wfile.write(content)

        def _read_json(self) -> dict[str, Any]:
            length = int(self.headers.get("Content-Length", "0"))
            if length == 0:
                return {}
            raw = self.rfile.read(length)
            try:
                data = json.loads(raw.decode("utf-8"))
            except json.JSONDecodeError:
                return {}
            return data if isinstance(data, dict) else {}

    return KnowledgeIslandHandler
