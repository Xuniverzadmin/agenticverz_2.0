# M12.1 High-Concurrency Load Test
# Tests multi-agent system under high load (1000 items x 50 workers)
#
# Based on: PIN-063-m12.1-stabilization.md
# Purpose: Validate FOR UPDATE SKIP LOCKED under production-like load
#
# NOTE: These tests require the 'agents' schema to be present in the database.
# The schema is defined in PIN-062 and includes: agents.jobs, agents.job_items,
# agents.instances, agents.messages. Tests are skipped if schema is missing.

import os
import random
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Dict, List, Tuple
from uuid import UUID, uuid4

import pytest

# Set test environment
os.environ.setdefault(
    "DATABASE_URL",
    "postgresql://nova:novapass@localhost:6432/nova_aos",
)
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")

# Test configuration
DATABASE_URL = os.getenv("DATABASE_URL")


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

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.hoc.int.agent.engines.blackboard_engine import get_blackboard_service
from app.hoc.int.agent.engines.credit_engine import CreditService, get_credit_service
from app.hoc.int.agent.engines.job_engine import JobConfig, JobService, get_job_service
from app.hoc.int.agent.engines.worker_engine import WorkerService, get_worker_service

# Test configuration
LOAD_TEST_ITEMS = int(os.environ.get("LOAD_TEST_ITEMS", "1000"))
LOAD_TEST_WORKERS = int(os.environ.get("LOAD_TEST_WORKERS", "50"))
LOAD_TEST_TIMEOUT = int(os.environ.get("LOAD_TEST_TIMEOUT", "120"))  # seconds


class LoadTestMetrics:
    """Collect metrics during load test."""

    def __init__(self):
        self.claims = 0
        self.claim_times: List[float] = []
        self.completions = 0
        self.completion_times: List[float] = []
        self.errors: List[str] = []
        self.double_claims = 0
        self.lock = threading.Lock()
        self.claimed_items: Dict[str, str] = {}  # item_id -> worker_id

    def record_claim(self, duration_ms: float, item_id: str, worker_id: str):
        with self.lock:
            self.claims += 1
            self.claim_times.append(duration_ms)
            if item_id in self.claimed_items:
                self.double_claims += 1
                self.errors.append(f"Double claim: {item_id} by {worker_id} (first: {self.claimed_items[item_id]})")
            else:
                self.claimed_items[item_id] = worker_id

    def record_completion(self, duration_ms: float):
        with self.lock:
            self.completions += 1
            self.completion_times.append(duration_ms)

    def record_error(self, error: str):
        with self.lock:
            self.errors.append(error)

    def summary(self) -> Dict[str, Any]:
        with self.lock:
            return {
                "claims": self.claims,
                "completions": self.completions,
                "double_claims": self.double_claims,
                "errors": len(self.errors),
                "avg_claim_ms": sum(self.claim_times) / len(self.claim_times) if self.claim_times else 0,
                "max_claim_ms": max(self.claim_times) if self.claim_times else 0,
                "avg_completion_ms": sum(self.completion_times) / len(self.completion_times)
                if self.completion_times
                else 0,
                "p95_claim_ms": sorted(self.claim_times)[int(len(self.claim_times) * 0.95)]
                if len(self.claim_times) > 20
                else 0,
            }


def worker_loop(
    worker_id: str,
    job_id: UUID,
    worker_service: WorkerService,
    metrics: LoadTestMetrics,
    stop_event: threading.Event,
    items_per_worker: int = 0,
):
    """Simulate a worker claiming and processing items."""
    claimed_count = 0

    while not stop_event.is_set():
        try:
            # Claim next item
            start = time.perf_counter()
            item = worker_service.claim_item(job_id, worker_id)
            claim_ms = (time.perf_counter() - start) * 1000

            if item is None:
                # No more items
                break

            metrics.record_claim(claim_ms, str(item.id), worker_id)
            claimed_count += 1

            # Simulate work (1-5ms)
            time.sleep(random.uniform(0.001, 0.005))

            # Complete the item
            start = time.perf_counter()
            worker_service.complete_item(
                item_id=item.id,
                output={"processed": True, "worker": worker_id},
            )
            completion_ms = (time.perf_counter() - start) * 1000
            metrics.record_completion(completion_ms)

            # Optional limit per worker
            if items_per_worker > 0 and claimed_count >= items_per_worker:
                break

        except Exception as e:
            metrics.record_error(f"{worker_id}: {str(e)[:100]}")
            time.sleep(0.01)  # Brief pause on error


@pytest.fixture
def job_service():
    """Get job service instance."""
    return get_job_service()


@pytest.fixture
def worker_service():
    """Get worker service instance."""
    return get_worker_service()


@pytest.fixture
def credit_service():
    """Get credit service instance."""
    return get_credit_service()


@pytest.mark.slow
class TestM12HighConcurrency:
    """High-concurrency load tests for M12 multi-agent system.

    These are stress tests designed for load testing, not CI. Run with:
    LOAD_TEST_ITEMS=100 LOAD_TEST_WORKERS=10 pytest tests/test_m12_load.py -v
    """

    @pytest.mark.timeout(LOAD_TEST_TIMEOUT + 30)
    def test_concurrent_job_claim_1000x50(
        self,
        job_service: JobService,
        worker_service: WorkerService,
        credit_service: CreditService,
    ):
        """
        Test 1000 items claimed by 50 concurrent workers.

        Success criteria:
        - No double claims (FOR UPDATE SKIP LOCKED works)
        - All items claimed exactly once
        - Completion within timeout
        - Error rate < 1%
        """
        # Create test job with items
        job_config = JobConfig(
            orchestrator_agent="load_test_orchestrator",
            worker_agent="load_test_worker",
            task="Process load test items",
            items=[{"index": i, "data": f"item_{i}"} for i in range(LOAD_TEST_ITEMS)],
            parallelism=LOAD_TEST_WORKERS,
        )

        job = job_service.create_job(
            config=job_config,
            orchestrator_instance_id="orchestrator_001",
            tenant_id="load_test",
        )
        job_id = job.id

        print(f"\n[LOAD TEST] Created job {job_id} with {LOAD_TEST_ITEMS} items")

        # Track metrics
        metrics = LoadTestMetrics()
        stop_event = threading.Event()

        # Launch workers
        start_time = time.perf_counter()

        with ThreadPoolExecutor(max_workers=LOAD_TEST_WORKERS) as executor:
            futures = []
            for i in range(LOAD_TEST_WORKERS):
                worker_id = f"worker_{i:03d}"
                future = executor.submit(
                    worker_loop,
                    worker_id,
                    job_id,
                    worker_service,
                    metrics,
                    stop_event,
                )
                futures.append(future)

            # Wait for all workers with timeout
            try:
                for future in as_completed(futures, timeout=LOAD_TEST_TIMEOUT):
                    try:
                        future.result()
                    except Exception as e:
                        metrics.record_error(f"Worker exception: {e}")
            except TimeoutError:
                stop_event.set()
                pytest.fail(f"Load test timed out after {LOAD_TEST_TIMEOUT}s")

        elapsed = time.perf_counter() - start_time
        summary = metrics.summary()

        # Print results
        print("\n[LOAD TEST RESULTS]")
        print(f"  Duration: {elapsed:.2f}s")
        print(f"  Items: {LOAD_TEST_ITEMS}")
        print(f"  Workers: {LOAD_TEST_WORKERS}")
        print(f"  Claims: {summary['claims']}")
        print(f"  Completions: {summary['completions']}")
        print(f"  Double claims: {summary['double_claims']}")
        print(f"  Errors: {summary['errors']}")
        print(f"  Avg claim time: {summary['avg_claim_ms']:.2f}ms")
        print(f"  Max claim time: {summary['max_claim_ms']:.2f}ms")
        print(f"  P95 claim time: {summary['p95_claim_ms']:.2f}ms")
        print(f"  Throughput: {summary['claims'] / elapsed:.1f} items/sec")

        # Assertions
        assert summary["double_claims"] == 0, f"Double claims detected: {summary['double_claims']}"
        assert summary["claims"] == LOAD_TEST_ITEMS, f"Not all items claimed: {summary['claims']}/{LOAD_TEST_ITEMS}"
        assert summary["completions"] == LOAD_TEST_ITEMS, (
            f"Not all items completed: {summary['completions']}/{LOAD_TEST_ITEMS}"
        )

        error_rate = summary["errors"] / max(summary["claims"], 1)
        assert error_rate < 0.01, f"Error rate too high: {error_rate:.2%}"

        # Verify job status
        job = job_service.get_job(job_id)
        assert job is not None
        # Job should be completed
        assert job.progress.completed == LOAD_TEST_ITEMS, (
            f"Job completed mismatch: {job.progress.completed}/{LOAD_TEST_ITEMS}"
        )

        print("\n[LOAD TEST] ✓ PASSED - No double claims, all items processed")

    @pytest.mark.timeout(60)
    def test_concurrent_blackboard_operations(self):
        """
        Test concurrent blackboard read/write operations.

        Validates Redis-based blackboard under concurrent access.
        """
        try:
            blackboard = get_blackboard_service()
        except Exception:
            pytest.skip("Redis not available")

        job_id = uuid4()
        key = f"load_test_{uuid4().hex[:8]}"
        num_writers = 20
        writes_per_writer = 50

        results: List[Tuple[str, bool]] = []
        lock = threading.Lock()

        def writer_task(writer_id: int):
            for i in range(writes_per_writer):
                try:
                    value = {"writer": writer_id, "seq": i, "ts": time.time()}
                    success = blackboard.write(job_id, f"{key}_{writer_id}_{i}", value)
                    with lock:
                        results.append((f"{writer_id}_{i}", success))
                except Exception:
                    with lock:
                        results.append((f"{writer_id}_{i}", False))

        start = time.perf_counter()

        with ThreadPoolExecutor(max_workers=num_writers) as executor:
            futures = [executor.submit(writer_task, i) for i in range(num_writers)]
            for f in as_completed(futures, timeout=30):
                f.result()

        elapsed = time.perf_counter() - start

        success_count = sum(1 for _, s in results if s)
        total = num_writers * writes_per_writer

        print("\n[BLACKBOARD LOAD TEST]")
        print(f"  Writers: {num_writers}")
        print(f"  Writes/writer: {writes_per_writer}")
        print(f"  Total writes: {total}")
        print(f"  Successful: {success_count}")
        print(f"  Duration: {elapsed:.2f}s")
        print(f"  Throughput: {success_count / elapsed:.1f} writes/sec")

        assert success_count == total, f"Not all writes succeeded: {success_count}/{total}"

    @pytest.mark.timeout(60)
    def test_invoke_latency_with_notify(
        self,
        job_service: JobService,
    ):
        """
        Test that LISTEN/NOTIFY provides sub-second response for invokes.

        Note: This is a unit test of the pattern, not full integration.
        """
        from app.agents.skills.agent_invoke import AgentInvokeSkill

        db_url = os.environ.get("DATABASE_URL")
        if not db_url:
            pytest.skip("DATABASE_URL not set")

        # Test the NOTIFY channel naming
        invoke_id = f"inv_{uuid4().hex[:16]}"
        expected_channel = f"invoke_{invoke_id}"

        # Verify channel format is valid PostgreSQL identifier
        assert len(expected_channel) <= 63, "Channel name too long for PostgreSQL"
        assert expected_channel.replace("_", "").isalnum(), "Channel name has invalid chars"

        print(f"\n[NOTIFY TEST] Channel: {expected_channel}")
        print("  ✓ Channel naming valid")

        # Test respond_to_invoke doesn't crash with invalid invoke_id
        result = AgentInvokeSkill.respond_to_invoke(
            invoke_id="nonexistent_invoke",
            response_payload={"test": True},
            database_url=db_url,
        )
        assert result is False, "Should return False for nonexistent invoke"
        print("  ✓ respond_to_invoke handles missing invokes correctly")


@pytest.mark.slow
class TestM12StressPatterns:
    """Stress test specific patterns from M12.

    These are stress tests designed for validating concurrent access patterns.
    """

    @pytest.mark.timeout(30)
    def test_for_update_skip_locked_correctness(self, job_service: JobService):
        """
        Verify FOR UPDATE SKIP LOCKED prevents double claims.

        Create a small job and have multiple threads race to claim.
        """
        db_url = os.environ.get("DATABASE_URL")
        engine = create_engine(db_url, pool_pre_ping=True)
        Session = sessionmaker(bind=engine)

        # Create a small job
        job_config = JobConfig(
            orchestrator_agent="skip_locked_test",
            worker_agent="skip_locked_worker",
            task="FOR UPDATE SKIP LOCKED test",
            items=[{"index": i} for i in range(10)],
            parallelism=10,
        )

        job = job_service.create_job(
            config=job_config,
            orchestrator_instance_id="skip_locked_001",
            tenant_id="stress_test",
        )
        job_id = job.id

        # Simulate concurrent claims with raw SQL
        claimed_ids: List[str] = []
        lock = threading.Lock()

        def claim_one(worker_id: str):
            with Session() as session:
                try:
                    result = session.execute(
                        text(
                            """
                            UPDATE agents.job_items
                            SET status = 'claimed',
                                worker_instance_id = :worker_id,
                                claimed_at = now()
                            WHERE id = (
                                SELECT id FROM agents.job_items
                                WHERE job_id = :job_id AND status = 'pending'
                                ORDER BY item_index
                                LIMIT 1
                                FOR UPDATE SKIP LOCKED
                            )
                            RETURNING id::text
                        """
                        ),
                        {"job_id": str(job_id), "worker_id": worker_id},
                    )
                    row = result.fetchone()
                    session.commit()

                    if row:
                        with lock:
                            claimed_ids.append(row[0])
                except Exception:
                    session.rollback()

        # Race 50 threads to claim 10 items
        with ThreadPoolExecutor(max_workers=50) as executor:
            futures = [executor.submit(claim_one, f"worker_{i}") for i in range(50)]
            for f in as_completed(futures, timeout=10):
                f.result()

        # Verify exactly 10 unique claims (no duplicates)
        assert len(claimed_ids) == 10, f"Expected 10 claims, got {len(claimed_ids)}"
        assert len(set(claimed_ids)) == 10, "Duplicate claims detected"

        print("\n[SKIP LOCKED TEST] ✓ 10 items claimed by 50 racing threads with no duplicates")

    @pytest.mark.timeout(30)
    def test_job_cancellation_under_load(
        self,
        job_service: JobService,
        worker_service: WorkerService,
    ):
        """Test job cancellation while workers are claiming items."""
        # Create job with 100 items
        job_config = JobConfig(
            orchestrator_agent="cancel_test_orchestrator",
            worker_agent="cancel_test_worker",
            task="Cancellation test",
            items=[{"index": i} for i in range(100)],
            parallelism=10,
        )

        job = job_service.create_job(
            config=job_config,
            orchestrator_instance_id="cancel_test_001",
            tenant_id="cancel_test",
        )
        job_id = job.id

        # Start workers claiming items
        stop_event = threading.Event()
        claims = []
        lock = threading.Lock()

        def claim_loop(worker_id: str):
            while not stop_event.is_set():
                item = worker_service.claim_item(job_id, worker_id)
                if item is None:
                    break
                with lock:
                    claims.append(item.id)
                time.sleep(0.01)  # Simulate work

        # Launch 5 workers
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(claim_loop, f"w{i}") for i in range(5)]

            # Let workers claim some items
            time.sleep(0.1)

            # Cancel the job
            cancel_result = job_service.cancel_job(
                job_id=job_id,
                cancelled_by="test",
                reason="Testing cancellation under load",
            )

            stop_event.set()
            for f in futures:
                f.result()

        assert cancel_result is not None, "Cancellation failed"

        # Verify job is cancelled
        job = job_service.get_job(job_id)
        assert job.status == "cancelled"

        print(f"\n[CANCEL TEST] ✓ Job cancelled after {len(claims)} items claimed")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
