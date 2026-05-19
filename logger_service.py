"""Centralized logger creation helpers."""

from __future__ import annotations

import logging
import os

_DEFAULT_FORMAT = "%(asctime)s %(levelname)s [%(name)s] %(message)s"


def configure_logger(
    logger: logging.Logger,
    *,
    level: int = logging.INFO,
    fmt: str = _DEFAULT_FORMAT,
) -> logging.Logger:
    """Configure a logger instance with a default stream handler."""
    logger.setLevel(level)

    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter(fmt))
        logger.addHandler(handler)

    logger.propagate = False
    return logger


def get_logger(name: str = "supergrok", *, level: int | None = None) -> logging.Logger:
    """Return a configured logger, deriving level from LOG_LEVEL when unset."""
    logger = logging.getLogger(name)
    if level is None:
        env_level = os.getenv("LOG_LEVEL", "INFO").upper()
        level = logging._nameToLevel.get(env_level, logging.INFO)
    return configure_logger(logger, level=level)


class LoggerService:
    """Small service wrapper for module-level logger retrieval."""

    @staticmethod
    def get_logger(name: str = "supergrok", *, level: int | None = None) -> logging.Logger:
        return get_logger(name=name, level=level)
