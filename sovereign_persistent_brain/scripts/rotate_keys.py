"""Rotate the persistent brain signing key."""

from __future__ import annotations

from ._brain_store import signer


def rotate_keys() -> dict:
    signer.rotate()
    return {"status": "ok", "rotated": True}
