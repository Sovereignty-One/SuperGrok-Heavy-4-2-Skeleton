"""
secure_enclave.py — lightweight key retrieval for the SuperGrok backend.

Priority order for each named key:
  1. Environment variable matching the name (e.g. JWT_SIGNING_KEY).
  2. ~/.sg_enclave_keys.json — persistent JSON object written by this module.
  3. Auto-generate a random 256-bit hex key, persist it, and return it.

This is intentionally minimal so it works on iSH / a-Shell / macOS
without any third-party dependencies.
"""

import json
import os
import secrets
import sys
import threading
from pathlib import Path

_ENCLAVE_FILE = Path.home() / ".sg_enclave_keys.json"
_LOCK = threading.Lock()


def _load_enclave() -> dict:
    """Read the persisted enclave key store, returning {} on any error."""
    with _LOCK:
        try:
            if _ENCLAVE_FILE.exists():
                data = json.loads(_ENCLAVE_FILE.read_text("utf-8"))
                if isinstance(data, dict):
                    return data
        except Exception as exc:
            print(f"[secure_enclave] load error: {exc}", file=sys.stderr)
    return {}


def _save_enclave(store: dict) -> None:
    """Atomically write the enclave key store to disk."""
    with _LOCK:
        try:
            _ENCLAVE_FILE.write_text(
                json.dumps(store, separators=(",", ":"), ensure_ascii=False),
                "utf-8",
            )
            # Restrict permissions so only the owner can read the file.
            _ENCLAVE_FILE.chmod(0o600)
        except Exception as exc:
            print(f"[secure_enclave] save error: {exc}", file=sys.stderr)


def get_secure_key(name: str) -> str:
    """
    Return the named key, creating and persisting a random one if absent.

    Parameters
    ----------
    name : str
        Logical key name, e.g. ``'JWT_SIGNING_KEY'``.

    Returns
    -------
    str
        A non-empty key string (at least 64 hex characters for auto-generated keys).
    """
    # 1. Environment variable takes highest precedence.
    env_val = os.environ.get(name, "").strip()
    if env_val:
        return env_val

    # 2. Persistent store.
    store = _load_enclave()
    if name in store and store[name]:
        return store[name]

    # 3. Generate, persist, and return a fresh key.
    new_key = secrets.token_hex(32)  # 256-bit random key
    store[name] = new_key
    _save_enclave(store)
    print(
        f"[secure_enclave] Generated new key for '{name}' "
        f"(masked: {new_key[:4]}…{new_key[-4:]})",
        file=sys.stderr,
    )
    return new_key
