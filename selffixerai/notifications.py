"""Notifications Module

Provides a lightweight notifier that logs and prints structured events
for the self-fixer AI system.
"""

import json
import logging
import time

logger = logging.getLogger(__name__)


class Notifier:
    """Sends structured notifications for self-fixer events."""

    def send_notification(self, event: str, data: dict) -> None:
        """Log and print a notification event with a timestamp."""
        entry = {
            "ts": int(time.time() * 1000),
            "event": event,
            "data": data,
        }
        logger.warning("NOTIFY %s: %s", event, json.dumps(data))
        print(json.dumps(entry))
