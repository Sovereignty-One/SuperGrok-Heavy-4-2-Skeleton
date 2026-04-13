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
import secrets
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
MAX_CODE_REVIEW_LENGTH = 4000  # max chars of user code sent to AI for review

# How many days before a key is flagged as stale and rotation is recommended.
KEY_ROTATION_DAYS = int(os.environ.get("SG_KEY_ROTATION_DAYS", 30))

KEYS = {
    "anthropic": os.environ.get("ANTHROPIC_API_KEY", ""),
    "openai": os.environ.get("OPENAI_API_KEY", ""),
    "grok": os.environ.get("GROK_API_KEY", os.environ.get("XAI_API_KEY", "")),
}

# ---------------------------------------------------------------------
# Audit log — append-only, written to ~/.sg_audit.jsonl + broadcast
# ---------------------------------------------------------------------

_AUDIT_FILE = Path.home() / ".sg_audit.jsonl"
_AUDIT_LOCK = threading.Lock()
# In-memory ring buffer for /api/audit endpoint (capped at 500 entries)
_AUDIT_RING: list = []
_AUDIT_MAX = 500


def _audit(event_type: str, data: dict | None = None) -> dict:
    """Record one audit entry, persist it, and return the entry dict."""
    entry = {
        "ts": int(time.time() * 1000),
        "type": event_type,
        "data": data or {},
    }
    serialised = json.dumps(entry, separators=(",", ":"))
    with _AUDIT_LOCK:
        # Ring buffer
        _AUDIT_RING.append(entry)
        if len(_AUDIT_RING) > _AUDIT_MAX:
            _AUDIT_RING.pop(0)
        # Append to file
        try:
            with _AUDIT_FILE.open("a", encoding="utf-8") as fh:
                fh.write(serialised + "\n")
        except Exception:
            pass
    print(f"  [AUDIT] {event_type}  {','.join(str(k) for k in (data or {}).keys())}")
    # Broadcast to all connected WS clients
    _ws_broadcast({"type": "audit_event", "entry": entry})
    return entry


# ---------------------------------------------------------------------
# Key rotation manager
# ---------------------------------------------------------------------

_KEY_META_LOCK = threading.Lock()
_KEY_META: dict = {
    "anthropic": {"rotated_at": 0, "use_count": 0},
    "openai":    {"rotated_at": 0, "use_count": 0},
    "grok":      {"rotated_at": 0, "use_count": 0},
}

# Seed rotation timestamps from env so restarts don't reset the clock.
_KEY_ROTATION_TIMESTAMPS = {
    "anthropic": int(os.environ.get("SG_ANTHROPIC_ROTATED_AT", "0")),
    "openai":    int(os.environ.get("SG_OPENAI_ROTATED_AT", "0")),
    "grok":      int(os.environ.get("SG_GROK_ROTATED_AT", "0")),
}
for _k in _KEY_META:
    if _KEY_ROTATION_TIMESTAMPS[_k]:
        _KEY_META[_k]["rotated_at"] = _KEY_ROTATION_TIMESTAMPS[_k]


def _key_use(provider: str) -> None:
    """Increment use counter for a provider key."""
    with _KEY_META_LOCK:
        if provider in _KEY_META:
            _KEY_META[provider]["use_count"] += 1


def _key_stale(provider: str) -> bool:
    """Return True when the key hasn't been rotated within KEY_ROTATION_DAYS."""
    meta = _KEY_META.get(provider, {})
    rotated = meta.get("rotated_at", 0)
    if rotated == 0:
        return False  # never set — not stale, just untracked
    age_days = (time.time() * 1000 - rotated) / (86400 * 1000)
    return age_days >= KEY_ROTATION_DAYS


def _key_status_payload() -> dict:
    """Return a safe (masked) snapshot of all key metadata."""
    now_ms = int(time.time() * 1000)
    result = {}
    with _KEY_META_LOCK:
        for provider, meta in _KEY_META.items():
            raw = KEYS.get(provider, "")
            rotated = meta["rotated_at"]
            age_days = round((time.time() * 1000 - rotated) / (86400 * 1000), 1) if rotated else None
            result[provider] = {
                "set": bool(raw),
                "masked": (raw[:4] + "…" + raw[-4:]) if len(raw) > 8 else ("***" if raw else ""),
                "use_count": meta["use_count"],
                "rotated_at": rotated,
                "age_days": age_days,
                "stale": _key_stale(provider),
                "rotation_due_days": KEY_ROTATION_DAYS,
            }
    return result


def _rotate_key(provider: str, new_key: str) -> tuple[bool, str]:
    """
    Rotate an API key for the given provider.
    Returns (success, message).
    Validates basic key-format requirements (non-empty, minimum length).
    """
    if provider not in KEYS:
        return False, f"Unknown provider: {provider}"
    new_key = new_key.strip()
    if len(new_key) < 8:
        return False, "New key is too short (minimum 8 characters)"
    # Check for obviously wrong values
    if new_key in ("your-key-here", "sk-...", "xai-...", "placeholder"):
        return False, "Key looks like a placeholder — not accepted"
    old_masked = (KEYS[provider][:4] + "…" + KEYS[provider][-4:]) if len(KEYS[provider]) > 8 else "unset"
    KEYS[provider] = new_key
    os.environ[provider.upper() + "_API_KEY"] = new_key
    now_ms = int(time.time() * 1000)
    with _KEY_META_LOCK:
        _KEY_META[provider]["rotated_at"] = now_ms
        _KEY_META[provider]["use_count"] = 0
    _audit("KEY_ROTATED", {
        "provider": provider,
        "old_masked": old_masked,
        "new_masked": new_key[:4] + "…" + new_key[-4:],
        "ts": now_ms,
    })
    # Broadcast rotation event to all WS clients
    _ws_broadcast({
        "type": "key_rotated",
        "provider": provider,
        "masked": new_key[:4] + "…" + new_key[-4:],
        "ts": now_ms,
    })
    return True, f"Key for {provider} rotated successfully"


# ---------------------------------------------------------------------
# Session-token registry — one token per WS connection, rotated daily
# ---------------------------------------------------------------------

_SESSION_LOCK = threading.Lock()
_SESSIONS: dict = {}   # token → {addr, created_at, last_seen}
_SESSION_TTL = 86400   # 24 hours in seconds


def _session_create(addr) -> str:
    token = secrets.token_hex(32)
    now = time.time()
    with _SESSION_LOCK:
        _SESSIONS[token] = {"addr": str(addr), "created_at": now, "last_seen": now}
    _audit("SESSION_CREATED", {"addr": str(addr), "token_prefix": token[:8]})
    return token


def _session_touch(token: str) -> bool:
    """Update last_seen; return False if token is expired or unknown."""
    now = time.time()
    with _SESSION_LOCK:
        s = _SESSIONS.get(token)
        if not s:
            return False
        if now - s["created_at"] > _SESSION_TTL:
            del _SESSIONS[token]
            return False
        s["last_seen"] = now
    return True


def _session_expire_old() -> None:
    """Purge sessions older than TTL (called periodically)."""
    now = time.time()
    with _SESSION_LOCK:
        expired = [t for t, s in _SESSIONS.items() if now - s["created_at"] > _SESSION_TTL]
        for t in expired:
            _SESSIONS.pop(t, None)
    if expired:
        _audit("SESSIONS_EXPIRED", {"count": len(expired)})


def _session_purge_thread() -> None:
    """Background thread: expire old sessions every hour."""
    while True:
        time.sleep(3600)
        _session_expire_old()


# ---------------------------------------------------------------------
# Connected-client broadcast registry
# ---------------------------------------------------------------------

_WS_CLIENTS_LOCK = threading.Lock()
_WS_CLIENTS: list = []   # list of socket.socket
_ws_write_fn = None       # set to ws_write after that function is defined


def _ws_register(conn: socket.socket) -> None:
    with _WS_CLIENTS_LOCK:
        if conn not in _WS_CLIENTS:
            _WS_CLIENTS.append(conn)


def _ws_unregister(conn: socket.socket) -> None:
    with _WS_CLIENTS_LOCK:
        try:
            _WS_CLIENTS.remove(conn)
        except ValueError:
            pass


def _ws_broadcast(payload: dict) -> None:
    """Send a JSON payload to every currently-connected WS client."""
    with _WS_CLIENTS_LOCK:
        clients = list(_WS_CLIENTS)
    dead = []
    for c in clients:
        try:
            msg = json.dumps(payload, separators=(",", ":")).encode("utf-8")
            # _ws_write_fn is set to ws_write after that function is defined.
            if _ws_write_fn is not None:
                _ws_write_fn(c, msg)
        except Exception:
            dead.append(c)
    if dead:
        with _WS_CLIENTS_LOCK:
            for c in dead:
                try:
                    _WS_CLIENTS.remove(c)
                except ValueError:
                    pass

# ---------------------------------------------------------------------
# HTML discovery
# ---------------------------------------------------------------------


def find_html() -> str | None:
    dirs = [Path.home(), Path.cwd(), Path("/root"), Path("/var/mobile")]
    # Priority order: SGHv119 first, then earlier SGH versions, then SuperGrok named files
    pats = [
        "SGHv119.html",
        "SGHv11*.html",
        "SGH*.html",
        "SuperGrok_v119*",
        "SuperGrok_v107*",
        "SuperGrok_v10*",
        "SuperGrok*.html",
        "*.html",
    ]
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
    _key_use("anthropic")
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
    _key_use("openai")
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
    _key_use("grok")
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


# Register ws_write so _ws_broadcast (defined earlier) can call it.
_ws_write_fn = ws_write


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

    elif t in ("ai_chat", "chat_message"):
        # Agent chat: {type:"ai_chat", agent:"claude", message:"...", context:"...", history:[]}
        agent = msg.get("agent", msg.get("provider", "claude"))
        message = msg.get("message", msg.get("prompt", msg.get("content", "")))
        context = msg.get("context", "")
        history = msg.get("history", [])
        messages = history + [{"role": "user", "content": message}]
        ws_json(conn, {"type": "agent_thinking", "agent": agent, "request_id": rid, "context": context})
        text, err = route_ai(agent, messages, msg.get("model"))
        ws_json(
            conn,
            {
                "type": "ai_response",
                "agent": agent,
                "request_id": rid,
                "context": context,
                "text": text or "",
                "response": text or "",
                "error": err,
            },
        )

    elif t == "ai_code_review":
        # CodeMaster AI Fix: {type:"ai_code_review", lang:"js", code:"...", prompt:"..."}
        lang = msg.get("lang", "javascript")
        raw_code = msg.get("code", "")
        truncated = len(raw_code) > MAX_CODE_REVIEW_LENGTH
        code = raw_code[:MAX_CODE_REVIEW_LENGTH]
        prompt_text = msg.get(
            "prompt",
            f"Review this {lang} code. List errors with line numbers. "
            f"For each error provide the exact fix. Be concise.",
        )
        truncation_note = (
            f"\n\n[Note: code was truncated to {MAX_CODE_REVIEW_LENGTH} chars for review]"
            if truncated else ""
        )
        review_prompt = (
            f"Language: {lang}\n\n"
            f"```{lang}\n{code}\n```\n\n"
            f"{prompt_text}{truncation_note}"
        )
        messages = [{"role": "user", "content": review_prompt}]
        text, err = route_ai(None, messages)
        if text:
            ws_json(conn, {"type": "ai_code_review_result", "review": text, "lang": lang, "truncated": truncated})
        else:
            ws_json(
                conn,
                {
                    "type": "ai_code_review_result",
                    "review": f"# Bridge AI Error\n{err or 'No AI provider key set. Set ANTHROPIC_API_KEY, OPENAI_API_KEY, or GROK_API_KEY.'}",
                    "lang": lang,
                },
            )

    elif t == "selffix_report":
        # Self-Fixer bridge report: {type:"selffix_report", score:N, bugs:N, errors:[...]}
        score = msg.get("score", 100)
        bugs = msg.get("bugs", 0)
        errors = msg.get("errors", [])
        print(f"  [SELFFIX] score={score}% bugs={bugs} errors={len(errors)}")
        ws_json(
            conn,
            {
                "type": "selffix_ack",
                "score": score,
                "bugs": bugs,
                "ts": int(time.time() * 1000),
            },
        )

    elif t == "keys_set":
        for k, v in (msg.get("keys") or {}).items():
            if k in KEYS and v:
                ok, msg_text = _rotate_key(k, v)
                if not ok:
                    ws_json(conn, {"type": "keys_save_error", "provider": k, "error": msg_text})
        ws_json(conn, {"type": "keys_saved", "status": _key_status_payload()})

    elif t == "rotate_key":
        # Explicit single-key rotation: {type:"rotate_key", provider:"anthropic", new_key:"sk-..."}
        provider = msg.get("provider", "")
        new_key = msg.get("new_key", "")
        ok, msg_text = _rotate_key(provider, new_key)
        ws_json(conn, {
            "type": "rotate_key_result",
            "ok": ok,
            "provider": provider,
            "message": msg_text,
            "status": _key_status_payload(),
        })

    elif t == "key_status":
        # Query rotation metadata: {type:"key_status"}
        ws_json(conn, {
            "type": "key_status_result",
            "status": _key_status_payload(),
            "rotation_days": KEY_ROTATION_DAYS,
        })

    elif t == "audit_query":
        # Return recent audit entries: {type:"audit_query", limit:50}
        limit = min(int(msg.get("limit", 50)), _AUDIT_MAX)
        with _AUDIT_LOCK:
            recent = list(_AUDIT_RING[-limit:])
        ws_json(conn, {"type": "audit_result", "entries": recent, "total": len(_AUDIT_RING)})

    elif t == "health":
        ws_json(
            conn,
            {
                "type": "health_ok",
                "version": "v4.0",
                "keys": {k: bool(v) for k, v in KEYS.items()},
                "key_status": _key_status_payload(),
            },
        )

    else:
        ws_json(conn, {"type": "ack", "received": t, "ts": int(time.time() * 1000)})


def run_ws(conn: socket.socket, addr, path: str) -> None:
    print(f"[WS]  + {addr}  path={path}")
    # Issue a session token for this connection
    session_token = _session_create(addr)
    _ws_register(conn)
    # Warn immediately if any key is stale
    stale = [p for p in KEYS if KEYS[p] and _key_stale(p)]
    ws_json(
        conn,
        {
            "type": "connected",
            "version": "SuperGrok Bridge v4.0",
            "session_token": session_token,
            "keys": {k: bool(v) for k, v in KEYS.items()},
            "key_status": _key_status_payload(),
            "stale_keys": stale,
        },
    )
    if stale:
        for p in stale:
            _audit("KEY_STALE_WARN", {"provider": p, "age_days": _key_status_payload()[p]["age_days"]})
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
                # Validate session token when present (non-fatal — log only)
                try:
                    incoming = json.loads(payload.decode("utf-8", errors="replace"))
                    tok = incoming.get("session_token", "")
                    if tok and not _session_touch(tok):
                        _audit("SESSION_INVALID", {"addr": str(addr), "token_prefix": tok[:8]})
                        ws_json(conn, {"type": "session_expired", "msg": "Session token expired — reconnect to get a fresh token"})
                except Exception:
                    pass
                handle_ws_msg(conn, payload)
    except Exception as e:
        print(f"[WS]  ! {addr}  {e}")
    finally:
        _audit("SESSION_CLOSED", {"addr": str(addr), "token_prefix": session_token[:8]})
        _ws_unregister(conn)
        print(f"[WS]  - {addr}")
        try:
            conn.close()
        except Exception:
            pass


# ---------------------------------------------------------------------
# HTTP handler
# ---------------------------------------------------------------------

# Precisely match Node.js process names to avoid false positives from
# processes like 'nodemon', 'annotated', etc.
_NODE_PROC_NAMES = {"node", "node.exe"}

def _is_node_proc(proc_name: str) -> bool:
    """Return True only if proc_name is an exact Node.js executable name."""
    cleaned = proc_name.strip()
    name = cleaned.split()[0].lower() if cleaned else ""
    # Extract just the basename (e.g. '/usr/bin/node' -> 'node')
    name = name.rsplit("/", 1)[-1].rsplit("\\", 1)[-1]
    return name in _NODE_PROC_NAMES


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
        "<p style='color:#ff9800'>Place SGHv119.html (or any SuperGrok*.html) in ~/ then reload.</p>"
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

        elif path == "/api/conflicts":
            # Report port conflicts so the dashboard can display them
            try:
                r = subprocess.run(
                    ["lsof", "-t", f"-i:{PORT}"],
                    capture_output=True, text=True, timeout=3,
                )
                pids = [p.strip() for p in r.stdout.strip().splitlines() if p.strip()]
                confs = []
                for pid in pids:
                    pr = subprocess.run(
                        ["ps", "-p", pid, "-o", "comm=,pid="],
                        capture_output=True, text=True, timeout=3,
                    )
                    confs.append({"pid": pid, "proc": pr.stdout.strip()})
                http_send(conn, 200, {"port": PORT, "conflicts": confs, "has_node": any(_is_node_proc(c["proc"]) for c in confs)})
            except Exception as exc:
                http_send(conn, 200, {"port": PORT, "conflicts": [], "has_node": False, "error": str(exc)})

        elif path == "/api/key-status":
            http_send(conn, 200, {
                "status": _key_status_payload(),
                "rotation_days": KEY_ROTATION_DAYS,
            })

        elif path == "/api/audit":
            limit = 100
            with _AUDIT_LOCK:
                recent = list(_AUDIT_RING[-limit:])
            http_send(conn, 200, {"entries": recent, "total": len(_AUDIT_RING)})

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
            errors = []
            for k, v in body.items():
                ok, msg_text = _rotate_key(k, v)
                if not ok:
                    errors.append({"provider": k, "error": msg_text})
            http_send(conn, 200, {
                "saved": not errors,
                "errors": errors,
                "keys": {k: bool(v) for k, v in KEYS.items()},
                "status": _key_status_payload(),
            })

        elif path == "/api/rotate-key":
            provider = body.get("provider", "")
            new_key = body.get("new_key", body.get("key", ""))
            ok, msg_text = _rotate_key(provider, new_key)
            http_send(conn, 200 if ok else 400, {
                "ok": ok,
                "provider": provider,
                "message": msg_text,
                "status": _key_status_payload(),
            })

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
    # ------------------------------------------------------------------
    # Port conflict detection — warn if Node.js already holds port 9898
    # ------------------------------------------------------------------
    def _check_port_conflict(port: int) -> tuple:
        """Return (pid, process_name) if something already owns the port, else (None, None)."""
        try:
            # Try lsof (macOS / Linux)
            r = subprocess.run(
                ["lsof", "-t", f"-i:{port}"],
                capture_output=True, text=True, timeout=3,
            )
            if r.stdout.strip():
                for pid in r.stdout.strip().splitlines():
                    try:
                        pr = subprocess.run(
                            ["ps", "-p", pid.strip(), "-o", "comm="],
                            capture_output=True, text=True, timeout=3,
                        )
                        process_name = pr.stdout.strip().lower()
                        return pid.strip(), process_name
                    except Exception:
                        return pid.strip(), "unknown"
        except Exception:
            pass
        try:
            # Fallback: ss (Linux)
            r = subprocess.run(
                ["ss", "-tlnp", f"sport = :{port}"],
                capture_output=True, text=True, timeout=3,
            )
            if "node" in r.stdout.lower():
                return "?", "node"
        except Exception:
            pass
        return None, None

    _conflict_pid, _conflict_proc = _check_port_conflict(PORT)
    if _conflict_pid:
        _is_node = _is_node_proc(_conflict_proc or "")
        print(f"\n⚠  PORT CONFLICT DETECTED on {PORT}")
        print(f"   Process : {_conflict_proc or 'unknown'} (PID {_conflict_pid})")
        if _is_node:
            print("   Cause   : Node.js server (Unified_Server.js) already bound to this port.")
            print(f"   Fix     : Stop Node first — `kill {_conflict_pid}`")
            print("             Or set a different port: SG_PORT=9899 python3 python3_bridge.py")
        else:
            print(f"   Fix     : kill {_conflict_pid}  or set SG_PORT=<other port>")
        print()

    print("=" * 58)
    print("  SuperGrok Unified Bridge v4.0")
    print(f"  HTTP + WebSocket on single port {PORT} — no split")
    print("=" * 58)
    print(f"  Dashboard  : http://127.0.0.1:{PORT}")
    print(f"  Health     : http://127.0.0.1:{PORT}/api/health")
    print(f"  Key Status : http://127.0.0.1:{PORT}/api/key-status")
    print(f"  Audit Log  : http://127.0.0.1:{PORT}/api/audit")
    print(f"  Audit File : {_AUDIT_FILE}")
    print(f"  HTML       : {HTML_FILE or 'NOT FOUND — place SGHv119.html in ~/'}")
    print()
    print("  Claude    : " + ("ready" if KEYS["anthropic"] else "export ANTHROPIC_API_KEY=sk-ant-…"))
    print("  OpenAI    : " + ("ready" if KEYS["openai"] else "export OPENAI_API_KEY=sk-…"))
    print("  Grok      : " + ("ready" if KEYS["grok"] else "export GROK_API_KEY=xai-…"))
    print(f"  Key rotation warning after {KEY_ROTATION_DAYS} days (SG_KEY_ROTATION_DAYS)")
    print()
    print(f"  OPEN SAFARI AT: http://127.0.0.1:{PORT}")
    print("=" * 58)

    # Start background housekeeping thread for session expiry
    threading.Thread(target=_session_purge_thread, daemon=True).start()

    # Record bridge start in audit log
    _audit("BRIDGE_START", {"port": PORT, "html": HTML_FILE or "not found"})

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
            _audit("BRIDGE_STOP", {"port": PORT})
            print("\nStopped.")
            break
        except Exception as e:
            print(f"[ERR] {e}")
