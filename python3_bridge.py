from __future__ import annotations

import os

DEFAULT_AI_MAX_TOKENS = 131072


def _resolve_ai_max_tokens(value: str | None) -> int:
    if not value:
        return DEFAULT_AI_MAX_TOKENS
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return DEFAULT_AI_MAX_TOKENS
    return parsed if parsed > 0 else DEFAULT_AI_MAX_TOKENS


AI_MAX_TOKENS = _resolve_ai_max_tokens(os.getenv("SG_MAX_TOKENS"))