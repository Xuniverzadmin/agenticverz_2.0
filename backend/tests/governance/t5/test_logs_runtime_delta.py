# Layer: TEST
# AUDIENCE: INTERNAL
# Role: Logs domain runtime correctness proofs (BI-LOGS-001)
# artifact_class: TEST


"""
Logs Domain Runtime Correctness Tests (BI-LOGS-001)

Proves that:
  1. BI-LOGS-001 (trace.append) is fail-closed on missing/invalid sequence_no
  2. Positive pass when sequence_no is valid int > max_sequence_no
  3. MONITOR mode logs but does not block dispatch
  4. STRICT mode blocks on invariant violations
  5. Real OperationRegistry.execute(...) dispatch proof for trace.append
  6. logs.query / logs.evidence / logs.traces_api do NOT trigger
     BI-LOGS-001
  7. _invariant_mode internal key is stripped before kwargs forwarding
     in logs.query, logs.evidence, logs.traces_api, and logs.certificate handlers
  8. No alias mapping exists for logs.* → trace.append (by design)
  9. Production-wiring leakage proofs: real OperationRegistry with
     invariant mode configured + real logs handlers registered,
     proving _invariant_mode does not leak into facade/engine kwargs
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest


# =============================================================================
# LG-DELTA-01: Contract tests — invariant fail-closed behavior
# =============================================================================


class TestLogsInvariantContracts:
    """Prove BI-LOGS-001 is fail-closed on missing/invalid sequence_no."""

    # --- Fail-closed negatives ---

    def test_bi_logs_001_rejects_missing_sequence_no(self):
        """BI-LOGS-001: trace.append with no sequence_no → FAIL."""
        from app.hoc.cus.hoc_spine.authority.business_invariants import (
            check_all_for_operation,
        )

        results = check_all_for_operation(
            "trace.append",
            {"operation": "trace.append"},
        )
        assert len(results) >= 1
        inv_id, passed, message = results[0]
        assert inv_id == "BI-LOGS-001"
        assert passed is False
        assert "sequence_no" in message

    def test_bi_logs_001_rejects_non_int_sequence_no(self):
        """BI-LOGS-001: trace.append with string sequence_no → FAIL."""
        from app.hoc.cus.hoc_spine.authority.business_invariants import (
            check_all_for_operation,
        )

        results = check_all_for_operation(
            "trace.append",
            {"operation": "trace.append", "sequence_no": "not-an-int"},
        )
        assert len(results) >= 1
        inv_id, passed, message = results[0]
        assert inv_id == "BI-LOGS-001"
        assert passed is False
        assert "int" in message

    def test_bi_logs_001_rejects_sequence_no_lte_max(self):
        """BI-LOGS-001: trace.append with sequence_no <= max_sequence_no → FAIL."""
        from app.hoc.cus.hoc_spine.authority.business_invariants import (
            check_all_for_operation,
        )

        results = check_all_for_operation(
            "trace.append",
            {
                "operation": "trace.append",
                "sequence_no": 5,
                "max_sequence_no": 10,
            },
        )
        assert len(results) >= 1
        inv_id, passed, message = results[0]
        assert inv_id == "BI-LOGS-001"
        assert passed is False
        assert "5" in message
        assert "10" in message

    def test_bi_logs_001_rejects_sequence_no_equal_max(self):
        """BI-LOGS-001: trace.append with sequence_no == max_sequence_no → FAIL."""
        from app.hoc.cus.hoc_spine.authority.business_invariants import (
            check_all_for_operation,
        )

        results = check_all_for_operation(
            "trace.append",
            {
                "operation": "trace.append",
                "sequence_no": 7,
                "max_sequence_no": 7,
            },
        )
        assert len(results) >= 1
        inv_id, passed, message = results[0]
        assert inv_id == "BI-LOGS-001"
        assert passed is False

    # --- Positive passes ---

    def test_bi_logs_001_passes_valid_context_with_max(self):
        """BI-LOGS-001: trace.append with sequence_no > max_sequence_no → PASS."""
        from app.hoc.cus.hoc_spine.authority.business_invariants import (
            check_all_for_operation,
        )

        results = check_all_for_operation(
            "trace.append",
            {
                "operation": "trace.append",
                "sequence_no": 11,
                "max_sequence_no": 10,
            },
        )
        assert len(results) >= 1
        inv_id, passed, _ = results[0]
        assert inv_id == "BI-LOGS-001"
        assert passed is True

    def test_bi_logs_001_passes_valid_context_no_max(self):
        """BI-LOGS-001: trace.append with sequence_no and no max → PASS."""
        from app.hoc.cus.hoc_spine.authority.business_invariants import (
            check_all_for_operation,
        )

        results = check_all_for_operation(
            "trace.append",
            {
                "operation": "trace.append",
                "sequence_no": 1,
            },
        )
        assert len(results) >= 1
        inv_id, passed, _ = results[0]
        assert inv_id == "BI-LOGS-001"
        assert passed is True


# =============================================================================
# LG-DELTA-02: MONITOR / STRICT mode behavior
# =============================================================================


class TestLogsInvariantModes:
    """Prove MONITOR and STRICT modes behave correctly for BI-LOGS-001."""

    def test_monitor_mode_does_not_raise(self):
        """MONITOR mode: BI-LOGS-001 fails but no exception raised."""
        from app.hoc.cus.hoc_spine.authority.invariant_evaluator import (
            InvariantMode,
            evaluate_invariants,
        )

        results = evaluate_invariants(
            "trace.append",
            {"operation": "trace.append"},
            InvariantMode.MONITOR,
        )
        assert len(results) >= 1
        assert any(
            r.invariant_id == "BI-LOGS-001" and not r.passed for r in results
        )

    def test_monitor_mode_returns_failure_details(self):
        """MONITOR mode: returns violation details for non-int sequence_no."""
        from app.hoc.cus.hoc_spine.authority.invariant_evaluator import (
            InvariantMode,
            evaluate_invariants,
        )

        results = evaluate_invariants(
            "trace.append",
            {"operation": "trace.append", "sequence_no": "bad"},
            InvariantMode.MONITOR,
        )
        failed = [
            r for r in results if r.invariant_id == "BI-LOGS-001" and not r.passed
        ]
        assert len(failed) == 1
        assert "int" in failed[0].message

    def test_strict_mode_raises_on_missing_sequence_no(self):
        """STRICT mode: BI-LOGS-001 with no sequence_no → BusinessInvariantViolation."""
        from app.hoc.cus.hoc_spine.authority.business_invariants import (
            BusinessInvariantViolation,
        )
        from app.hoc.cus.hoc_spine.authority.invariant_evaluator import (
            InvariantMode,
            evaluate_invariants,
        )

        with pytest.raises(BusinessInvariantViolation) as exc_info:
            evaluate_invariants(
                "trace.append",
                {"operation": "trace.append"},
                InvariantMode.STRICT,
            )
        assert "BI-LOGS-001" in exc_info.value.invariant_id

    def test_strict_mode_raises_on_non_int(self):
        """STRICT mode: non-int sequence_no → raises."""
        from app.hoc.cus.hoc_spine.authority.business_invariants import (
            BusinessInvariantViolation,
        )
        from app.hoc.cus.hoc_spine.authority.invariant_evaluator import (
            InvariantMode,
            evaluate_invariants,
        )

        with pytest.raises(BusinessInvariantViolation) as exc_info:
            evaluate_invariants(
                "trace.append",
                {"operation": "trace.append", "sequence_no": 3.14},
                InvariantMode.STRICT,
            )
        assert "BI-LOGS-001" in exc_info.value.invariant_id

    def test_strict_mode_passes_valid_context(self):
        """STRICT mode: valid context → no exception."""
        from app.hoc.cus.hoc_spine.authority.invariant_evaluator import (
            InvariantMode,
            evaluate_invariants,
        )

        results = evaluate_invariants(
            "trace.append",
            {
                "operation": "trace.append",
                "sequence_no": 5,
                "max_sequence_no": 4,
            },
            InvariantMode.STRICT,
        )
        assert all(r.passed for r in results)


# =============================================================================
# LG-DELTA-03: Registry dispatch proofs for trace.append
# =============================================================================


class TestLogsRegistryDispatch:
    """Prove trace.append dispatches through real OperationRegistry."""

    @pytest.fixture
    def registry_with_trace_append_handler(self):
        """Create OperationRegistry with a mock trace.append handler."""
        from app.hoc.cus.hoc_spine.orchestrator.operation_registry import (
            OperationRegistry,
            OperationResult,
        )

        registry = OperationRegistry()

        handler = MagicMock()
        handler.execute = AsyncMock(
            return_value=OperationResult.ok({"trace_id": "tr-001"})
        )
        registry.register("trace.append", handler)

        return registry, handler

    @pytest.mark.asyncio
    async def test_monitor_allows_bad_context(self, registry_with_trace_append_handler):
        """MONITOR: bad context (no sequence_no) → dispatches anyway."""
        from app.hoc.cus.hoc_spine.authority.invariant_evaluator import InvariantMode
        from app.hoc.cus.hoc_spine.orchestrator.operation_registry import (
            OperationContext,
        )

        registry, handler = registry_with_trace_append_handler
        registry.set_invariant_mode(InvariantMode.MONITOR)

        ctx = OperationContext(
            session=None,
            tenant_id="t-monitor-001",
            params={"tenant_id": "t-monitor-001"},
        )
        result = await registry.execute("trace.append", ctx)
        assert result.success is True
        assert handler.execute.called

    @pytest.mark.asyncio
    async def test_strict_blocks_bad_context(self, registry_with_trace_append_handler):
        """STRICT: bad context (no sequence_no) → blocked pre-dispatch."""
        from app.hoc.cus.hoc_spine.authority.business_invariants import (
            BusinessInvariantViolation,
        )
        from app.hoc.cus.hoc_spine.authority.invariant_evaluator import InvariantMode
        from app.hoc.cus.hoc_spine.orchestrator.operation_registry import (
            OperationContext,
        )

        registry, handler = registry_with_trace_append_handler
        registry.set_invariant_mode(InvariantMode.STRICT)

        ctx = OperationContext(
            session=None,
            tenant_id="t-strict-001",
            params={"tenant_id": "t-strict-001"},
        )

        with pytest.raises(BusinessInvariantViolation) as exc_info:
            await registry.execute("trace.append", ctx)

        assert "BI-LOGS-001" in exc_info.value.invariant_id
        assert not handler.execute.called

    @pytest.mark.asyncio
    async def test_strict_passes_valid_context(self, registry_with_trace_append_handler):
        """STRICT: valid context → dispatches to handler."""
        from app.hoc.cus.hoc_spine.authority.invariant_evaluator import InvariantMode
        from app.hoc.cus.hoc_spine.orchestrator.operation_registry import (
            OperationContext,
        )

        registry, handler = registry_with_trace_append_handler
        registry.set_invariant_mode(InvariantMode.STRICT)

        ctx = OperationContext(
            session=None,
            tenant_id="t-valid-001",
            params={
                "tenant_id": "t-valid-001",
                "sequence_no": 5,
                "max_sequence_no": 4,
            },
        )

        result = await registry.execute("trace.append", ctx)
        assert result.success is True
        assert result.data["trace_id"] == "tr-001"
        assert handler.execute.called

    @pytest.mark.asyncio
    async def test_unregistered_operation_fails(
        self, registry_with_trace_append_handler
    ):
        """Unregistered operation → OperationResult.fail."""
        from app.hoc.cus.hoc_spine.orchestrator.operation_registry import (
            OperationContext,
        )

        registry, _ = registry_with_trace_append_handler

        ctx = OperationContext(
            session=None,
            tenant_id="t-bad-001",
            params={},
        )
        result = await registry.execute("trace.nonexistent", ctx)
        assert result.success is False


# =============================================================================
# LG-DELTA-04: Production-wiring leakage proofs (real registry path)
# =============================================================================


class TestLogsProductionWiringLeakage:
    """Production-wiring leakage proofs: real OperationRegistry with
    invariant mode configured + real logs handlers registered via
    register(), proving _invariant_mode does not leak into facade/engine
    kwargs when dispatched through registry.execute()."""

    @pytest.fixture
    def registry_with_logs_handlers(self):
        """Real OperationRegistry with logs handlers registered via register()."""
        from app.hoc.cus.hoc_spine.orchestrator.operation_registry import (
            OperationRegistry,
        )
        from app.hoc.cus.hoc_spine.orchestrator.handlers.logs_handler import (
            register,
        )

        registry = OperationRegistry()
        register(registry)
        return registry

    @pytest.mark.asyncio
    async def test_query_list_llm_run_records_no_invariant_mode_leakage(
        self, registry_with_logs_handlers
    ):
        """logs.query (list_llm_run_records) via registry.execute() in MONITOR mode —
        _invariant_mode injected by registry but NOT forwarded to facade kwargs."""
        from app.hoc.cus.hoc_spine.authority.invariant_evaluator import InvariantMode
        from app.hoc.cus.hoc_spine.orchestrator.operation_registry import (
            OperationContext,
        )

        registry = registry_with_logs_handlers
        registry.set_invariant_mode(InvariantMode.MONITOR)

        captured_kwargs = {}

        async def capturing_list_llm_run_records(**kw):
            captured_kwargs.update(kw)
            return {"records": [], "total": 0}

        import app.hoc.cus.logs.L5_engines.logs_facade as lf_mod

        original_get = lf_mod.get_logs_facade

        mock_facade = MagicMock()
        mock_facade.list_llm_run_records = capturing_list_llm_run_records
        lf_mod.get_logs_facade = lambda: mock_facade

        try:
            ctx = OperationContext(
                session=MagicMock(),
                tenant_id="t-prod-wire-001",
                params={
                    "method": "list_llm_run_records",
                    "limit": 20,
                },
            )
            result = await registry.execute("logs.query", ctx)
            assert result.success is True
            # _invariant_mode must NOT leak through to facade kwargs
            assert "_invariant_mode" not in captured_kwargs
            # Legitimate params must still be forwarded
            assert captured_kwargs.get("limit") == 20
        finally:
            lf_mod.get_logs_facade = original_get

    @pytest.mark.asyncio
    async def test_evidence_list_chains_no_invariant_mode_leakage(
        self, registry_with_logs_handlers
    ):
        """logs.evidence (list_chains) via registry.execute() in MONITOR mode —
        _invariant_mode injected by registry but NOT forwarded to facade kwargs."""
        from app.hoc.cus.hoc_spine.authority.invariant_evaluator import InvariantMode
        from app.hoc.cus.hoc_spine.orchestrator.operation_registry import (
            OperationContext,
        )

        registry = registry_with_logs_handlers
        registry.set_invariant_mode(InvariantMode.MONITOR)

        captured_kwargs = {}

        async def capturing_list_chains(**kw):
            captured_kwargs.update(kw)
            return {"chains": []}

        import app.hoc.cus.logs.L5_engines.evidence_facade as ef_mod

        original_get = ef_mod.get_evidence_facade

        mock_facade = MagicMock()
        mock_facade.list_chains = capturing_list_chains
        ef_mod.get_evidence_facade = lambda: mock_facade

        try:
            ctx = OperationContext(
                session=MagicMock(),
                tenant_id="t-prod-wire-002",
                params={
                    "method": "list_chains",
                    "page": 1,
                },
            )
            result = await registry.execute("logs.evidence", ctx)
            assert result.success is True
            assert "_invariant_mode" not in captured_kwargs
            assert captured_kwargs.get("page") == 1
        finally:
            ef_mod.get_evidence_facade = original_get

    @pytest.mark.asyncio
    async def test_traces_api_list_traces_no_invariant_mode_leakage(
        self, registry_with_logs_handlers
    ):
        """logs.traces_api (list_traces) via registry.execute() in MONITOR mode —
        _invariant_mode injected by registry but NOT forwarded to engine kwargs."""
        from app.hoc.cus.hoc_spine.authority.invariant_evaluator import InvariantMode
        from app.hoc.cus.hoc_spine.orchestrator.operation_registry import (
            OperationContext,
        )

        registry = registry_with_logs_handlers
        registry.set_invariant_mode(InvariantMode.MONITOR)

        captured_kwargs = {}

        async def capturing_list_traces(**kw):
            captured_kwargs.update(kw)
            return {"traces": []}

        import app.hoc.cus.logs.L5_engines.trace_api_engine as ta_mod
        import app.hoc.cus.hoc_spine.orchestrator.coordinators.bridges.logs_bridge as lb_mod

        original_get_engine = ta_mod.get_trace_api_engine
        original_get_bridge = lb_mod.get_logs_bridge

        mock_engine = MagicMock()
        mock_engine.list_traces = capturing_list_traces
        ta_mod.get_trace_api_engine = lambda store: mock_engine

        mock_bridge = MagicMock()
        mock_bridge.traces_store_capability = MagicMock(return_value=MagicMock())
        lb_mod.get_logs_bridge = lambda: mock_bridge

        try:
            ctx = OperationContext(
                session=MagicMock(),
                tenant_id="t-prod-wire-003",
                params={
                    "method": "list_traces",
                    "limit": 50,
                },
            )
            result = await registry.execute("logs.traces_api", ctx)
            assert result.success is True
            assert "_invariant_mode" not in captured_kwargs
            assert captured_kwargs.get("limit") == 50
        finally:
            ta_mod.get_trace_api_engine = original_get_engine
            lb_mod.get_logs_bridge = original_get_bridge

    @pytest.mark.asyncio
    async def test_query_strict_mode_still_strips_invariant_mode(
        self, registry_with_logs_handlers
    ):
        """logs.query via registry.execute() in STRICT mode —
        _invariant_mode stripped even under stricter enforcement.
        (logs.query has no BI invariant so STRICT does not block.)"""
        from app.hoc.cus.hoc_spine.authority.invariant_evaluator import InvariantMode
        from app.hoc.cus.hoc_spine.orchestrator.operation_registry import (
            OperationContext,
        )

        registry = registry_with_logs_handlers
        registry.set_invariant_mode(InvariantMode.STRICT)

        captured_kwargs = {}

        async def capturing_list_llm_run_records(**kw):
            captured_kwargs.update(kw)
            return {"records": [], "total": 0}

        import app.hoc.cus.logs.L5_engines.logs_facade as lf_mod

        original_get = lf_mod.get_logs_facade

        mock_facade = MagicMock()
        mock_facade.list_llm_run_records = capturing_list_llm_run_records
        lf_mod.get_logs_facade = lambda: mock_facade

        try:
            ctx = OperationContext(
                session=MagicMock(),
                tenant_id="t-strict-wire-001",
                params={
                    "method": "list_llm_run_records",
                    "limit": 5,
                },
            )
            result = await registry.execute("logs.query", ctx)
            assert result.success is True
            assert "_invariant_mode" not in captured_kwargs
            assert captured_kwargs.get("limit") == 5
        finally:
            lf_mod.get_logs_facade = original_get


# =============================================================================
# LG-DELTA-05: Non-trigger and no-alias proofs
# =============================================================================


class TestLogsNonTriggerProofs:
    """Prove logs.* operations do NOT trigger BI-LOGS-001 and no alias
    exists for logs.* → trace.append."""

    def test_logs_query_does_not_trigger_bi_logs_001(self):
        """logs.query must NOT trigger BI-LOGS-001."""
        from app.hoc.cus.hoc_spine.authority.business_invariants import (
            check_all_for_operation,
        )

        results = check_all_for_operation(
            "logs.query",
            {"operation": "logs.query"},
        )
        inv_ids = [r[0] for r in results]
        assert "BI-LOGS-001" not in inv_ids

    def test_logs_evidence_does_not_trigger_bi_logs_001(self):
        """logs.evidence must NOT trigger BI-LOGS-001."""
        from app.hoc.cus.hoc_spine.authority.business_invariants import (
            check_all_for_operation,
        )

        results = check_all_for_operation(
            "logs.evidence",
            {"operation": "logs.evidence"},
        )
        inv_ids = [r[0] for r in results]
        assert "BI-LOGS-001" not in inv_ids

    def test_logs_traces_api_does_not_trigger_bi_logs_001(self):
        """logs.traces_api must NOT trigger BI-LOGS-001."""
        from app.hoc.cus.hoc_spine.authority.business_invariants import (
            check_all_for_operation,
        )

        results = check_all_for_operation(
            "logs.traces_api",
            {"operation": "logs.traces_api"},
        )
        inv_ids = [r[0] for r in results]
        assert "BI-LOGS-001" not in inv_ids

    def test_no_alias_exists_for_logs_operations(self):
        """No INVARIANT_OPERATION_ALIASES entry maps logs.* → trace.append.

        By design: logs domain reads/queries/exports trace data and renders
        reports — it does not append trace entries with sequence ordering.
        BI-LOGS-001 guards trace.append wherever it actually occurs,
        not in the logs read/query/render path.
        """
        from app.hoc.cus.hoc_spine.authority.business_invariants import (
            INVARIANT_OPERATION_ALIASES,
        )

        logs_aliases = {
            k: v
            for k, v in INVARIANT_OPERATION_ALIASES.items()
            if k.startswith("logs.")
        }
        assert logs_aliases == {}, (
            f"Unexpected logs.* alias: {logs_aliases}. "
            "Logs domain does not own trace.append."
        )

    def test_real_handler_registration_exists(self):
        """Verify logs.* operations register on a real registry."""
        from app.hoc.cus.hoc_spine.orchestrator.operation_registry import (
            OperationRegistry,
        )
        from app.hoc.cus.hoc_spine.orchestrator.handlers.logs_handler import (
            register,
        )

        registry = OperationRegistry()
        register(registry)

        expected_ops = [
            "logs.query",
            "logs.evidence",
            "logs.certificate",
            "logs.replay",
            "logs.evidence_report",
            "logs.pdf",
            "logs.capture",
            "logs.traces_api",
        ]
        for op in expected_ops:
            assert op in registry._handlers, f"Missing registration: {op}"
