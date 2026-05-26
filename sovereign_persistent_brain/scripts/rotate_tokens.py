"""Rotate the brain token counter."""

from __future__ import annotations

from ._brain_store import load_brain, save_brain


def rotate_tokens() -> dict:
    brain = load_brain()
    brain["token_rotation"] = int(brain.get("token_rotation", 0)) + 1
    save_brain(brain)
    return {"status": "ok", "token_rotation": brain["token_rotation"]}
