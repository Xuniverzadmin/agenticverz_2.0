# Layer: TEST
# AUDIENCE: INTERNAL
# Role: Activity domain runtime correctness proofs (BI-ACTIVITY-001)
# artifact_class: TEST


"""
Activity Domain Runtime Correctness Tests (BI-ACTIVITY-001)

Proves that:
  1. BI-ACTIVITY-001 (run.create) is fail-closed on missing tenant_id/project_id
  2. Positive pass when both tenant_id and project_id present
  3. MONITOR mode logs but does not block dispatch
  4. STRICT mode blocks on invariant violations
  5. Real OperationRegistry.execute(...) dispatch proof for run.create
  6. activity.query does NOT trigger BI-ACTIVITY-001
  7. _invariant_mode internal key is stripped before kwargs forwarding
     in activity.query and activity.telemetry handlers (unit-level)
  8. No alias mapping exists for activity.* → run.create (by design)
  9. Production-wiring leakage proofs: real OperationRegistry with
     invariant mode configured + real activity handlers registered,
     proving _invariant_mode does not leak into facade/engine kwargs
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest


# =============================================================================
# AC-DELTA-01: Contract tests — invariant fail-closed behavior
# =============================================================================


class TestActivityInvariantContracts:
    """Prove BI-ACTIVITY-001 is fail-closed on missing tenant_id/project_id."""

    # --- Fail-closed negatives ---

    def test_bi_activity_001_rejects_missing_tenant_id(self):
        """BI-ACTIVITY-001: run.create with no tenant_id → FAIL."""
        from app.hoc.cus.hoc_spine.authority.business_invariants import (
            check_all_for_operation,
        )

        results = check_all_for_operation(
            "run.create",
            {"operation": "run.create", "project_id": "proj-1"},
        )
        assert len(results) >= 1
        inv_id, passed, message = results[0]
        assert inv_id == "BI-ACTIVITY-001"
        assert passed is False
        assert "tenant_id" in message

    def test_bi_activity_001_rejects_missing_project_id(self):
        """BI-ACTIVITY-001: run.create with no project_id → FAIL."""
        from app.hoc.cus.hoc_spine.authority.business_invariants import (
            check_all_for_operation,
        )

        results = check_all_for_operation(
            "run.create",
            {"operation": "run.create", "tenant_id": "t-001"},
        )
        assert len(results) >= 1
        inv_id, passed, message = results[0]
        assert inv_id == "BI-ACTIVITY-001"
        assert passed is False
        assert "project_id" in message

    def test_bi_activity_001_rejects_both_missing(self):
        """BI-ACTIVITY-001: run.create with neither tenant_id nor project_id → FAIL."""
        from app.hoc.cus.hoc_spine.authority.business_invariants import (
            check_all_for_operation,
        )

        results = check_all_for_operation(
            "run.create",
            {"operation": "run.create"},
        )
        assert len(results) >= 1
        inv_id, passed, message = results[0]
        assert inv_id == "BI-ACTIVITY-001"
        assert passed is False
        assert "tenant_id" in message
        assert "project_id" in message

    def test_bi_activity_001_rejects_empty_tenant_id(self):
        """BI-ACTIVITY-001: run.create with empty tenant_id → FAIL."""
        from app.hoc.cus.hoc_spine.authority.business_invariants import (
            check_all_for_operation,
        )

        results = check_all_for_operation(
            "run.create",
            {"operation": "run.create", "tenant_id": "", "project_id": "proj-1"},
        )
        assert len(results) >= 1
        inv_id, passed, message = results[0]
        assert inv_id == "BI-ACTIVITY-001"
        assert passed is False

    def test_bi_activity_001_rejects_empty_project_id(self):
        """BI-ACTIVITY-001: run.create with empty project_id → FAIL."""
        from app.hoc.cus.hoc_spine.authority.business_invariants import (
            check_all_for_operation,
        )

        results = check_all_for_operation(
            "run.create",
            {"operation": "run.create", "tenant_id": "t-001", "project_id": ""},
        )
        assert len(results) >= 1
        inv_id, passed, message = results[0]
        assert inv_id == "BI-ACTIVITY-001"
        assert passed is False

    # --- Positive pass ---

    def test_bi_activity_001_passes_valid_context(self):
        """BI-ACTIVITY-001: run.create with valid tenant_id + project_id → PASS."""
        from app.hoc.cus.hoc_spine.authority.business_invariants import (
            check_all_for_operation,
        )

        results = check_all_for_operation(
            "run.create",
            {
                "operation": "run.create",
                "tenant_id": "t-active-001",
                "project_id": "proj-001",
            },
        )
        assert len(results) >= 1
        inv_id, passed, _ = results[0]
        assert inv_id == "BI-ACTIVITY-001"
        assert passed is True


# =============================================================================
# AC-DELTA-02: MONITOR / STRICT mode behavior
# =============================================================================


class TestActivityInvariantModes:
    """Prove MONITOR and STRICT modes behave correctly for BI-ACTIVITY-001."""

    def test_monitor_mode_does_not_raise(self):
        """MONITOR mode: BI-ACTIVITY-001 fails but no exception raised."""
        from app.hoc.cus.hoc_spine.authority.invariant_evaluator import (
            InvariantMode,
            evaluate_invariants,
        )

        results = evaluate_invariants(
            "run.create",
            {"operation": "run.create"},
            InvariantMode.MONITOR,
        )
        assert len(results) >= 1
        assert any(
            r.invariant_id == "BI-ACTIVITY-001" and not r.passed for r in results
        )

    def test_monitor_mode_returns_failure_details(self):
        """MONITOR mode: returns violation details for missing project_id."""
        from app.hoc.cus.hoc_spine.authority.invariant_evaluator import (
            InvariantMode,
            evaluate_invariants,
        )

        results = evaluate_invariants(
            "run.create",
            {"operation": "run.create", "tenant_id": "t-001"},
            InvariantMode.MONITOR,
        )
        failed = [
            r for r in results if r.invariant_id == "BI-ACTIVITY-001" and not r.passed
        ]
        assert len(failed) == 1
        assert "project_id" in failed[0].message

    def test_strict_mode_raises_on_missing_fields(self):
        """STRICT mode: BI-ACTIVITY-001 with no fields → BusinessInvariantViolation."""
        from app.hoc.cus.hoc_spine.authority.business_invariants import (
            BusinessInvariantViolation,
        )
        from app.hoc.cus.hoc_spine.authority.invariant_evaluator import (
            InvariantMode,
            evaluate_invariants,
        )

        with pytest.raises(BusinessInvariantViolation) as exc_info:
            evaluate_invariants(
                "run.create",
                {"operation": "run.create"},
                InvariantMode.STRICT,
            )
        assert "BI-ACTIVITY-001" in exc_info.value.invariant_id

    def test_strict_mode_raises_on_missing_project_id(self):
        """STRICT mode: tenant_id present but no project_id → raises."""
        from app.hoc.cus.hoc_spine.authority.business_invariants import (
            BusinessInvariantViolation,
        )
        from app.hoc.cus.hoc_spine.authority.invariant_evaluator import (
            InvariantMode,
            evaluate_invariants,
        )

        with pytest.raises(BusinessInvariantViolation) as exc_info:
            evaluate_invariants(
                "run.create",
                {"operation": "run.create", "tenant_id": "t-001"},
                InvariantMode.STRICT,
            )
        assert "BI-ACTIVITY-001" in exc_info.value.invariant_id

    def test_strict_mode_passes_valid_context(self):
        """STRICT mode: valid context → no exception."""
        from app.hoc.cus.hoc_spine.authority.invariant_evaluator import (
            InvariantMode,
            evaluate_invariants,
        )

        results = evaluate_invariants(
            "run.create",
            {
                "operation": "run.create",
                "tenant_id": "t-active-001",
                "project_id": "proj-001",
            },
            InvariantMode.STRICT,
        )
        assert all(r.passed for r in results)


# =============================================================================
# AC-DELTA-03: Registry dispatch proofs for run.create
# =============================================================================


class TestActivityRegistryDispatch:
    """Prove run.create dispatches through real OperationRegistry."""

    @pytest.fixture
    def registry_with_run_create_handler(self):
        """Create OperationRegistry with a mock run.create handler."""
        from app.hoc.cus.hoc_spine.orchestrator.operation_registry import (
            OperationRegistry,
            OperationResult,
        )

        registry = OperationRegistry()

        handler = MagicMock()
        handler.execute = AsyncMock(
            return_value=OperationResult.ok({"run_id": "run-001"})
        )
        registry.register("run.create", handler)

        return registry, handler

    @pytest.mark.asyncio
    async def test_monitor_allows_bad_context(self, registry_with_run_create_handler):
        """MONITOR: bad context (no project_id) → dispatches anyway."""
        from app.hoc.cus.hoc_spine.authority.invariant_evaluator import InvariantMode
        from app.hoc.cus.hoc_spine.orchestrator.operation_registry import (
            OperationContext,
        )

        registry, handler = registry_with_run_create_handler
        registry.set_invariant_mode(InvariantMode.MONITOR)

        ctx = OperationContext(
            session=None,
            tenant_id="t-monitor-001",
            params={"tenant_id": "t-monitor-001"},
        )
        result = await registry.execute("run.create", ctx)
        assert result.success is True
        assert handler.execute.called

    @pytest.mark.asyncio
    async def test_strict_blocks_bad_context(self, registry_with_run_create_handler):
        """STRICT: bad context (no project_id) → blocked pre-dispatch."""
        from app.hoc.cus.hoc_spine.authority.business_invariants import (
            BusinessInvariantViolation,
        )
        from app.hoc.cus.hoc_spine.authority.invariant_evaluator import InvariantMode
        from app.hoc.cus.hoc_spine.orchestrator.operation_registry import (
            OperationContext,
        )

        registry, handler = registry_with_run_create_handler
        registry.set_invariant_mode(InvariantMode.STRICT)

        ctx = OperationContext(
            session=None,
            tenant_id="t-strict-001",
            params={"tenant_id": "t-strict-001"},
        )

        with pytest.raises(BusinessInvariantViolation) as exc_info:
            await registry.execute("run.create", ctx)

        assert "BI-ACTIVITY-001" in exc_info.value.invariant_id
        assert not handler.execute.called

    @pytest.mark.asyncio
    async def test_strict_passes_valid_context(self, registry_with_run_create_handler):
        """STRICT: valid context → dispatches to handler."""
        from app.hoc.cus.hoc_spine.authority.invariant_evaluator import InvariantMode
        from app.hoc.cus.hoc_spine.orchestrator.operation_registry import (
            OperationContext,
        )

        registry, handler = registry_with_run_create_handler
        registry.set_invariant_mode(InvariantMode.STRICT)

        ctx = OperationContext(
            session=None,
            tenant_id="t-valid-001",
            params={"tenant_id": "t-valid-001", "project_id": "proj-001"},
        )

        result = await registry.execute("run.create", ctx)
        assert result.success is True
        assert result.data["run_id"] == "run-001"
        assert handler.execute.called

    @pytest.mark.asyncio
    async def test_unregistered_operation_fails(self, registry_with_run_create_handler):
        """Unregistered operation → OperationResult.fail."""
        from app.hoc.cus.hoc_spine.orchestrator.operation_registry import (
            OperationContext,
        )

        registry, _ = registry_with_run_create_handler

        ctx = OperationContext(
            session=None,
            tenant_id="t-bad-001",
            params={},
        )
        result = await registry.execute("run.nonexistent", ctx)
        assert result.success is False


# =============================================================================
# AC-DELTA-04: _invariant_mode leakage regression tests
# =============================================================================


class TestActivityInvariantModeLeakage:
    """Prove that _invariant_mode internal key is stripped before kwargs
    forwarding in activity.query and activity.telemetry handlers."""

    @pytest.mark.asyncio
    async def test_activity_query_strips_invariant_mode(self):
        """activity.query handler strips _invariant_mode before forwarding kwargs.

        When OperationRegistry injects _invariant_mode into enriched_params,
        ActivityQueryHandler must not forward it as a kwarg to facade methods.
        """
        from app.hoc.cus.hoc_spine.orchestrator.handlers.activity_handler import (
            ActivityQueryHandler,
        )
        from app.hoc.cus.hoc_spine.orchestrator.operation_registry import (
            OperationContext,
        )

        handler = ActivityQueryHandler()

        # Mock the facade method to capture kwargs
        captured_kwargs = {}
        mock_facade_method = AsyncMock(return_value={"runs": []})

        async def capturing_method(**kw):
            captured_kwargs.update(kw)
            return {"runs": []}

        # Patch the facade import inside execute
        import app.hoc.cus.activity.L5_engines.activity_facade as facade_mod

        original_get = facade_mod.get_activity_facade

        mock_facade = MagicMock()
        mock_facade.get_runs = capturing_method
        facade_mod.get_activity_facade = lambda: mock_facade

        try:
            ctx = OperationContext(
                session=MagicMock(),
                tenant_id="t-leak-test",
                params={
                    "method": "get_runs",
                    "_invariant_mode": "STRICT",  # injected by registry
                    "limit": 10,
                },
            )
            result = await handler.execute(ctx)
            assert result.success is True
            # _invariant_mode must NOT appear in forwarded kwargs
            assert "_invariant_mode" not in captured_kwargs
            # But legitimate params must still be forwarded
            assert captured_kwargs.get("limit") == 10
        finally:
            facade_mod.get_activity_facade = original_get

    @pytest.mark.asyncio
    async def test_activity_telemetry_strips_invariant_mode(self):
        """activity.telemetry handler strips _invariant_mode before forwarding kwargs.

        When OperationRegistry injects _invariant_mode into enriched_params,
        ActivityTelemetryHandler must not forward it to telemetry methods.
        """
        from app.hoc.cus.hoc_spine.orchestrator.handlers.activity_handler import (
            ActivityTelemetryHandler,
        )
        from app.hoc.cus.hoc_spine.orchestrator.operation_registry import (
            OperationContext,
        )

        handler = ActivityTelemetryHandler()

        captured_kwargs = {}

        async def capturing_method(**kw):
            captured_kwargs.update(kw)
            return {"total_tokens": 0}

        import app.hoc.cus.activity.L5_engines.cus_telemetry_engine as telem_mod

        original_get = telem_mod.get_cus_telemetry_engine

        mock_engine = MagicMock()
        mock_engine.get_usage_summary = capturing_method
        telem_mod.get_cus_telemetry_engine = lambda: mock_engine

        try:
            ctx = OperationContext(
                session=MagicMock(),
                tenant_id="t-leak-test",
                params={
                    "method": "get_usage_summary",
                    "_invariant_mode": "STRICT",  # injected by registry
                    "tenant_id": "t-leak-test",
                },
            )
            result = await handler.execute(ctx)
            assert result.success is True
            # _invariant_mode must NOT appear in forwarded kwargs
            assert "_invariant_mode" not in captured_kwargs
            # But tenant_id must still be forwarded
            assert captured_kwargs.get("tenant_id") == "t-leak-test"
        finally:
            telem_mod.get_cus_telemetry_engine = original_get


# =============================================================================
# AC-DELTA-04b: Production-wiring leakage proofs (re-audit remedy)
# =============================================================================


class TestActivityProductionWiringLeakage:
    """Production-wiring leakage proofs: real OperationRegistry with
    invariant mode configured + real activity handlers registered via
    activity_handler.register(), proving _invariant_mode does not leak
    into facade/engine kwargs when dispatched through registry.execute()."""

    @pytest.fixture
    def registry_with_activity_handlers(self):
        """Real OperationRegistry with activity handlers registered via register()."""
        from app.hoc.cus.hoc_spine.orchestrator.operation_registry import (
            OperationRegistry,
        )
        from app.hoc.cus.hoc_spine.orchestrator.handlers.activity_handler import (
            register,
        )

        registry = OperationRegistry()
        register(registry)
        return registry

    @pytest.mark.asyncio
    async def test_query_get_runs_no_invariant_mode_leakage(
        self, registry_with_activity_handlers
    ):
        """activity.query (get_runs) via registry.execute() in MONITOR mode —
        _invariant_mode injected by registry but NOT forwarded to facade kwargs."""
        from app.hoc.cus.hoc_spine.authority.invariant_evaluator import InvariantMode
        from app.hoc.cus.hoc_spine.orchestrator.operation_registry import (
            OperationContext,
        )

        registry = registry_with_activity_handlers
        registry.set_invariant_mode(InvariantMode.MONITOR)

        captured_kwargs = {}

        async def capturing_get_runs(**kw):
            captured_kwargs.update(kw)
            return {"runs": []}

        import app.hoc.cus.activity.L5_engines.activity_facade as facade_mod

        original_get = facade_mod.get_activity_facade

        mock_facade = MagicMock()
        mock_facade.get_runs = capturing_get_runs
        facade_mod.get_activity_facade = lambda: mock_facade

        try:
            ctx = OperationContext(
                session=MagicMock(),
                tenant_id="t-prod-wire-001",
                params={
                    "method": "get_runs",
                    "limit": 25,
                },
            )
            result = await registry.execute("activity.query", ctx)
            assert result.success is True
            # _invariant_mode must NOT leak through to facade kwargs
            assert "_invariant_mode" not in captured_kwargs
            # Legitimate params must still be forwarded
            assert captured_kwargs.get("limit") == 25
        finally:
            facade_mod.get_activity_facade = original_get

    @pytest.mark.asyncio
    async def test_telemetry_get_usage_summary_no_invariant_mode_leakage(
        self, registry_with_activity_handlers
    ):
        """activity.telemetry (get_usage_summary) via registry.execute() in MONITOR mode —
        _invariant_mode injected by registry but NOT forwarded to engine kwargs."""
        from app.hoc.cus.hoc_spine.authority.invariant_evaluator import InvariantMode
        from app.hoc.cus.hoc_spine.orchestrator.operation_registry import (
            OperationContext,
        )

        registry = registry_with_activity_handlers
        registry.set_invariant_mode(InvariantMode.MONITOR)

        captured_kwargs = {}

        async def capturing_get_usage_summary(**kw):
            captured_kwargs.update(kw)
            return {"total_tokens": 0}

        import app.hoc.cus.activity.L5_engines.cus_telemetry_engine as telem_mod

        original_get = telem_mod.get_cus_telemetry_engine

        mock_engine = MagicMock()
        mock_engine.get_usage_summary = capturing_get_usage_summary
        telem_mod.get_cus_telemetry_engine = lambda: mock_engine

        try:
            ctx = OperationContext(
                session=MagicMock(),
                tenant_id="t-prod-wire-002",
                params={
                    "method": "get_usage_summary",
                    "tenant_id": "t-prod-wire-002",
                },
            )
            result = await registry.execute("activity.telemetry", ctx)
            assert result.success is True
            # _invariant_mode must NOT leak through to engine kwargs
            assert "_invariant_mode" not in captured_kwargs
            # Legitimate params must still be forwarded
            assert captured_kwargs.get("tenant_id") == "t-prod-wire-002"
        finally:
            telem_mod.get_cus_telemetry_engine = original_get

    @pytest.mark.asyncio
    async def test_query_strict_mode_still_strips_invariant_mode(
        self, registry_with_activity_handlers
    ):
        """activity.query via registry.execute() in STRICT mode —
        _invariant_mode stripped even under stricter enforcement.
        (activity.query has no BI invariant so STRICT does not block.)"""
        from app.hoc.cus.hoc_spine.authority.invariant_evaluator import InvariantMode
        from app.hoc.cus.hoc_spine.orchestrator.operation_registry import (
            OperationContext,
        )

        registry = registry_with_activity_handlers
        registry.set_invariant_mode(InvariantMode.STRICT)

        captured_kwargs = {}

        async def capturing_get_runs(**kw):
            captured_kwargs.update(kw)
            return {"runs": []}

        import app.hoc.cus.activity.L5_engines.activity_facade as facade_mod

        original_get = facade_mod.get_activity_facade

        mock_facade = MagicMock()
        mock_facade.get_runs = capturing_get_runs
        facade_mod.get_activity_facade = lambda: mock_facade

        try:
            ctx = OperationContext(
                session=MagicMock(),
                tenant_id="t-strict-wire-001",
                params={
                    "method": "get_runs",
                    "limit": 10,
                },
            )
            result = await registry.execute("activity.query", ctx)
            assert result.success is True
            assert "_invariant_mode" not in captured_kwargs
            assert captured_kwargs.get("limit") == 10
        finally:
            facade_mod.get_activity_facade = original_get


# =============================================================================
# AC-DELTA-05: Non-trigger and no-alias proofs
# =============================================================================


class TestActivityNonTriggerProofs:
    """Prove activity.query does NOT trigger BI-ACTIVITY-001 and no alias
    exists for activity.* → run.create."""

    def test_activity_query_does_not_trigger_bi_activity_001(self):
        """activity.query must NOT trigger BI-ACTIVITY-001."""
        from app.hoc.cus.hoc_spine.authority.business_invariants import (
            check_all_for_operation,
        )

        results = check_all_for_operation(
            "activity.query",
            {"operation": "activity.query"},
        )
        inv_ids = [r[0] for r in results]
        assert "BI-ACTIVITY-001" not in inv_ids

    def test_activity_telemetry_does_not_trigger_bi_activity_001(self):
        """activity.telemetry must NOT trigger BI-ACTIVITY-001."""
        from app.hoc.cus.hoc_spine.authority.business_invariants import (
            check_all_for_operation,
        )

        results = check_all_for_operation(
            "activity.telemetry",
            {"operation": "activity.telemetry"},
        )
        inv_ids = [r[0] for r in results]
        assert "BI-ACTIVITY-001" not in inv_ids

    def test_no_alias_exists_for_activity_operations(self):
        """No INVARIANT_OPERATION_ALIASES entry maps activity.* → run.create.

        By design: activity domain monitors runs, it does not create them.
        BI-ACTIVITY-001 guards run creation wherever it actually occurs,
        not in the activity query/telemetry path.
        """
        from app.hoc.cus.hoc_spine.authority.business_invariants import (
            INVARIANT_OPERATION_ALIASES,
        )

        activity_aliases = {
            k: v
            for k, v in INVARIANT_OPERATION_ALIASES.items()
            if k.startswith("activity.")
        }
        assert activity_aliases == {}, (
            f"Unexpected activity.* alias: {activity_aliases}. "
            "Activity domain does not own run creation."
        )

    def test_real_handler_registration_exists(self):
        """Verify activity.* operations register on a real registry."""
        from app.hoc.cus.hoc_spine.orchestrator.operation_registry import (
            OperationRegistry,
        )
        from app.hoc.cus.hoc_spine.orchestrator.handlers.activity_handler import (
            register,
        )

        registry = OperationRegistry()
        register(registry)

        expected_ops = [
            "activity.query",
            "activity.signal_fingerprint",
            "activity.signal_feedback",
            "activity.telemetry",
            "activity.discovery",
            "activity.orphan_recovery",
        ]
        for op in expected_ops:
            assert op in registry._handlers, f"Missing registration: {op}"
