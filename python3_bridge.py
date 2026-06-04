"""Compatibility wrapper for the actual bridge server implementation."""

from __future__ import annotations

import os

from bridge.python3_bridge import (  # noqa: F401
    DEFAULT_AI_MAX_TOKENS,
    BridgeHandler,
    build_health_payload,
    main,
    _resolve_ai_max_tokens,
)

# Dynamically compute AI_MAX_TOKENS to support environment variable changes.
AI_MAX_TOKENS = _resolve_ai_max_tokens(os.getenv("SG_MAX_TOKENS"))

__all__ = [
    "AI_MAX_TOKENS",
    "DEFAULT_AI_MAX_TOKENS",
    "BridgeHandler",
    "build_health_payload",
    "main",
    "_resolve_ai_max_tokens",
]


if __name__ == "__main__":
    main()
