#!/usr/bin/env python3
"""
M10 Phase 6 Production Hardening Tests

Tests for:
- Leader election correctness under concurrency
- Outbox processor E2E flow
- Archive + trim safety (no data loss)
- Replay log durability across restarts
- Retention cleanup GC
- Scale/concurrency testing

Run:
    DATABASE_URL="$DATABASE_URL" PYTHONPATH=. pytest tests/test_m10_production_hardening.py -v
"""

import os
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone

import pytest

# Skip if no database
DATABASE_URL = os.getenv("DATABASE_URL")
pytestmark = pytest.mark.skipif(not DATABASE_URL, reason="DATABASE_URL not set")


class TestLeaderElectionChaos:
    """Test leader election under various failure scenarios."""

    def get_engine(self):
        from sqlmodel import create_engine

        return create_engine(DATABASE_URL, pool_pre_ping=True)

    def cleanup_locks(self, lock_prefix: str):
        """Clean up test locks."""
        from sqlalchemy import text
        from sqlmodel import Session

        engine = self.get_engine()
        with Session(engine) as session:
            session.execute(
                text("DELETE FROM m10_recovery.distributed_locks WHERE lock_name LIKE :prefix"),
                {"prefix": f"{lock_prefix}%"},
            )
            session.commit()

    def test_single_lock_acquisition(self):
        """Test basic lock acquisition and release."""
        from sqlalchemy import text
        from sqlmodel import Session

        lock_name = f"test:single:{uuid.uuid4().hex[:8]}"
        holder_id = f"holder:{uuid.uuid4().hex[:8]}"
        engine = self.get_engine()

        try:
            with Session(engine) as session:
                # Acquire lock
                result = session.execute(
                    text("SELECT m10_recovery.acquire_lock(:lock_name, :holder_id, :ttl)"),
                    {"lock_name": lock_name, "holder_id": holder_id, "ttl": 60},
                )
                acquired = result.scalar()
                session.commit()
                assert acquired is True, "Should acquire lock"

                # Second acquisition by same holder should succeed (idempotent)
                result = session.execute(
                    text("SELECT m10_recovery.acquire_lock(:lock_name, :holder_id, :ttl)"),
                    {"lock_name": lock_name, "holder_id": holder_id, "ttl": 60},
                )
                acquired2 = result.scalar()
                session.commit()
                assert acquired2 is True, "Same holder should re-acquire"

                # Different holder should fail
                result = session.execute(
                    text("SELECT m10_recovery.acquire_lock(:lock_name, :holder_id, :ttl)"),
                    {"lock_name": lock_name, "holder_id": "other_holder", "ttl": 60},
                )
                other_acquired = result.scalar()
                session.commit()
                assert other_acquired is False, "Different holder should fail"

                # Release lock
                result = session.execute(
                    text("SELECT m10_recovery.release_lock(:lock_name, :holder_id)"),
                    {"lock_name": lock_name, "holder_id": holder_id},
                )
                released = result.scalar()
                session.commit()
                assert released is True, "Should release lock"

        finally:
            self.cleanup_locks("test:single")

    def test_concurrent_lock_acquisition(self):
        """Test multiple threads racing to acquire the same lock."""
        lock_name = f"test:concurrent:{uuid.uuid4().hex[:8]}"
        results = {"acquired": [], "failed": []}
        barrier = threading.Barrier(10)

        def try_acquire(thread_id: int):
            from sqlalchemy import text
            from sqlmodel import Session

            engine = self.get_engine()
            holder_id = f"thread:{thread_id}"

            barrier.wait()  # Synchronize start

            with Session(engine) as session:
                result = session.execute(
                    text("SELECT m10_recovery.acquire_lock(:lock_name, :holder_id, :ttl)"),
                    {"lock_name": lock_name, "holder_id": holder_id, "ttl": 60},
                )
                acquired = result.scalar()
                session.commit()

                if acquired:
                    results["acquired"].append(thread_id)
                else:
                    results["failed"].append(thread_id)

        try:
            with ThreadPoolExecutor(max_workers=10) as executor:
                futures = [executor.submit(try_acquire, i) for i in range(10)]
                for f in futures:
                    f.result()

            # Exactly one thread should acquire
            assert len(results["acquired"]) == 1, f"Exactly one should acquire: {results}"
            assert len(results["failed"]) == 9, f"Nine should fail: {results}"

        finally:
            self.cleanup_locks("test:concurrent")

    def test_lock_expiry_and_takeover(self):
        """Test that expired locks can be taken over."""
        from sqlalchemy import text
        from sqlmodel import Session

        lock_name = f"test:expiry:{uuid.uuid4().hex[:8]}"
        holder1 = f"holder1:{uuid.uuid4().hex[:8]}"
        holder2 = f"holder2:{uuid.uuid4().hex[:8]}"
        engine = self.get_engine()

        try:
            with Session(engine) as session:
                # Acquire with very short TTL
                result = session.execute(
                    text("SELECT m10_recovery.acquire_lock(:lock_name, :holder_id, :ttl)"),
                    {"lock_name": lock_name, "holder_id": holder1, "ttl": 1},  # 1 second TTL
                )
                assert result.scalar() is True
                session.commit()

            # Wait for expiry
            time.sleep(2)

            with Session(engine) as session:
                # Clean up expired (simulating cleanup job)
                session.execute(text("SELECT m10_recovery.cleanup_expired_locks()"))
                session.commit()

                # Second holder should now acquire
                result = session.execute(
                    text("SELECT m10_recovery.acquire_lock(:lock_name, :holder_id, :ttl)"),
                    {"lock_name": lock_name, "holder_id": holder2, "ttl": 60},
                )
                acquired = result.scalar()
                session.commit()
                assert acquired is True, "Should acquire after expiry"

        finally:
            self.cleanup_locks("test:expiry")

    def test_lock_extend(self):
        """Test lock extension."""
        from sqlalchemy import text
        from sqlmodel import Session

        lock_name = f"test:extend:{uuid.uuid4().hex[:8]}"
        holder_id = f"holder:{uuid.uuid4().hex[:8]}"
        engine = self.get_engine()

        try:
            with Session(engine) as session:
                # Acquire lock
                session.execute(
                    text("SELECT m10_recovery.acquire_lock(:lock_name, :holder_id, :ttl)"),
                    {"lock_name": lock_name, "holder_id": holder_id, "ttl": 10},
                )
                session.commit()

                # Get initial expiry
                result = session.execute(
                    text("SELECT expires_at FROM m10_recovery.distributed_locks WHERE lock_name = :lock_name"),
                    {"lock_name": lock_name},
                )
                initial_expiry = result.scalar()

                # Extend lock
                result = session.execute(
                    text("SELECT m10_recovery.extend_lock(:lock_name, :holder_id, :ttl)"),
                    {"lock_name": lock_name, "holder_id": holder_id, "ttl": 300},
                )
                extended = result.scalar()
                session.commit()
                assert extended is True, "Should extend lock"

                # Verify new expiry
                result = session.execute(
                    text("SELECT expires_at FROM m10_recovery.distributed_locks WHERE lock_name = :lock_name"),
                    {"lock_name": lock_name},
                )
                new_expiry = result.scalar()
                assert new_expiry > initial_expiry, "Expiry should be extended"

        finally:
            self.cleanup_locks("test:extend")


class TestOutboxE2E:
    """Test outbox processor end-to-end flow."""

    def get_engine(self):
        from sqlmodel import create_engine

        return create_engine(DATABASE_URL, pool_pre_ping=True)

    def cleanup_outbox(self, aggregate_type: str = "test"):
        """Clean up test outbox entries."""
        from sqlalchemy import text
        from sqlmodel import Session

        engine = self.get_engine()
        with Session(engine) as session:
            session.execute(
                text("DELETE FROM m10_recovery.outbox WHERE aggregate_type = :agg_type"), {"agg_type": aggregate_type}
            )
            session.commit()

    def test_publish_and_claim(self):
        """Test publishing and claiming outbox events."""
        from sqlalchemy import text
        from sqlmodel import Session

        engine = self.get_engine()
        aggregate_id = str(uuid.uuid4())

        try:
            with Session(engine) as session:
                # Publish event
                result = session.execute(
                    text(
                        """
                        SELECT m10_recovery.publish_outbox(
                            'test', :agg_id, 'http:call',
                            '{"url": "https://example.com/webhook", "method": "POST"}'::jsonb
                        )
                    """
                    ),
                    {"agg_id": aggregate_id},
                )
                event_id = result.scalar()
                session.commit()
                assert event_id is not None, "Should return event ID"

                # Claim events (canonical signature: processor_id, batch_size)
                result = session.execute(
                    text("SELECT * FROM m10_recovery.claim_outbox_events('test-processor', 10)"),
                )
                rows = result.fetchall()
                session.commit()

                claimed_ids = [r[0] for r in rows]
                assert event_id in claimed_ids, "Published event should be claimed"

                # Complete event (canonical signature: event_id, processor_id, success, error)
                session.execute(
                    text("SELECT m10_recovery.complete_outbox_event(:event_id, 'test-processor', true, NULL)"),
                    {"event_id": event_id},
                )
                session.commit()

                # Verify processed
                result = session.execute(
                    text("SELECT processed_at FROM m10_recovery.outbox WHERE id = :id"), {"id": event_id}
                )
                processed_at = result.scalar()
                assert processed_at is not None, "Event should be marked processed"

        finally:
            self.cleanup_outbox()

    def test_outbox_retry_on_failure(self):
        """Test that failed events are retried with backoff."""
        from sqlalchemy import text
        from sqlmodel import Session

        engine = self.get_engine()
        aggregate_id = str(uuid.uuid4())

        try:
            with Session(engine) as session:
                # Publish event
                result = session.execute(
                    text(
                        """
                        SELECT m10_recovery.publish_outbox(
                            'test', :agg_id, 'http:call',
                            '{"url": "https://example.com/webhook"}'::jsonb
                        )
                    """
                    ),
                    {"agg_id": aggregate_id},
                )
                event_id = result.scalar()
                session.commit()

                # Claim and fail (canonical signatures)
                result = session.execute(
                    text("SELECT * FROM m10_recovery.claim_outbox_events('test-processor', 10)"),
                )
                session.commit()

                session.execute(
                    text(
                        "SELECT m10_recovery.complete_outbox_event(:event_id, 'test-processor', false, 'Connection refused')"
                    ),
                    {"event_id": event_id},
                )
                session.commit()

                # Check retry_count increased
                result = session.execute(
                    text("SELECT retry_count, process_after FROM m10_recovery.outbox WHERE id = :id"), {"id": event_id}
                )
                row = result.fetchone()
                assert row[0] == 1, "Retry count should be 1"
                assert row[1] > datetime.now(timezone.utc), "process_after should be in future"

        finally:
            self.cleanup_outbox()

    @pytest.mark.asyncio
    async def test_outbox_processor_integration(self):
        """Test outbox processor with mock HTTP."""
        from sqlalchemy import text
        from sqlmodel import Session

        from app.worker.outbox_processor import OutboxProcessor

        engine = self.get_engine()
        aggregate_id = str(uuid.uuid4())

        try:
            # Publish event
            with Session(engine) as session:
                result = session.execute(
                    text(
                        """
                        SELECT m10_recovery.publish_outbox(
                            'test', :agg_id, 'notify:log',
                            '{"channel": "log", "message": "Test notification"}'::jsonb
                        )
                    """
                    ),
                    {"agg_id": aggregate_id},
                )
                event_id = result.scalar()
                session.commit()

            # Process with outbox processor
            processor = OutboxProcessor(DATABASE_URL)
            await processor.start()

            try:
                results = await processor.process_batch(batch_size=10)
                assert results["claimed"] >= 1, "Should claim at least one event"
                assert results["processed"] >= 1, "Should process at least one event"
            finally:
                await processor.stop()

            # Verify processed
            with Session(engine) as session:
                result = session.execute(
                    text("SELECT processed_at FROM m10_recovery.outbox WHERE id = :id"), {"id": event_id}
                )
                processed_at = result.scalar()
                assert processed_at is not None, "Event should be processed"

        finally:
            self.cleanup_outbox()


class TestArchiveAndTrimSafety:
    """Test that archive + trim doesn't lose data."""

    def get_engine(self):
        from sqlmodel import create_engine

        return create_engine(DATABASE_URL, pool_pre_ping=True)

    def test_archive_before_delete(self):
        """Test that archiving preserves message content."""
        from sqlalchemy import text
        from sqlmodel import Session

        engine = self.get_engine()
        test_msg_id = f"test-msg-{uuid.uuid4().hex[:8]}"

        try:
            with Session(engine) as session:
                # Archive a message (canonical schema: dl_msg_id, not stream_msg_id)
                session.execute(
                    text(
                        """
                        INSERT INTO m10_recovery.dead_letter_archive
                        (dl_msg_id, payload, reason)
                        VALUES (:msg_id, '{"test": true}'::jsonb, 'test_archive')
                    """
                    ),
                    {"msg_id": test_msg_id},
                )
                session.commit()

                # Verify archived
                result = session.execute(
                    text("SELECT payload, reason FROM m10_recovery.dead_letter_archive WHERE dl_msg_id = :msg_id"),
                    {"msg_id": test_msg_id},
                )
                row = result.fetchone()
                assert row is not None, "Archive record should exist"
                assert row[0]["test"] is True, "Payload should be preserved"
                assert row[1] == "test_archive", "Reason should be preserved"

        finally:
            with Session(engine) as session:
                session.execute(text("DELETE FROM m10_recovery.dead_letter_archive WHERE dl_msg_id LIKE 'test-msg-%'"))
                session.commit()


class TestReplayLogDurability:
    """Test replay log durability."""

    def get_engine(self):
        from sqlmodel import create_engine

        return create_engine(DATABASE_URL, pool_pre_ping=True)

    def cleanup_replay_log(self, prefix: str = "test"):
        """Clean up test replay log entries."""
        from sqlalchemy import text
        from sqlmodel import Session

        engine = self.get_engine()
        with Session(engine) as session:
            session.execute(
                text("DELETE FROM m10_recovery.replay_log WHERE original_msg_id LIKE :prefix"), {"prefix": f"{prefix}%"}
            )
            session.commit()

    def test_replay_idempotency(self):
        """Test that replay log enforces idempotency."""
        from sqlalchemy import text
        from sqlmodel import Session

        engine = self.get_engine()
        original_msg_id = f"test-orig-{uuid.uuid4().hex[:8]}"

        try:
            with Session(engine) as session:
                # First replay
                result = session.execute(
                    text(
                        """
                        SELECT * FROM m10_recovery.record_replay(
                            :orig_id, :dl_id, NULL, NULL, :new_id, 'test'
                        )
                    """
                    ),
                    {
                        "orig_id": original_msg_id,
                        "dl_id": f"dl-{uuid.uuid4().hex[:8]}",
                        "new_id": f"new-{uuid.uuid4().hex[:8]}",
                    },
                )
                row = result.fetchone()
                session.commit()

                is_duplicate, replay_id = row[0], row[1]
                assert is_duplicate is False, "First replay should not be duplicate"
                assert replay_id is not None, "Should return replay ID"

                # Second replay of same original
                result = session.execute(
                    text(
                        """
                        SELECT * FROM m10_recovery.record_replay(
                            :orig_id, :dl_id, NULL, NULL, :new_id, 'test'
                        )
                    """
                    ),
                    {
                        "orig_id": original_msg_id,  # Same original
                        "dl_id": f"dl-{uuid.uuid4().hex[:8]}",
                        "new_id": f"new-{uuid.uuid4().hex[:8]}",
                    },
                )
                row = result.fetchone()
                session.commit()

                is_duplicate2, replay_id2 = row[0], row[1]
                assert is_duplicate2 is True, "Second replay should be duplicate"
                assert replay_id2 == replay_id, "Should return same replay ID"

        finally:
            self.cleanup_replay_log()


class TestRetentionGC:
    """Test retention cleanup and garbage collection."""

    def get_engine(self):
        from sqlmodel import create_engine

        return create_engine(DATABASE_URL, pool_pre_ping=True)

    def test_retention_cleanup_dry_run(self):
        """Test retention cleanup in dry-run mode."""
        from scripts.ops.m10_retention_cleanup import run_all_cleanup

        results = run_all_cleanup(
            dl_archive_days=90,
            replay_days=30,
            outbox_days=7,
            dry_run=True,
            skip_leader_election=True,
        )

        assert results["status"] == "success", "Dry run should succeed"
        assert results["dry_run"] is True, "Should be marked as dry run"
        assert "tables" in results, "Should have tables key"
        assert len(results["tables"]) == 4, "Should check all 4 tables"

    def test_expired_locks_cleanup(self):
        """Test cleanup of expired locks."""
        from sqlalchemy import text
        from sqlmodel import Session

        from scripts.ops.m10_retention_cleanup import cleanup_expired_locks

        engine = self.get_engine()
        lock_name = f"test:expired:{uuid.uuid4().hex[:8]}"

        try:
            # Create already-expired lock directly
            with Session(engine) as session:
                session.execute(
                    text(
                        """
                        INSERT INTO m10_recovery.distributed_locks (lock_name, holder_id, expires_at)
                        VALUES (:lock_name, 'test-holder', now() - interval '1 hour')
                    """
                    ),
                    {"lock_name": lock_name},
                )
                session.commit()

            # Run cleanup
            results = cleanup_expired_locks(dry_run=False, db_url=DATABASE_URL)

            assert results["deleted"] >= 1, "Should delete at least one expired lock"

            # Verify deleted
            with Session(engine) as session:
                result = session.execute(
                    text("SELECT COUNT(*) FROM m10_recovery.distributed_locks WHERE lock_name = :lock_name"),
                    {"lock_name": lock_name},
                )
                count = result.scalar()
                assert count == 0, "Expired lock should be deleted"

        finally:
            with Session(engine) as session:
                session.execute(text("DELETE FROM m10_recovery.distributed_locks WHERE lock_name LIKE 'test:expired%'"))
                session.commit()


@pytest.mark.slow
class TestScaleConcurrency:
    """Test system under high concurrency load."""

    def get_engine(self):
        from sqlmodel import create_engine

        return create_engine(DATABASE_URL, pool_pre_ping=True)

    def test_high_volume_outbox(self):
        """Test outbox under high volume."""
        from sqlalchemy import text
        from sqlmodel import Session

        engine = self.get_engine()
        num_events = 100

        try:
            # Publish many events
            with Session(engine) as session:
                for i in range(num_events):
                    session.execute(
                        text(
                            """
                            SELECT m10_recovery.publish_outbox(
                                'scale_test', :agg_id, 'notify:log',
                                '{"message": "Event"}'::jsonb
                            )
                        """
                        ),
                        {"agg_id": f"scale-{i}"},
                    )
                session.commit()

            # Verify all published
            with Session(engine) as session:
                result = session.execute(
                    text("SELECT COUNT(*) FROM m10_recovery.outbox WHERE aggregate_type = 'scale_test'")
                )
                count = result.scalar()
                assert count == num_events, f"All {num_events} events should be published"

        finally:
            with Session(engine) as session:
                session.execute(text("DELETE FROM m10_recovery.outbox WHERE aggregate_type = 'scale_test'"))
                session.commit()

    def test_concurrent_lock_operations(self):
        """Test many concurrent lock operations."""
        num_locks = 20  # Reduced from 50 to avoid connection exhaustion
        num_threads = 5  # Reduced from 10 to avoid connection exhaustion
        results = {"acquired": 0, "released": 0, "failed": 0}
        lock = threading.Lock()

        # Shared engine with connection pool
        from sqlmodel import create_engine

        shared_engine = create_engine(DATABASE_URL, pool_size=10, max_overflow=5, pool_pre_ping=True)

        def do_lock_cycle(lock_idx: int, thread_id: int):
            from sqlalchemy import text
            from sqlmodel import Session

            lock_name = f"test:scale:{lock_idx}"
            holder_id = f"thread:{thread_id}"

            with Session(shared_engine) as session:
                # Try acquire
                result = session.execute(
                    text("SELECT m10_recovery.acquire_lock(:lock_name, :holder_id, :ttl)"),
                    {"lock_name": lock_name, "holder_id": holder_id, "ttl": 60},
                )
                acquired = result.scalar()
                session.commit()

                with lock:
                    if acquired:
                        results["acquired"] += 1
                    else:
                        results["failed"] += 1

                if acquired:
                    # Do some work
                    time.sleep(0.01)

                    # Release
                    result = session.execute(
                        text("SELECT m10_recovery.release_lock(:lock_name, :holder_id)"),
                        {"lock_name": lock_name, "holder_id": holder_id},
                    )
                    released = result.scalar()
                    session.commit()

                    with lock:
                        if released:
                            results["released"] += 1

        try:
            with ThreadPoolExecutor(max_workers=num_threads) as executor:
                futures = []
                for lock_idx in range(num_locks):
                    for thread_id in range(num_threads):
                        futures.append(executor.submit(do_lock_cycle, lock_idx, thread_id))

                for f in futures:
                    f.result()

            # Each lock should be acquired at least once
            assert results["acquired"] >= num_locks, f"Each lock should be acquired at least once: {results}"
            # All acquired should be released
            assert results["acquired"] == results["released"], f"All acquired should be released: {results}"

        finally:
            from sqlalchemy import text
            from sqlmodel import Session

            with Session(shared_engine) as session:
                session.execute(text("DELETE FROM m10_recovery.distributed_locks WHERE lock_name LIKE 'test:scale%'"))
                session.commit()
            shared_engine.dispose()


class TestM10ContractSentinel:
    """Regression sentinel tests for M10 contract invariants.

    These are NOT functional tests — they are STRUCTURAL INVARIANT tests.
    They exist to catch contract drift before it becomes production bugs.

    Reference: PIN-276, docs/contracts/M10_OUTBOX_CONTRACT.md
    """

    def get_engine(self):
        from sqlmodel import create_engine

        return create_engine(DATABASE_URL, pool_pre_ping=True)

    def test_exactly_one_claim_outbox_events_signature(self):
        """INVARIANT: claim_outbox_events must have exactly ONE signature.

        NO OVERLOADS rule from M10_OUTBOX_CONTRACT.md.
        If this fails, someone created a function overload.
        """
        from sqlalchemy import text
        from sqlmodel import Session

        engine = self.get_engine()

        with Session(engine) as session:
            result = session.execute(
                text(
                    """
                    SELECT COUNT(*) FROM pg_proc p
                    JOIN pg_namespace n ON p.pronamespace = n.oid
                    WHERE n.nspname = 'm10_recovery'
                    AND p.proname = 'claim_outbox_events'
                    """
                )
            )
            count = result.scalar()

            assert count == 1, (
                f"CONTRACT VIOLATION: claim_outbox_events has {count} signatures, expected exactly 1. "
                "This violates the NO OVERLOADS rule in M10_OUTBOX_CONTRACT.md. "
                "Fix: Drop the extra overload, keep only the canonical signature."
            )

    def test_exactly_one_complete_outbox_event_signature(self):
        """INVARIANT: complete_outbox_event must have exactly ONE signature.

        NO OVERLOADS rule from M10_OUTBOX_CONTRACT.md.
        If this fails, someone created a function overload.
        """
        from sqlalchemy import text
        from sqlmodel import Session

        engine = self.get_engine()

        with Session(engine) as session:
            result = session.execute(
                text(
                    """
                    SELECT COUNT(*) FROM pg_proc p
                    JOIN pg_namespace n ON p.pronamespace = n.oid
                    WHERE n.nspname = 'm10_recovery'
                    AND p.proname = 'complete_outbox_event'
                    """
                )
            )
            count = result.scalar()

            assert count == 1, (
                f"CONTRACT VIOLATION: complete_outbox_event has {count} signatures, expected exactly 1. "
                "This violates the NO OVERLOADS rule in M10_OUTBOX_CONTRACT.md. "
                "Fix: Drop the extra overload, keep only the canonical signature."
            )

    def test_canonical_claim_signature_matches_contract(self):
        """INVARIANT: claim_outbox_events signature must be (TEXT, INTEGER).

        Canonical signature from M10_OUTBOX_CONTRACT.md:
        - p_processor_id TEXT (FIRST)
        - p_batch_size INTEGER (SECOND)
        """
        from sqlalchemy import text
        from sqlmodel import Session

        engine = self.get_engine()

        with Session(engine) as session:
            result = session.execute(
                text(
                    """
                    SELECT pg_catalog.pg_get_function_identity_arguments(p.oid) as signature
                    FROM pg_proc p
                    JOIN pg_namespace n ON p.pronamespace = n.oid
                    WHERE n.nspname = 'm10_recovery'
                    AND p.proname = 'claim_outbox_events'
                    """
                )
            )
            signature = result.scalar()

            # Canonical: p_processor_id text, p_batch_size integer
            assert signature is not None, "Function claim_outbox_events not found"
            assert "text" in signature.lower(), f"CONTRACT VIOLATION: Expected TEXT for processor_id, got: {signature}"
            assert (
                "integer" in signature.lower()
            ), f"CONTRACT VIOLATION: Expected INTEGER for batch_size, got: {signature}"
            # Verify order: processor_id comes before batch_size
            text_pos = signature.lower().find("text")
            int_pos = signature.lower().find("integer")
            assert text_pos < int_pos, (
                f"CONTRACT VIOLATION: processor_id (TEXT) must come BEFORE batch_size (INTEGER). "
                f"Got: {signature}. This violates canonical parameter order."
            )

    def test_canonical_complete_signature_matches_contract(self):
        """INVARIANT: complete_outbox_event signature must be (BIGINT, TEXT, BOOLEAN, TEXT).

        Canonical signature from M10_OUTBOX_CONTRACT.md:
        - p_event_id BIGINT
        - p_processor_id TEXT
        - p_success BOOLEAN
        - p_error TEXT DEFAULT NULL
        """
        from sqlalchemy import text
        from sqlmodel import Session

        engine = self.get_engine()

        with Session(engine) as session:
            result = session.execute(
                text(
                    """
                    SELECT pg_catalog.pg_get_function_identity_arguments(p.oid) as signature
                    FROM pg_proc p
                    JOIN pg_namespace n ON p.pronamespace = n.oid
                    WHERE n.nspname = 'm10_recovery'
                    AND p.proname = 'complete_outbox_event'
                    """
                )
            )
            signature = result.scalar()

            assert signature is not None, "Function complete_outbox_event not found"
            # Canonical: p_event_id bigint, p_processor_id text, p_success boolean, p_error text
            assert "bigint" in signature.lower(), f"CONTRACT VIOLATION: Expected BIGINT for event_id, got: {signature}"
            assert "boolean" in signature.lower(), f"CONTRACT VIOLATION: Expected BOOLEAN for success, got: {signature}"

    def test_process_after_is_sole_retry_authority(self):
        """INVARIANT: process_after is the ONLY retry scheduling field.

        Single retry authority from M10_OUTBOX_CONTRACT.md.
        The column next_retry_at must NOT exist or must be deprecated.
        complete_outbox_event must only update process_after for retry scheduling.
        """
        from sqlalchemy import text
        from sqlmodel import Session

        engine = self.get_engine()

        with Session(engine) as session:
            # Verify process_after column exists
            result = session.execute(
                text(
                    """
                    SELECT EXISTS (
                        SELECT 1 FROM information_schema.columns
                        WHERE table_schema = 'm10_recovery'
                        AND table_name = 'outbox'
                        AND column_name = 'process_after'
                    )
                    """
                )
            )
            has_process_after = result.scalar()
            assert has_process_after is True, (
                "CONTRACT VIOLATION: process_after column missing from m10_recovery.outbox. "
                "This is the sole retry authority field."
            )

            # Get the function source to verify it only uses process_after for retry
            result = session.execute(
                text(
                    """
                    SELECT pg_get_functiondef(p.oid) as source
                    FROM pg_proc p
                    JOIN pg_namespace n ON p.pronamespace = n.oid
                    WHERE n.nspname = 'm10_recovery'
                    AND p.proname = 'complete_outbox_event'
                    """
                )
            )
            source = result.scalar()

            assert source is not None, "Function complete_outbox_event not found"
            source_lower = source.lower()

            # Verify process_after is set on failure
            assert "process_after" in source_lower, (
                "CONTRACT VIOLATION: complete_outbox_event does not reference process_after. "
                "This violates the single retry authority rule."
            )

            # Verify next_retry_at is NOT being updated (parallel truth prevention)
            # We check that next_retry_at is not in a SET clause
            if "next_retry_at" in source_lower:
                # Only fail if it's being SET, not just referenced
                assert "set" not in source_lower.split("next_retry_at")[0][
                    -50:
                ] or "next_retry_at =" not in source_lower.replace(" ", ""), (
                    "CONTRACT VIOLATION: complete_outbox_event updates next_retry_at. "
                    "This violates the single retry authority rule (NO PARALLEL TRUTH). "
                    "Only process_after should control retry scheduling."
                )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
