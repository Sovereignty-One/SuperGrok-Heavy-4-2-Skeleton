from __future__ import annotations

import os

from bridge.python3_bridge import (  # noqa: F401
    AI_MAX_TOKENS,
    DEFAULT_AI_MAX_TOKENS,
    BridgeHandler,
    build_connect_payload,
    build_health_payload,
    main,
    _parse_ai_max_tokens,
)

# Keep the compatibility layer in sync with runtime environment changes.
AI_MAX_TOKENS = _parse_ai_max_tokens()

__all__ = [
    "AI_MAX_TOKENS",
    "DEFAULT_AI_MAX_TOKENS",
    "BridgeHandler",
    "build_connect_payload",
    "build_health_payload",
    "main",
    "_parse_ai_max_tokens",
]


if __name__ == "__main__":
    main()
