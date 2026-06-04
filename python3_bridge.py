"""Compatibility wrapper for the actual bridge server implementation."""

from bridge.python3_bridge import (  # noqa: F401
    AI_MAX_TOKENS,
    DEFAULT_AI_MAX_TOKENS,
    BridgeHandler,
    build_health_payload,
    main,
    _resolve_ai_max_tokens,
)

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
