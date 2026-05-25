"""Normalize error handling for the persistent brain."""

from __future__ import annotations

import traceback
from typing import Any

from ._brain_store import load_brain, save_brain


def handle_error(error: Any, context: str = "") -> dict:
    message = str(error)
    record = {
        "context": context,
        "error": message,
        "type": type(error).__name__ if not isinstance(error, str) else "Error",
        "traceback": traceback.format_exc() if not isinstance(error, str) else "",
    }
    brain = load_brain()
    brain.setdefault("errors", []).append(record)
    save_brain(brain)
    return record
