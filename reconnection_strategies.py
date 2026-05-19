"""Reconnection strategy helpers for resilient network clients."""

from __future__ import annotations

import random
from dataclasses import dataclass


@dataclass(frozen=True)
class ReconnectionStrategy:
    """Base class for reconnect delay calculations."""

    max_delay_seconds: float = 30.0

    def next_delay(self, attempt: int) -> float:
        """Return delay before the next reconnect attempt."""
        raise NotImplementedError


@dataclass(frozen=True)
class FixedDelayStrategy(ReconnectionStrategy):
    """Return the same reconnect delay for every attempt."""

    delay_seconds: float = 1.0

    def next_delay(self, attempt: int) -> float:
        _ = attempt
        return min(max(self.delay_seconds, 0.0), self.max_delay_seconds)


@dataclass(frozen=True)
class ExponentialBackoffStrategy(ReconnectionStrategy):
    """Use exponential growth to space retries."""

    base_delay_seconds: float = 1.0
    multiplier: float = 2.0

    def next_delay(self, attempt: int) -> float:
        safe_attempt = max(attempt, 0)
        delay = self.base_delay_seconds * (self.multiplier ** safe_attempt)
        return min(max(delay, 0.0), self.max_delay_seconds)


@dataclass(frozen=True)
class JitteredBackoffStrategy(ExponentialBackoffStrategy):
    """Exponential backoff with full jitter to avoid synchronized retries."""

    def next_delay(self, attempt: int) -> float:
        ceiling = super().next_delay(attempt)
        return random.uniform(0.0, ceiling)
