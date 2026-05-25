"""Notifications Module

Provides a lightweight, sovereign-aware notifier with both sync and async
support. All events are optionally persisted to the SCAR audit chain.
"""

import json
import logging
import time
import asyncio
from typing import Optional, Dict, Any
from fixers.persist_brain import persist_brain

logger = logging.getLogger(__name__)

class Notifier:
    def __init__(self, brain_state: Optional[dict] = None, log_level: int = logging.INFO, enable_stdout: bool = True, enable_audit: bool = True):
        self.brain_state = brain_state or {}
        self.enable_stdout = enable_stdout
        self.enable_audit = enable_audit
        self._last_event = None
        self._last_ts = 0.0
        logger.setLevel(log_level)

    def send_notification(self, event: str, data: Dict[str, Any], level: int = logging.INFO, dedup_window: float = 2.0) -> None:
        asyncio.run(self._send_notification_async(event, data, level, dedup_window))

    async def send_notification_async(self, event: str, data: Dict[str, Any], level: int = logging.INFO, dedup_window: float = 2.0) -> None:
        if not isinstance(event, str) or not event:
            raise ValueError("event must be a non-empty string")
        if not isinstance(data, dict):
            raise ValueError("data must be a dictionary")
        now = time.time()
        if event == self._last_event and (now - self._last_ts) < dedup_window:
            return
        self._last_event = event
        self._last_ts = now
        entry = {"ts": int(now * 1000), "iso": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now)), "event": event, "data": data}
        logger.log(level, "NOTIFY %s: %s", event, json.dumps(data, default=str))
        if self.enable_stdout:
            print(json.dumps(entry, indent=2))
        if self.enable_audit and self.brain_state:
            try:
                await asyncio.to_thread(persist_brain, self.brain_state.get("state", {}), new_logs=[{"type": "notification", "event": event, "data": data, "timestamp": entry["iso"]}])
            except Exception as e:
                logger.error("Failed to persist notification to SCAR: %s", e)