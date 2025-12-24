"""
Publisher interface for events. Uses pluggable adapters (nats_adapter).
If no adapter is configured, falls back to logging publisher.
"""

import logging
import os
from typing import Any, Dict

logger = logging.getLogger("nova.events.publisher")


class BasePublisher:
    """Base class for event publishers."""

    def publish(self, topic: str, payload: Dict[str, Any]):
        raise NotImplementedError


class LoggingPublisher(BasePublisher):
    """Fallback publisher that logs events."""

    def publish(self, topic: str, payload: Dict[str, Any]):
        logger.info("publish_event", extra={"topic": topic, "payload": payload})


def get_publisher() -> BasePublisher:
    """Get configured event publisher."""
    adapter = os.getenv("EVENT_PUBLISHER", "logging").lower()

    if adapter == "nats":
        try:
            from .nats_adapter import NatsAdapter

            return NatsAdapter()
        except Exception:
            logger.exception("nats_adapter_load_failed; falling back to logging")
            return LoggingPublisher()

    return LoggingPublisher()
