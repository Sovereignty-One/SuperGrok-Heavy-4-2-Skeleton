"""Prometheus metrics wrappers with graceful no-op fallback."""

from __future__ import annotations

from contextlib import contextmanager
from time import monotonic

try:
    from prometheus_client import CollectorRegistry, Counter, Histogram
except ImportError:  # pragma: no cover - optional dependency
    CollectorRegistry = Counter = Histogram = None


class PrometheusInstrumentation:
    """Collect application metrics when prometheus_client is available."""

    def __init__(self, registry=None):
        self.enabled = Counter is not None and Histogram is not None
        self.registry = registry or (CollectorRegistry() if self.enabled else None)
        self._counters: dict[str, object] = {}
        self._histograms: dict[str, object] = {}

    def increment_counter(self, name: str, description: str, amount: float = 1.0) -> None:
        """Increment a named counter metric."""
        if not self.enabled:
            return
        metric = self._counters.get(name)
        if metric is None:
            metric = Counter(name, description, registry=self.registry)
            self._counters[name] = metric
        metric.inc(amount)

    def observe_histogram(self, name: str, description: str, value: float) -> None:
        """Record a value in a histogram metric."""
        if not self.enabled:
            return
        metric = self._histograms.get(name)
        if metric is None:
            metric = Histogram(name, description, registry=self.registry)
            self._histograms[name] = metric
        metric.observe(value)

    @contextmanager
    def time_operation(self, histogram_name: str, description: str):
        """Measure operation duration and submit it to a histogram."""
        start = monotonic()
        try:
            yield
        finally:
            self.observe_histogram(histogram_name, description, monotonic() - start)
