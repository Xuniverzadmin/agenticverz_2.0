#!/usr/bin/env python3
# capability_id: CAP-001
# Layer: L5 — Domain Engine
# AUDIENCE: INTERNAL
# Role: Outbox Processor Worker
"""
Outbox Processor Worker

Processes transactional outbox events for exactly-once external side-effects.
Uses FOR UPDATE SKIP LOCKED pattern for concurrent-safe claiming.

Features:
- Leader election via distributed locks
- Idempotent external calls (HTTP with Idempotency-Key header)
- Exponential backoff on failures
- Dead-letter after max retries
- Prometheus metrics for observability

Usage:
    # Run as worker (continuous)
    python -m app.hoc.int.worker.outbox_processor

    # One-time processing
    python -m app.hoc.int.worker.outbox_processor --once

    # With custom batch size
    python -m app.hoc.int.worker.outbox_processor --batch-size 50

Environment Variables:
    DATABASE_URL: PostgreSQL connection URL
    OUTBOX_BATCH_SIZE: Batch size (default: 20)
    OUTBOX_POLL_INTERVAL: Seconds between polls (default: 5)
    OUTBOX_MAX_RETRIES: Max retries before dead-letter (default: 5)
    OUTBOX_LOCK_TTL: Lock TTL in seconds (default: 300)
"""

import argparse
import asyncio
import hashlib
import logging
import os
import signal
import socket
import sys
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

import httpx

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.infra import FeatureIntent, RetryPolicy

# Phase-2.3: Feature Intent Declaration
# Outbox pattern enables recoverable delivery - external dispatch is idempotent
FEATURE_INTENT = FeatureIntent.RECOVERABLE_OPERATION
RETRY_POLICY = RetryPolicy.SAFE

logger = logging.getLogger("nova.worker.outbox")

# Configuration
DATABASE_URL = os.getenv("DATABASE_URL")
BATCH_SIZE = int(os.getenv("OUTBOX_BATCH_SIZE", "20"))
POLL_INTERVAL = int(os.getenv("OUTBOX_POLL_INTERVAL", "5"))
MAX_RETRIES = int(os.getenv("OUTBOX_MAX_RETRIES", "5"))
LOCK_TTL = int(os.getenv("OUTBOX_LOCK_TTL", "300"))

# Concurrency limits - prevent overwhelming external endpoints
MAX_CONCURRENT_HTTP = int(os.getenv("OUTBOX_MAX_CONCURRENT_HTTP", "10"))
HTTP_TIMEOUT = int(os.getenv("OUTBOX_HTTP_TIMEOUT", "30"))

# Worker identity
WORKER_ID = f"{socket.gethostname()}:{os.getpid()}:{uuid.uuid4().hex[:8]}"
LOCK_NAME = "m10:outbox_processor"

# Backoff settings
BASE_BACKOFF_SECONDS = 30
MAX_BACKOFF_SECONDS = 3600  # 1 hour


class OutboxProcessor:
    """Processes outbox events with exactly-once semantics."""

    def __init__(self, db_url: Optional[str] = None):
        self.db_url = db_url or DATABASE_URL
        if not self.db_url:
            raise ValueError("DATABASE_URL not configured")

        self._running = False
        self._engine = None
        self._http_client = None

    async def start(self):
        """Initialize resources."""
        from sqlmodel import create_engine

        self._engine = create_engine(self.db_url, pool_pre_ping=True)
        # Use connection limits to prevent overwhelming external endpoints
        limits = httpx.Limits(
            max_connections=MAX_CONCURRENT_HTTP,
            max_keepalive_connections=MAX_CONCURRENT_HTTP // 2,
        )
        self._http_client = httpx.AsyncClient(
            timeout=float(HTTP_TIMEOUT),
            limits=limits,
        )
        self._running = True
        self._semaphore = asyncio.Semaphore(MAX_CONCURRENT_HTTP)

    async def stop(self):
        """Cleanup resources."""
        self._running = False
        if self._http_client:
            await self._http_client.aclose()

    def acquire_lock(self) -> bool:
        """Acquire distributed lock for this worker."""
        from sqlalchemy import text
        from sqlmodel import Session

        try:
            with Session(self._engine) as session:
                result = session.execute(
                    text("SELECT m10_recovery.acquire_lock(:lock_name, :holder_id, :ttl)"),
                    {"lock_name": LOCK_NAME, "holder_id": WORKER_ID, "ttl": LOCK_TTL},
                )
                acquired = result.scalar()
                session.commit()

                if acquired:
                    logger.debug(f"Acquired lock {LOCK_NAME}")
                    self._update_metric("m10_outbox_lock_acquired_total", 1)
                else:
                    self._update_metric("m10_outbox_lock_failed_total", 1)

                return bool(acquired)
        except Exception as e:
            logger.error(f"Failed to acquire lock: {e}")
            return False

    def release_lock(self) -> bool:
        """Release distributed lock."""
        from sqlalchemy import text
        from sqlmodel import Session

        try:
            with Session(self._engine) as session:
                result = session.execute(
                    text("SELECT m10_recovery.release_lock(:lock_name, :holder_id)"),
                    {"lock_name": LOCK_NAME, "holder_id": WORKER_ID},
                )
                released = result.scalar()
                session.commit()
                return bool(released)
        except Exception as e:
            logger.error(f"Failed to release lock: {e}")
            return False

    def extend_lock(self) -> bool:
        """Extend lock TTL while processing."""
        from sqlalchemy import text
        from sqlmodel import Session

        try:
            with Session(self._engine) as session:
                result = session.execute(
                    text("SELECT m10_recovery.extend_lock(:lock_name, :holder_id, :ttl)"),
                    {"lock_name": LOCK_NAME, "holder_id": WORKER_ID, "ttl": LOCK_TTL},
                )
                extended = result.scalar()
                session.commit()
                return bool(extended)
        except Exception as e:
            logger.warning(f"Failed to extend lock: {e}")
            return False

    def claim_events(self, batch_size: int = BATCH_SIZE) -> List[Dict[str, Any]]:
        """
        Claim a batch of unprocessed outbox events.

        Uses FOR UPDATE SKIP LOCKED for concurrent-safe claiming.
        """
        from sqlalchemy import text
        from sqlmodel import Session

        try:
            with Session(self._engine) as session:
                result = session.execute(
                    text("SELECT * FROM m10_recovery.claim_outbox_events(:processor_id, :batch_size)"),
                    {"processor_id": WORKER_ID, "batch_size": batch_size},
                )
                rows = result.fetchall()
                session.commit()

                events = []
                for row in rows:
                    events.append(
                        {
                            "id": row[0],
                            "aggregate_type": row[1],
                            "aggregate_id": row[2],
                            "event_type": row[3],
                            "payload": row[4],
                            "retry_count": row[5],
                        }
                    )

                if events:
                    logger.info(f"Claimed {len(events)} outbox events")
                    self._update_metric("m10_outbox_claimed_total", len(events))

                return events

        except Exception as e:
            logger.error(f"Failed to claim events: {e}")
            return []

    async def process_event(self, event: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """
        Process a single outbox event with concurrency limiting.

        Returns:
            Tuple of (success, error_message)
        """
        event_type = event["event_type"]
        payload = event["payload"]

        try:
            # Use semaphore to limit concurrent HTTP requests
            async with self._semaphore:
                # Route to appropriate handler
                if event_type.startswith("http:"):
                    return await self._handle_http_event(event)
                elif event_type.startswith("webhook:"):
                    return await self._handle_webhook_event(event)
                elif event_type.startswith("notify:"):
                    return await self._handle_notification_event(event)
                else:
                    logger.warning(f"Unknown event type: {event_type}")
                    return True, None  # Skip unknown types

        except Exception as e:
            logger.error(f"Error processing event {event['id']}: {e}")
            return False, str(e)

    async def _handle_http_event(self, event: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """Handle HTTP call events with idempotency."""
        payload = event["payload"]
        url = payload.get("url")
        method = payload.get("method", "POST").upper()
        headers = payload.get("headers", {})
        body = payload.get("body")

        if not url:
            return False, "Missing URL in payload"

        # Add idempotency key header
        idempotency_key = self._generate_idempotency_key(event)
        headers["Idempotency-Key"] = idempotency_key
        headers["X-Outbox-Event-Id"] = str(event["id"])

        try:
            response = await self._http_client.request(
                method=method,
                url=url,
                headers=headers,
                json=body if body else None,
            )

            if response.status_code < 400:
                logger.info(f"HTTP {method} {url} succeeded: {response.status_code}")
                return True, None
            elif response.status_code in (409, 422):
                # Idempotency conflict or validation - treat as success
                logger.info(f"HTTP {method} {url} idempotent skip: {response.status_code}")
                return True, None
            else:
                error = f"HTTP {response.status_code}: {response.text[:200]}"
                logger.warning(f"HTTP {method} {url} failed: {error}")
                return False, error

        except httpx.TimeoutException:
            return False, "Request timeout"
        except httpx.RequestError as e:
            return False, f"Request error: {e}"

    async def _handle_webhook_event(self, event: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """Handle webhook events."""
        payload = event["payload"]
        url = payload.get("webhook_url")
        data = payload.get("data", {})

        if not url:
            return False, "Missing webhook_url in payload"

        # Add standard webhook headers
        headers = {
            "Content-Type": "application/json",
            "X-Webhook-Event": event["event_type"],
            "X-Webhook-Timestamp": datetime.now(timezone.utc).isoformat(),
            "X-Idempotency-Key": self._generate_idempotency_key(event),
        }

        try:
            response = await self._http_client.post(
                url=url,
                headers=headers,
                json=data,
            )

            if response.status_code < 400:
                return True, None
            else:
                return False, f"Webhook failed: {response.status_code}"

        except Exception as e:
            return False, f"Webhook error: {e}"

    async def _handle_notification_event(self, event: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """Handle notification events (email, Slack, etc.)."""
        payload = event["payload"]
        channel = payload.get("channel", "log")

        if channel == "log":
            # Just log the notification (for testing)
            logger.info(f"Notification: {payload.get('message', 'No message')}")
            return True, None

        elif channel == "slack":
            webhook_url = payload.get("slack_webhook_url") or os.getenv("SLACK_WEBHOOK_URL")
            if not webhook_url:
                return False, "No Slack webhook URL configured"

            try:
                response = await self._http_client.post(
                    url=webhook_url,
                    json={"text": payload.get("message", "Notification from AOS")},
                )
                return (
                    response.status_code == 200,
                    None if response.status_code == 200 else f"Slack: {response.status_code}",
                )
            except Exception as e:
                return False, f"Slack error: {e}"

        else:
            logger.warning(f"Unknown notification channel: {channel}")
            return True, None  # Skip unknown channels

    def complete_event(self, event_id: int, success: bool, error: Optional[str] = None):
        """Mark event as processed or schedule retry."""
        from sqlalchemy import text
        from sqlmodel import Session

        try:
            with Session(self._engine) as session:
                session.execute(
                    text("SELECT m10_recovery.complete_outbox_event(:event_id, :processor_id, :success, :error)"),
                    {
                        "event_id": event_id,
                        "processor_id": WORKER_ID,
                        "success": success,
                        "error": error,
                    },
                )
                session.commit()

                if success:
                    self._update_metric("m10_outbox_processed_total", 1)
                else:
                    self._update_metric("m10_outbox_failed_total", 1)

        except Exception as e:
            logger.error(f"Failed to complete event {event_id}: {e}")

    def _generate_idempotency_key(self, event: Dict[str, Any]) -> str:
        """Generate deterministic idempotency key for an event."""
        key_parts = [
            str(event["id"]),
            event["aggregate_type"],
            event["aggregate_id"],
            event["event_type"],
        ]
        key_string = ":".join(key_parts)
        return hashlib.sha256(key_string.encode()).hexdigest()[:32]

    def _update_metric(self, name: str, value: float):
        """Update Prometheus metric (if available)."""
        try:
            from app.metrics import get_metric

            metric = get_metric(name)
            if metric:
                metric.inc(value)
        except Exception:
            pass  # Metrics optional

    async def process_batch(self, batch_size: int = BATCH_SIZE) -> Dict[str, int]:
        """Process a single batch of events."""
        results = {"claimed": 0, "processed": 0, "failed": 0, "skipped": 0}

        # Claim events
        events = self.claim_events(batch_size)
        results["claimed"] = len(events)

        if not events:
            return results

        # Process each event
        for event in events:
            success, error = await self.process_event(event)

            if success:
                self.complete_event(event["id"], success=True)
                results["processed"] += 1
            else:
                self.complete_event(event["id"], success=False, error=error)
                results["failed"] += 1

            # Extend lock periodically
            if results["processed"] % 10 == 0:
                self.extend_lock()

        return results

    async def run(self, once: bool = False, batch_size: int = BATCH_SIZE):
        """
        Main processing loop.

        Args:
            once: If True, process one batch and exit
            batch_size: Number of events to claim per batch
        """
        await self.start()

        try:
            while self._running:
                # Acquire lock
                if not self.acquire_lock():
                    logger.info("Another worker has the lock, waiting...")
                    await asyncio.sleep(POLL_INTERVAL)
                    continue

                try:
                    results = await self.process_batch(batch_size)

                    if results["claimed"] > 0:
                        logger.info(
                            f"Batch complete: claimed={results['claimed']}, "
                            f"processed={results['processed']}, failed={results['failed']}"
                        )

                    if once:
                        break

                    # Short sleep if we processed events, longer if idle
                    sleep_time = 1 if results["claimed"] > 0 else POLL_INTERVAL
                    await asyncio.sleep(sleep_time)

                finally:
                    self.release_lock()

        finally:
            await self.stop()


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="Process outbox events for exactly-once delivery")
    parser.add_argument(
        "--once",
        action="store_true",
        help="Process one batch and exit",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=BATCH_SIZE,
        help=f"Batch size (default: {BATCH_SIZE})",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging",
    )

    args = parser.parse_args()

    # Configure logging
    log_level = logging.DEBUG if args.debug else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )

    # Handle graceful shutdown
    processor = OutboxProcessor()

    def shutdown_handler(_signum, _frame):
        logger.info("Shutdown signal received...")
        processor._running = False

    signal.signal(signal.SIGTERM, shutdown_handler)
    signal.signal(signal.SIGINT, shutdown_handler)

    # Run
    logger.info(f"Starting outbox processor (worker_id={WORKER_ID})")
    asyncio.run(processor.run(once=args.once, batch_size=args.batch_size))
    logger.info("Outbox processor stopped")


if __name__ == "__main__":
    main()
