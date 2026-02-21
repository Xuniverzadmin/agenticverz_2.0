# capability_id: CAP-009
# Layer: L3 — Boundary Adapter
# Product: system-wide
# Temporal:
#   Trigger: api|worker
#   Execution: async
# Role: Event publishing abstraction
# Callers: services, workers
# Allowed Imports: L4, L6
# Forbidden Imports: L1, L2, L5
# Reference: Event System

"""
Publisher interface for events. Uses pluggable adapters.

DESIGN CONSTRAINTS:
1. Adapter pattern (redis, nats, logging)
2. Fail-fast if misconfigured (no silent fallback)
3. Observable at runtime

Supported adapters:
- redis: Redis Pub/Sub (recommended for realtime)
- nats: NATS messaging
- logging: Fallback that logs events (default)
"""

import logging
import os
from typing import Any, Dict, Optional

logger = logging.getLogger("nova.events.publisher")

# Singleton publisher instance
_publisher_instance: Optional["BasePublisher"] = None


class BasePublisher:
    """Base class for event publishers."""

    def publish(self, topic: str, payload: Dict[str, Any]) -> None:
        raise NotImplementedError

    def close(self) -> None:
        """Close any connections. Override in subclasses."""
        pass


class LoggingPublisher(BasePublisher):
    """Fallback publisher that logs events."""

    def __init__(self):
        logger.info("LoggingPublisher initialized (events logged, not streamed)")

    def publish(self, topic: str, payload: Dict[str, Any]) -> None:
        logger.info("publish_event", extra={"topic": topic, "payload": payload})


def get_publisher() -> BasePublisher:
    """
    Get configured event publisher.

    FAIL-FAST: If adapter is misconfigured, raises RuntimeError.
    No silent fallback to logging for non-logging adapters.

    Returns:
        Configured publisher instance

    Raises:
        RuntimeError: If adapter is unknown or misconfigured
    """
    global _publisher_instance

    # Return cached instance if available
    if _publisher_instance is not None:
        return _publisher_instance

    adapter = os.getenv("EVENT_PUBLISHER", "logging").lower()

    if adapter == "redis":
        from .redis_publisher import RedisPublisher

        _publisher_instance = RedisPublisher()
        logger.info("[BOOT] EventPublisher=redis channel=aos.events")
        return _publisher_instance

    if adapter == "nats":
        from .nats_adapter import NatsAdapter

        _publisher_instance = NatsAdapter()
        logger.info("[BOOT] EventPublisher=nats")
        return _publisher_instance

    if adapter == "logging":
        _publisher_instance = LoggingPublisher()
        logger.info("[BOOT] EventPublisher=logging (events not streamed)")
        return _publisher_instance

    # Unknown adapter - fail fast
    raise RuntimeError(f"Unknown EVENT_PUBLISHER={adapter}. Valid options: redis, nats, logging")


def reset_publisher() -> None:
    """Reset publisher instance (for testing)."""
    global _publisher_instance
    if _publisher_instance:
        _publisher_instance.close()
    _publisher_instance = None
