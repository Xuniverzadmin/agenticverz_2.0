# capability_id: CAP-001
# Layer: L3 — Boundary Adapter
# Product: system-wide
# Temporal:
#   Trigger: worker
#   Execution: async
# Role: NATS event streaming adapter
# Callers: event publisher
# Allowed Imports: L4, L6
# Forbidden Imports: L1, L2, L5
# Reference: Event System

"""
NATS adapter stub. Does not actually require a NATS server by default.
If NATS is configured in env (NATS_URL), this adapter will attempt a connect.
In many test/dev setups this remains a logging stub.
"""

import json
import logging
import os

from .publisher import BasePublisher

logger = logging.getLogger("nova.events.nats")


class NatsAdapter(BasePublisher):
    """NATS event publisher adapter."""

    def __init__(self):
        self.nats_url = os.getenv("NATS_URL", "")
        self.nc = None
        self.loop = None

        if not self.nats_url:
            logger.info("NatsAdapter initialized in stub mode (no NATS_URL)")
        else:
            # lazy import to avoid hard dependency
            try:
                import asyncio

                from nats.aio.client import Client as NATS

                self.loop = asyncio.new_event_loop()
                self.nc = NATS()
                self.loop.run_until_complete(self.nc.connect(servers=[self.nats_url]))
                logger.info("NatsAdapter connected", extra={"nats_url": self.nats_url})
            except Exception:
                logger.exception("NatsAdapter_connect_failed; operating as logging stub")
                self.nc = None

    def publish(self, topic: str, payload: dict):
        """Publish event to NATS or log if stub mode."""
        if self.nc and self.loop:
            try:
                data = json.dumps(payload).encode()
                self.loop.run_until_complete(self.nc.publish(topic.encode(), data))
                logger.info("nats_publish_ok", extra={"topic": topic})
            except Exception:
                logger.exception("nats_publish_failed", extra={"topic": topic})
        else:
            logger.info("nats_stub_publish", extra={"topic": topic, "payload": payload})
