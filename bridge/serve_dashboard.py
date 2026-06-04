from __future__ import annotations

import json
import mimetypes
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

DEFAULT_DASHBOARD_PORT = 9898
REPO_ROOT = Path(__file__).resolve().parents[1]
DASHBOARD_CANDIDATES = (
    "SGHv119.html",
    "FullDashboard.html",
    "SuperGrok_Global_Role_Dashboard.html",
)


def _resolve_ai_max_tokens(value: str | None) -> int:
    if not value:
        return 131072
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return 131072
    return parsed if parsed > 0 else 131072


def _dashboard_port() -> int:
    value = os.getenv("PORT") or os.getenv("DASHBOARD_PORT") or os.getenv("SG_DASHBOARD_PORT")
    try:
        return int(value) if value else DEFAULT_DASHBOARD_PORT
    except (TypeError, ValueError):
        return DEFAULT_DASHBOARD_PORT


def _dashboard_path() -> Path | None:
    for name in DASHBOARD_CANDIDATES:
        candidate = REPO_ROOT / name
        if candidate.is_file():
            return candidate
    return None


def _status_payload() -> dict[str, int | str | bool]:
    return {
        "status": "ok",
        "port": _dashboard_port(),
        "max_tokens": _resolve_ai_max_tokens(os.getenv("SG_MAX_TOKENS")),
        "dashboard_found": _dashboard_path() is not None,
    }


def _fallback_html() -> bytes:
    payload = _status_payload()
    return (
        "<!doctype html><html><body>"
        "<h1>SuperGrok Dashboard</h1>"
        f"<pre>{json.dumps(payload, indent=2)}</pre>"
        "</body></html>"
    ).encode("utf-8")


class DashboardHandler(BaseHTTPRequestHandler):
    server_version = "SuperGrokDashboard/1.0"

    def log_message(self, format: str, *args) -> None:  # pragma: no cover
        return

    def _send_json(self, payload: dict[str, int | str | bool]) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_file(self, path: Path) -> None:
        body = path.read_bytes()
        content_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802
        if self.path in {"/health", "/api/health"}:
            self._send_json(_status_payload())
            return

        if self.path in {"/", "/index.html"}:
            dashboard = _dashboard_path()
            if dashboard is not None:
                self._send_file(dashboard)
                return
            body = _fallback_html()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return

        candidate = (REPO_ROOT / self.path.lstrip("/")).resolve()
        if candidate.is_file() and candidate.is_relative_to(REPO_ROOT):
            self._send_file(candidate)
            return

        self.send_error(404, "Not Found")


def main() -> None:
    port = _dashboard_port()
    host = os.getenv("DASHBOARD_HOST", "127.0.0.1")
    server = ThreadingHTTPServer((host, port), DashboardHandler)
    print(f"Dashboard listening on http://{host}:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()