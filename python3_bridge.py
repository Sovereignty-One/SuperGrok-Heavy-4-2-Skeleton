#!/usr/bin/env python3
"""
SuperGrok Unified Bridge v4.0
Single port 9898 — HTTP + WebSocket upgrade on same socket.
No external dependencies. Pure Python 3.6+ stdlib only.

Quick start (a-Shell or iSH):
export ANTHROPIC_API_KEY=sk-ant-…
python3 bridge.py

Then open Safari at:  http://127.0.0.1:9898
"""

import base64
import hashlib
import json
import os
import socket
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path

PORT = int(os.environ.get("SG_PORT", 9898))
HOST = "127.0.0.1"
KEYS = {
    "anthropic": os.environ.get("ANTHROPIC_API_KEY", ""),
    "openai": os.environ.get("OPENAI_API_KEY", ""),
    "grok": os.environ.get("GROK_API_KEY", os.environ.get("XAI_API_KEY", "")),
}

# ---------------------------------------------------------------------
# HTML discovery
# ---------------------------------------------------------------------


def find_html() -> str | None:
    dirs = [Path.home(), Path.cwd(), Path("/root"), Path("/var/mobile")]
    pats = ["SuperGrok_v107*", "SuperGrok_v10*", "SuperGrok*.html", "*.html"]
    for d in dirs:
        for p in pats:
            hits = sorted(d.glob(p), reverse=True)
            if hits:
                return str(hits[0])
    return None


HTML_FILE = find_html()

# ---------------------------------------------------------------------
# AI providers
# ---------------------------------------------------------------------


def post_json(url: str, headers: dict, body: dict):
    try:
        data = json.dumps(body).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.loads(r.read().decode("utf-8", errors="replace")), None
    except urllib.error.HTTPError as e:
        try:
            payload = e.read().decode("utf-8", errors="replace")[:200]
        except Exception:
            payload = ""
        return None, f"{e.code}: {payload}"
    except Exception as e:
        return None, str(e)


def ai_claude(messages, model: str = "claude-opus-4-5"):
    k = KEYS["anthropic"]
    if not k:
        return None, "ANTHROPIC_API_KEY not set"
    r, e = post_json(
        "https://api.anthropic.com/v1/messages",
        {
            "Content-Type": "application/json",
            "x-api-key": k,
            "anthropic-version": "2023-06-01",
        },
        {"model": model, "max_tokens": 2000, "messages": messages},
    )
    return (r["content"][0]["text"], None) if r else (None, e)


def ai_openai(messages, model: str = "gpt-4o"):
    k = KEYS["openai"]
    if not k:
        return None, "OPENAI_API_KEY not set"
    r, e = post_json(
        "https://api.openai.com/v1/chat/completions",
        {"Content-Type": "application/json", "Authorization": "Bearer " + k},
        {"model": model, "max_tokens": 2000, "messages": messages},
    )
    return (r["choices"][0]["message"]["content"], None) if r else (None, e)


def ai_grok(messages, model: str = "grok-3-latest"):
    k = KEYS["grok"]
    if not k:
        return None, "GROK_API_KEY not set"
    r, e = post_json(
        "https://api.x.ai/v1/chat/completions",
        {"Content-Type": "application/json", "Authorization": "Bearer " + k},
        {"model": model, "max_tokens": 2000, "messages": messages},
    )
    return (r["choices"][0]["message"]["content"], None) if r else (None, e)


def route_ai(agent: str | None, messages, model: str | None = None):
    a = (agent or "claude").lower()
    if a in ("claude", "anthropic", "arbiter"):
        order = [ai_claude, ai_openai, ai_grok]
    elif "gpt" in a or "openai" in a:
        order = [ai_openai, ai_claude, ai_grok]
    elif "grok" in a or "xai" in a:
        order = [ai_grok, ai_claude, ai_openai]
    else:
        order = [ai_claude, ai_openai, ai_grok]

    for fn in order:
        text, err = (fn(messages, model) if model else fn(messages))
        if text:
            return text, None
    return None, "All providers failed or no API keys set"


def shell_exec(cmd: str) -> str:
    try:
        r = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=30,
            cwd=str(Path.home()),
        )
        return (r.stdout + r.stderr)[:8192]
    except subprocess.TimeoutExpired:
        return "Timed out (30s)"
    except Exception as e:
        return str(e)


# ---------------------------------------------------------------------
# WebSocket RFC 6455 — raw implementation, no library needed
# ---------------------------------------------------------------------

WS_GUID = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"


def ws_accept_key(key: str) -> str:
    raw = hashlib.sha1((key.strip() + WS_GUID).encode("utf-8")).digest()
    return base64.b64encode(raw).decode("utf-8")


def ws_handshake(conn: socket.socket, key: str) -> None:
    resp = (
        "HTTP/1.1 101 Switching Protocols\r\n"
        "Upgrade: websocket\r\n"
        "Connection: Upgrade\r\n"
        "Sec-WebSocket-Accept: " + ws_accept_key(key) + "\r\n"
        "Access-Control-Allow-Origin: *\r\n"
        "\r\n"
    )
    conn.sendall(resp.encode("utf-8"))


def ws_read_frame(conn: socket.socket):
    """Returns (opcode, bytes_payload) or (None, None) on disconnect."""

    def recv_exact(n: int) -> bytes:
        buf = b""
        while len(buf) < n:
            chunk = conn.recv(n - len(buf))
            if not chunk:
                raise ConnectionError("disconnected")
            buf += chunk
        return buf

    try:
        h = recv_exact(2)
        opcode = h[0] & 0x0F
        masked = bool(h[1] & 0x80)
        plen = h[1] & 0x7F
        if plen == 126:
            plen = int.from_bytes(recv_exact(2), "big")
        elif plen == 127:
            plen = int.from_bytes(recv_exact(8), "big")
        mask = recv_exact(4) if masked else b"\x00\x00\x00\x00"
        data = bytearray(recv_exact(plen))
        if masked:
            for i in range(len(data)):
                data[i] ^= mask[i % 4]
        return opcode, bytes(data)
    except Exception:
        return None, None


def ws_write(conn: socket.socket, payload, opcode: int = 0x01) -> bool:
    if isinstance(payload, str):
        payload = payload.encode("utf-8")
    n = len(payload)
    if n < 126:
        hdr = bytes([0x80 | opcode, n])
    elif n < 65536:
        hdr = bytes([0x80 | opcode, 126]) + n.to_bytes(2, "big")
    else:
        hdr = bytes([0x80 | opcode, 127]) + n.to_bytes(8, "big")
    try:
        conn.sendall(hdr + payload)
        return True
    except Exception:
        return False


def ws_json(conn: socket.socket, obj: dict) -> bool:
    return ws_write(conn, json.dumps(obj))


# ---------------------------------------------------------------------
# WebSocket message handler
# ---------------------------------------------------------------------


def handle_ws_msg(conn: socket.socket, raw: bytes) -> None:
    try:
        msg = json.loads(raw.decode("utf-8", errors="replace"))
    except Exception:
        ws_json(conn, {"type": "error", "error": "invalid JSON"})
        return

    t = msg.get("type", "")
    rid = msg.get("request_id", "")
    print(f"  [WS] {t}")

    if t == "ping":
        ws_json(conn, {"type": "pong", "ts": int(time.time() * 1000)})

    elif t in ("agent_query", "ai_query", "chat", "message", "query"):
        agent = msg.get("agent", msg.get("provider", "claude"))
        prompt = msg.get("prompt", msg.get("message", msg.get("content", "")))
        history = msg.get("history", [])
        messages = history + [{"role": "user", "content": prompt}]
        ws_json(conn, {"type": "agent_thinking", "agent": agent, "request_id": rid})
        text, err = route_ai(agent, messages, msg.get("model"))
        ws_json(
            conn,
            {
                "type": "agent_response",
                "agent": agent,
                "request_id": rid,
                "text": text or "",
                "response": text or "",
                "error": err,
            },
        )

    elif t in ("exec", "shell_exec", "terminal", "run"):
        cmd = msg.get("cmd", msg.get("command", ""))
        ws_json(conn, {"type": "exec_result", "output": shell_exec(cmd), "cmd": cmd})

    elif t in ("ssh_input", "ssh_data"):
        ws_json(conn, {"type": "ssh_data", "data": shell_exec(msg.get("data", "").strip())})

    elif t == "ssh_connect":
        ws_json(
            conn,
            {
                "type": "ssh_connected",
                "banner": "SuperGrok SSH Bridge\n%s:%s\n"
                % (msg.get("host", "localhost"), msg.get("port", 22)),
                "prompt": "%s@%s:~$ "
                % (msg.get("username", "root"), msg.get("host", "localhost")),
            },
        )

    elif t == "tts_xai":
        text = msg.get("text", "")
        key = msg.get("key", KEYS.get("grok", ""))
        if key:
            try:
                r, err = post_json(
                    "https://api.x.ai/v1/audio/speech",
                    {"Content-Type": "application/json", "Authorization": "Bearer " + key},
                    {"model": "tts-1", "input": text, "voice": msg.get("voice", "shimmer")},
                )
                if r:
                    ws_json(conn, {"type": "tts_result", "text": text, "status": "ok"})
                else:
                    threading.Thread(
                        target=lambda: subprocess.run(
                            f'say "{text}" 2>/dev/null || espeak "{text}" 2>/dev/null',
                            shell=True,
                        ),
                        daemon=True,
                    ).start()
                    ws_json(conn, {"type": "speak_result", "text": text})
            except Exception:
                ws_json(conn, {"type": "speak_result", "text": text})
        else:
            threading.Thread(
                target=lambda: subprocess.run(
                    f'say "{text}" 2>/dev/null || espeak "{text}" 2>/dev/null',
                    shell=True,
                ),
                daemon=True,
            ).start()
            ws_json(conn, {"type": "speak_result", "text": text})

    elif t == "speak":
        text = msg.get("text", "")
        threading.Thread(
            target=lambda: subprocess.run(
                f'say "{text}" 2>/dev/null || espeak "{text}" 2>/dev/null',
                shell=True,
            ),
            daemon=True,
        ).start()
        ws_json(conn, {"type": "speak_result", "text": text})

    elif t == "stt_start":
        ws_json(conn, {"type": "stt_ready"})

    elif t == "keys_set":
        for k, v in (msg.get("keys") or {}).items():
            if k in KEYS and v:
                KEYS[k] = v
                os.environ[k.upper() + "_API_KEY"] = v
        ws_json(conn, {"type": "keys_saved"})

    elif t == "health":
        ws_json(
            conn,
            {
                "type": "health_ok",
                "version": "v4.0",
                "keys": {k: bool(v) for k, v in KEYS.items()},
            },
        )

    else:
        ws_json(conn, {"type": "ack", "received": t, "ts": int(time.time() * 1000)})


def run_ws(conn: socket.socket, addr, path: str) -> None:
    print(f"[WS]  + {addr}  path={path}")
    ws_json(
        conn,
        {
            "type": "connected",
            "version": "SuperGrok Bridge v4.0",
            "keys": {k: bool(v) for k, v in KEYS.items()},
        },
    )
    try:
        while True:
            opcode, payload = ws_read_frame(conn)
            if opcode is None:
                break
            if opcode == 0x8:
                break
            if opcode == 0x9:
                ws_write(conn, b"", 0xA)
                continue
            if opcode in (0x1, 0x2):
                handle_ws_msg(conn, payload)
    except Exception as e:
        print(f"[WS]  ! {addr}  {e}")
    finally:
        print(f"[WS]  - {addr}")
        try:
            conn.close()
        except Exception:
            pass


# ---------------------------------------------------------------------
# HTTP handler
# ---------------------------------------------------------------------

CORS_HDR = (
    "Access-Control-Allow-Origin: *\r\n"
    "Access-Control-Allow-Methods: GET, POST, OPTIONS\r\n"
    "Access-Control-Allow-Headers: Content-Type, Authorization, X-API-Key\r\n"
)


def http_send(conn: socket.socket, code: int, body, ctype: str = "application/json") -> None:
    phrase = {
        200: "OK",
        204: "No Content",
        404: "Not Found",
        405: "Method Not Allowed",
        500: "Internal Server Error",
    }.get(code, "OK")

    if isinstance(body, dict):
        body = json.dumps(body).encode("utf-8")
    elif isinstance(body, str):
        body = body.encode("utf-8")

    hdr = (
        f"HTTP/1.1 {code} {phrase}\r\n"
        f"Content-Type: {ctype}; charset=utf-8\r\n"
        f"Content-Length: {len(body)}\r\n"
        f"{CORS_HDR}"
        "Cache-Control: no-store\r\n"
        "Connection: close\r\n"
        "\r\n"
    )
    try:
        conn.sendall(hdr.encode("utf-8") + body)
    except Exception:
        pass


def fallback_html() -> bytes:
    rows = ""
    for k, v in KEYS.items():
        color = "#3fb950" if v else "#ff6b6b"
        note = "set" if v else f"not set – export {k.upper()}_API_KEY=…"
        rows += f'<li style="color:{color}">{k}: {note}</li>'
    html = (
        "<!DOCTYPE html><html><head><meta charset='UTF-8'><title>SuperGrok Bridge</title>"
        "<style>body{background:#0d1117;color:#c9d1d9;font-family:monospace;padding:40px;"
        "max-width:700px;margin:0 auto}h1{color:#00ffc8}"
        "code{background:#161b22;padding:2px 6px;border-radius:4px;color:#79c0ff}"
        "a{color:#58a6ff}</style></head><body>"
        "<h1>SuperGrok Bridge v4.0 — Running</h1>"
        f"<p style='color:#3fb950'>HTTP + WebSocket on port {PORT}</p>"
        "<p style='color:#ff9800'>Place SuperGrok_v107_FINAL.html in ~/ then reload.</p>"
        f"<ul>{rows}</ul>"
        "<p><a href='/api/health'>/api/health</a></p>"
        "</body></html>"
    )
    return html.encode("utf-8")


def handle_http(conn: socket.socket, method: str, path: str, body_bytes: bytes) -> None:
    if method == "OPTIONS":
        http_send(conn, 204, b"")
        return

    if method == "GET":
        if path in ("/", "/index.html"):
            if HTML_FILE and Path(HTML_FILE).exists():
                http_send(conn, 200, Path(HTML_FILE).read_bytes(), "text/html")
            else:
                http_send(conn, 200, fallback_html(), "text/html")

        elif path == "/api/health":
            http_send(
                conn,
                200,
                {
                    "status": "ok",
                    "version": "v4.0",
                    "port": PORT,
                    "html": HTML_FILE or "not found",
                    "keys": {k: bool(v) for k, v in KEYS.items()},
                    "ts": int(time.time()),
                },
            )

        else:
            http_send(conn, 404, {"error": "not found"})
        return

    if method == "POST":
        body = {}
        if body_bytes:
            try:
                body = json.loads(body_bytes.decode("utf-8", errors="replace"))
            except Exception:
                body = {}

        if path in ("/api/ai", "/api/agent", "/api/chat"):
            agent = body.get("agent", "claude")
            prompt = body.get("prompt", body.get("message", body.get("content", "")))
            history = body.get("history", [])
            messages = history + [{"role": "user", "content": prompt}]
            text, err = route_ai(agent, messages, body.get("model"))
            http_send(
                conn,
                200,
                {
                    "type": "agent_response",
                    "agent": agent,
                    "text": text or "",
                    "response": text or "",
                    "error": err,
                },
            )

        elif path in ("/api/exec", "/api/terminal", "/api/shell"):
            cmd = body.get("cmd", body.get("command", ""))
            http_send(conn, 200, {"type": "exec_result", "output": shell_exec(cmd)})

        elif path == "/api/keys":
            for k, v in body.items():
                if k in KEYS and v:
                    KEYS[k] = v
                    os.environ[k.upper() + "_API_KEY"] = v
            http_send(conn, 200, {"saved": True, "keys": {k: bool(v) for k, v in KEYS.items()}})

        elif path == "/api/speak":
            text = body.get("text", "")
            subprocess.run(
                f'say "{text}" 2>/dev/null || espeak "{text}" 2>/dev/null',
                shell=True,
            )
            http_send(conn, 200, {"done": True})

        else:
            http_send(conn, 404, {"error": "not found"})
        return

    http_send(conn, 405, {"error": "method not allowed"})


# ---------------------------------------------------------------------
# Connection dispatcher — same socket serves HTTP and WS
# ---------------------------------------------------------------------


def handle_conn(conn: socket.socket, addr) -> None:
    conn.settimeout(30)
    try:
        buf = b""
        while b"\r\n\r\n" not in buf:
            c = conn.recv(4096)
            if not c:
                return
            buf += c
            if len(buf) > 65536:
                return

        head_raw, _, body_start = buf.partition(b"\r\n\r\n")
        lines = head_raw.decode("utf-8", errors="replace").split("\r\n")
        req = lines[0].split()
        if len(req) < 2:
            return
        method = req[0].upper()
        path = req[1]

        hdrs = {}
        for ln in lines[1:]:
            if ":" in ln:
                k, _, v = ln.partition(":")
                hdrs[k.strip().lower()] = v.strip()

        if hdrs.get("upgrade", "").lower() == "websocket" and "sec-websocket-key" in hdrs:
            ws_handshake(conn, hdrs["sec-websocket-key"])
            conn.settimeout(None)
            run_ws(conn, addr, path)
            return

        clen = int(hdrs.get("content-length", 0))
        body_raw = body_start
        while len(body_raw) < clen:
            c = conn.recv(min(4096, clen - len(body_raw)))
            if not c:
                break
            body_raw += c

        handle_http(conn, method, path, body_raw)
    except Exception:
        pass
    finally:
        try:
            conn.close()
        except Exception:
            pass


# ---------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------

if __name__ == "__main__":
    print("=" * 58)
    print("  SuperGrok Unified Bridge v4.0")
    print(f"  HTTP + WebSocket on single port {PORT} — no split")
    print("=" * 58)
    print(f"  Dashboard : http://127.0.0.1:{PORT}")
    print(f"  Health    : http://127.0.0.1:{PORT}/api/health")
    print(f"  HTML      : {HTML_FILE or 'NOT FOUND — place SuperGrok_v107_FINAL.html in ~/'}")
    print()
    print("  Claude    : " + ("ready" if KEYS["anthropic"] else "export ANTHROPIC_API_KEY=sk-ant-…"))
    print("  OpenAI    : " + ("ready" if KEYS["openai"] else "export OPENAI_API_KEY=sk-…"))
    print("  Grok      : " + ("ready" if KEYS["grok"] else "export GROK_API_KEY=xai-…"))
    print()
    print(f"  OPEN SAFARI AT: http://127.0.0.1:{PORT}")
    print("=" * 58)

    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        srv.bind((HOST, PORT))
    except OSError as e:
        print(f"\nCannot bind {HOST}:{PORT} — {e}")
        print(f"Kill the existing process: kill $(lsof -t -i:{PORT})")
        sys.exit(1)

    srv.listen(32)
    print("\n[OK]  Accepting connections ...\n")
    while True:
        try:
            conn, addr = srv.accept()
            threading.Thread(target=handle_conn, args=(conn, addr), daemon=True).start()
        except KeyboardInterrupt:
            print("\nStopped.")
            break
        except Exception as e:
            print(f"[ERR] {e}")
