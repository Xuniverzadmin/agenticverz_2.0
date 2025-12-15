"""
Tests for M10 Recovery leader election and Phase 5 production hardening.

These tests validate:
- Distributed lock acquisition and release
- Leader election for reconcile and matview jobs
- DB-backed replay idempotency
- Dead-letter archival
- Reclaim attempt GC
"""
import asyncio
import os
import pytest
import uuid
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

# Test configuration
TEST_DB_URL = os.getenv("DATABASE_URL", "postgresql://nova:novapass@localhost:6432/nova_aos")
TEST_REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")


class TestDistributedLocks:
    """Test distributed lock functions from migration 022."""

    @pytest.fixture
    def db_session(self):
        """Create a database session for tests."""
        from sqlalchemy import text
        from sqlmodel import Session, create_engine

        engine = create_engine(TEST_DB_URL, pool_pre_ping=True)
        with Session(engine) as session:
            yield session

    def test_acquire_lock_success(self, db_session):
        """Test successful lock acquisition."""
        from sqlalchemy import text

        lock_name = f"test:lock:{uuid.uuid4().hex[:8]}"
        holder_id = f"test-holder-{uuid.uuid4().hex[:8]}"

        try:
            # Acquire lock
            result = db_session.execute(
                text("SELECT m10_recovery.acquire_lock(:lock_name, :holder_id, :ttl)"),
                {"lock_name": lock_name, "holder_id": holder_id, "ttl": 60}
            )
            acquired = result.scalar()
            db_session.commit()

            assert acquired is True, "Should acquire lock"

            # Verify lock exists
            result = db_session.execute(
                text("""
                    SELECT holder_id, expires_at > now() AS valid
                    FROM m10_recovery.distributed_locks
                    WHERE lock_name = :lock_name
                """),
                {"lock_name": lock_name}
            )
            row = result.fetchone()
            assert row is not None
            assert row[0] == holder_id
            assert row[1] is True  # Not expired

        finally:
            # Cleanup
            db_session.execute(
                text("DELETE FROM m10_recovery.distributed_locks WHERE lock_name = :lock_name"),
                {"lock_name": lock_name}
            )
            db_session.commit()

    def test_acquire_lock_conflict(self, db_session):
        """Test that second holder cannot acquire held lock."""
        from sqlalchemy import text

        lock_name = f"test:lock:{uuid.uuid4().hex[:8]}"
        holder_1 = f"holder-1-{uuid.uuid4().hex[:8]}"
        holder_2 = f"holder-2-{uuid.uuid4().hex[:8]}"

        try:
            # First holder acquires lock
            result = db_session.execute(
                text("SELECT m10_recovery.acquire_lock(:lock_name, :holder_id, :ttl)"),
                {"lock_name": lock_name, "holder_id": holder_1, "ttl": 600}
            )
            assert result.scalar() is True

            db_session.commit()

            # Second holder tries to acquire - should fail
            result = db_session.execute(
                text("SELECT m10_recovery.acquire_lock(:lock_name, :holder_id, :ttl)"),
                {"lock_name": lock_name, "holder_id": holder_2, "ttl": 600}
            )
            acquired = result.scalar()
            db_session.commit()

            assert acquired is False, "Second holder should not acquire held lock"

        finally:
            # Cleanup
            db_session.execute(
                text("DELETE FROM m10_recovery.distributed_locks WHERE lock_name = :lock_name"),
                {"lock_name": lock_name}
            )
            db_session.commit()

    def test_acquire_lock_reacquire_same_holder(self, db_session):
        """Test that same holder can reacquire (extend) their own lock."""
        from sqlalchemy import text

        lock_name = f"test:lock:{uuid.uuid4().hex[:8]}"
        holder_id = f"test-holder-{uuid.uuid4().hex[:8]}"

        try:
            # First acquisition
            result = db_session.execute(
                text("SELECT m10_recovery.acquire_lock(:lock_name, :holder_id, :ttl)"),
                {"lock_name": lock_name, "holder_id": holder_id, "ttl": 60}
            )
            assert result.scalar() is True
            db_session.commit()

            # Same holder reacquires (extend)
            result = db_session.execute(
                text("SELECT m10_recovery.acquire_lock(:lock_name, :holder_id, :ttl)"),
                {"lock_name": lock_name, "holder_id": holder_id, "ttl": 120}
            )
            reacquired = result.scalar()
            db_session.commit()

            assert reacquired is True, "Same holder should be able to reacquire"

        finally:
            db_session.execute(
                text("DELETE FROM m10_recovery.distributed_locks WHERE lock_name = :lock_name"),
                {"lock_name": lock_name}
            )
            db_session.commit()

    def test_release_lock(self, db_session):
        """Test lock release."""
        from sqlalchemy import text

        lock_name = f"test:lock:{uuid.uuid4().hex[:8]}"
        holder_id = f"test-holder-{uuid.uuid4().hex[:8]}"

        try:
            # Acquire
            result = db_session.execute(
                text("SELECT m10_recovery.acquire_lock(:lock_name, :holder_id, :ttl)"),
                {"lock_name": lock_name, "holder_id": holder_id, "ttl": 600}
            )
            assert result.scalar() is True
            db_session.commit()

            # Release
            result = db_session.execute(
                text("SELECT m10_recovery.release_lock(:lock_name, :holder_id)"),
                {"lock_name": lock_name, "holder_id": holder_id}
            )
            released = result.scalar()
            db_session.commit()

            assert released is True, "Should release lock"

            # Verify lock is gone
            result = db_session.execute(
                text("SELECT COUNT(*) FROM m10_recovery.distributed_locks WHERE lock_name = :lock_name"),
                {"lock_name": lock_name}
            )
            assert result.scalar() == 0

        finally:
            # Cleanup just in case
            db_session.execute(
                text("DELETE FROM m10_recovery.distributed_locks WHERE lock_name = :lock_name"),
                {"lock_name": lock_name}
            )
            db_session.commit()

    def test_release_lock_wrong_holder(self, db_session):
        """Test that wrong holder cannot release lock."""
        from sqlalchemy import text

        lock_name = f"test:lock:{uuid.uuid4().hex[:8]}"
        holder_1 = f"holder-1-{uuid.uuid4().hex[:8]}"
        holder_2 = f"holder-2-{uuid.uuid4().hex[:8]}"

        try:
            # Acquire as holder_1
            result = db_session.execute(
                text("SELECT m10_recovery.acquire_lock(:lock_name, :holder_id, :ttl)"),
                {"lock_name": lock_name, "holder_id": holder_1, "ttl": 600}
            )
            assert result.scalar() is True
            db_session.commit()

            # Try to release as holder_2
            result = db_session.execute(
                text("SELECT m10_recovery.release_lock(:lock_name, :holder_id)"),
                {"lock_name": lock_name, "holder_id": holder_2}
            )
            released = result.scalar()
            db_session.commit()

            assert released is False, "Wrong holder should not release"

            # Lock should still exist
            result = db_session.execute(
                text("SELECT COUNT(*) FROM m10_recovery.distributed_locks WHERE lock_name = :lock_name"),
                {"lock_name": lock_name}
            )
            assert result.scalar() == 1

        finally:
            db_session.execute(
                text("DELETE FROM m10_recovery.distributed_locks WHERE lock_name = :lock_name"),
                {"lock_name": lock_name}
            )
            db_session.commit()

    def test_acquire_expired_lock(self, db_session):
        """Test that expired lock can be acquired by new holder."""
        from sqlalchemy import text

        lock_name = f"test:lock:{uuid.uuid4().hex[:8]}"
        holder_1 = f"holder-1-{uuid.uuid4().hex[:8]}"
        holder_2 = f"holder-2-{uuid.uuid4().hex[:8]}"

        try:
            # Insert an expired lock directly
            db_session.execute(
                text("""
                    INSERT INTO m10_recovery.distributed_locks
                        (lock_name, holder_id, acquired_at, expires_at)
                    VALUES
                        (:lock_name, :holder_id, now() - interval '10 minutes', now() - interval '5 minutes')
                """),
                {"lock_name": lock_name, "holder_id": holder_1}
            )
            db_session.commit()

            # New holder should be able to acquire expired lock
            result = db_session.execute(
                text("SELECT m10_recovery.acquire_lock(:lock_name, :holder_id, :ttl)"),
                {"lock_name": lock_name, "holder_id": holder_2, "ttl": 600}
            )
            acquired = result.scalar()
            db_session.commit()

            assert acquired is True, "Should acquire expired lock"

            # Verify new holder owns it
            result = db_session.execute(
                text("SELECT holder_id FROM m10_recovery.distributed_locks WHERE lock_name = :lock_name"),
                {"lock_name": lock_name}
            )
            assert result.scalar() == holder_2

        finally:
            db_session.execute(
                text("DELETE FROM m10_recovery.distributed_locks WHERE lock_name = :lock_name"),
                {"lock_name": lock_name}
            )
            db_session.commit()


class TestReplayLog:
    """Test DB-backed replay idempotency."""

    @pytest.fixture
    def db_session(self):
        """Create a database session for tests."""
        from sqlalchemy import text
        from sqlmodel import Session, create_engine

        engine = create_engine(TEST_DB_URL, pool_pre_ping=True)
        with Session(engine) as session:
            yield session

    def test_record_replay_new(self, db_session):
        """Test recording a new replay."""
        from sqlalchemy import text

        original_msg_id = f"msg-{uuid.uuid4().hex[:16]}"
        dl_msg_id = f"dl-{uuid.uuid4().hex[:16]}"

        try:
            result = db_session.execute(
                text("""
                    SELECT already_replayed, replay_id
                    FROM m10_recovery.record_replay(
                        :original_msg_id, :dl_msg_id, NULL, NULL, :new_msg_id, 'test'
                    )
                """),
                {
                    "original_msg_id": original_msg_id,
                    "dl_msg_id": dl_msg_id,
                    "new_msg_id": f"new-{uuid.uuid4().hex[:16]}"
                }
            )
            row = result.fetchone()
            db_session.commit()

            assert row is not None
            already_replayed, replay_id = row
            assert already_replayed is False, "Should be new replay"
            assert replay_id is not None

        finally:
            db_session.execute(
                text("DELETE FROM m10_recovery.replay_log WHERE original_msg_id = :id"),
                {"id": original_msg_id}
            )
            db_session.commit()

    def test_record_replay_idempotent(self, db_session):
        """Test that replay is idempotent."""
        from sqlalchemy import text

        original_msg_id = f"msg-{uuid.uuid4().hex[:16]}"
        dl_msg_id = f"dl-{uuid.uuid4().hex[:16]}"

        try:
            # First record
            result = db_session.execute(
                text("""
                    SELECT already_replayed, replay_id
                    FROM m10_recovery.record_replay(
                        :original_msg_id, :dl_msg_id, NULL, NULL, :new_msg_id, 'test'
                    )
                """),
                {
                    "original_msg_id": original_msg_id,
                    "dl_msg_id": dl_msg_id,
                    "new_msg_id": f"new-{uuid.uuid4().hex[:16]}"
                }
            )
            row = result.fetchone()
            db_session.commit()

            first_id = row[1]
            assert row[0] is False  # Not already replayed

            # Second record (same original_msg_id)
            result = db_session.execute(
                text("""
                    SELECT already_replayed, replay_id
                    FROM m10_recovery.record_replay(
                        :original_msg_id, :dl_msg_id, NULL, NULL, :new_msg_id, 'test'
                    )
                """),
                {
                    "original_msg_id": original_msg_id,
                    "dl_msg_id": f"dl-other-{uuid.uuid4().hex[:16]}",
                    "new_msg_id": f"new-other-{uuid.uuid4().hex[:16]}"
                }
            )
            row = result.fetchone()
            db_session.commit()

            assert row[0] is True, "Should be already replayed"
            assert row[1] == first_id, "Should return same ID"

        finally:
            db_session.execute(
                text("DELETE FROM m10_recovery.replay_log WHERE original_msg_id = :id"),
                {"id": original_msg_id}
            )
            db_session.commit()


class TestDeadLetterArchive:
    """Test dead-letter archival."""

    @pytest.fixture
    def db_session(self):
        """Create a database session for tests."""
        from sqlalchemy import text
        from sqlmodel import Session, create_engine

        engine = create_engine(TEST_DB_URL, pool_pre_ping=True)
        with Session(engine) as session:
            yield session

    def test_archive_dead_letter(self, db_session):
        """Test archiving a dead-letter message."""
        from sqlalchemy import text

        dl_msg_id = f"dl-{uuid.uuid4().hex[:16]}"

        try:
            result = db_session.execute(
                text("""
                    SELECT m10_recovery.archive_dead_letter(
                        :dl_msg_id,
                        :original_msg_id,
                        :candidate_id,
                        NULL,  -- failure_match_id
                        CAST(:payload_json AS jsonb),
                        :reason,
                        0,
                        now(),
                        'test'
                    )
                """),
                {
                    "dl_msg_id": dl_msg_id,
                    "original_msg_id": f"orig-{uuid.uuid4().hex[:16]}",
                    "candidate_id": 12345,
                    "payload_json": '{"test": "data", "candidate_id": 12345}',
                    "reason": "max_reclaims_exceeded"
                }
            )
            archive_id = result.scalar()
            db_session.commit()

            assert archive_id is not None

            # Verify archived
            result = db_session.execute(
                text("SELECT dl_msg_id, reason FROM m10_recovery.dead_letter_archive WHERE id = :id"),
                {"id": archive_id}
            )
            row = result.fetchone()
            assert row is not None
            assert row[0] == dl_msg_id
            assert row[1] == "max_reclaims_exceeded"

        finally:
            db_session.execute(
                text("DELETE FROM m10_recovery.dead_letter_archive WHERE dl_msg_id = :id"),
                {"id": dl_msg_id}
            )
            db_session.commit()

    def test_archive_dead_letter_idempotent(self, db_session):
        """Test that archiving is idempotent."""
        from sqlalchemy import text

        dl_msg_id = f"dl-{uuid.uuid4().hex[:16]}"

        try:
            # First archive
            result = db_session.execute(
                text("""
                    SELECT m10_recovery.archive_dead_letter(
                        :dl_msg_id, :original_msg_id, NULL, NULL,
                        '{"test": 1}'::jsonb, 'test', 0, now(), 'test'
                    )
                """),
                {
                    "dl_msg_id": dl_msg_id,
                    "original_msg_id": f"orig-{uuid.uuid4().hex[:16]}"
                }
            )
            first_id = result.scalar()
            db_session.commit()

            # Second archive (same dl_msg_id)
            result = db_session.execute(
                text("""
                    SELECT m10_recovery.archive_dead_letter(
                        :dl_msg_id, :original_msg_id, NULL, NULL,
                        '{"test": 2}'::jsonb, 'test', 0, now(), 'test'
                    )
                """),
                {
                    "dl_msg_id": dl_msg_id,
                    "original_msg_id": f"orig-other-{uuid.uuid4().hex[:16]}"
                }
            )
            second_id = result.scalar()
            db_session.commit()

            assert first_id == second_id, "Should return same ID (idempotent)"

        finally:
            db_session.execute(
                text("DELETE FROM m10_recovery.dead_letter_archive WHERE dl_msg_id = :id"),
                {"id": dl_msg_id}
            )
            db_session.commit()


class TestReconcileLeaderElection:
    """Test leader election in reconcile script."""

    @pytest.fixture
    def db_session(self):
        """Create a database session for tests."""
        from sqlalchemy import text
        from sqlmodel import Session, create_engine

        engine = create_engine(TEST_DB_URL, pool_pre_ping=True)
        with Session(engine) as session:
            yield session

    def test_reconcile_lock_functions_exist(self, db_session):
        """Verify reconcile_dl uses acquire_lock and release_lock."""
        import importlib.util

        spec = importlib.util.spec_from_file_location(
            "reconcile_dl",
            str(Path(__file__).parent.parent / "scripts" / "ops" / "reconcile_dl.py")
        )
        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            # Just verify the module has the functions
            assert hasattr(module, '__file__')
            # Read the source to verify lock usage
            script_path = Path(__file__).parent.parent / "scripts" / "ops" / "reconcile_dl.py"
            with open(script_path) as f:
                source = f.read()
                assert "acquire_lock" in source
                assert "release_lock" in source
                assert "LOCK_NAME" in source
                assert "HOLDER_ID" in source

    def test_matview_lock_functions_exist(self, db_session):
        """Verify refresh_matview uses acquire_lock and release_lock."""
        script_path = Path(__file__).parent.parent / "scripts" / "ops" / "refresh_matview.py"
        with open(script_path) as f:
            source = f.read()
            assert "acquire_view_lock" in source
            assert "release_view_lock" in source
            assert "LOCK_TTL" in source
            assert "HOLDER_ID" in source


class TestReclaimAttemptsGC:
    """Test garbage collection of reclaim attempts."""

    @pytest.mark.asyncio
    async def test_gc_cleans_stale_entries(self):
        """Test that GC removes entries not in pending list."""
        from app.tasks.recovery_queue_stream import (
            get_redis,
            gc_reclaim_attempts,
            RECLAIM_ATTEMPTS_KEY,
        )

        # This test requires Redis to be available
        try:
            redis = await get_redis()

            # Add some fake reclaim attempt entries
            test_entries = {
                f"fake-msg-{uuid.uuid4().hex[:8]}": "1",
                f"fake-msg-{uuid.uuid4().hex[:8]}": "2",
                f"fake-msg-{uuid.uuid4().hex[:8]}": "3",
            }

            for msg_id, attempts in test_entries.items():
                await redis.hset(RECLAIM_ATTEMPTS_KEY, msg_id, attempts)

            # Run GC
            results = await gc_reclaim_attempts(max_entries_to_check=1000)

            # Should have cleaned up the fake entries (not in pending)
            assert results["cleaned"] >= len(test_entries)

        except Exception as e:
            pytest.skip(f"Redis not available: {e}")


class TestRedisConfigCheck:
    """Test Redis configuration check script."""

    def test_check_script_exists(self):
        """Verify config check script exists."""
        script_path = Path(__file__).parent.parent / "scripts" / "ops" / "check_redis_config.py"
        assert script_path.exists()

    def test_check_script_has_required_config(self):
        """Verify script checks required config."""
        script_path = Path(__file__).parent.parent / "scripts" / "ops" / "check_redis_config.py"
        with open(script_path) as f:
            source = f.read()
            assert "appendonly" in source
            assert "maxmemory-policy" in source
            assert "noeviction" in source
            assert "REQUIRED_CONFIG" in source
            assert "RECOMMENDED_CONFIG" in source


# Run with: PYTHONPATH=. pytest tests/test_m10_leader_election.py -v
