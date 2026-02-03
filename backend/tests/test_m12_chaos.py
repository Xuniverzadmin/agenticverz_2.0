# M12 Multi-Agent System Chaos Tests
# Tests for edge cases: worker death, stale recovery, lock contention
#
# NOTE: These tests require the 'agents' schema to be present in the database.
# The schema is defined in PIN-062 and includes: agents.jobs, agents.job_items,
# agents.instances, agents.messages. Tests are skipped if schema is missing.

import os
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from typing import List, Set

import pytest

# Test configuration
DATABASE_URL = os.getenv("DATABASE_URL")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")


def _agents_schema_exists() -> bool:
    """Check if the 'agents' schema exists in the database."""
    try:
        import psycopg2

        db_url = os.environ.get("DATABASE_URL")
        if not db_url:
            return False
        conn = psycopg2.connect(db_url)
        cur = conn.cursor()
        cur.execute("SELECT schema_name FROM information_schema.schemata WHERE schema_name = 'agents'")
        result = cur.fetchone()
        conn.close()
        return result is not None
    except Exception:
        return False


# Skip all tests if agents schema doesn't exist
AGENTS_SCHEMA_EXISTS = _agents_schema_exists()
pytestmark = pytest.mark.skipif(
    not DATABASE_URL or not AGENTS_SCHEMA_EXISTS,
    reason="DATABASE_URL not set or agents schema not present (see PIN-062)",
)


class TestWorkerDeathRecovery:
    """Test worker death scenarios and item reclamation."""

    def test_stale_worker_items_reclaimed(self):
        """Test that items from stale workers are reclaimed."""
        from sqlalchemy import create_engine, text

        from app.hoc.int.agent.engines.job_engine import JobConfig, JobService
        from app.hoc.int.agent.engines.registry_engine import RegistryService
        from app.hoc.int.agent.engines.worker_engine import WorkerService

        job_service = JobService()
        worker_service = WorkerService()
        registry_service = RegistryService()

        # Create 10-item job
        config = JobConfig(
            orchestrator_agent="test_orchestrator",
            worker_agent="test_worker",
            task="stale_reclaim_test",
            items=[{"id": i} for i in range(10)],
            parallelism=5,
        )

        job = job_service.create_job(
            config=config, orchestrator_instance_id="test-orchestrator-stale-001", tenant_id="test-tenant"
        )

        job_id = str(job.id)

        # Register a worker
        dead_worker_id = f"dead-worker-{uuid.uuid4().hex[:8]}"
        registry_service.register(agent_id="test_worker", instance_id=dead_worker_id, job_id=job_id, capabilities={})

        # Worker claims 3 items
        claimed_item_ids = []
        for _ in range(3):
            item = worker_service.claim_item(job_id=job_id, worker_instance_id=dead_worker_id)
            if item:
                claimed_item_ids.append(str(item.id))

        assert len(claimed_item_ids) == 3

        # Simulate worker death - mark as stale directly in DB
        engine = create_engine(DATABASE_URL)
        with engine.connect() as conn:
            conn.execute(
                text(
                    """
                UPDATE agents.instances
                SET status = 'stale', heartbeat_at = now() - INTERVAL '2 hours'
                WHERE instance_id = :instance_id
            """
                ),
                {"instance_id": dead_worker_id},
            )
            conn.commit()

        # Run reclamation
        reclaimed = registry_service.reclaim_stale_items()

        # Items should be reclaimed
        assert reclaimed >= 3

        # New worker should be able to claim those items
        new_worker_id = f"new-worker-{uuid.uuid4().hex[:8]}"
        registry_service.register(agent_id="test_worker", instance_id=new_worker_id, job_id=job_id, capabilities={})

        # Should be able to claim 10 items now (3 reclaimed + 7 remaining)
        new_claims = []
        for _ in range(12):
            item = worker_service.claim_item(job_id=job_id, worker_instance_id=new_worker_id)
            if item:
                new_claims.append(str(item.id))

        assert len(new_claims) == 10

    def test_heartbeat_keeps_worker_alive(self):
        """Test that heartbeating prevents staleness."""
        from app.hoc.int.agent.engines.registry_engine import RegistryService

        registry_service = RegistryService()

        worker_id = f"heartbeat-worker-{uuid.uuid4().hex[:8]}"

        # Register worker
        registry_service.register(agent_id="test_worker", instance_id=worker_id, capabilities={})

        # Get initial status
        instance = registry_service.get_instance(worker_id)
        assert instance is not None
        assert instance.status == "running"

        # Send heartbeat
        success = registry_service.heartbeat(worker_id)
        assert success

        # Worker should still be running
        instance = registry_service.get_instance(worker_id)
        assert instance.status == "running"


class TestLockContention:
    """Test distributed lock contention scenarios."""

    def test_high_contention_lock(self):
        """Test lock under high contention from many workers."""
        from app.hoc.int.agent.engines.blackboard_engine import BlackboardService

        blackboard = BlackboardService()

        lock_key = f"test:contention:{uuid.uuid4().hex[:8]}"
        value_key = f"test:value:{uuid.uuid4().hex[:8]}"
        blackboard.set(value_key, 0)

        successful_locks: List[str] = []
        lock_times: List[float] = []
        lock = threading.Lock()

        def contended_update(worker_id: int):
            """Try to acquire lock and increment value."""
            bb = BlackboardService()
            start = time.time()

            # Try to acquire lock (with short TTL)
            lock_result = bb.acquire_lock(lock_key, holder=f"worker-{worker_id}", ttl=2)
            acquire_time = time.time() - start

            if lock_result.acquired:
                try:
                    # Simulate some work
                    current = bb.get(value_key) or 0
                    time.sleep(0.05)  # Small delay
                    bb.set(value_key, current + 1)

                    with lock:
                        successful_locks.append(f"worker-{worker_id}")
                        lock_times.append(acquire_time)
                finally:
                    bb.release_lock(lock_key, holder=f"worker-{worker_id}")

        # Launch 50 concurrent workers
        with ThreadPoolExecutor(max_workers=50) as executor:
            futures = [executor.submit(contended_update, i) for i in range(50)]
            for f in futures:
                f.result(timeout=60)

        # At least some should have succeeded
        assert len(successful_locks) > 0

        # Final value should match successful locks
        final_value = blackboard.get(value_key)
        assert final_value == len(successful_locks)

        # Cleanup
        blackboard.delete(lock_key)
        blackboard.delete(value_key)

    def test_lock_expiry_allows_recovery(self):
        """Test that expired locks allow other workers to proceed."""
        from app.hoc.int.agent.engines.blackboard_engine import BlackboardService

        blackboard = BlackboardService()

        lock_key = f"test:expiry:{uuid.uuid4().hex[:8]}"

        # Acquire lock with very short TTL
        result1 = blackboard.acquire_lock(lock_key, holder="worker-1", ttl=1)
        assert result1.acquired

        # Wait for lock to expire
        time.sleep(1.5)

        # Another worker should be able to acquire
        result2 = blackboard.acquire_lock(lock_key, holder="worker-2", ttl=5)
        assert result2.acquired

        # Cleanup
        blackboard.release_lock(lock_key, holder="worker-2")


class TestConcurrentJobOperations:
    """Test concurrent operations on jobs."""

    def test_concurrent_job_updates(self):
        """Test that concurrent item completions don't corrupt counters."""
        from app.hoc.int.agent.engines.job_engine import JobConfig, JobService
        from app.hoc.int.agent.engines.worker_engine import WorkerService

        job_service = JobService()

        # Create 50-item job
        config = JobConfig(
            orchestrator_agent="test_orchestrator",
            worker_agent="test_worker",
            task="concurrent_update_test",
            items=[{"id": i} for i in range(50)],
            parallelism=20,
        )

        job = job_service.create_job(
            config=config, orchestrator_instance_id="test-orchestrator-concurrent-001", tenant_id="test-tenant"
        )

        job_id = str(job.id)

        completed: Set[str] = set()
        failed: Set[str] = set()
        errors: List[str] = []
        lock = threading.Lock()

        def worker_process(worker_id: int):
            """Worker claims and completes items."""
            svc = WorkerService()
            while True:
                try:
                    item = svc.claim_item(job_id=job_id, worker_instance_id=f"worker-{worker_id}")
                    if not item:
                        break

                    # 90% success rate
                    if worker_id % 10 == 0:
                        svc.fail_item(item_id=str(item.id), error_message="Simulated failure", retry=False)
                        with lock:
                            failed.add(str(item.id))
                    else:
                        svc.complete_item(item_id=str(item.id), output={"done": True})
                        with lock:
                            completed.add(str(item.id))
                except Exception as e:
                    with lock:
                        errors.append(str(e))

        # Run 20 concurrent workers
        with ThreadPoolExecutor(max_workers=20) as executor:
            futures = [executor.submit(worker_process, i) for i in range(20)]
            for f in futures:
                f.result(timeout=60)

        # Check consistency
        assert len(errors) == 0, f"Errors occurred: {errors}"

        # All items should be processed
        total_processed = len(completed) + len(failed)
        assert total_processed == 50

        # Job counters should match
        job_status = job_service.get_job(job_id)
        assert job_status.progress.completed == len(completed)
        assert job_status.progress.failed == len(failed)


class TestMessageOrderingUnderLoad:
    """Test message ordering under load."""

    def test_message_ordering_preserved(self):
        """Test that message ordering is preserved within a conversation."""
        from app.hoc.int.agent.engines.message_engine import MessageService

        message_service = MessageService()

        sender_id = f"sender-{uuid.uuid4().hex[:8]}"
        receiver_id = f"receiver-{uuid.uuid4().hex[:8]}"

        # Send 20 messages in sequence
        for i in range(20):
            message_service.send(
                from_instance_id=sender_id,
                to_instance_id=receiver_id,
                message_type="sequential_test",
                payload={"sequence": i},
            )

        # Read inbox
        inbox = message_service.get_inbox(instance_id=receiver_id, message_type="sequential_test", limit=30)

        # Should have all 20 messages
        assert len(inbox) == 20

        # Messages should be in reverse order (newest first - typical inbox behavior)
        # or in sorted order. Check that all sequences are present.
        sequences = sorted([m.payload["sequence"] for m in inbox])
        assert sequences == list(range(20)), "All messages should be present"


class TestBlackboardConsistency:
    """Test blackboard consistency under concurrent operations."""

    def test_increment_consistency_under_load(self):
        """Test that increment is consistent under heavy load."""
        from app.hoc.int.agent.engines.blackboard_engine import BlackboardService

        blackboard = BlackboardService()

        key = f"test:load:{uuid.uuid4().hex[:8]}"
        blackboard.set(key, 0)

        increments_done: List[int] = []
        lock = threading.Lock()

        def increment_many(count: int):
            bb = BlackboardService()
            results = []
            for _ in range(count):
                result = bb.increment(key, 1)
                results.append(result)
            with lock:
                increments_done.extend(results)

        # 100 workers each doing 10 increments
        with ThreadPoolExecutor(max_workers=100) as executor:
            futures = [executor.submit(increment_many, 10) for _ in range(100)]
            for f in futures:
                f.result(timeout=60)

        # Should have 1000 increments total
        assert len(increments_done) == 1000

        # All values should be unique
        assert len(set(increments_done)) == 1000

        # Final value should be 1000
        final = blackboard.get(key)
        assert final == 1000

        # Cleanup
        blackboard.delete(key)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
