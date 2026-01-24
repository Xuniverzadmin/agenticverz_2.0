# Layer: L3 — Boundary Adapter
# Product: system-wide
# Temporal:
#   Trigger: api|worker
#   Execution: async
# Role: Redis pub/sub event adapter
# Callers: event publisher
# Allowed Imports: L4, L6
# Forbidden Imports: L1, L2, L5
# Reference: Event System

"""
Redis Pub/Sub Event Publisher Adapter.

Publishes events to Redis channel 'aos.events' for realtime consumption
by Ops Console and other subscribers.

DESIGN CONSTRAINTS (Non-Negotiable):
1. Fire-and-forget (no retries, no persistence in v1)
2. Fail-fast if misconfigured (no silent fallback)
3. Schema-stable events (standard envelope)
4. Observable at runtime

Usage:
    publisher = RedisPublisher()
    publisher.publish("INCIDENT_CREATED", {"incident_id": "123", ...})
"""

import json
import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from .publisher import BasePublisher

logger = logging.getLogger("nova.events.redis")

# Channel for all AOS events
AOS_EVENTS_CHANNEL = "aos.events"


class RedisPublisher(BasePublisher):
    """
    Redis Pub/Sub event publisher.

    Publishes events to a single channel with typed event envelopes.
    Fails fast if REDIS_URL is not configured.
    """

    def __init__(self):
        self.redis_url = os.getenv("REDIS_URL", "")
        self.channel = AOS_EVENTS_CHANNEL
        self._client: Optional[Any] = None

        if not self.redis_url:
            raise RuntimeError(
                "EVENT_PUBLISHER=redis requires REDIS_URL to be set. "
                "Either set REDIS_URL or use EVENT_PUBLISHER=logging"
            )

        # Import redis lazily to avoid hard dependency
        try:
            import redis
        except ImportError:
            raise RuntimeError("redis package not installed. Install with: pip install redis")

        # Connect to Redis
        try:
            self._client = redis.Redis.from_url(
                self.redis_url,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
            )
            # Verify connection
            self._client.ping()
            logger.info(
                "RedisPublisher connected",
                extra={
                    "channel": self.channel,
                    "redis_url": self._sanitize_url(self.redis_url),
                },
            )
        except Exception as e:
            raise RuntimeError(f"Failed to connect to Redis at {self._sanitize_url(self.redis_url)}: {e}")

    def _sanitize_url(self, url: str) -> str:
        """Remove password from URL for logging."""
        if "@" in url:
            # Format: redis://user:pass@host:port  # pragma: allowlist secret
            prefix = url.split("@")[0]
            suffix = url.split("@")[1]
            if ":" in prefix:
                # Has password
                proto_user = prefix.rsplit(":", 1)[0]
                return f"{proto_user}:***@{suffix}"
        return url

    def publish(self, event_type: str, payload: Dict[str, Any]) -> None:
        """
        Publish event to Redis Pub/Sub channel.

        Event envelope format:
        {
            "event_type": "INCIDENT_CREATED",
            "timestamp": "2025-01-09T12:32:11Z",
            "source": "guard",
            "payload": { ...original payload... }
        }

        Args:
            event_type: Type of event (e.g., INCIDENT_CREATED, RECOVERY_SUGGESTED)
            payload: Event payload dictionary
        """
        if not self._client:
            logger.error("redis_publish_failed: client not initialized")
            return

        # Build event envelope
        event = {
            "event_type": event_type,
            "timestamp": payload.get("timestamp") or datetime.now(timezone.utc).isoformat(),
            "source": payload.get("source", "aos"),
            "payload": payload,
        }

        try:
            message = json.dumps(event, default=str)
            subscriber_count = self._client.publish(self.channel, message)

            logger.info(
                "redis_publish_ok",
                extra={
                    "event_type": event_type,
                    "channel": self.channel,
                    "subscribers": subscriber_count,
                },
            )
        except Exception as e:
            # Log error but don't crash - fire-and-forget semantics
            logger.error(
                "redis_publish_failed",
                extra={
                    "event_type": event_type,
                    "channel": self.channel,
                    "error": str(e),
                },
            )

    def close(self) -> None:
        """Close Redis connection."""
        if self._client:
            self._client.close()
            logger.info("RedisPublisher connection closed")
