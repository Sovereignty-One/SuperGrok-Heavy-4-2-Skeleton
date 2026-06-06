from __future__ import annotations

import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

DEFAULT_AI_MAX_TOKENS = 131072


def _resolve_ai_max_tokens(value: str | None) -> int:
    if not value:
        return DEFAULT_AI_MAX_TOKENS
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return DEFAULT_AI_MAX_TOKENS
    return parsed if parsed > 0 else DEFAULT_AI_MAX_TOKENS


AI_MAX_TOKENS = _resolve_ai_max_tokens(os.getenv("SG_MAX_TOKENS"))


def build_health_payload() -> dict[str, int | str]:
    return {
        "status": "ok",
        "port": _bridge_port(),
        "max_tokens": AI_MAX_TOKENS,
    }


def _bridge_port() -> int:
    try:
        return int(os.getenv("SG_PORT", "9897"))
    except (TypeError, ValueError):
        return 9897


class BridgeHandler(BaseHTTPRequestHandler):
    server_version = "SovereignBridge/1.0"

    def log_message(self, format: str, *args) -> None:  # pragma: no cover
        return

    def _send_json(self, payload: dict[str, int | str]) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802
        if self.path in {"/", "/health", "/api/health"}:
            self._send_json(build_health_payload())
            return
        self.send_error(404, "Not Found")


def main() -> None:
    host = os.getenv("SG_HOST", "127.0.0.1")
    port = _bridge_port()
    server = ThreadingHTTPServer((host, port), BridgeHandler)
    print(f"Python bridge listening on http://{host}:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
