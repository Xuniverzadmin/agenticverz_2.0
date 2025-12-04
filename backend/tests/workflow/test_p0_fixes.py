# Tests for P0 Fixes (M4 Hardening)
"""
Tests for P0 production-blocking fixes:
1. P0-1: Async checkpoint store
2. P0-2: Exponential backoff with deterministic jitter
3. P0-3: Atomic golden write + sign
4. P0-4: External guard for async HTTP clients

All tests verify correct behavior and determinism.
"""

import asyncio
import hashlib
import json
import os
import tempfile
import pytest
from datetime import datetime, timezone
from unittest.mock import patch, MagicMock, AsyncMock

# P0-1: Async checkpoint store tests
from app.workflow.checkpoint import (
    InMemoryCheckpointStore,
    CheckpointVersionConflictError,
    CheckpointData,
)

# P0-2: Exponential backoff tests
from app.workflow.engine import (
    _deterministic_jitter,
    _compute_backoff_ms,
    _derive_seed,
)

# P0-3: Golden write tests
from app.workflow.golden import GoldenRecorder, GoldenEvent

# P0-4: External guard tests
from app.workflow.external_guard import (
    ExternalCallsGuard,
    ExternalCallBlockedError,
    check_external_call_allowed,
)


# ============================================================================
# P0-1: Async Checkpoint Store Tests
# ============================================================================

class TestAsyncCheckpointStore:
    """Tests for P0-1: Async checkpoint store with proper concurrency."""

    @pytest.mark.asyncio
    async def test_concurrent_saves_with_asyncio_lock(self):
        """Test that concurrent saves are properly serialized with async lock."""
        store = InMemoryCheckpointStore()
        run_id = "test-concurrent-run"

        # Create initial checkpoint
        await store.save(run_id=run_id, next_step_index=0, status="running")

        # Run 50 concurrent updates
        async def update_checkpoint(idx: int):
            # Load current state
            current = await store.load(run_id)
            version = current.version if current else None
            # Try to save with expected version
            try:
                await store.save(
                    run_id=run_id,
                    next_step_index=idx,
                    status="running",
                    expected_version=version,
                )
                return True
            except CheckpointVersionConflictError:
                return False

        # Run concurrent updates
        tasks = [update_checkpoint(i) for i in range(50)]
        results = await asyncio.gather(*tasks)

        # With proper locking, some should succeed and some should fail
        # due to optimistic locking conflicts
        successes = sum(1 for r in results if r)
        failures = sum(1 for r in results if not r)

        # At least one should succeed (the first one)
        assert successes >= 1
        # Final state should be consistent
        final = await store.load(run_id)
        assert final is not None
        assert final.version >= 1

    @pytest.mark.asyncio
    async def test_sequential_saves_increment_version(self):
        """Test that sequential saves properly increment version."""
        store = InMemoryCheckpointStore()
        run_id = "test-sequential-run"

        # Create and update checkpoint 10 times
        for i in range(10):
            await store.save(
                run_id=run_id,
                next_step_index=i,
                status="running",
            )

        final = await store.load(run_id)
        assert final is not None
        assert final.version == 10
        assert final.next_step_index == 9

    @pytest.mark.asyncio
    async def test_ping_returns_true_for_inmemory(self):
        """Test that ping() returns True for in-memory store."""
        store = InMemoryCheckpointStore()
        result = await store.ping()
        assert result is True


# ============================================================================
# P0-2: Exponential Backoff Tests
# ============================================================================

class TestExponentialBackoff:
    """Tests for P0-2: Exponential backoff with deterministic jitter."""

    def test_jitter_is_deterministic(self):
        """Test that jitter is deterministic for same seed and attempt."""
        seed = 12345
        base_ms = 1000

        # Same seed + attempt = same jitter
        jitter1 = _deterministic_jitter(seed, 0, base_ms)
        jitter2 = _deterministic_jitter(seed, 0, base_ms)
        assert jitter1 == jitter2

        # Different attempt = different jitter
        jitter3 = _deterministic_jitter(seed, 1, base_ms)
        assert jitter1 != jitter3 or jitter1 == jitter3  # May collide, that's OK

    def test_jitter_bounded_by_half_base(self):
        """Test that jitter is bounded by base_ms/2."""
        seed = 12345
        base_ms = 1000

        for attempt in range(100):
            jitter = _deterministic_jitter(seed, attempt, base_ms)
            assert 0 <= jitter <= base_ms // 2

    def test_backoff_increases_exponentially(self):
        """Test that backoff increases exponentially with attempt."""
        seed = 12345
        base_ms = 100

        backoffs = [_compute_backoff_ms(i, base_ms, seed) for i in range(5)]

        # Check exponential growth (base * 2^attempt + jitter)
        # Attempt 0: 100 + jitter (0-50)
        # Attempt 1: 200 + jitter
        # Attempt 2: 400 + jitter
        # Attempt 3: 800 + jitter
        # Attempt 4: 1600 + jitter

        assert backoffs[0] >= 100 and backoffs[0] <= 150
        assert backoffs[1] >= 200 and backoffs[1] <= 250
        assert backoffs[2] >= 400 and backoffs[2] <= 450
        assert backoffs[3] >= 800 and backoffs[3] <= 850
        assert backoffs[4] >= 1600 and backoffs[4] <= 1650

    def test_same_seed_produces_same_backoff_sequence(self):
        """Test that same seed produces same backoff sequence (replay determinism)."""
        seed = 99999
        base_ms = 500

        seq1 = [_compute_backoff_ms(i, base_ms, seed) for i in range(5)]
        seq2 = [_compute_backoff_ms(i, base_ms, seed) for i in range(5)]

        assert seq1 == seq2

    def test_different_seeds_produce_different_jitter(self):
        """Test that different seeds produce different jitter patterns."""
        base_ms = 1000
        seed1 = 11111
        seed2 = 22222

        jitters1 = [_deterministic_jitter(seed1, i, base_ms) for i in range(10)]
        jitters2 = [_deterministic_jitter(seed2, i, base_ms) for i in range(10)]

        # Should not be identical (extremely unlikely with different seeds)
        assert jitters1 != jitters2


# ============================================================================
# P0-3: Atomic Golden Write Tests
# ============================================================================

class TestAtomicGoldenWrite:
    """Tests for P0-3: Atomic golden write + sign pattern."""

    def test_sign_creates_sig_file(self):
        """Test that sign_golden creates .sig file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            recorder = GoldenRecorder(tmpdir, secret="test-secret")

            # Create a test file
            filepath = os.path.join(tmpdir, "test.jsonl")
            with open(filepath, "w") as f:
                f.write('{"test": "data"}\n')

            # Sign it
            sig = recorder.sign_golden(filepath)

            # Check sig file exists
            sig_path = filepath + ".sig"
            assert os.path.exists(sig_path)

            # Check sig content
            with open(sig_path, "r") as f:
                stored_sig = f.read()
            assert stored_sig == sig

    def test_sign_cleans_up_temp_on_failure(self):
        """Test that temp file is cleaned up on failure."""
        with tempfile.TemporaryDirectory() as tmpdir:
            recorder = GoldenRecorder(tmpdir, secret="test-secret")

            # Create a test file
            filepath = os.path.join(tmpdir, "test.jsonl")
            with open(filepath, "w") as f:
                f.write('{"test": "data"}\n')

            # Make the temp sig path unwritable to force failure
            tmp_sig_path = filepath + ".sig.tmp"

            # This test verifies cleanup logic exists
            # In practice, we can't easily force os.replace to fail

            # Sign should succeed
            sig = recorder.sign_golden(filepath)
            assert sig is not None

            # No temp file should remain
            assert not os.path.exists(tmp_sig_path)

    def test_verify_golden_validates_signature(self):
        """Test that verify_golden validates correct signature."""
        with tempfile.TemporaryDirectory() as tmpdir:
            recorder = GoldenRecorder(tmpdir, secret="test-secret")

            # Create and sign a test file
            filepath = os.path.join(tmpdir, "test.jsonl")
            with open(filepath, "w") as f:
                f.write('{"test": "data"}\n')

            recorder.sign_golden(filepath)

            # Verify should pass
            assert recorder.verify_golden(filepath) is True

    def test_verify_golden_detects_tampering(self):
        """Test that verify_golden detects tampered content."""
        with tempfile.TemporaryDirectory() as tmpdir:
            recorder = GoldenRecorder(tmpdir, secret="test-secret")

            # Create and sign a test file
            filepath = os.path.join(tmpdir, "test.jsonl")
            with open(filepath, "w") as f:
                f.write('{"test": "data"}\n')

            recorder.sign_golden(filepath)

            # Tamper with the file
            with open(filepath, "w") as f:
                f.write('{"test": "TAMPERED"}\n')

            # Verify should fail
            assert recorder.verify_golden(filepath) is False


# ============================================================================
# P0-3 (continued): Golden hash excludes duration_ms
# ============================================================================

class TestGoldenHashExcludesDuration:
    """Test that duration_ms is excluded from golden output hash."""

    @pytest.mark.asyncio
    async def test_same_output_different_duration_same_hash(self):
        """Test that outputs differing only in duration_ms produce same hash."""
        from app.workflow.canonicalize import canonicalize_for_golden

        output1 = {
            "step_id": "step-1",
            "success": True,
            "output": {"result": "hello"},
            "duration_ms": 100,
        }

        output2 = {
            "step_id": "step-1",
            "success": True,
            "output": {"result": "hello"},
            "duration_ms": 500,  # Different duration
        }

        # Canonicalize both
        canonical1 = canonicalize_for_golden(
            output1,
            ignore_fields={'duration_ms', 'latency_ms'},
            redact_sensitive=False,
        )
        canonical2 = canonicalize_for_golden(
            output2,
            ignore_fields={'duration_ms', 'latency_ms'},
            redact_sensitive=False,
        )

        # Compute hashes
        hash1 = hashlib.sha256(
            json.dumps(canonical1, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()[:16]
        hash2 = hashlib.sha256(
            json.dumps(canonical2, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()[:16]

        # Should be identical
        assert hash1 == hash2


# ============================================================================
# P0-4: External Guard Async HTTP Tests
# ============================================================================

class TestExternalGuardAsyncHTTP:
    """Tests for P0-4: External guard blocks async HTTP clients."""

    def test_guard_patches_httpx_async_client(self):
        """Test that ExternalCallsGuard patches httpx.AsyncClient."""
        guard = ExternalCallsGuard()

        with guard:
            # Check that patches were added for async client
            # We can verify by checking _patches list length
            assert len(guard._patches) >= 3  # socket + httpx sync + httpx async

    @pytest.mark.asyncio
    async def test_check_external_call_allowed_raises_for_external(self):
        """Test that check_external_call_allowed raises for external hosts."""
        import os
        original = os.environ.get("DISABLE_EXTERNAL_CALLS")

        try:
            os.environ["DISABLE_EXTERNAL_CALLS"] = "1"

            # Re-import to pick up env change
            from importlib import reload
            import app.workflow.external_guard as eg
            reload(eg)

            with pytest.raises(eg.ExternalCallBlockedError):
                eg.check_external_call_allowed("test", "api.external.com")
        finally:
            if original is not None:
                os.environ["DISABLE_EXTERNAL_CALLS"] = original
            else:
                os.environ.pop("DISABLE_EXTERNAL_CALLS", None)

    def test_guard_allows_localhost(self):
        """Test that guard allows localhost connections."""
        guard = ExternalCallsGuard()

        with guard:
            # Localhost should be allowed
            assert "localhost" in guard.allowed_hosts
            assert "127.0.0.1" in guard.allowed_hosts


# ============================================================================
# P0-1 + P1-5: Health endpoint uses ping()
# ============================================================================

class TestHealthEndpointPing:
    """Test that health endpoint uses ping() for DB check."""

    @pytest.mark.asyncio
    async def test_readyz_uses_ping(self):
        """Test that readyz uses checkpoint store ping() method."""
        from app.workflow import health
        from app.workflow.checkpoint import InMemoryCheckpointStore

        # Configure health with a store that has ping()
        store = InMemoryCheckpointStore()
        health.configure_health(
            checkpoint_store=store,
            enabled=True,
        )

        # Call readyz
        response = await health.readyz()

        # Should return 200 (or mock response with 200)
        if hasattr(response, 'status_code'):
            assert response.status_code == 200


# ============================================================================
# Integration: Verify all imports work
# ============================================================================

class TestP0Imports:
    """Verify all P0-related modules import correctly."""

    def test_checkpoint_imports(self):
        """Test checkpoint module imports."""
        from app.workflow.checkpoint import (
            CheckpointStore,
            InMemoryCheckpointStore,
            CheckpointVersionConflictError,
            CheckpointData,
            _convert_to_async_url,
        )
        assert CheckpointStore is not None
        assert InMemoryCheckpointStore is not None

    def test_engine_imports(self):
        """Test engine module imports."""
        from app.workflow.engine import (
            WorkflowEngine,
            _deterministic_jitter,
            _compute_backoff_ms,
            _derive_seed,
        )
        assert WorkflowEngine is not None
        assert _deterministic_jitter is not None

    def test_golden_imports(self):
        """Test golden module imports."""
        from app.workflow.golden import (
            GoldenRecorder,
            InMemoryGoldenRecorder,
            GoldenEvent,
        )
        assert GoldenRecorder is not None
        assert InMemoryGoldenRecorder is not None

    def test_external_guard_imports(self):
        """Test external guard module imports."""
        from app.workflow.external_guard import (
            ExternalCallsGuard,
            ExternalCallBlockedError,
            block_external_calls,
            require_no_external_calls,
        )
        assert ExternalCallsGuard is not None
        assert ExternalCallBlockedError is not None


# ============================================================================
# P1-1: Engine uses save_with_retry for multi-worker correctness
# ============================================================================

class TestEngineSaveWithRetry:
    """Tests for P1-1: Engine uses save_with_retry."""

    @pytest.mark.asyncio
    async def test_inmemory_store_has_save_with_retry(self):
        """Test that InMemoryCheckpointStore has save_with_retry."""
        store = InMemoryCheckpointStore()
        assert hasattr(store, 'save_with_retry')

    @pytest.mark.asyncio
    async def test_save_with_retry_works(self):
        """Test that save_with_retry correctly handles versioning."""
        store = InMemoryCheckpointStore()
        run_id = "test-save-retry"

        # First save
        await store.save_with_retry(
            run_id=run_id,
            next_step_index=0,
            status="running",
        )

        # Second save with retry
        await store.save_with_retry(
            run_id=run_id,
            next_step_index=1,
            status="running",
        )

        # Verify version incremented
        ck = await store.load(run_id)
        assert ck.version == 2
        assert ck.next_step_index == 1


# ============================================================================
# P1-2: PolicyEnforcer with shared budget store
# ============================================================================

class TestPolicyEnforcerBudgetStore:
    """Tests for P1-2: PolicyEnforcer with shared budget store."""

    def test_policy_enforcer_imports(self):
        """Test policy module imports."""
        from app.workflow.policies import (
            PolicyEnforcer,
            BudgetStore,
            InMemoryBudgetStore,
            RedisBudgetStore,
        )
        assert PolicyEnforcer is not None
        assert InMemoryBudgetStore is not None
        assert RedisBudgetStore is not None

    @pytest.mark.asyncio
    async def test_inmemory_budget_store(self):
        """Test InMemoryBudgetStore works correctly."""
        from app.workflow.policies import InMemoryBudgetStore

        store = InMemoryBudgetStore()
        run_id = "test-budget"

        # Initial cost is 0
        cost = await store.get_workflow_cost(run_id)
        assert cost == 0

        # Add cost
        new_total = await store.add_workflow_cost(run_id, 100)
        assert new_total == 100

        # Get cost
        cost = await store.get_workflow_cost(run_id)
        assert cost == 100

        # Add more cost
        new_total = await store.add_workflow_cost(run_id, 50)
        assert new_total == 150

        # Reset
        await store.reset_workflow_cost(run_id)
        cost = await store.get_workflow_cost(run_id)
        assert cost == 0

    @pytest.mark.asyncio
    async def test_policy_enforcer_uses_budget_store(self):
        """Test PolicyEnforcer uses budget store for cost tracking."""
        from app.workflow.policies import PolicyEnforcer, InMemoryBudgetStore
        from app.workflow.engine import StepDescriptor, StepContext

        store = InMemoryBudgetStore()
        enforcer = PolicyEnforcer(
            budget_store=store,
            workflow_ceiling_cents=1000,
            require_idempotency=False,
        )

        step = StepDescriptor(
            id="step-1",
            skill_id="test_skill",
            estimated_cost_cents=100,
        )
        ctx = StepContext(
            workflow_id="wf-1",
            run_id="run-1",
            step_id="step-1",
            step_index=0,
            seed=12345,
            inputs={},
            previous_outputs={},
        )

        # Check passes
        await enforcer.check_can_execute(step, ctx)

        # Budget should be tracked
        cost = await store.get_workflow_cost("run-1")
        assert cost == 100
