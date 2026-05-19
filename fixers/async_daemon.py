"""Async daemon service utilities."""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Awaitable, Callable
from typing import Optional
from fixers.persist_brain import persist_brain

logger = logging.getLogger(__name__)

class AsyncDaemonService:
    def __init__(self, callback: Callable[[], Awaitable[None]], *, interval_seconds: float = 1.0, brain_state: Optional[dict] = None, name: str = "daemon"):
        if interval_seconds <= 0:
            raise ValueError("interval_seconds must be greater than zero")
        self._callback = callback
        self._interval_seconds = interval_seconds
        self._brain_state = brain_state or {}
        self._name = name
        self._running = False
        self._task: Optional[asyncio.Task] = None

    async def __aenter__(self):
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.stop()
        return False

    async def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._run_loop())
        if self._brain_state:
            persist_brain(self._brain_state.get("state", {}), new_logs=[{"type": "daemon_started", "name": self._name, "interval": self._interval_seconds}])
        logger.info(f"[{self._name}] Daemon started (interval={self._interval_seconds}s)")

    async def _run_loop(self) -> None:
        try:
            while self._running:
                try:
                    await self._callback()
                except Exception as e:
                    logger.error(f"[{self._name}] Callback error: {e}")
                await asyncio.sleep(self._interval_seconds)
        finally:
            self._running = False
            logger.info(f"[{self._name}] Daemon stopped")

    async def stop(self) -> None:
        if not self._running:
            return
        self._running = False
        if self._task:
            try:
                await asyncio.wait_for(self._task, timeout=5.0)
            except asyncio.TimeoutError:
                self._task.cancel()
                try:
                    await self._task
                except asyncio.CancelledError:
                    pass
        if self._brain_state:
            persist_brain(self._brain_state.get("state", {}), new_logs=[{"type": "daemon_stopped", "name": self._name}])

    def is_running(self) -> bool:
        return self._running