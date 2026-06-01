"""Async event bus for inter-agent communication.

Supports an in-process asyncio queue by default. When REDIS_URL is set in
the environment the bus uses Redis pub/sub so agents running in separate
processes can communicate.
"""

import asyncio
import json
import logging
import os
from typing import Any, Callable, Dict, Optional

logger = logging.getLogger(__name__)

# Optional Redis support
_redis_client: Optional[Any] = None
_REDIS_URL = os.getenv("REDIS_URL", "")

# In-process fallback queue (used when Redis is not configured)
_local_queue: asyncio.Queue = asyncio.Queue()

# Registered handlers: agent_id -> coroutine function
_handlers: Dict[str, Callable] = {}


async def _get_redis():
    """Return a redis.asyncio client, creating it on first call."""
    global _redis_client
    if _redis_client is None and _REDIS_URL:
        try:
            import redis.asyncio as aioredis  # redis>=4.2 ships redis.asyncio; drop the aioredis package

            _redis_client = await aioredis.from_url(_REDIS_URL)
            logger.info("Event bus connected to Redis at %s", _REDIS_URL)
        except Exception as exc:
            logger.warning(
                "Redis unavailable (%s); using in-process queue", exc
            )
    return _redis_client


async def send_event(agent_id: str, task: Dict[str, Any]) -> None:
    """Enqueue a task for *agent_id*.

    Args:
        agent_id: Identifier for the target agent (e.g. ``"judge"``,
            ``"ai_router"``).
        task: Arbitrary task payload dictionary.
    """
    event = {"agent_id": agent_id, "task": task}
    redis = await _get_redis()
    if redis:
        try:
            await redis.lpush("sg:events", json.dumps(event))
            logger.debug("Sent Redis event to %s: %s", agent_id, task)
            return
        except Exception as exc:
            logger.warning("Redis send failed (%s); falling back to queue", exc)
    await _local_queue.put(event)
    logger.debug("Sent local event to %s: %s", agent_id, task)


def register_handler(agent_id: str, handler: Callable) -> None:
    """Register a coroutine *handler* to process tasks for *agent_id*."""
    _handlers[agent_id] = handler
    logger.info("Registered handler for agent '%s'", agent_id)


async def process_events() -> None:
    """Continuously dequeue and dispatch events to registered handlers.

    Runs until the current task is cancelled.  Each event is dispatched to
    the handler registered for its ``agent_id``; unrecognised agents are
    logged and skipped.
    """
    logger.info("Event bus processing loop started")
    redis = await _get_redis()

    while True:
        try:
            if redis:
                raw = await redis.brpop("sg:events", timeout=1)
                if raw is None:
                    continue
                event = json.loads(raw[1])
            else:
                event = await asyncio.wait_for(_local_queue.get(), timeout=1.0)
        except asyncio.TimeoutError:
            continue
        except asyncio.CancelledError:
            logger.info("Event bus processing loop cancelled")
            raise

        agent_id = event.get("agent_id", "")
        task = event.get("task", {})
        handler = _handlers.get(agent_id)
        if handler is None:
            logger.warning("No handler for agent '%s'; dropping event", agent_id)
            continue
        try:
            await handler(task)
        except Exception as exc:
            logger.error(
                "Handler for '%s' raised an error: %s", agent_id, exc,
                exc_info=True,
            )
