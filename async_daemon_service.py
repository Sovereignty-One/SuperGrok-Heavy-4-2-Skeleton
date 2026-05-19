"""Async daemon service utilities."""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable


class AsyncDaemonService:
    """Run an async callback repeatedly until stopped."""

    def __init__(
        self,
        callback: Callable[[], Awaitable[None]],
        *,
        interval_seconds: float = 1.0,
    ):
        if interval_seconds <= 0:
            raise ValueError("interval_seconds must be greater than zero")
        self._callback = callback
        self._interval_seconds = interval_seconds
        self._running = False

    async def run(self) -> None:
        """Run the callback on an interval until stop() is called."""
        self._running = True
        while self._running:
            await self._callback()
            await asyncio.sleep(self._interval_seconds)

    def stop(self) -> None:
        """Stop the daemon loop on the next iteration."""
        self._running = False
