"""Load persistent brain state from disk."""

from __future__ import annotations

from ._brain_store import load_brain


def hydrate_brain() -> dict:
    return load_brain()
