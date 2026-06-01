"""Shared helpers for the persistent brain compatibility layer."""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import secrets
import threading
from pathlib import Path
from typing import Any

_LOCK = threading.Lock()
_BRAIN_FILE = Path.home() / ".sg_brain.json"
_SIGNING_KEY_FILE = Path.home() / ".sg_brain_signing.key"
_AGENTS_FILE = Path("brain") / "agents.json"


def _default_brain() -> dict[str, Any]:
    return {"state": {}, "scarlog": [], "agents": [], "events": [], "errors": []}


def load_brain() -> dict[str, Any]:
    with _LOCK:
        if not _BRAIN_FILE.exists():
            return _default_brain()
        try:
            data = json.loads(_BRAIN_FILE.read_text("utf-8"))
        except Exception:
            return _default_brain()
        if not isinstance(data, dict):
            return _default_brain()
        data.setdefault("state", {})
        data.setdefault("scarlog", [])
        data.setdefault("agents", [])
        data.setdefault("events", [])
        data.setdefault("errors", [])
        return data


def save_brain(data: dict[str, Any]) -> dict[str, Any]:
    with _LOCK:
        _BRAIN_FILE.parent.mkdir(parents=True, exist_ok=True)
        payload = json.dumps(data, indent=2, sort_keys=True, ensure_ascii=False)
        tmp = _BRAIN_FILE.with_suffix(".json.tmp")
        tmp.write_text(payload, "utf-8")
        os.replace(tmp, _BRAIN_FILE)
        return data


def load_signing_key() -> bytes:
    with _LOCK:
        if _SIGNING_KEY_FILE.exists():
            try:
                raw = bytes.fromhex(_SIGNING_KEY_FILE.read_text("utf-8").strip())
                if raw:
                    return raw
            except (ValueError, OSError):
                # Invalid/corrupt key file or unreadable file; fall back to generating a new key below.
                pass
        key = secrets.token_bytes(32)
        _SIGNING_KEY_FILE.write_text(key.hex(), "utf-8")
        return key


def save_signing_key(key: bytes) -> None:
    with _LOCK:
        _SIGNING_KEY_FILE.write_text(key.hex(), "utf-8")


def ensure_agents_file(agents: list[dict[str, Any]]) -> None:
    _AGENTS_FILE.parent.mkdir(parents=True, exist_ok=True)
    _AGENTS_FILE.write_text(json.dumps(agents, indent=2, sort_keys=True, ensure_ascii=False), "utf-8")


class Signer:
    def __init__(self) -> None:
        self._key = load_signing_key()

    def rotate(self) -> bytes:
        self._key = secrets.token_bytes(32)
        save_signing_key(self._key)
        return self._key

    def sign(self, data: bytes) -> bytes:
        return hmac.new(self._key, data, hashlib.sha256).digest()


signer = Signer()
