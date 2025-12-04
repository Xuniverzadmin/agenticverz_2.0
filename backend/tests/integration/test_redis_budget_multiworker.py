# Redis Budget Store Multi-Worker Integration Test
"""
Integration test for RedisBudgetStore under multi-worker conditions.

Prerequisites:
    - Redis running on REDIS_URL (default: redis://localhost:6379/0)
    - Run with: REDIS_URL=redis://localhost:6379/0 pytest tests/integration/test_redis_budget_multiworker.py -v

Tests:
    1. Basic CRUD operations
    2. Atomic INCRBY under concurrent access
    3. Multi-process budget race simulation
    4. TTL expiration
    5. Connection resilience
"""

import asyncio
import os
import pytest
import pytest_asyncio
from typing import List
from unittest.mock import patch

# Skip if Redis not available
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
REDIS_AVAILABLE = False

try:
    import redis.asyncio as aioredis
    # Quick connectivity check
    async def _check_redis():
        try:
            client = aioredis.from_url(REDIS_URL)
            await client.ping()
            await client.close()
            return True
        except Exception:
            return False

    REDIS_AVAILABLE = asyncio.get_event_loop().run_until_complete(_check_redis())
except ImportError:
    pass

pytestmark = pytest.mark.skipif(
    not REDIS_AVAILABLE,
    reason="Redis not available at REDIS_URL"
)


@pytest_asyncio.fixture
async def redis_store():
    """Create a RedisBudgetStore for testing."""
    from app.workflow.policies import RedisBudgetStore

    store = RedisBudgetStore(redis_url=REDIS_URL, ttl_seconds=60)
    yield store
    await store.close()


@pytest_asyncio.fixture
async def cleanup_redis():
    """Clean up test keys after each test."""
    import redis.asyncio as aioredis

    client = aioredis.from_url(REDIS_URL)
    yield
    # Clean up test keys
    keys = await client.keys("workflow:cost:test-*")
    if keys:
        await client.delete(*keys)
    await client.close()


class TestRedisBudgetStoreBasic:
    """Basic CRUD operations."""

    @pytest.mark.asyncio
    async def test_get_returns_zero_for_new_key(self, redis_store, cleanup_redis):
        """Test that get returns 0 for non-existent keys."""
        cost = await redis_store.get_workflow_cost("test-nonexistent")
        assert cost == 0

    @pytest.mark.asyncio
    async def test_add_and_get(self, redis_store, cleanup_redis):
        """Test basic add and get operations."""
        run_id = "test-basic-add"

        # Add cost
        total = await redis_store.add_workflow_cost(run_id, 100)
        assert total == 100

        # Get cost
        cost = await redis_store.get_workflow_cost(run_id)
        assert cost == 100

    @pytest.mark.asyncio
    async def test_multiple_adds_accumulate(self, redis_store, cleanup_redis):
        """Test that multiple adds accumulate correctly."""
        run_id = "test-accumulate"

        await redis_store.add_workflow_cost(run_id, 100)
        await redis_store.add_workflow_cost(run_id, 50)
        await redis_store.add_workflow_cost(run_id, 25)

        cost = await redis_store.get_workflow_cost(run_id)
        assert cost == 175

    @pytest.mark.asyncio
    async def test_reset_clears_cost(self, redis_store, cleanup_redis):
        """Test that reset clears the cost."""
        run_id = "test-reset"

        await redis_store.add_workflow_cost(run_id, 100)
        await redis_store.reset_workflow_cost(run_id)

        cost = await redis_store.get_workflow_cost(run_id)
        assert cost == 0


class TestRedisBudgetStoreConcurrency:
    """Concurrent access tests."""

    @pytest.mark.asyncio
    async def test_concurrent_adds_are_atomic(self, redis_store, cleanup_redis):
        """Test that concurrent INCRBY operations are atomic."""
        run_id = "test-concurrent"
        num_tasks = 100
        cost_per_task = 10

        async def add_cost():
            await redis_store.add_workflow_cost(run_id, cost_per_task)

        # Run 100 concurrent adds
        tasks = [add_cost() for _ in range(num_tasks)]
        await asyncio.gather(*tasks)

        # Total should be exactly 100 * 10 = 1000
        total = await redis_store.get_workflow_cost(run_id)
        assert total == num_tasks * cost_per_task

    @pytest.mark.asyncio
    async def test_concurrent_adds_different_runs(self, redis_store, cleanup_redis):
        """Test concurrent adds to different run IDs."""
        num_runs = 10
        num_tasks_per_run = 50
        cost_per_task = 5

        async def add_cost(run_id: str):
            await redis_store.add_workflow_cost(run_id, cost_per_task)

        # Run concurrent adds across multiple run IDs
        tasks = []
        for run_idx in range(num_runs):
            run_id = f"test-multi-{run_idx}"
            for _ in range(num_tasks_per_run):
                tasks.append(add_cost(run_id))

        await asyncio.gather(*tasks)

        # Verify each run has correct total
        for run_idx in range(num_runs):
            run_id = f"test-multi-{run_idx}"
            total = await redis_store.get_workflow_cost(run_id)
            assert total == num_tasks_per_run * cost_per_task


class TestRedisBudgetStoreMultiWorker:
    """Simulate multi-worker budget enforcement."""

    @pytest.mark.asyncio
    async def test_budget_enforcement_race(self, redis_store, cleanup_redis):
        """
        Simulate multi-worker budget race:
        - 3 workers trying to spend budget concurrently
        - Budget ceiling is 500 cents
        - Each step costs 100 cents
        - Only 5 steps should succeed
        """
        from app.workflow.policies import PolicyEnforcer, BudgetExceededError
        from app.workflow.engine import StepDescriptor, StepContext

        run_id = "test-budget-race"
        budget_ceiling = 500
        step_cost = 100
        num_workers = 3
        steps_per_worker = 3  # Each worker tries 3 steps

        # Create enforcer with shared Redis store
        enforcer = PolicyEnforcer(
            workflow_ceiling_cents=budget_ceiling,
            budget_store=redis_store,
            require_idempotency=False,
        )

        results: List[bool] = []
        lock = asyncio.Lock()

        async def worker_execute_steps(worker_id: int):
            """Simulate a worker executing multiple steps."""
            worker_results = []
            for step_idx in range(steps_per_worker):
                step = StepDescriptor(
                    id=f"step-w{worker_id}-s{step_idx}",
                    skill_id="test_skill",
                    estimated_cost_cents=step_cost,
                )
                ctx = StepContext(
                    workflow_id="wf-budget-test",
                    run_id=run_id,
                    step_id=step.id,
                    step_index=step_idx,
                    seed=12345,
                    inputs={},
                    previous_outputs={},
                )

                try:
                    await enforcer.check_can_execute(step, ctx)
                    worker_results.append(True)
                except BudgetExceededError:
                    worker_results.append(False)

            async with lock:
                results.extend(worker_results)

        # Run workers concurrently
        tasks = [worker_execute_steps(i) for i in range(num_workers)]
        await asyncio.gather(*tasks)

        # Count successes
        successes = sum(1 for r in results if r)
        failures = sum(1 for r in results if not r)

        # With ceiling=500 and cost=100, exactly 5 steps should succeed
        assert successes == 5, f"Expected 5 successes, got {successes}"
        assert failures == 4, f"Expected 4 failures, got {failures}"

        # Final cost should be exactly 500
        final_cost = await redis_store.get_workflow_cost(run_id)
        assert final_cost == 500


class TestRedisBudgetStoreTTL:
    """TTL and expiration tests."""

    @pytest.mark.asyncio
    async def test_key_has_ttl(self, cleanup_redis):
        """Test that keys are set with TTL."""
        from app.workflow.policies import RedisBudgetStore
        import redis.asyncio as aioredis

        ttl_seconds = 10
        store = RedisBudgetStore(redis_url=REDIS_URL, ttl_seconds=ttl_seconds)

        run_id = "test-ttl"
        await store.add_workflow_cost(run_id, 100)

        # Check TTL directly
        client = aioredis.from_url(REDIS_URL)
        key = f"workflow:cost:{run_id}"
        actual_ttl = await client.ttl(key)
        await client.close()
        await store.close()

        # TTL should be close to configured value (allow 2s tolerance)
        assert actual_ttl > 0
        assert actual_ttl <= ttl_seconds


class TestRedisBudgetStoreResilience:
    """Connection resilience tests."""

    @pytest.mark.asyncio
    async def test_graceful_degradation_on_connection_failure(self):
        """Test that store degrades gracefully on connection failure."""
        from app.workflow.policies import RedisBudgetStore

        # Use invalid URL
        store = RedisBudgetStore(redis_url="redis://invalid-host:6379/0")

        # Should return 0 on failure, not raise
        cost = await store.get_workflow_cost("test-fail")
        assert cost == 0

        # Should return cost on failure, not raise
        total = await store.add_workflow_cost("test-fail", 100)
        assert total == 100  # Returns the cost that was attempted

        await store.close()


class TestPolicyEnforcerWithRedis:
    """Full integration with PolicyEnforcer."""

    @pytest.mark.asyncio
    async def test_enforcer_tracks_across_steps(self, redis_store, cleanup_redis):
        """Test PolicyEnforcer tracks budget across multiple steps."""
        from app.workflow.policies import PolicyEnforcer
        from app.workflow.engine import StepDescriptor, StepContext

        enforcer = PolicyEnforcer(
            workflow_ceiling_cents=300,
            budget_store=redis_store,
            require_idempotency=False,
        )

        run_id = "test-tracking"

        # Execute 3 steps of 100 cents each
        for i in range(3):
            step = StepDescriptor(
                id=f"step-{i}",
                skill_id="test",
                estimated_cost_cents=100,
            )
            ctx = StepContext(
                workflow_id="wf",
                run_id=run_id,
                step_id=step.id,
                step_index=i,
                seed=1,
                inputs={},
                previous_outputs={},
            )
            await enforcer.check_can_execute(step, ctx)

        # Verify total in Redis
        total = await redis_store.get_workflow_cost(run_id)
        assert total == 300

    @pytest.mark.asyncio
    async def test_enforcer_async_methods(self, redis_store, cleanup_redis):
        """Test async helper methods on PolicyEnforcer."""
        from app.workflow.policies import PolicyEnforcer

        enforcer = PolicyEnforcer(
            budget_store=redis_store,
            require_idempotency=False,
        )

        run_id = "test-async-methods"

        # Record cost
        await enforcer.record_step_cost_async(run_id, 50)
        await enforcer.record_step_cost_async(run_id, 30)

        # Get cost async
        total = await enforcer.get_workflow_cost_async(run_id)
        assert total == 80

        # Reset
        await enforcer.reset_workflow_costs_async(run_id)
        total = await enforcer.get_workflow_cost_async(run_id)
        assert total == 0
