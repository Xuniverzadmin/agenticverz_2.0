# M4 Hardening Tests
"""
Tests for M4 hardening features:
1. Checkpoint concurrency (version-based optimistic locking)
2. Error taxonomy and classification
3. Golden canonicalization
4. External calls guard
5. Sensitive field redaction
"""

import asyncio

import pytest

from app.workflow.canonicalize import (
    canonical_hash,
    canonical_json,
    canonicalize_for_golden,
    compare_canonical,
    redact_sensitive_fields,
    strip_volatile_from_events,
)
from app.workflow.checkpoint import (
    CheckpointVersionConflictError,
    InMemoryCheckpointStore,
)
from app.workflow.errors import (
    ErrorCategory,
    WorkflowError,
    WorkflowErrorCode,
    classify_exception,
    get_error_metadata,
)
from app.workflow.external_guard import (
    ExternalCallBlockedError,
    check_external_call_allowed,
    clear_blocked_calls,
    get_blocked_calls,
)
from app.workflow.policies import BudgetExceededError, PolicyViolationError

# ============== Checkpoint Concurrency Tests ==============


class TestCheckpointConcurrency:
    """Tests for checkpoint version-based optimistic locking."""

    @pytest.mark.asyncio
    async def test_version_increments_on_save(self):
        """Version increments with each save."""
        store = InMemoryCheckpointStore()

        await store.save(run_id="test-1", next_step_index=0, status="running")
        ck1 = await store.load("test-1")
        assert ck1.version == 1

        await store.save(run_id="test-1", next_step_index=1, status="running")
        ck2 = await store.load("test-1")
        assert ck2.version == 2

        await store.save(run_id="test-1", next_step_index=2, status="completed")
        ck3 = await store.load("test-1")
        assert ck3.version == 3

    @pytest.mark.asyncio
    async def test_version_conflict_detection(self):
        """Detects version conflict on concurrent update."""
        store = InMemoryCheckpointStore()

        await store.save(run_id="conflict-1", next_step_index=0, status="running")
        ck = await store.load("conflict-1")

        # First update with correct version
        await store.save(
            run_id="conflict-1",
            next_step_index=1,
            status="running",
            expected_version=ck.version,
        )

        # Second update with stale version should fail
        with pytest.raises(CheckpointVersionConflictError) as exc_info:
            await store.save(
                run_id="conflict-1",
                next_step_index=2,
                status="running",
                expected_version=ck.version,  # Stale version
            )

        assert exc_info.value.run_id == "conflict-1"
        assert exc_info.value.expected_version == ck.version
        assert exc_info.value.actual_version == ck.version + 1

    @pytest.mark.asyncio
    async def test_concurrent_saves_detect_conflicts(self):
        """Multiple concurrent saves detect conflicts."""
        store = InMemoryCheckpointStore()
        await store.save(run_id="concurrent-1", next_step_index=0, status="running")

        conflicts = []
        successes = []

        async def update_checkpoint(worker_id: int):
            try:
                ck = await store.load("concurrent-1")
                # Simulate some work
                await asyncio.sleep(0.01)
                await store.save(
                    run_id="concurrent-1",
                    next_step_index=worker_id,
                    status="running",
                    expected_version=ck.version,
                )
                successes.append(worker_id)
            except CheckpointVersionConflictError:
                conflicts.append(worker_id)

        # Run 5 concurrent updates
        await asyncio.gather(*[update_checkpoint(i) for i in range(5)])

        # Only one should succeed, others should conflict
        assert len(successes) == 1
        assert len(conflicts) == 4

    @pytest.mark.asyncio
    async def test_new_checkpoint_no_version_check(self):
        """New checkpoint doesn't need version check."""
        store = InMemoryCheckpointStore()

        # First save with no expected_version for new checkpoint
        await store.save(
            run_id="new-1",
            next_step_index=0,
            status="running",
            expected_version=None,
        )

        ck = await store.load("new-1")
        assert ck.version == 1

    @pytest.mark.asyncio
    async def test_tenant_id_preserved(self):
        """Tenant ID is preserved across saves."""
        store = InMemoryCheckpointStore()

        await store.save(
            run_id="tenant-1",
            next_step_index=0,
            status="running",
            tenant_id="tenant-abc",
        )

        ck = await store.load("tenant-1")
        assert ck.tenant_id == "tenant-abc"

        await store.save(
            run_id="tenant-1",
            next_step_index=1,
            status="completed",
        )

        ck2 = await store.load("tenant-1")
        assert ck2.tenant_id == "tenant-abc"  # Preserved


# ============== Error Taxonomy Tests ==============


class TestErrorTaxonomy:
    """Tests for error taxonomy and classification."""

    def test_all_error_codes_have_metadata(self):
        """All error codes have metadata defined."""
        for code in WorkflowErrorCode:
            meta = get_error_metadata(code)
            assert "category" in meta
            assert "http_status" in meta
            assert "retryable" in meta
            assert "recovery" in meta

    def test_transient_errors_are_retryable(self):
        """Transient category errors are retryable."""
        transient_codes = [
            WorkflowErrorCode.TIMEOUT,
            WorkflowErrorCode.DNS_FAILURE,
            WorkflowErrorCode.CONNECTION_RESET,
            WorkflowErrorCode.SERVICE_UNAVAILABLE,
        ]
        for code in transient_codes:
            meta = get_error_metadata(code)
            assert meta["category"] == ErrorCategory.TRANSIENT
            assert meta["retryable"] is True

    def test_permanent_errors_not_retryable(self):
        """Permanent category errors are not retryable."""
        permanent_codes = [
            WorkflowErrorCode.SKILL_NOT_FOUND,
            WorkflowErrorCode.INVALID_SKILL,
            WorkflowErrorCode.STEP_FAILED,
        ]
        for code in permanent_codes:
            meta = get_error_metadata(code)
            assert meta["category"] == ErrorCategory.PERMANENT
            assert meta["retryable"] is False

    def test_budget_errors_classification(self):
        """Budget exceeded errors are properly classified."""
        exc = BudgetExceededError(
            "Step cost exceeded",
            breach_type="step_ceiling",
            limit_cents=100,
            current_cents=150,
        )
        error = classify_exception(exc, {"step_id": "s1"})

        assert error.code == WorkflowErrorCode.STEP_CEILING_EXCEEDED
        assert error.category == ErrorCategory.RESOURCE
        assert error.step_id == "s1"
        assert error.details["limit"] == 100
        assert error.details["current"] == 150

    def test_policy_errors_classification(self):
        """Policy violation errors are properly classified."""
        exc = PolicyViolationError(
            "Emergency stop enabled",
            policy="emergency_stop",
        )
        error = classify_exception(exc)

        assert error.code == WorkflowErrorCode.EMERGENCY_STOP
        assert error.category == ErrorCategory.PERMISSION

    def test_workflow_error_to_dict(self):
        """WorkflowError serializes correctly."""
        error = WorkflowError(
            code=WorkflowErrorCode.TIMEOUT,
            message="Request timed out",
            details={"timeout_ms": 5000},
            step_id="step-1",
            run_id="run-1",
        )

        d = error.to_dict()

        assert d["code"] == "TIMEOUT"
        assert d["category"] == "transient"
        assert d["message"] == "Request timed out"
        assert d["retryable"] is True
        assert "recovery" in d

    def test_error_category_is_retryable(self):
        """ErrorCategory.is_retryable() works correctly."""
        assert ErrorCategory.TRANSIENT.is_retryable() is True
        assert ErrorCategory.INFRASTRUCTURE.is_retryable() is True
        assert ErrorCategory.PERMANENT.is_retryable() is False
        assert ErrorCategory.RESOURCE.is_retryable() is False
        assert ErrorCategory.PERMISSION.is_retryable() is False


# ============== Canonicalization Tests ==============


class TestCanonicalization:
    """Tests for golden file canonicalization."""

    def test_removes_volatile_fields(self):
        """Removes default volatile fields."""
        obj = {
            "id": "test-1",
            "value": 42,
            "timestamp": "2025-01-01T00:00:00Z",
            "created_at": "2025-01-01T00:00:00Z",
            "duration_ms": 100,
        }

        canonical = canonicalize_for_golden(obj)

        assert "id" in canonical
        assert "value" in canonical
        assert "timestamp" not in canonical
        assert "created_at" not in canonical
        assert "duration_ms" not in canonical

    def test_redacts_sensitive_fields(self):
        """Redacts sensitive fields."""
        obj = {
            "user": "test",
            "password": "secret123",
            "api_key": "key-abc",
            "data": "normal",
        }

        canonical = canonicalize_for_golden(obj, redact_sensitive=True)

        assert canonical["user"] == "test"
        assert canonical["password"] == "[REDACTED]"
        assert canonical["api_key"] == "[REDACTED]"
        assert canonical["data"] == "normal"

    def test_normalizes_floats(self):
        """Normalizes float precision."""
        obj = {
            "value": 3.141592653589793,
            "small": 0.0000001234567,
        }

        canonical = canonicalize_for_golden(obj, float_precision=4)

        assert canonical["value"] == 3.1416
        assert canonical["small"] == 0.0

    def test_sorts_keys_deterministically(self):
        """Keys are sorted for deterministic output."""
        obj = {"z": 1, "a": 2, "m": 3}

        json_str = canonical_json(obj)

        # Keys should be in alphabetical order
        assert json_str.index('"a"') < json_str.index('"m"')
        assert json_str.index('"m"') < json_str.index('"z"')

    def test_canonical_hash_deterministic(self):
        """Same content produces same hash."""
        obj1 = {"a": 1, "b": 2}
        obj2 = {"b": 2, "a": 1}  # Different order

        hash1 = canonical_hash(obj1)
        hash2 = canonical_hash(obj2)

        assert hash1 == hash2

    def test_compare_canonical_finds_diffs(self):
        """Comparison finds differences."""
        actual = {"id": "1", "value": 42, "extra": "field"}
        expected = {"id": "1", "value": 100}

        result = compare_canonical(actual, expected)

        assert result["match"] is False
        assert len(result["diffs"]) >= 1

        # Find value mismatch
        value_diff = next((d for d in result["diffs"] if d["path"] == "value"), None)
        assert value_diff is not None
        assert value_diff["actual"] == 42
        assert value_diff["expected"] == 100

    def test_compare_canonical_ignores_volatile(self):
        """Comparison ignores volatile fields."""
        actual = {"id": "1", "timestamp": "2025-01-01"}
        expected = {"id": "1", "timestamp": "2025-01-02"}

        result = compare_canonical(actual, expected)

        assert result["match"] is True

    def test_strip_volatile_from_events(self):
        """Strips volatile fields from event list."""
        events = [
            {"event_type": "start", "timestamp": "T1", "data": {"x": 1}},
            {"event_type": "end", "timestamp": "T2", "data": {"y": 2}},
        ]

        stripped = strip_volatile_from_events(events)

        for event in stripped:
            assert "timestamp" not in event

    def test_nested_redaction(self):
        """Redacts sensitive fields in nested objects."""
        obj = {
            "user": "test",
            "auth": {
                "token": "secret-token",
                "refresh_token": "refresh-secret",
            },
            "nested": {
                "deep": {
                    "api_key": "nested-key",
                }
            },
        }

        redacted = redact_sensitive_fields(obj)

        assert redacted["auth"]["token"] == "[REDACTED]"
        assert redacted["auth"]["refresh_token"] == "[REDACTED]"
        assert redacted["nested"]["deep"]["api_key"] == "[REDACTED]"


# ============== External Guard Tests ==============


class TestExternalGuard:
    """Tests for external calls guard."""

    def test_guard_blocks_check_external_call(self):
        """check_external_call_allowed raises when disabled."""
        import os

        original = os.environ.get("DISABLE_EXTERNAL_CALLS")

        try:
            os.environ["DISABLE_EXTERNAL_CALLS"] = "1"
            # Reload to pick up env change
            import importlib

            from app.workflow import external_guard

            importlib.reload(external_guard)

            with pytest.raises(external_guard.ExternalCallBlockedError):
                external_guard.check_external_call_allowed("http", "api.example.com")

        finally:
            if original:
                os.environ["DISABLE_EXTERNAL_CALLS"] = original
            else:
                os.environ.pop("DISABLE_EXTERNAL_CALLS", None)
            importlib.reload(external_guard)

    def test_guard_allows_localhost(self):
        """Allows localhost connections."""
        clear_blocked_calls()

        # Should not raise for localhost
        check_external_call_allowed(
            "socket",
            "localhost",
            allowed_hosts={"localhost", "127.0.0.1"},
        )

        assert len(get_blocked_calls()) == 0

    def test_blocked_calls_tracked(self):
        """Blocked calls are tracked."""
        import os

        original = os.environ.get("DISABLE_EXTERNAL_CALLS")

        try:
            os.environ["DISABLE_EXTERNAL_CALLS"] = "1"
            import importlib

            from app.workflow import external_guard

            importlib.reload(external_guard)

            external_guard.clear_blocked_calls()

            try:
                external_guard.check_external_call_allowed("http", "api.example.com")
            except external_guard.ExternalCallBlockedError:
                pass

            blocked = external_guard.get_blocked_calls()
            assert len(blocked) == 1
            assert blocked[0] == ("http", "api.example.com")

        finally:
            if original:
                os.environ["DISABLE_EXTERNAL_CALLS"] = original
            else:
                os.environ.pop("DISABLE_EXTERNAL_CALLS", None)
            importlib.reload(external_guard)

    def test_external_call_blocked_error_message(self):
        """Error message includes call details."""
        error = ExternalCallBlockedError("http", "api.example.com", "Test message")

        assert "http" in str(error)
        assert "api.example.com" in str(error)
        assert error.call_type == "http"
        assert error.target == "api.example.com"


# ============== Integration Tests ==============


class TestHardeningIntegration:
    """Integration tests for hardening features."""

    @pytest.mark.asyncio
    async def test_checkpoint_with_error_codes(self):
        """Checkpoint stores error codes properly."""
        store = InMemoryCheckpointStore()

        error = WorkflowError(
            code=WorkflowErrorCode.STEP_FAILED,
            message="Step execution failed",
            step_id="s1",
        )

        await store.save(
            run_id="error-run",
            next_step_index=1,
            status="failed",
            step_outputs={
                "s1": {
                    "error": error.to_dict(),
                }
            },
        )

        ck = await store.load("error-run")
        assert ck.status == "failed"
        assert ck.step_outputs["s1"]["error"]["code"] == "STEP_FAILED"

    def test_canonical_error_serialization(self):
        """Error serialization is canonical."""
        error1 = WorkflowError(
            code=WorkflowErrorCode.TIMEOUT,
            message="Timed out",
            details={"timeout_ms": 5000},
        )
        error2 = WorkflowError(
            code=WorkflowErrorCode.TIMEOUT,
            message="Timed out",
            details={"timeout_ms": 5000},
        )

        json1 = canonical_json(error1.to_dict())
        json2 = canonical_json(error2.to_dict())

        assert json1 == json2


# ============== Budget Snapshot Tests ==============


class TestBudgetSnapshot:
    """Tests for budget snapshot in golden header."""

    @pytest.mark.asyncio
    async def test_golden_header_includes_budget_snapshot(self):
        """Golden header should include budget_snapshot when policy is present."""
        from app.workflow.checkpoint import InMemoryCheckpointStore
        from app.workflow.engine import StepDescriptor, WorkflowEngine, WorkflowSpec
        from app.workflow.golden import InMemoryGoldenRecorder
        from app.workflow.policies import PolicyEnforcer

        class SimpleRegistry:
            def get(self, skill_id: str):
                if skill_id == "noop":
                    return self._noop
                return None

            async def _noop(self, inputs):
                return {"ok": True}

        checkpoint = InMemoryCheckpointStore()
        golden = InMemoryGoldenRecorder()
        policy = PolicyEnforcer(step_ceiling_cents=100, workflow_ceiling_cents=500)

        engine = WorkflowEngine(
            registry=SimpleRegistry(),
            checkpoint_store=checkpoint,
            golden=golden,
            policy=policy,
        )

        spec = WorkflowSpec(
            id="budget-snapshot-test",
            name="Budget Snapshot Test",
            steps=[StepDescriptor(id="s1", skill_id="noop")],
        )

        await engine.run(spec, run_id="budget-run", seed=42)

        events = golden.get_events("budget-run")
        start_event = next(e for e in events if e.event_type == "run_start")

        # Verify budget_snapshot is present
        assert "budget_snapshot" in start_event.data
        snapshot = start_event.data["budget_snapshot"]
        assert "step_ceiling_cents" in snapshot
        assert "workflow_ceiling_cents" in snapshot
        assert "policy_version" in snapshot
        assert snapshot["step_ceiling_cents"] == 100
        assert snapshot["workflow_ceiling_cents"] == 500

    @pytest.mark.asyncio
    async def test_golden_header_no_budget_snapshot_without_policy(self):
        """Golden header should not have budget_snapshot without policy."""
        from app.workflow.checkpoint import InMemoryCheckpointStore
        from app.workflow.engine import StepDescriptor, WorkflowEngine, WorkflowSpec
        from app.workflow.golden import InMemoryGoldenRecorder

        class SimpleRegistry:
            def get(self, skill_id: str):
                if skill_id == "noop":
                    return self._noop
                return None

            async def _noop(self, inputs):
                return {"ok": True}

        checkpoint = InMemoryCheckpointStore()
        golden = InMemoryGoldenRecorder()

        engine = WorkflowEngine(
            registry=SimpleRegistry(),
            checkpoint_store=checkpoint,
            golden=golden,
            # No policy
        )

        spec = WorkflowSpec(
            id="no-budget-test",
            name="No Budget Test",
            steps=[StepDescriptor(id="s1", skill_id="noop")],
        )

        await engine.run(spec, run_id="no-budget-run", seed=42)

        events = golden.get_events("no-budget-run")
        start_event = next(e for e in events if e.event_type == "run_start")

        # budget_snapshot should not be present (or be None)
        assert start_event.data.get("budget_snapshot") is None

    @pytest.mark.asyncio
    async def test_budget_snapshot_deterministic(self):
        """Budget snapshot should be deterministic across runs."""
        from app.workflow.checkpoint import InMemoryCheckpointStore
        from app.workflow.engine import StepDescriptor, WorkflowEngine, WorkflowSpec
        from app.workflow.golden import InMemoryGoldenRecorder
        from app.workflow.policies import PolicyEnforcer

        class SimpleRegistry:
            def get(self, skill_id: str):
                if skill_id == "noop":
                    return self._noop
                return None

            async def _noop(self, inputs):
                return {"ok": True}

        spec = WorkflowSpec(
            id="determinism-test",
            name="Determinism Test",
            steps=[StepDescriptor(id="s1", skill_id="noop")],
        )

        snapshots = []
        for i in range(10):
            checkpoint = InMemoryCheckpointStore()
            golden = InMemoryGoldenRecorder()
            policy = PolicyEnforcer(step_ceiling_cents=100, workflow_ceiling_cents=500)

            engine = WorkflowEngine(
                registry=SimpleRegistry(),
                checkpoint_store=checkpoint,
                golden=golden,
                policy=policy,
            )

            await engine.run(spec, run_id=f"det-run-{i}", seed=42)

            events = golden.get_events(f"det-run-{i}")
            start_event = next(e for e in events if e.event_type == "run_start")
            snapshots.append(start_event.data.get("budget_snapshot"))

        # All snapshots should be identical (except for accumulated_cost which starts at 0)
        first = snapshots[0]
        for snap in snapshots[1:]:
            assert snap["step_ceiling_cents"] == first["step_ceiling_cents"]
            assert snap["workflow_ceiling_cents"] == first["workflow_ceiling_cents"]
            assert snap["policy_version"] == first["policy_version"]


# ============== Health Endpoint Tests ==============


class TestHealthEndpoint:
    """Tests for workflow health endpoints."""

    def test_configure_health(self):
        """configure_health should set global state."""
        from app.workflow.health import configure_health

        # Should not raise
        configure_health(
            checkpoint_store=InMemoryCheckpointStore(),
            golden_recorder=None,
            policy_enforcer=None,
            enabled=True,
        )

    @pytest.mark.asyncio
    async def test_healthz_returns_ok(self):
        """healthz should return OK status."""
        from app.workflow.health import healthz

        result = await healthz()

        assert result["status"] == "ok"
        assert result["service"] == "workflow_engine"
        assert "ts" in result

    @pytest.mark.asyncio
    async def test_readyz_not_ready_without_checkpoint_store(self):
        """readyz should return not ready without checkpoint store."""
        from app.workflow.health import configure_health, readyz

        # Configure with no checkpoint store
        configure_health(
            checkpoint_store=None,
            enabled=True,
        )

        response = await readyz()
        assert response.status_code == 503
        content = response.body.decode()
        assert "false" in content.lower() or '"ready": false' in content

    @pytest.mark.asyncio
    async def test_readyz_ready_with_checkpoint_store(self):
        """readyz should return ready with valid checkpoint store."""
        from app.workflow.health import configure_health, readyz

        # Configure with checkpoint store
        configure_health(
            checkpoint_store=InMemoryCheckpointStore(),
            enabled=True,
        )

        response = await readyz()
        assert response.status_code == 200


# ============== Stress Tests ==============


class TestConcurrentCheckpointStress:
    """Stress tests for concurrent checkpoint operations."""

    @pytest.mark.asyncio
    async def test_concurrent_checkpoint_stress_50_workers(self):
        """50 concurrent workers competing for same checkpoint."""
        store = InMemoryCheckpointStore()
        run_id = "stress-concurrent-50"

        # Initialize checkpoint
        await store.save(run_id=run_id, next_step_index=0, status="running")

        conflicts = []
        successes = []
        lock = asyncio.Lock()

        async def worker(worker_id: int):
            nonlocal conflicts, successes
            try:
                ck = await store.load(run_id)
                # Simulate variable work time
                await asyncio.sleep(0.001 * (worker_id % 5))
                await store.save(
                    run_id=run_id,
                    next_step_index=worker_id,
                    status="running",
                    expected_version=ck.version,
                )
                async with lock:
                    successes.append(worker_id)
            except CheckpointVersionConflictError:
                async with lock:
                    conflicts.append(worker_id)

        # Run 50 concurrent workers
        await asyncio.gather(*[worker(i) for i in range(50)])

        # Only one should succeed per version
        assert len(successes) == 1
        assert len(conflicts) == 49

        # Verify checkpoint integrity
        ck = await store.load(run_id)
        assert ck.version == 2
        assert ck.status == "running"

    @pytest.mark.asyncio
    async def test_sequential_checkpoint_stress_100_updates(self):
        """100 sequential updates should all succeed."""
        store = InMemoryCheckpointStore()
        run_id = "stress-sequential-100"

        # Initialize
        await store.save(run_id=run_id, next_step_index=0, status="running")

        for i in range(1, 101):
            ck = await store.load(run_id)
            await store.save(
                run_id=run_id,
                next_step_index=i,
                status="running" if i < 100 else "completed",
                expected_version=ck.version,
            )

        # Verify final state
        ck = await store.load(run_id)
        assert ck.version == 101  # 1 initial + 100 updates
        assert ck.next_step_index == 100
        assert ck.status == "completed"

    @pytest.mark.asyncio
    async def test_multi_run_concurrent_stress(self):
        """Multiple runs being updated concurrently."""
        store = InMemoryCheckpointStore()
        num_runs = 10
        updates_per_run = 20

        # Initialize all runs
        for i in range(num_runs):
            await store.save(
                run_id=f"multi-run-{i}",
                next_step_index=0,
                status="running",
                tenant_id=f"tenant-{i % 3}",
            )

        errors = []

        async def update_run(run_idx: int, update_idx: int):
            run_id = f"multi-run-{run_idx}"
            try:
                ck = await store.load(run_id)
                if ck:
                    await store.save(
                        run_id=run_id,
                        next_step_index=update_idx,
                        status="running" if update_idx < updates_per_run - 1 else "completed",
                        expected_version=ck.version,
                    )
            except CheckpointVersionConflictError:
                errors.append((run_idx, update_idx))

        # Sequential updates per run (to avoid conflicts within same run)
        for update_idx in range(1, updates_per_run):
            # But different runs update concurrently
            await asyncio.gather(*[update_run(run_idx, update_idx) for run_idx in range(num_runs)])

        # All runs should complete
        for i in range(num_runs):
            ck = await store.load(f"multi-run-{i}")
            assert ck.status == "completed"
            assert ck.version == updates_per_run

        # No conflicts expected for sequential within-run updates
        assert len(errors) == 0


class TestGoldenReplayStress:
    """Stress tests for golden canonical replay (100x determinism)."""

    @pytest.mark.asyncio
    async def test_golden_replay_100x_determinism(self):
        """Same workflow produces identical golden output 100 times."""
        from app.workflow.checkpoint import InMemoryCheckpointStore
        from app.workflow.engine import StepDescriptor, WorkflowEngine, WorkflowSpec
        from app.workflow.golden import InMemoryGoldenRecorder

        # Simple deterministic skill registry
        class SimpleRegistry:
            def get(self, skill_id: str):
                if skill_id == "add":
                    return self._add_skill
                elif skill_id == "multiply":
                    return self._multiply_skill
                return None

            async def _add_skill(self, inputs):
                return {"result": inputs.get("a", 0) + inputs.get("b", 0)}

            async def _multiply_skill(self, inputs):
                return {"result": inputs.get("x", 1) * inputs.get("y", 1)}

        spec = WorkflowSpec(
            id="replay-stress",
            name="Replay Stress Test",
            steps=[
                StepDescriptor(id="step1", skill_id="add", inputs={"a": 10, "b": 20}),
                StepDescriptor(id="step2", skill_id="multiply", inputs={"x": 3, "y": 7}),
                StepDescriptor(id="step3", skill_id="add", inputs={"a": "${step1.result}", "b": "${step2.result}"}),
            ],
        )

        registry = SimpleRegistry()
        golden_outputs = []
        step_hashes = []

        for i in range(100):
            checkpoint = InMemoryCheckpointStore()
            golden = InMemoryGoldenRecorder()
            engine = WorkflowEngine(
                registry=registry,
                checkpoint_store=checkpoint,
                golden=golden,
            )

            result = await engine.run(spec, run_id=f"replay-{i}", seed=12345)

            # Record golden events (excluding run_id which is unique per run)
            events = golden.get_events(f"replay-{i}")
            normalized_events = []
            for e in events:
                d = e.to_deterministic_dict()
                # Normalize run_id to test determinism of output, not identifier
                d["run_id"] = "normalized"
                normalized_events.append(d)
            golden_outputs.append(normalized_events)

            # Record step outputs
            outputs = [r.output for r in result.step_results if r.success]
            step_hashes.append(canonical_hash({"outputs": outputs}))

        # All 100 runs should produce identical deterministic output (excluding run_id)
        first_output = golden_outputs[0]
        for i, output in enumerate(golden_outputs[1:], start=1):
            assert output == first_output, f"Run {i} differs from run 0"

        # All step hashes should be identical
        first_hash = step_hashes[0]
        for i, h in enumerate(step_hashes[1:], start=1):
            assert h == first_hash, f"Run {i} hash differs: {h} vs {first_hash}"

    @pytest.mark.asyncio
    async def test_golden_with_failures_replay_determinism(self):
        """Workflows with failures also replay deterministically."""
        from app.workflow.checkpoint import InMemoryCheckpointStore
        from app.workflow.engine import StepDescriptor, WorkflowEngine, WorkflowSpec
        from app.workflow.golden import InMemoryGoldenRecorder

        class FailingRegistry:
            def get(self, skill_id: str):
                if skill_id == "succeed":
                    return self._succeed
                elif skill_id == "fail":
                    return self._fail
                return None

            async def _succeed(self, inputs):
                return {"ok": True, "value": 42}

            async def _fail(self, inputs):
                return {"ok": False, "error": {"code": "STEP_FAILED", "message": "Intentional failure"}}

        spec = WorkflowSpec(
            id="fail-replay",
            name="Failure Replay Test",
            steps=[
                StepDescriptor(id="s1", skill_id="succeed"),
                StepDescriptor(id="s2", skill_id="fail", on_error="abort"),
            ],
        )

        registry = FailingRegistry()
        error_codes = []
        statuses = []

        for i in range(50):
            checkpoint = InMemoryCheckpointStore()
            golden = InMemoryGoldenRecorder()
            engine = WorkflowEngine(
                registry=registry,
                checkpoint_store=checkpoint,
                golden=golden,
            )

            result = await engine.run(spec, run_id=f"fail-{i}", seed=99999)
            statuses.append(result.status)

            # Check error_code is recorded in golden
            events = golden.get_events(f"fail-{i}")
            step_events = [e for e in events if e.event_type == "step"]
            if len(step_events) >= 2:
                error_codes.append(step_events[1].data.get("error_code"))

        # All runs should fail consistently
        assert all(s == "failed" for s in statuses)

        # All error codes should be consistent
        assert all(ec == error_codes[0] for ec in error_codes)

    @pytest.mark.asyncio
    async def test_canonical_hash_stability_100x(self):
        """Canonical hash is stable across 100 computations."""
        from app.workflow.canonicalize import canonical_hash

        complex_obj = {
            "workflow_id": "test-workflow",
            "steps": [
                {"id": "s1", "skill": "http", "inputs": {"url": "https://api.example.com", "method": "GET"}},
                {"id": "s2", "skill": "llm", "inputs": {"prompt": "Analyze this", "model": "gpt-4"}},
            ],
            "metadata": {
                "created_by": "test-user",
                "tags": ["production", "critical"],
                "config": {"retries": 3, "timeout_ms": 30000},
            },
            "results": [
                {"step_id": "s1", "output": {"status": 200, "body": {"data": [1, 2, 3]}}},
                {"step_id": "s2", "output": {"text": "Analysis complete", "confidence": 0.95}},
            ],
        }

        hashes = []
        for _ in range(100):
            h = canonical_hash(complex_obj)
            hashes.append(h)

        # All hashes should be identical
        assert len(set(hashes)) == 1, f"Hash instability: {len(set(hashes))} unique hashes"

    @pytest.mark.asyncio
    async def test_volatile_stripping_consistency(self):
        """Volatile field stripping is consistent across runs."""
        events_with_volatile = [
            {
                "event_type": "step",
                "timestamp": "2025-01-01T12:00:00Z",
                "duration_ms": 123,
                "data": {"step_id": "s1", "output": {"value": 42}},
            },
            {
                "event_type": "step",
                "timestamp": "2025-01-01T12:00:01Z",
                "latency_ms": 456,
                "data": {"step_id": "s2", "output": {"value": 84}},
            },
        ]

        stripped_results = []
        for _ in range(50):
            stripped = strip_volatile_from_events(events_with_volatile)
            stripped_results.append(canonical_json(stripped))

        # All stripped results should be identical
        assert len(set(stripped_results)) == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
