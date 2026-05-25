"""Persist brain state and audit logs."""

from __future__ import annotations

from typing import Any

from ._brain_store import load_brain, save_brain, signer


def persist_brain(state: dict[str, Any] | None, new_logs: list[dict[str, Any]] | None = None) -> dict:
    brain = load_brain()
    if state is not None:
        brain["state"] = state
    if new_logs:
        brain.setdefault("scarlog", []).extend(new_logs)
    return save_brain(brain)
