"""Async Event Bus for inter-agent communication.

Sovereign-aware: supports both in-process and Redis backends,
full SCAR audit logging, async context manager, and clean shutdown.
"""

import asyncio
import json
import logging
import os
from typing import Any, Callable, Dict, Optional, List
from fixers.persist_brain import persist_brain

logger = logging.getLogger(__name__)

class AsyncEventBus:
    def __init__(self, brain_state: Optional[dict] = None, redis_url: Optional[str] = None, name: str = "event_bus"):
        self.brain_state = brain_state or {}
        self.name = name
        self._redis_url = redis_url or os.getenv("REDIS_URL", "")
        self._redis_client: Optional[Any] = None
        self._local_queue: asyncio.Queue = asyncio.Queue()
        self._handlers: Dict[str, Callable] = {}
        self._running = False
        self._processor_task: Optional[asyncio.Task] = None

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
        self._processor_task = asyncio.create_task(self._process_loop())
        self._audit("event_bus_started")

    async def stop(self) -> None:
        if not self._running:
            return
        self._running = False
        if self._processor_task:
            self._processor_task.cancel()
            try:
                await self._processor_task
            except asyncio.CancelledError:
                pass
        self._audit("event_bus_stopped")

    async def _get_redis(self):
        if self._redis_client is None and self._redis_url:
            try:
                import redis.asyncio as redis
                self._redis_client = redis.from_url(self._redis_url)
                logger.info("[%s] Connected to Redis at %s", self.name, self._redis_url)
            except Exception as exc:
                logger.warning("[%s] Redis unavailable (%s) — using local queue", self.name, exc)
        return self._redis_client

    async def send_event(self, agent_id: str, task: Dict[str, Any]) -> None:
        if not isinstance(agent_id, str) or not agent_id:
            raise ValueError("agent_id must be a non-empty string")
        if not isinstance(task, dict):
            raise ValueError("task must be a dictionary")
        event = {"agent_id": agent_id, "task": task, "timestamp": __import__("time").time()}
        redis = await self._get_redis()
        if redis:
            try:
                await redis.lpush("sg:events", json.dumps(event))
                logger.debug("[%s] Sent Redis event to %s", self.name, agent_id)
            except Exception as exc:
                logger.warning("[%s] Redis send failed — falling back to local queue: %s", self.name, exc)
                await self._local_queue.put(event)
        else:
            await self._local_queue.put(event)
        self._audit("event_sent", {"agent_id": agent_id, "task_type": task.get("type", "unknown")})

    def register_handler(self, agent_id: str, handler: Callable) -> None:
        if not asyncio.iscoroutinefunction(handler):
            raise TypeError("handler must be an async function")
        self._handlers[agent_id] = handler
        logger.info("[%s] Registered handler for agent '%s'", self.name, agent_id)

    async def _process_loop(self) -> None:
        logger.info("[%s] Event processor started", self.name)
        redis = await self._get_redis()
        while self._running:
            try:
                if redis:
                    raw = await redis.brpop("sg:events", timeout=1)
                    if raw is None:
                        continue
                    event = json.loads(raw[1])
                else:
                    event = await asyncio.wait_for(self._local_queue.get(), timeout=1.0)
            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                break
            except Exception as exc:
                logger.error("[%s] Event receive error: %s", self.name, exc)
                continue
            agent_id = event.get("agent_id", "")
            task = event.get("task", {})
            handler = self._handlers.get(agent_id)
            if handler is None:
                logger.warning("[%s] No handler for agent '%s' — dropping event", self.name, agent_id)
                continue
            try:
                await handler(task)
                self._audit("event_processed", {"agent_id": agent_id})
            except Exception as exc:
                logger.error("[%s] Handler '%s' failed: %s", self.name, agent_id, exc, exc_info=True)
                self._audit("event_handler_error", {"agent_id": agent_id, "error": str(exc)})

    def _audit(self, event_type: str, extra: dict = None):
        if self.brain_state:
            try:
                persist_brain(self.brain_state.get("state", {}), new_logs=[{"type": "event_bus", "bus_name": self.name, "event": event_type, **(extra or {})}])
            except Exception:
                pass