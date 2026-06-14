#!/usr/bin/env python3
"""
Sovereign Bridge 9897 — Minimal Production
Auto-loads identity + memory context on first connect.
"""

from __future__ import annotations

import json
import os
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

DEFAULT_AI_MAX_TOKENS = 131072


def _parse_ai_max_tokens() -> int:
    raw = os.getenv("SG_MAX_TOKENS")
    if raw is None:
        return DEFAULT_AI_MAX_TOKENS

    try:
        value = int(raw)
    except (TypeError, ValueError):
        return DEFAULT_AI_MAX_TOKENS

    return value if value > 0 else DEFAULT_AI_MAX_TOKENS


AI_MAX_TOKENS = _parse_ai_max_tokens()

# --- Simple in-memory identity store (replace with real REPMHL later) ---
CURRENT_IDENTITY = {
    "name": "Derek Appel",
    "handle": "Appel420(root)",
    "role": "root",
}
MEMORY_CONTEXT = "User is building sovereign AI systems. Prefers direct, no-fluff responses. Working on persistent memory and identity across sessions."


def build_health_payload() -> dict:
    return {
        "status": "live",
        "service": "SovereignBridge",
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }


def build_connect_payload() -> dict:
    """This is the key endpoint. Frontend calls this on load to get identity immediately."""
    return {
        "status": "connected",
        "identity": CURRENT_IDENTITY,
        "memory_context": MEMORY_CONTEXT,
        "message": f"Welcome back, {CURRENT_IDENTITY['name']}",
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }


class BridgeHandler(BaseHTTPRequestHandler):
    server_version = "SovereignBridge/1.0"

    def log_message(self, format: str, *args) -> None:
        return

    def _send_json(self, code: int, payload: dict) -> None:
        body = json.dumps(payload, indent=2).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self) -> None:
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self) -> None:
        if self.path in {"/", "/health", "/api/health"}:
            self._send_json(200, build_health_payload())
            return

        # NEW: Auto identity + memory load on connect
        if self.path in {"/connect", "/api/connect", "/api/bootstrap"}:
            self._send_json(200, build_connect_payload())
            return

        self.send_error(404, "Not Found")


def main() -> None:
    host = os.getenv("SG_HOST", "127.0.0.1")
    port = int(os.getenv("SG_PORT", "9897"))
    server = ThreadingHTTPServer((host, port), BridgeHandler)
    print(f"🚀 Sovereign Bridge listening on http://{host}:{port}")
    print("   /api/connect → returns identity + memory automatically")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
