"""Configuration loading utilities."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any


class ConfigLoader:
    """Load configuration from JSON files and environment variables."""

    def __init__(self, config_path: str | Path | None = None):
        self.config_path = Path(config_path) if config_path else None

    def load(self, config_path: str | Path | None = None) -> dict[str, Any]:
        """Load and return configuration data from a JSON file."""
        path = Path(config_path) if config_path else self.config_path
        if path is None:
            return {}
        if not path.exists():
            raise FileNotFoundError(f"Configuration file not found: {path}")

        with path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)

        if not isinstance(data, dict):
            raise ValueError("Top-level JSON config must be an object")
        return data

    @staticmethod
    def load_env(prefix: str = "") -> dict[str, str]:
        """Return environment variables, optionally filtered by prefix."""
        if not prefix:
            return dict(os.environ)
        return {
            key[len(prefix):]: value
            for key, value in os.environ.items()
            if key.startswith(prefix)
        }


def load_config(config_path: str | Path) -> dict[str, Any]:
    """Convenience helper for loading JSON configuration files."""
    return ConfigLoader(config_path).load()
