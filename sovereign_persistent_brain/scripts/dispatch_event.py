"""Record events in the persistent brain."""

from __future__ import annotations

from typing import Any

from ._brain_store import load_brain, save_brain


def dispatch_event(event_type: str, data: dict[str, Any]) -> dict:
    event = {"type": event_type, "data": data}
    brain = load_brain()
    brain.setdefault("events", []).append(event)
    save_brain(brain)
    return event
