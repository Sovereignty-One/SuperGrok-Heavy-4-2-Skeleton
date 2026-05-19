"""Simple circuit breaker implementation for fault-tolerant calls."""

from __future__ import annotations

from dataclasses import dataclass, field
from time import monotonic
from typing import Callable, TypeVar

T = TypeVar("T")


class CircuitBreakerOpenError(RuntimeError):
    """Raised when a call is attempted while the breaker is open."""


@dataclass
class CircuitBreaker:
    """Track failures and temporarily stop executing failing operations."""

    failure_threshold: int = 5
    recovery_timeout_seconds: float = 30.0
    _failure_count: int = 0
    _opened_at: float | None = None
    _last_error: Exception | None = field(default=None, init=False, repr=False)

    def _is_open(self) -> bool:
        if self._opened_at is None:
            return False
        return monotonic() - self._opened_at < self.recovery_timeout_seconds

    def _record_failure(self, error: Exception) -> None:
        self._failure_count += 1
        self._last_error = error
        if self._failure_count >= self.failure_threshold:
            self._opened_at = monotonic()

    def _record_success(self) -> None:
        self._failure_count = 0
        self._opened_at = None
        self._last_error = None

    def call(self, operation: Callable[..., T], *args, **kwargs) -> T:
        """Execute an operation unless the breaker is currently open."""
        if self._is_open():
            raise CircuitBreakerOpenError("Circuit breaker is open")

        try:
            result = operation(*args, **kwargs)
        except Exception as error:
            self._record_failure(error)
            raise
        else:
            self._record_success()
            return result

    @property
    def last_error(self) -> Exception | None:
        return self._last_error
