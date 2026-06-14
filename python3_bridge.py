from __future__ import annotations

import importlib
import os
from types import ModuleType

_impl: ModuleType = importlib.import_module("bridge.python3_bridge")

DEFAULT_AI_MAX_TOKENS = getattr(_impl, "DEFAULT_AI_MAX_TOKENS", 131072)
AI_MAX_TOKENS = getattr(_impl, "AI_MAX_TOKENS", DEFAULT_AI_MAX_TOKENS)
BridgeHandler = getattr(_impl, "BridgeHandler")
build_health_payload = getattr(_impl, "build_health_payload")
build_connect_payload = getattr(_impl, "build_connect_payload")
main = getattr(_impl, "main")
_parse_ai_max_tokens = getattr(_impl, "_parse_ai_max_tokens", lambda: DEFAULT_AI_MAX_TOKENS)

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
