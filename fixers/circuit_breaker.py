"""Simple circuit breaker implementation for fault-tolerant calls."""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from time import monotonic
from typing import Callable, TypeVar, Optional, Any
from fixers.persist_brain import persist_brain

logger = logging.getLogger(__name__)
T = TypeVar("T")

class CircuitBreakerOpenError(RuntimeError):
    pass

@dataclass
class CircuitBreaker:
    failure_threshold: int = 5
    recovery_timeout_seconds: float = 30.0
    brain_state: Optional[dict] = None
    name: str = "default"
    _failure_count: int = field(default=0, init=False, repr=False)
    _opened_at: float | None = field(default=None, init=False, repr=False)
    _last_error: Exception | None = field(default=None, init=False, repr=False)
    _state: str = field(default="closed", init=False, repr=False)

    def _is_open(self) -> bool:
        if self._state == "closed":
            return False
        if self._state == "half_open":
            return False
        if self._opened_at is None:
            return False
        return monotonic() - self._opened_at < self.recovery_timeout_seconds

    def _record_failure(self, error: Exception) -> None:
        self._failure_count += 1
        self._last_error = error
        if self._failure_count >= self.failure_threshold:
            self._opened_at = monotonic()
            self._state = "open"
            self._audit("circuit_opened", {"error": str(error)})

    def _record_success(self) -> None:
        self._failure_count = 0
        self._opened_at = None
        self._last_error = None
        if self._state == "half_open":
            self._state = "closed"
            self._audit("circuit_closed")

    def _audit(self, event: str, extra: dict = None):
        if self.brain_state:
            try:
                persist_brain(self.brain_state.get("state", {}), new_logs=[{"type": "circuit_breaker", "name": self.name, "event": event, "state": self._state, **(extra or {})}])
            except Exception:
                pass

    async def call_async(self, operation: Callable[..., Any], *args, **kwargs) -> T:
        if self._is_open():
            raise CircuitBreakerOpenError(f"Circuit breaker '{self.name}' is open")
        try:
            if asyncio.iscoroutinefunction(operation):
                result = await operation(*args, **kwargs)
            else:
                result = operation(*args, **kwargs)
        except Exception as error:
            self._record_failure(error)
            raise
        else:
            self._record_success()
            return result

    def call(self, operation: Callable[..., T], *args, **kwargs) -> T:
        if self._is_open():
            raise CircuitBreakerOpenError(f"Circuit breaker '{self.name}' is open")
        try:
            result = operation(*args, **kwargs)
        except Exception as error:
            self._record_failure(error)
            raise
        else:
            self._record_success()
            return result

    def reset(self):
        self._failure_count = 0
        self._opened_at = None
        self._last_error = None
        self._state = "closed"
        self._audit("circuit_manual_reset")

    @property
    def state(self) -> str:
        return self._state

    @property
    def last_error(self) -> Exception | None:
        return self._last_error

    @property
    def is_open(self) -> bool:
        return self._state == "open"