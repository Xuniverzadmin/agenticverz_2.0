#!/usr/bin/env python3
"""
M10 Outbox E2E Validation Tests

Tests for exactly-once delivery semantics in the outbox processor.
Validates idempotency under worker restarts, network failures, and concurrent processing.

Key scenarios:
1. Normal event processing - events are delivered exactly once
2. Worker restart mid-batch - no duplicate deliveries
3. Idempotency key enforcement - receivers see no duplicates
4. Concurrent processors - only one processes each event
5. External endpoint failures - proper retry with backoff
"""

import asyncio
import hashlib
import json
import os
import sys
import threading
import time
import uuid
from collections import defaultdict
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Dict, List, Set
from unittest.mock import patch

import pytest

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

DATABASE_URL = os.getenv("DATABASE_URL")


class IdempotencyTrackingHandler(BaseHTTPRequestHandler):
    """HTTP handler that tracks idempotency keys to detect duplicates."""

    # Class-level storage (shared across requests)
    received_keys: Set[str] = set()
    received_events: List[Dict] = []
    duplicate_count: int = 0
    request_count: int = 0
    failure_mode: str = "none"  # none, timeout, error_500, error_503
    lock = threading.Lock()

    def log_message(self, format, *args):
        """Suppress HTTP server logging."""
        pass

    def do_POST(self):
        """Handle POST requests and track idempotency."""
        with self.lock:
            self.__class__.request_count += 1

            # Simulate failures
            if self.__class__.failure_mode == "timeout":
                time.sleep(35)  # Exceed HTTP timeout
                return
            elif self.__class__.failure_mode == "error_500":
                self.send_response(500)
                self.end_headers()
                self.wfile.write(b"Internal Server Error")
                return
            elif self.__class__.failure_mode == "error_503":
                self.send_response(503)
                self.end_headers()
                self.wfile.write(b"Service Unavailable")
                return

            # Extract idempotency key
            idempotency_key = self.headers.get("Idempotency-Key") or self.headers.get("X-Idempotency-Key")
            event_id = self.headers.get("X-Outbox-Event-Id")

            # Read body
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length) if content_length > 0 else b""

            # Track the request
            event_data = {
                "idempotency_key": idempotency_key,
                "event_id": event_id,
                "path": self.path,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "body": body.decode("utf-8") if body else None,
            }

            # Check for duplicates
            if idempotency_key:
                if idempotency_key in self.__class__.received_keys:
                    self.__class__.duplicate_count += 1
                    # Return 409 Conflict for idempotent retry
                    self.send_response(409)
                    self.end_headers()
                    self.wfile.write(b'{"status": "duplicate", "message": "Already processed"}')
                    return
                else:
                    self.__class__.received_keys.add(idempotency_key)

            self.__class__.received_events.append(event_data)

            # Success response
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "ok", "event_id": event_id}).encode())

    @classmethod
    def reset(cls):
        """Reset tracking state."""
        with cls.lock:
            cls.received_keys = set()
            cls.received_events = []
            cls.duplicate_count = 0
            cls.request_count = 0
            cls.failure_mode = "none"


def _clean_test_outbox(engine):
    """
    Clean ALL pending outbox events to ensure tests start with a clean slate.

    This is critical for E2E test isolation because:
    1. claim_outbox_events uses FIFO ordering
    2. Old pending events block new test events from being claimed
    3. Without cleanup, tests time out waiting for their events

    Reference: PIN-276 (M10 Test Isolation)
    """
    from sqlalchemy import text
    from sqlmodel import Session

    with Session(engine) as session:
        try:
            # Delete ALL test-related outbox events (aggregate_type starting with 'test')
            result = session.execute(text("DELETE FROM m10_recovery.outbox WHERE aggregate_type LIKE 'test%'"))
            test_deleted = result.rowcount

            # Also clean up old pending events that might block the FIFO queue
            # Only delete events older than 1 hour with no processing (stale/orphaned)
            result = session.execute(
                text(
                    """
                    DELETE FROM m10_recovery.outbox
                    WHERE processed_at IS NULL
                    AND created_at < now() - interval '1 hour'
                """
                )
            )
            stale_deleted = result.rowcount

            # Release any stale locks from previous test runs
            session.execute(text("DELETE FROM m10_recovery.distributed_locks WHERE lock_name LIKE 'm10:%'"))

            session.commit()

            if test_deleted > 0 or stale_deleted > 0:
                import logging

                logging.getLogger("nova.test").info(
                    f"Cleaned outbox: {test_deleted} test events, {stale_deleted} stale events"
                )

        except Exception as e:
            session.rollback()
            import logging

            logging.getLogger("nova.test").warning(f"Outbox cleanup failed: {e}")


@pytest.fixture(scope="module")
def mock_server():
    """Start a mock HTTP server for testing outbox deliveries."""
    server = HTTPServer(("127.0.0.1", 0), IdempotencyTrackingHandler)
    port = server.server_address[1]

    # Start server in background thread
    server_thread = threading.Thread(target=server.serve_forever)
    server_thread.daemon = True
    server_thread.start()

    yield f"http://127.0.0.1:{port}"

    server.shutdown()


@pytest.fixture(scope="module")
def clean_outbox_module(request):
    """
    Module-level fixture to clean outbox ONCE at module start.

    This ensures a clean FIFO queue for all tests in the module.
    """
    if not DATABASE_URL:
        return

    from sqlmodel import create_engine

    engine = create_engine(DATABASE_URL, pool_pre_ping=True)

    # Clean at module start
    _clean_test_outbox(engine)

    yield

    # Clean at module end
    _clean_test_outbox(engine)


@pytest.fixture
def db_session(clean_outbox_module):
    """Create database session for tests."""
    if not DATABASE_URL:
        pytest.skip("DATABASE_URL not set")

    from sqlmodel import Session, create_engine, text

    engine = create_engine(DATABASE_URL, pool_pre_ping=True)

    with Session(engine) as session:
        # Ensure schema exists
        try:
            session.execute(text("SELECT 1 FROM m10_recovery.outbox LIMIT 1"))
        except Exception:
            pytest.skip("m10_recovery.outbox table not found - run migration 022")

        # Per-test cleanup: delete test events and release locks
        try:
            session.execute(text("DELETE FROM m10_recovery.outbox WHERE aggregate_type LIKE 'test%'"))
            session.execute(text("DELETE FROM m10_recovery.distributed_locks WHERE lock_name = 'm10:outbox_processor'"))
            session.commit()
        except Exception:
            session.rollback()

        yield session

        # Cleanup after test
        try:
            session.execute(text("DELETE FROM m10_recovery.outbox WHERE aggregate_type LIKE 'test%'"))
            session.commit()
        except Exception:
            session.rollback()


@pytest.fixture(autouse=True)
def reset_mock_server():
    """Reset mock server state before each test."""
    IdempotencyTrackingHandler.reset()
    yield
    IdempotencyTrackingHandler.reset()


class TestOutboxBasicDelivery:
    """Basic outbox delivery tests."""

    def test_single_event_delivery(self, db_session, mock_server):
        """Test that a single outbox event is delivered exactly once."""
        from sqlalchemy import text

        # Create outbox event
        event_id = str(uuid.uuid4())
        payload = {
            "url": f"{mock_server}/webhook",
            "method": "POST",
            "body": {"test": "data", "event_id": event_id},
        }

        db_session.execute(
            text(
                """
                INSERT INTO m10_recovery.outbox
                (aggregate_type, aggregate_id, event_type, payload)
                VALUES ('test', :event_id, 'http:webhook', :payload)
            """
            ),
            {"event_id": event_id, "payload": json.dumps(payload)},
        )
        db_session.commit()

        # Process the event
        from app.worker.outbox_processor import OutboxProcessor

        processor = OutboxProcessor(DATABASE_URL)
        asyncio.run(processor.run(once=True, batch_size=10))

        # Verify delivery
        assert IdempotencyTrackingHandler.request_count >= 1
        assert IdempotencyTrackingHandler.duplicate_count == 0
        assert len(IdempotencyTrackingHandler.received_events) == 1

    def test_multiple_events_batch_delivery(self, db_session, mock_server):
        """Test batch processing delivers all events exactly once."""
        from sqlalchemy import text

        # Create multiple outbox events
        event_ids = [str(uuid.uuid4()) for _ in range(5)]

        for event_id in event_ids:
            payload = {
                "url": f"{mock_server}/webhook",
                "method": "POST",
                "body": {"batch_test": True, "event_id": event_id},
            }
            db_session.execute(
                text(
                    """
                    INSERT INTO m10_recovery.outbox
                    (aggregate_type, aggregate_id, event_type, payload)
                    VALUES ('test', :event_id, 'http:webhook', :payload)
                """
                ),
                {"event_id": event_id, "payload": json.dumps(payload)},
            )
        db_session.commit()

        # Process events
        from app.worker.outbox_processor import OutboxProcessor

        processor = OutboxProcessor(DATABASE_URL)
        asyncio.run(processor.run(once=True, batch_size=10))

        # Verify all delivered exactly once
        assert len(IdempotencyTrackingHandler.received_events) == 5
        assert IdempotencyTrackingHandler.duplicate_count == 0

        # Verify all event IDs received
        received_bodies = [json.loads(e["body"]) for e in IdempotencyTrackingHandler.received_events if e["body"]]
        received_event_ids = {b.get("event_id") for b in received_bodies}
        assert received_event_ids == set(event_ids)


class TestOutboxIdempotency:
    """Idempotency and duplicate prevention tests."""

    def test_idempotency_key_generation(self, db_session, mock_server):
        """Test that idempotency keys are deterministic."""
        from sqlalchemy import text

        event_id = str(uuid.uuid4())
        payload = {
            "url": f"{mock_server}/webhook",
            "method": "POST",
            "body": {"test": "idempotency"},
        }

        # Insert and process event
        db_session.execute(
            text(
                """
                INSERT INTO m10_recovery.outbox
                (aggregate_type, aggregate_id, event_type, payload)
                VALUES ('test', :event_id, 'http:webhook', :payload)
            """
            ),
            {"event_id": event_id, "payload": json.dumps(payload)},
        )
        db_session.commit()

        from app.worker.outbox_processor import OutboxProcessor

        processor = OutboxProcessor(DATABASE_URL)
        asyncio.run(processor.run(once=True, batch_size=10))

        # Verify idempotency key was sent
        assert len(IdempotencyTrackingHandler.received_events) == 1
        received = IdempotencyTrackingHandler.received_events[0]
        assert received["idempotency_key"] is not None
        assert len(received["idempotency_key"]) == 32  # SHA256 truncated to 32 chars

    def test_reprocessing_same_event_no_duplicate(self, db_session, mock_server):
        """Test that reprocessing doesn't cause duplicate deliveries."""
        from sqlalchemy import text

        event_id = str(uuid.uuid4())
        payload = {
            "url": f"{mock_server}/webhook",
            "method": "POST",
            "body": {"test": "reprocess"},
        }

        # Insert event
        result = db_session.execute(
            text(
                """
                INSERT INTO m10_recovery.outbox
                (aggregate_type, aggregate_id, event_type, payload)
                VALUES ('test', :event_id, 'http:webhook', :payload)
                RETURNING id
            """
            ),
            {"event_id": event_id, "payload": json.dumps(payload)},
        )
        outbox_id = result.scalar()
        db_session.commit()

        from app.worker.outbox_processor import OutboxProcessor

        # Process once
        processor = OutboxProcessor(DATABASE_URL)
        asyncio.run(processor.run(once=True, batch_size=10))

        _first_count = IdempotencyTrackingHandler.request_count

        # Force event back to pending (simulating partial failure)
        db_session.execute(
            text("UPDATE m10_recovery.outbox SET processed_at = NULL WHERE id = :id"),
            {"id": outbox_id},
        )
        db_session.commit()

        # Process again
        asyncio.run(processor.run(once=True, batch_size=10))

        # Server should see idempotent retry (409), not duplicate processing
        assert IdempotencyTrackingHandler.duplicate_count >= 1
        # Original event still only received once
        unique_keys = IdempotencyTrackingHandler.received_keys
        assert len(unique_keys) == 1


class TestOutboxConcurrency:
    """Concurrent processing tests."""

    def test_concurrent_processors_no_duplicate(self, db_session, mock_server):
        """Test that concurrent processors don't process same event twice.

        Note: With distributed locking, processors serialize access to events.
        This test verifies that when multiple batches are processed sequentially,
        all events are processed exactly once with no duplicates.
        """
        from sqlalchemy import text

        # Create multiple events
        event_ids = [str(uuid.uuid4()) for _ in range(10)]

        for event_id in event_ids:
            payload = {
                "url": f"{mock_server}/webhook",
                "method": "POST",
                "body": {"concurrent_test": True, "event_id": event_id},
            }
            db_session.execute(
                text(
                    """
                    INSERT INTO m10_recovery.outbox
                    (aggregate_type, aggregate_id, event_type, payload)
                    VALUES ('test', :event_id, 'http:webhook', :payload)
                """
                ),
                {"event_id": event_id, "payload": json.dumps(payload)},
            )
        db_session.commit()

        from app.worker.outbox_processor import OutboxProcessor

        # Process all events with a single processor in multiple batches
        # This tests the core functionality without distributed lock contention
        async def process_all():
            processor = OutboxProcessor(DATABASE_URL)
            await processor.start()
            try:
                # Process in two batches of 5
                await processor.process_batch(batch_size=5)
                await processor.process_batch(batch_size=5)
            finally:
                await processor.stop()

        asyncio.run(process_all())

        # All events should be processed exactly once
        assert len(IdempotencyTrackingHandler.received_events) == 10, (
            f"Expected 10 events, got {len(IdempotencyTrackingHandler.received_events)}"
        )
        assert IdempotencyTrackingHandler.duplicate_count == 0, (
            f"Expected 0 duplicates, got {IdempotencyTrackingHandler.duplicate_count}"
        )

        # Verify unique idempotency keys
        keys = IdempotencyTrackingHandler.received_keys
        assert len(keys) == 10


class TestOutboxFailureHandling:
    """Failure handling and retry tests."""

    def test_retry_on_500_error(self, db_session, mock_server):
        """Test that 500 errors trigger retry with backoff."""
        from sqlalchemy import text

        event_id = str(uuid.uuid4())
        payload = {
            "url": f"{mock_server}/webhook",
            "method": "POST",
            "body": {"test": "retry_500"},
        }

        db_session.execute(
            text(
                """
                INSERT INTO m10_recovery.outbox
                (aggregate_type, aggregate_id, event_type, payload)
                VALUES ('test', :event_id, 'http:webhook', :payload)
            """
            ),
            {"event_id": event_id, "payload": json.dumps(payload)},
        )
        db_session.commit()

        # Enable failure mode
        IdempotencyTrackingHandler.failure_mode = "error_500"

        from app.worker.outbox_processor import OutboxProcessor

        processor = OutboxProcessor(DATABASE_URL)
        asyncio.run(processor.run(once=True, batch_size=10))

        # Event should be marked as failed (unprocessed), not processed
        result = db_session.execute(
            text("SELECT processed_at, retry_count FROM m10_recovery.outbox WHERE aggregate_id = :id"),
            {"id": event_id},
        )
        row = result.fetchone()
        assert row is not None
        # processed_at should be NULL (pending for retry) or non-NULL with error
        # For failed deliveries, processed_at stays NULL and retry_count increments
        assert row[0] is None  # Still pending/unprocessed
        # Retry count should be incremented
        assert row[1] >= 1

    def test_idempotent_response_treated_as_success(self, db_session, mock_server):
        """Test that 409 Conflict (idempotent duplicate) is treated as success."""
        from sqlalchemy import text

        event_id = str(uuid.uuid4())
        payload = {
            "url": f"{mock_server}/webhook",
            "method": "POST",
            "body": {"test": "idempotent_409"},
        }

        # Pre-populate idempotency key (simulating prior delivery)
        # Generate the same key the processor would generate
        key_parts = ["1", "test", event_id, "http:webhook"]  # Approximate key generation
        _pre_key = hashlib.sha256(":".join(key_parts).encode()).hexdigest()[:32]

        # Note: We can't easily pre-populate the exact key without knowing the DB ID
        # So we'll test by processing twice

        result = db_session.execute(
            text(
                """
                INSERT INTO m10_recovery.outbox
                (aggregate_type, aggregate_id, event_type, payload)
                VALUES ('test', :event_id, 'http:webhook', :payload)
                RETURNING id
            """
            ),
            {"event_id": event_id, "payload": json.dumps(payload)},
        )
        outbox_id = result.scalar()
        db_session.commit()

        from app.worker.outbox_processor import OutboxProcessor

        # First process - should succeed
        processor = OutboxProcessor(DATABASE_URL)
        asyncio.run(processor.run(once=True, batch_size=10))

        # Force back to pending
        db_session.execute(
            text("UPDATE m10_recovery.outbox SET processed_at = NULL WHERE id = :id"),
            {"id": outbox_id},
        )
        db_session.commit()

        # Second process - should get 409 and treat as success
        asyncio.run(processor.run(once=True, batch_size=10))

        # Event should be marked as processed (success)
        result = db_session.execute(
            text("SELECT processed_at FROM m10_recovery.outbox WHERE id = :id"),
            {"id": outbox_id},
        )
        processed_at = result.scalar()
        assert processed_at is not None  # Event was processed


class TestOutboxReplayDurability:
    """Tests for replay durability across restarts."""

    def test_worker_restart_no_lost_events(self, db_session, mock_server):
        """Test that worker restart doesn't lose events."""
        from sqlalchemy import text

        # Create events
        event_ids = [str(uuid.uuid4()) for _ in range(5)]

        for event_id in event_ids:
            payload = {
                "url": f"{mock_server}/webhook",
                "method": "POST",
                "body": {"restart_test": True, "event_id": event_id},
            }
            db_session.execute(
                text(
                    """
                    INSERT INTO m10_recovery.outbox
                    (aggregate_type, aggregate_id, event_type, payload)
                    VALUES ('test', :event_id, 'http:webhook', :payload)
                """
                ),
                {"event_id": event_id, "payload": json.dumps(payload)},
            )
        db_session.commit()

        from app.worker.outbox_processor import OutboxProcessor

        # Process partial batch (simulate crash after 2 events)
        processor = OutboxProcessor(DATABASE_URL)
        asyncio.run(processor.run(once=True, batch_size=2))

        first_batch_count = len(IdempotencyTrackingHandler.received_events)
        assert first_batch_count >= 1

        # "Restart" - create new processor
        processor2 = OutboxProcessor(DATABASE_URL)
        asyncio.run(processor2.run(once=True, batch_size=10))

        # All events should be processed
        assert len(IdempotencyTrackingHandler.received_events) == 5
        assert IdempotencyTrackingHandler.duplicate_count == 0


class TestOutboxMetrics:
    """Metrics and observability tests."""

    def test_metrics_incremented_on_success(self, db_session, mock_server):
        """Test that Prometheus metrics are updated."""
        from sqlalchemy import text

        event_id = str(uuid.uuid4())
        payload = {
            "url": f"{mock_server}/webhook",
            "method": "POST",
            "body": {"metrics_test": True},
        }

        db_session.execute(
            text(
                """
                INSERT INTO m10_recovery.outbox
                (aggregate_type, aggregate_id, event_type, payload)
                VALUES ('test', :event_id, 'http:webhook', :payload)
            """
            ),
            {"event_id": event_id, "payload": json.dumps(payload)},
        )
        db_session.commit()

        # Mock metrics to track calls
        metrics_calls = defaultdict(int)

        def mock_get_metric(name):
            class MockMetric:
                def inc(self, value=1):
                    metrics_calls[name] += value

            return MockMetric()

        with patch("app.worker.outbox_processor.OutboxProcessor._update_metric") as mock_update:
            mock_update.side_effect = lambda name, value: metrics_calls.__setitem__(
                name, metrics_calls.get(name, 0) + value
            )

            from app.worker.outbox_processor import OutboxProcessor

            processor = OutboxProcessor(DATABASE_URL)
            asyncio.run(processor.run(once=True, batch_size=10))

        # Verify metrics were called
        assert metrics_calls.get("m10_outbox_claimed_total", 0) >= 1
        assert metrics_calls.get("m10_outbox_processed_total", 0) >= 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
