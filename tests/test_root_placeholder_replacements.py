"""Tests for root-level service utility modules."""

from __future__ import annotations

import asyncio
import importlib
import json
import logging

import pytest

from async_daemon_service import AsyncDaemonService
from circuit_breaker import CircuitBreaker, CircuitBreakerOpenError
from config_loader import ConfigLoader, load_config
from logger_service import LoggerService
from prometheus_instrumentation import PrometheusInstrumentation
from reconnection_strategies import ExponentialBackoffStrategy, FixedDelayStrategy, JitteredBackoffStrategy


def test_config_loader_reads_json(tmp_path):
    config_file = tmp_path / "config.json"
    config_file.write_text(json.dumps({"name": "supergrok"}), encoding="utf-8")

    loader = ConfigLoader(config_file)
    assert loader.load()["name"] == "supergrok"
    assert load_config(config_file)["name"] == "supergrok"


def test_logger_service_returns_logger():
    logger = LoggerService.get_logger("test-root-logger")
    assert logger.name == "test-root-logger"


def test_logger_service_honors_log_level_env(monkeypatch):
    monkeypatch.setenv("LOG_LEVEL", "debug")

    logger = LoggerService.get_logger("test-root-logger-env")

    assert logger.level == logging.DEBUG


def test_reconnection_strategies_return_expected_ranges():
    fixed = FixedDelayStrategy(delay_seconds=2.0, max_delay_seconds=5.0)
    backoff = ExponentialBackoffStrategy(base_delay_seconds=1.0, multiplier=2.0, max_delay_seconds=4.0)
    jitter = JitteredBackoffStrategy(base_delay_seconds=1.0, multiplier=2.0, max_delay_seconds=4.0)

    assert fixed.next_delay(3) == 2.0
    assert backoff.next_delay(3) == 4.0
    assert 0.0 <= jitter.next_delay(3) <= 4.0


def test_prometheus_instrumentation_noop_or_collects():
    instrumentation = PrometheusInstrumentation()
    instrumentation.increment_counter("test_counter", "A counter for tests")
    instrumentation.observe_histogram("test_histogram", "A histogram for tests", 1.23)
    with instrumentation.time_operation("test_timer", "A timer for tests"):
        pass


def test_circuit_breaker_opens_after_threshold():
    breaker = CircuitBreaker(failure_threshold=1, recovery_timeout_seconds=0.2)

    def fail_once() -> None:
        raise ValueError("boom")

    with pytest.raises(ValueError):
        breaker.call(fail_once)

    with pytest.raises(CircuitBreakerOpenError):
        breaker.call(lambda: "ok")


def test_async_daemon_resets_running_when_callback_raises():
    calls = 0

    async def callback() -> None:
        nonlocal calls
        calls += 1
        raise ValueError("boom")

    service = AsyncDaemonService(callback, interval_seconds=0.01)

    with pytest.raises(ValueError):
        asyncio.run(service.run())

    assert calls == 1
    assert service._running is False


def test_python_bridge_invalid_max_tokens_falls_back(monkeypatch):
    monkeypatch.setenv("SG_MAX_TOKENS", "2k")

    import python3_bridge

    bridge = importlib.reload(python3_bridge)

    assert bridge.AI_MAX_TOKENS == 131072


def test_python_bridge_valid_max_tokens_is_used(monkeypatch):
    monkeypatch.setenv("SG_MAX_TOKENS", "2048")

    import python3_bridge

    bridge = importlib.reload(python3_bridge)

    assert bridge.AI_MAX_TOKENS == 2048


def test_bridge_entrypoints_import():
    import bridge.python3_bridge as bridge_python
    import bridge.serve_dashboard as bridge_dashboard

    assert bridge_python.AI_MAX_TOKENS == 131072
    assert callable(bridge_python.main)
    assert callable(bridge_dashboard.main)
