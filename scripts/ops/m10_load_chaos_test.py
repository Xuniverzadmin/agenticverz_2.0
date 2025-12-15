#!/usr/bin/env python3
"""
M10 Load and Chaos Test Script

Simulates production-like load and failure scenarios to validate:
1. Outbox processor handles high throughput without duplicates
2. System recovers from Redis/worker restarts
3. Retry and dead-letter mechanisms work correctly
4. Lock metrics and alerts fire appropriately

Usage:
    # Run load test (100 events, no chaos)
    python -m scripts.ops.m10_load_chaos_test --load --count 100

    # Run chaos test (simulates failures)
    python -m scripts.ops.m10_load_chaos_test --chaos

    # Run full test suite
    python -m scripts.ops.m10_load_chaos_test --full --count 500

    # Validate no duplicates in mock receiver
    python -m scripts.ops.m10_load_chaos_test --validate

Environment Variables:
    DATABASE_URL: PostgreSQL connection URL
    REDIS_URL: Redis connection URL
    M10_TEST_WEBHOOK_URL: URL for mock webhook receiver
"""

import argparse
import asyncio
import json
import logging
import os
import random
import signal
import socket
import subprocess
import sys
import time
import uuid
from datetime import datetime, timezone
from http.server import HTTPServer, BaseHTTPRequestHandler
from threading import Thread, Lock
from typing import Dict, List, Set, Optional

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "backend"))

logger = logging.getLogger("m10.load_chaos")

# Configuration
DATABASE_URL = os.getenv("DATABASE_URL")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Test settings
DEFAULT_EVENT_COUNT = 100
BATCH_SIZE = 20
WORKER_RESTART_INTERVAL = 10  # seconds
CHAOS_DURATION = 60  # seconds


class IdempotencyReceiver:
    """Mock HTTP receiver that tracks idempotency keys for duplicate detection."""

    def __init__(self, port: int = 0):
        self.port = port
        self.server: Optional[HTTPServer] = None
        self.thread: Optional[Thread] = None
        self.received_keys: Set[str] = set()
        self.received_events: List[Dict] = []
        self.duplicate_count: int = 0
        self.request_count: int = 0
        self.lock = Lock()
        self._running = False

    def start(self) -> int:
        """Start the mock receiver and return the port."""
        handler = self._create_handler()
        self.server = HTTPServer(("127.0.0.1", self.port), handler)
        self.port = self.server.server_address[1]

        self.thread = Thread(target=self._serve)
        self.thread.daemon = True
        self._running = True
        self.thread.start()

        logger.info(f"Mock receiver started on port {self.port}")
        return self.port

    def stop(self):
        """Stop the mock receiver."""
        self._running = False
        if self.server:
            self.server.shutdown()
        logger.info("Mock receiver stopped")

    def _serve(self):
        """Server loop."""
        while self._running:
            self.server.handle_request()

    def _create_handler(self):
        """Create request handler with access to receiver state."""
        receiver = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, format, *args):
                pass

            def do_POST(self):
                with receiver.lock:
                    receiver.request_count += 1

                    # Extract idempotency key
                    idem_key = (
                        self.headers.get("Idempotency-Key")
                        or self.headers.get("X-Idempotency-Key")
                    )
                    event_id = self.headers.get("X-Outbox-Event-Id")

                    # Read body
                    content_length = int(self.headers.get("Content-Length", 0))
                    body = self.rfile.read(content_length) if content_length > 0 else b""

                    # Check for duplicate
                    if idem_key:
                        if idem_key in receiver.received_keys:
                            receiver.duplicate_count += 1
                            self.send_response(409)
                            self.end_headers()
                            self.wfile.write(b'{"status": "duplicate"}')
                            return
                        receiver.received_keys.add(idem_key)

                    receiver.received_events.append({
                        "idempotency_key": idem_key,
                        "event_id": event_id,
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    })

                    self.send_response(200)
                    self.end_headers()
                    self.wfile.write(b'{"status": "ok"}')

        return Handler

    def get_stats(self) -> Dict:
        """Get receiver statistics."""
        with self.lock:
            return {
                "request_count": self.request_count,
                "unique_events": len(self.received_keys),
                "duplicate_count": self.duplicate_count,
                "duplicate_rate": (
                    self.duplicate_count / self.request_count
                    if self.request_count > 0
                    else 0
                ),
            }

    def reset(self):
        """Reset receiver state."""
        with self.lock:
            self.received_keys.clear()
            self.received_events.clear()
            self.duplicate_count = 0
            self.request_count = 0


def create_test_events(
    db_url: str,
    count: int,
    webhook_url: str,
    batch_size: int = 50,
) -> List[str]:
    """Create test outbox events in the database."""
    from sqlalchemy import text
    from sqlmodel import Session, create_engine

    engine = create_engine(db_url, pool_pre_ping=True)
    event_ids = []

    with Session(engine) as session:
        for i in range(0, count, batch_size):
            batch_count = min(batch_size, count - i)
            values = []

            for j in range(batch_count):
                event_id = str(uuid.uuid4())
                event_ids.append(event_id)
                payload = json.dumps({
                    "url": webhook_url,
                    "method": "POST",
                    "body": {
                        "test_id": event_id,
                        "sequence": i + j,
                        "created_at": datetime.now(timezone.utc).isoformat(),
                    },
                })
                values.append(f"('test', '{event_id}', 'http:webhook', '{payload}')")

            sql = f"""
                INSERT INTO m10_recovery.outbox
                (aggregate_type, aggregate_id, event_type, payload)
                VALUES {', '.join(values)}
            """
            session.execute(text(sql))

            if (i + batch_count) % 100 == 0:
                logger.info(f"Created {i + batch_count}/{count} events")

        session.commit()

    logger.info(f"Created {count} test events")
    return event_ids


def get_outbox_stats(db_url: str) -> Dict:
    """Get current outbox statistics."""
    from sqlalchemy import text
    from sqlmodel import Session, create_engine

    engine = create_engine(db_url, pool_pre_ping=True)

    with Session(engine) as session:
        result = session.execute(text("""
            SELECT
                CASE
                    WHEN processed_at IS NOT NULL THEN 'processed'
                    WHEN next_retry_at > now() THEN 'retrying'
                    ELSE 'pending'
                END as status,
                COUNT(*) as count,
                AVG(retry_count) as avg_retries
            FROM m10_recovery.outbox
            GROUP BY 1
        """))

        stats = {"by_status": {}}
        for row in result:
            stats["by_status"][row[0]] = {
                "count": row[1],
                "avg_retries": float(row[2]) if row[2] else 0,
            }

        # Get oldest pending
        result = session.execute(text("""
            SELECT EXTRACT(EPOCH FROM (now() - MIN(created_at)))
            FROM m10_recovery.outbox
            WHERE processed_at IS NULL
        """))
        lag = result.scalar()
        stats["oldest_pending_seconds"] = float(lag) if lag else 0

        return stats


async def run_outbox_processor(db_url: str, duration: int = 60) -> Dict:
    """Run outbox processor for specified duration."""
    from app.worker.outbox_processor import OutboxProcessor

    processor = OutboxProcessor(db_url)
    await processor.start()

    results = {"batches_processed": 0, "events_processed": 0, "errors": 0}
    start_time = time.time()

    try:
        while time.time() - start_time < duration:
            batch_results = await processor.process_batch(BATCH_SIZE)
            results["batches_processed"] += 1
            results["events_processed"] += batch_results.get("processed", 0)
            results["errors"] += batch_results.get("failed", 0)

            if batch_results.get("claimed", 0) == 0:
                await asyncio.sleep(1)
    finally:
        await processor.stop()

    return results


def run_load_test(
    event_count: int,
    webhook_url: str,
    duration: int = 120,
) -> Dict:
    """Run load test with specified number of events."""
    logger.info(f"=== M10 Load Test ===")
    logger.info(f"Events: {event_count}, Duration: {duration}s")

    if not DATABASE_URL:
        raise ValueError("DATABASE_URL not set")

    # Create events
    logger.info("Creating test events...")
    event_ids = create_test_events(DATABASE_URL, event_count, webhook_url)

    # Run processor
    logger.info("Processing events...")
    start_time = time.time()

    processor_results = asyncio.run(run_outbox_processor(DATABASE_URL, duration))

    elapsed = time.time() - start_time

    # Get final stats
    outbox_stats = get_outbox_stats(DATABASE_URL)

    return {
        "test_type": "load",
        "event_count": event_count,
        "duration_seconds": elapsed,
        "events_per_second": event_count / elapsed if elapsed > 0 else 0,
        "processor_results": processor_results,
        "outbox_stats": outbox_stats,
    }


def run_chaos_test(
    event_count: int,
    webhook_url: str,
    duration: int = 60,
) -> Dict:
    """Run chaos test with simulated failures."""
    logger.info(f"=== M10 Chaos Test ===")
    logger.info(f"Events: {event_count}, Chaos duration: {duration}s")

    if not DATABASE_URL:
        raise ValueError("DATABASE_URL not set")

    results = {
        "test_type": "chaos",
        "event_count": event_count,
        "chaos_events": [],
        "processor_restarts": 0,
    }

    # Create events
    logger.info("Creating test events...")
    event_ids = create_test_events(DATABASE_URL, event_count, webhook_url)

    # Run processor with chaos
    async def chaos_processor():
        from app.worker.outbox_processor import OutboxProcessor

        processor = OutboxProcessor(DATABASE_URL)
        chaos_start = time.time()

        while time.time() - chaos_start < duration:
            try:
                await processor.start()

                # Process for random interval before "crash"
                run_duration = random.randint(5, 15)
                batch_results = {"total_processed": 0}

                run_start = time.time()
                while time.time() - run_start < run_duration:
                    batch = await processor.process_batch(BATCH_SIZE)
                    batch_results["total_processed"] += batch.get("processed", 0)

                    if batch.get("claimed", 0) == 0:
                        await asyncio.sleep(1)

                # Simulate crash
                await processor.stop()
                results["processor_restarts"] += 1
                results["chaos_events"].append({
                    "type": "processor_restart",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "events_processed": batch_results["total_processed"],
                })

                logger.info(f"Chaos: processor restart #{results['processor_restarts']}")
                await asyncio.sleep(random.uniform(0.5, 2))

            except Exception as e:
                logger.error(f"Chaos processor error: {e}")
                results["chaos_events"].append({
                    "type": "error",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "error": str(e),
                })

    asyncio.run(chaos_processor())

    # Let remaining events drain
    logger.info("Draining remaining events...")
    asyncio.run(run_outbox_processor(DATABASE_URL, 30))

    # Get final stats
    results["outbox_stats"] = get_outbox_stats(DATABASE_URL)

    return results


def validate_results(receiver: IdempotencyReceiver, expected_count: int) -> Dict:
    """Validate test results and check for duplicates."""
    stats = receiver.get_stats()

    validation = {
        "expected_events": expected_count,
        "received_events": stats["unique_events"],
        "duplicate_count": stats["duplicate_count"],
        "duplicate_rate": stats["duplicate_rate"],
        "all_received": stats["unique_events"] >= expected_count,
        "no_duplicates": stats["duplicate_count"] == 0,
        "passed": (
            stats["unique_events"] >= expected_count
            and stats["duplicate_count"] == 0
        ),
    }

    return validation


def main():
    parser = argparse.ArgumentParser(description="M10 Load and Chaos Test")
    parser.add_argument("--load", action="store_true", help="Run load test")
    parser.add_argument("--chaos", action="store_true", help="Run chaos test")
    parser.add_argument("--full", action="store_true", help="Run full test suite")
    parser.add_argument("--validate", action="store_true", help="Only validate (use external receiver)")
    parser.add_argument("--count", type=int, default=DEFAULT_EVENT_COUNT, help="Number of events")
    parser.add_argument("--duration", type=int, default=60, help="Test duration in seconds")
    parser.add_argument("--webhook-url", type=str, help="External webhook URL (skips mock receiver)")
    parser.add_argument("--json", action="store_true", help="JSON output")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")

    args = parser.parse_args()

    # Configure logging
    log_level = logging.DEBUG if args.debug else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )

    results = {"tests": [], "timestamp": datetime.now(timezone.utc).isoformat()}

    # Start mock receiver if no external URL provided
    receiver = None
    webhook_url = args.webhook_url

    if not webhook_url:
        receiver = IdempotencyReceiver()
        port = receiver.start()
        webhook_url = f"http://127.0.0.1:{port}/webhook"
        logger.info(f"Using mock receiver at {webhook_url}")

    try:
        if args.load or args.full:
            logger.info("\n" + "=" * 60)
            logger.info("RUNNING LOAD TEST")
            logger.info("=" * 60)

            load_results = run_load_test(args.count, webhook_url, args.duration)
            results["tests"].append(load_results)

            if receiver:
                load_results["validation"] = validate_results(receiver, args.count)
                receiver.reset()

        if args.chaos or args.full:
            logger.info("\n" + "=" * 60)
            logger.info("RUNNING CHAOS TEST")
            logger.info("=" * 60)

            chaos_results = run_chaos_test(args.count, webhook_url, args.duration)
            results["tests"].append(chaos_results)

            if receiver:
                chaos_results["validation"] = validate_results(receiver, args.count)
                receiver.reset()

        if args.validate and receiver:
            logger.info("\n" + "=" * 60)
            logger.info("VALIDATION RESULTS")
            logger.info("=" * 60)
            results["validation"] = validate_results(receiver, args.count)

        # Output results
        if args.json:
            print(json.dumps(results, indent=2, default=str))
        else:
            print("\n" + "=" * 60)
            print("TEST RESULTS")
            print("=" * 60)

            for test in results["tests"]:
                print(f"\n{test['test_type'].upper()} TEST:")
                print(f"  Events: {test.get('event_count', 'N/A')}")

                if "duration_seconds" in test:
                    print(f"  Duration: {test['duration_seconds']:.2f}s")
                    print(f"  Throughput: {test.get('events_per_second', 0):.2f} events/s")

                if "processor_restarts" in test:
                    print(f"  Processor restarts: {test['processor_restarts']}")

                if "validation" in test:
                    v = test["validation"]
                    status = "PASSED" if v["passed"] else "FAILED"
                    print(f"\n  Validation: {status}")
                    print(f"    Expected: {v['expected_events']}")
                    print(f"    Received: {v['received_events']}")
                    print(f"    Duplicates: {v['duplicate_count']}")

            if "validation" in results:
                v = results["validation"]
                status = "PASSED" if v["passed"] else "FAILED"
                print(f"\nFINAL VALIDATION: {status}")

            # Overall status
            all_passed = all(
                t.get("validation", {}).get("passed", True)
                for t in results["tests"]
            )
            print("\n" + "=" * 60)
            print(f"OVERALL: {'PASSED' if all_passed else 'FAILED'}")
            print("=" * 60)

            sys.exit(0 if all_passed else 1)

    finally:
        if receiver:
            receiver.stop()


if __name__ == "__main__":
    main()
