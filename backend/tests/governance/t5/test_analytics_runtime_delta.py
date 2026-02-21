# Layer: TEST
# AUDIENCE: INTERNAL
# Role: Analytics domain runtime correctness proofs (BI-ANALYTICS-001)
# artifact_class: TEST


"""
Analytics Domain Runtime Correctness Tests (BI-ANALYTICS-001)

Proves that:
  1. BI-ANALYTICS-001 (cost_record.create) is fail-closed on missing/invalid run_id
  2. Positive pass when run_id present with run_exists=True
  3. MONITOR mode logs but does not block dispatch
  4. STRICT mode blocks on invariant violations
  5. Real OperationRegistry.execute(...) dispatch proof for cost_record.create
  6. analytics.query / analytics.feedback / analytics.detection do NOT trigger
     BI-ANALYTICS-001
  7. _invariant_mode internal key is stripped before kwargs forwarding
     in analytics.feedback, analytics.query, and analytics.detection handlers
  8. No alias mapping exists for analytics.* → cost_record.create (by design)
  9. Production-wiring leakage proofs: real OperationRegistry with
     invariant mode configured + real analytics handlers registered,
     proving _invariant_mode does not leak into facade/engine kwargs
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest


# =============================================================================
# AN-DELTA-01: Contract tests — invariant fail-closed behavior
# =============================================================================


class TestAnalyticsInvariantContracts:
    """Prove BI-ANALYTICS-001 is fail-closed on missing/invalid run_id."""

    # --- Fail-closed negatives ---

    def test_bi_analytics_001_rejects_missing_run_id(self):
        """BI-ANALYTICS-001: cost_record.create with no run_id → FAIL."""
        from app.hoc.cus.hoc_spine.authority.business_invariants import (
            check_all_for_operation,
        )

        results = check_all_for_operation(
            "cost_record.create",
            {"operation": "cost_record.create"},
        )
        assert len(results) >= 1
        inv_id, passed, message = results[0]
        assert inv_id == "BI-ANALYTICS-001"
        assert passed is False
        assert "run_id" in message

    def test_bi_analytics_001_rejects_run_not_exists(self):
        """BI-ANALYTICS-001: cost_record.create with run_exists=False → FAIL."""
        from app.hoc.cus.hoc_spine.authority.business_invariants import (
            check_all_for_operation,
        )

        results = check_all_for_operation(
            "cost_record.create",
            {
                "operation": "cost_record.create",
                "run_id": "run-orphan-001",
                "run_exists": False,
            },
        )
        assert len(results) >= 1
        inv_id, passed, message = results[0]
        assert inv_id == "BI-ANALYTICS-001"
        assert passed is False
        assert "run-orphan-001" in message

    def test_bi_analytics_001_rejects_empty_run_id(self):
        """BI-ANALYTICS-001: cost_record.create with empty run_id → FAIL."""
        from app.hoc.cus.hoc_spine.authority.business_invariants import (
            check_all_for_operation,
        )

        results = check_all_for_operation(
            "cost_record.create",
            {"operation": "cost_record.create", "run_id": "", "run_exists": True},
        )
        assert len(results) >= 1
        inv_id, passed, message = results[0]
        assert inv_id == "BI-ANALYTICS-001"
        assert passed is False

    def test_bi_analytics_001_rejects_run_exists_default_false(self):
        """BI-ANALYTICS-001: run_id present but run_exists not set → FAIL (default False)."""
        from app.hoc.cus.hoc_spine.authority.business_invariants import (
            check_all_for_operation,
        )

        results = check_all_for_operation(
            "cost_record.create",
            {"operation": "cost_record.create", "run_id": "run-001"},
        )
        assert len(results) >= 1
        inv_id, passed, message = results[0]
        assert inv_id == "BI-ANALYTICS-001"
        assert passed is False
        assert "does not exist" in message

    # --- Positive pass ---

    def test_bi_analytics_001_passes_valid_context(self):
        """BI-ANALYTICS-001: cost_record.create with valid run_id + run_exists=True → PASS."""
        from app.hoc.cus.hoc_spine.authority.business_invariants import (
            check_all_for_operation,
        )

        results = check_all_for_operation(
            "cost_record.create",
            {
                "operation": "cost_record.create",
                "run_id": "run-valid-001",
                "run_exists": True,
            },
        )
        assert len(results) >= 1
        inv_id, passed, _ = results[0]
        assert inv_id == "BI-ANALYTICS-001"
        assert passed is True


# =============================================================================
# AN-DELTA-02: MONITOR / STRICT mode behavior
# =============================================================================


class TestAnalyticsInvariantModes:
    """Prove MONITOR and STRICT modes behave correctly for BI-ANALYTICS-001."""

    def test_monitor_mode_does_not_raise(self):
        """MONITOR mode: BI-ANALYTICS-001 fails but no exception raised."""
        from app.hoc.cus.hoc_spine.authority.invariant_evaluator import (
            InvariantMode,
            evaluate_invariants,
        )

        results = evaluate_invariants(
            "cost_record.create",
            {"operation": "cost_record.create"},
            InvariantMode.MONITOR,
        )
        assert len(results) >= 1
        assert any(
            r.invariant_id == "BI-ANALYTICS-001" and not r.passed for r in results
        )

    def test_monitor_mode_returns_failure_details(self):
        """MONITOR mode: returns violation details for run_exists=False."""
        from app.hoc.cus.hoc_spine.authority.invariant_evaluator import (
            InvariantMode,
            evaluate_invariants,
        )

        results = evaluate_invariants(
            "cost_record.create",
            {
                "operation": "cost_record.create",
                "run_id": "run-orphan",
                "run_exists": False,
            },
            InvariantMode.MONITOR,
        )
        failed = [
            r for r in results if r.invariant_id == "BI-ANALYTICS-001" and not r.passed
        ]
        assert len(failed) == 1
        assert "run-orphan" in failed[0].message

    def test_strict_mode_raises_on_missing_run_id(self):
        """STRICT mode: BI-ANALYTICS-001 with no run_id → BusinessInvariantViolation."""
        from app.hoc.cus.hoc_spine.authority.business_invariants import (
            BusinessInvariantViolation,
        )
        from app.hoc.cus.hoc_spine.authority.invariant_evaluator import (
            InvariantMode,
            evaluate_invariants,
        )

        with pytest.raises(BusinessInvariantViolation) as exc_info:
            evaluate_invariants(
                "cost_record.create",
                {"operation": "cost_record.create"},
                InvariantMode.STRICT,
            )
        assert "BI-ANALYTICS-001" in exc_info.value.invariant_id

    def test_strict_mode_raises_on_run_not_exists(self):
        """STRICT mode: run_id present but run_exists=False → raises."""
        from app.hoc.cus.hoc_spine.authority.business_invariants import (
            BusinessInvariantViolation,
        )
        from app.hoc.cus.hoc_spine.authority.invariant_evaluator import (
            InvariantMode,
            evaluate_invariants,
        )

        with pytest.raises(BusinessInvariantViolation) as exc_info:
            evaluate_invariants(
                "cost_record.create",
                {
                    "operation": "cost_record.create",
                    "run_id": "run-orphan",
                    "run_exists": False,
                },
                InvariantMode.STRICT,
            )
        assert "BI-ANALYTICS-001" in exc_info.value.invariant_id

    def test_strict_mode_passes_valid_context(self):
        """STRICT mode: valid context → no exception."""
        from app.hoc.cus.hoc_spine.authority.invariant_evaluator import (
            InvariantMode,
            evaluate_invariants,
        )

        results = evaluate_invariants(
            "cost_record.create",
            {
                "operation": "cost_record.create",
                "run_id": "run-valid-001",
                "run_exists": True,
            },
            InvariantMode.STRICT,
        )
        assert all(r.passed for r in results)


# =============================================================================
# AN-DELTA-03: Registry dispatch proofs for cost_record.create
# =============================================================================


class TestAnalyticsRegistryDispatch:
    """Prove cost_record.create dispatches through real OperationRegistry."""

    @pytest.fixture
    def registry_with_cost_record_handler(self):
        """Create OperationRegistry with a mock cost_record.create handler."""
        from app.hoc.cus.hoc_spine.orchestrator.operation_registry import (
            OperationRegistry,
            OperationResult,
        )

        registry = OperationRegistry()

        handler = MagicMock()
        handler.execute = AsyncMock(
            return_value=OperationResult.ok({"cost_record_id": "cr-001"})
        )
        registry.register("cost_record.create", handler)

        return registry, handler

    @pytest.mark.asyncio
    async def test_monitor_allows_bad_context(self, registry_with_cost_record_handler):
        """MONITOR: bad context (no run_id) → dispatches anyway."""
        from app.hoc.cus.hoc_spine.authority.invariant_evaluator import InvariantMode
        from app.hoc.cus.hoc_spine.orchestrator.operation_registry import (
            OperationContext,
        )

        registry, handler = registry_with_cost_record_handler
        registry.set_invariant_mode(InvariantMode.MONITOR)

        ctx = OperationContext(
            session=None,
            tenant_id="t-monitor-001",
            params={"tenant_id": "t-monitor-001"},
        )
        result = await registry.execute("cost_record.create", ctx)
        assert result.success is True
        assert handler.execute.called

    @pytest.mark.asyncio
    async def test_strict_blocks_bad_context(self, registry_with_cost_record_handler):
        """STRICT: bad context (no run_id) → blocked pre-dispatch."""
        from app.hoc.cus.hoc_spine.authority.business_invariants import (
            BusinessInvariantViolation,
        )
        from app.hoc.cus.hoc_spine.authority.invariant_evaluator import InvariantMode
        from app.hoc.cus.hoc_spine.orchestrator.operation_registry import (
            OperationContext,
        )

        registry, handler = registry_with_cost_record_handler
        registry.set_invariant_mode(InvariantMode.STRICT)

        ctx = OperationContext(
            session=None,
            tenant_id="t-strict-001",
            params={"tenant_id": "t-strict-001"},
        )

        with pytest.raises(BusinessInvariantViolation) as exc_info:
            await registry.execute("cost_record.create", ctx)

        assert "BI-ANALYTICS-001" in exc_info.value.invariant_id
        assert not handler.execute.called

    @pytest.mark.asyncio
    async def test_strict_passes_valid_context(self, registry_with_cost_record_handler):
        """STRICT: valid context → dispatches to handler."""
        from app.hoc.cus.hoc_spine.authority.invariant_evaluator import InvariantMode
        from app.hoc.cus.hoc_spine.orchestrator.operation_registry import (
            OperationContext,
        )

        registry, handler = registry_with_cost_record_handler
        registry.set_invariant_mode(InvariantMode.STRICT)

        ctx = OperationContext(
            session=None,
            tenant_id="t-valid-001",
            params={
                "tenant_id": "t-valid-001",
                "run_id": "run-valid-001",
                "run_exists": True,
            },
        )

        result = await registry.execute("cost_record.create", ctx)
        assert result.success is True
        assert result.data["cost_record_id"] == "cr-001"
        assert handler.execute.called

    @pytest.mark.asyncio
    async def test_unregistered_operation_fails(
        self, registry_with_cost_record_handler
    ):
        """Unregistered operation → OperationResult.fail."""
        from app.hoc.cus.hoc_spine.orchestrator.operation_registry import (
            OperationContext,
        )

        registry, _ = registry_with_cost_record_handler

        ctx = OperationContext(
            session=None,
            tenant_id="t-bad-001",
            params={},
        )
        result = await registry.execute("cost_record.nonexistent", ctx)
        assert result.success is False


# =============================================================================
# AN-DELTA-04: Production-wiring leakage proofs (real registry path)
# =============================================================================


class TestAnalyticsProductionWiringLeakage:
    """Production-wiring leakage proofs: real OperationRegistry with
    invariant mode configured + real analytics handlers registered via
    register(), proving _invariant_mode does not leak into facade/engine
    kwargs when dispatched through registry.execute()."""

    @pytest.fixture
    def registry_with_analytics_handlers(self):
        """Real OperationRegistry with analytics handlers registered via register()."""
        from app.hoc.cus.hoc_spine.orchestrator.operation_registry import (
            OperationRegistry,
        )
        from app.hoc.cus.hoc_spine.orchestrator.handlers.analytics_handler import (
            register,
        )

        registry = OperationRegistry()
        register(registry)
        return registry

    @pytest.mark.asyncio
    async def test_feedback_list_feedback_no_invariant_mode_leakage(
        self, registry_with_analytics_handlers
    ):
        """analytics.feedback (list_feedback) via registry.execute() in MONITOR mode —
        _invariant_mode injected by registry but NOT forwarded to engine kwargs."""
        from app.hoc.cus.hoc_spine.authority.invariant_evaluator import InvariantMode
        from app.hoc.cus.hoc_spine.orchestrator.operation_registry import (
            OperationContext,
        )

        registry = registry_with_analytics_handlers
        registry.set_invariant_mode(InvariantMode.MONITOR)

        captured_kwargs = {}

        async def capturing_list_feedback(**kw):
            captured_kwargs.update(kw)
            return {"feedbacks": [], "total": 0}

        import app.hoc.cus.analytics.L5_engines.feedback_read_engine as fb_mod

        original_get = fb_mod.get_feedback_read_engine

        mock_engine = MagicMock()
        mock_engine.list_feedback = capturing_list_feedback
        fb_mod.get_feedback_read_engine = lambda: mock_engine

        try:
            ctx = OperationContext(
                session=MagicMock(),
                tenant_id="t-prod-wire-001",
                params={
                    "method": "list_feedback",
                    "limit": 20,
                },
            )
            result = await registry.execute("analytics.feedback", ctx)
            assert result.success is True
            # _invariant_mode must NOT leak through to engine kwargs
            assert "_invariant_mode" not in captured_kwargs
            # Legitimate params must still be forwarded
            assert captured_kwargs.get("limit") == 20
        finally:
            fb_mod.get_feedback_read_engine = original_get

    @pytest.mark.asyncio
    async def test_query_get_usage_statistics_no_invariant_mode_leakage(
        self, registry_with_analytics_handlers
    ):
        """analytics.query (get_usage_statistics) via registry.execute() in MONITOR mode —
        _invariant_mode injected by registry but NOT forwarded to facade kwargs."""
        from app.hoc.cus.hoc_spine.authority.invariant_evaluator import InvariantMode
        from app.hoc.cus.hoc_spine.orchestrator.operation_registry import (
            OperationContext,
        )

        registry = registry_with_analytics_handlers
        registry.set_invariant_mode(InvariantMode.MONITOR)

        captured_kwargs = {}

        async def capturing_get_usage_statistics(**kw):
            captured_kwargs.update(kw)
            return {"total_runs": 0}

        import app.hoc.cus.analytics.L5_engines.analytics_facade as af_mod

        original_get = af_mod.get_analytics_facade

        mock_facade = MagicMock()
        mock_facade.get_usage_statistics = capturing_get_usage_statistics
        af_mod.get_analytics_facade = lambda: mock_facade

        try:
            ctx = OperationContext(
                session=MagicMock(),
                tenant_id="t-prod-wire-002",
                params={
                    "method": "get_usage_statistics",
                    "days": 30,
                },
            )
            result = await registry.execute("analytics.query", ctx)
            assert result.success is True
            assert "_invariant_mode" not in captured_kwargs
            assert captured_kwargs.get("days") == 30
        finally:
            af_mod.get_analytics_facade = original_get

    @pytest.mark.asyncio
    async def test_detection_get_detection_status_no_invariant_mode_leakage(
        self, registry_with_analytics_handlers
    ):
        """analytics.detection (get_detection_status) via registry.execute() in MONITOR mode —
        _invariant_mode injected by registry but NOT forwarded to facade kwargs."""
        from app.hoc.cus.hoc_spine.authority.invariant_evaluator import InvariantMode
        from app.hoc.cus.hoc_spine.orchestrator.operation_registry import (
            OperationContext,
        )

        registry = registry_with_analytics_handlers
        registry.set_invariant_mode(InvariantMode.MONITOR)

        captured_kwargs = {}

        async def capturing_get_detection_status(**kw):
            captured_kwargs.update(kw)
            return {"status": "idle"}

        import app.hoc.cus.analytics.L5_engines.detection_facade as df_mod

        original_get = df_mod.get_detection_facade

        mock_facade = MagicMock()
        mock_facade.get_detection_status = capturing_get_detection_status
        df_mod.get_detection_facade = lambda: mock_facade

        try:
            ctx = OperationContext(
                session=MagicMock(),
                tenant_id="t-prod-wire-003",
                params={
                    "method": "get_detection_status",
                },
            )
            result = await registry.execute("analytics.detection", ctx)
            assert result.success is True
            assert "_invariant_mode" not in captured_kwargs
        finally:
            df_mod.get_detection_facade = original_get

    @pytest.mark.asyncio
    async def test_feedback_strict_mode_still_strips_invariant_mode(
        self, registry_with_analytics_handlers
    ):
        """analytics.feedback via registry.execute() in STRICT mode —
        _invariant_mode stripped even under stricter enforcement.
        (analytics.feedback has no BI invariant so STRICT does not block.)"""
        from app.hoc.cus.hoc_spine.authority.invariant_evaluator import InvariantMode
        from app.hoc.cus.hoc_spine.orchestrator.operation_registry import (
            OperationContext,
        )

        registry = registry_with_analytics_handlers
        registry.set_invariant_mode(InvariantMode.STRICT)

        captured_kwargs = {}

        async def capturing_list_feedback(**kw):
            captured_kwargs.update(kw)
            return {"feedbacks": [], "total": 0}

        import app.hoc.cus.analytics.L5_engines.feedback_read_engine as fb_mod

        original_get = fb_mod.get_feedback_read_engine

        mock_engine = MagicMock()
        mock_engine.list_feedback = capturing_list_feedback
        fb_mod.get_feedback_read_engine = lambda: mock_engine

        try:
            ctx = OperationContext(
                session=MagicMock(),
                tenant_id="t-strict-wire-001",
                params={
                    "method": "list_feedback",
                    "limit": 5,
                },
            )
            result = await registry.execute("analytics.feedback", ctx)
            assert result.success is True
            assert "_invariant_mode" not in captured_kwargs
            assert captured_kwargs.get("limit") == 5
        finally:
            fb_mod.get_feedback_read_engine = original_get


# =============================================================================
# AN-DELTA-05: Non-trigger and no-alias proofs
# =============================================================================


class TestAnalyticsNonTriggerProofs:
    """Prove analytics.* operations do NOT trigger BI-ANALYTICS-001 and no alias
    exists for analytics.* → cost_record.create."""

    def test_analytics_query_does_not_trigger_bi_analytics_001(self):
        """analytics.query must NOT trigger BI-ANALYTICS-001."""
        from app.hoc.cus.hoc_spine.authority.business_invariants import (
            check_all_for_operation,
        )

        results = check_all_for_operation(
            "analytics.query",
            {"operation": "analytics.query"},
        )
        inv_ids = [r[0] for r in results]
        assert "BI-ANALYTICS-001" not in inv_ids

    def test_analytics_feedback_does_not_trigger_bi_analytics_001(self):
        """analytics.feedback must NOT trigger BI-ANALYTICS-001."""
        from app.hoc.cus.hoc_spine.authority.business_invariants import (
            check_all_for_operation,
        )

        results = check_all_for_operation(
            "analytics.feedback",
            {"operation": "analytics.feedback"},
        )
        inv_ids = [r[0] for r in results]
        assert "BI-ANALYTICS-001" not in inv_ids

    def test_analytics_detection_does_not_trigger_bi_analytics_001(self):
        """analytics.detection must NOT trigger BI-ANALYTICS-001."""
        from app.hoc.cus.hoc_spine.authority.business_invariants import (
            check_all_for_operation,
        )

        results = check_all_for_operation(
            "analytics.detection",
            {"operation": "analytics.detection"},
        )
        inv_ids = [r[0] for r in results]
        assert "BI-ANALYTICS-001" not in inv_ids

    def test_no_alias_exists_for_analytics_operations(self):
        """No INVARIANT_OPERATION_ALIASES entry maps analytics.* → cost_record.create.

        By design: analytics domain reads/queries cost data, it does not create
        cost records. BI-ANALYTICS-001 guards cost record creation wherever it
        actually occurs, not in the analytics read/query path.
        """
        from app.hoc.cus.hoc_spine.authority.business_invariants import (
            INVARIANT_OPERATION_ALIASES,
        )

        analytics_aliases = {
            k: v
            for k, v in INVARIANT_OPERATION_ALIASES.items()
            if k.startswith("analytics.")
        }
        assert analytics_aliases == {}, (
            f"Unexpected analytics.* alias: {analytics_aliases}. "
            "Analytics domain does not own cost record creation."
        )

    def test_real_handler_registration_exists(self):
        """Verify analytics.* operations register on a real registry."""
        from app.hoc.cus.hoc_spine.orchestrator.operation_registry import (
            OperationRegistry,
        )
        from app.hoc.cus.hoc_spine.orchestrator.handlers.analytics_handler import (
            register,
        )

        registry = OperationRegistry()
        register(registry)

        expected_ops = [
            "analytics.feedback",
            "analytics.query",
            "analytics.detection",
            "analytics.canary_reports",
            "analytics.canary",
            "analytics.costsim.status",
            "analytics.costsim.simulate",
            "analytics.costsim.divergence",
            "analytics.costsim.datasets",
            "analytics.artifacts",
        ]
        for op in expected_ops:
            assert op in registry._handlers, f"Missing registration: {op}"
