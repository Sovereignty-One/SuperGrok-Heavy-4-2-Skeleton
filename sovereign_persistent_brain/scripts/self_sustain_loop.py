"""Background loop placeholder for the persistent brain."""

from __future__ import annotations

import asyncio


async def self_sustain_loop(poll_interval: float = 60.0) -> None:
    while True:
        await asyncio.sleep(poll_interval)
