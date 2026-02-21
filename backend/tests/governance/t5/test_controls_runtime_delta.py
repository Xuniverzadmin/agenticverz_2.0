# Layer: TEST
# AUDIENCE: INTERNAL
# Role: CTRL-DELTA-02/03 — Controls domain runtime correctness proofs
# artifact_class: TEST


"""
Controls Domain Runtime Correctness Tests (CTRL-DELTA-02, CTRL-DELTA-03)

Proves that:
  1. BI-CTRL-001 (control.set_threshold) is fail-closed on invalid thresholds
  2. BI-CTRL-002 (killswitch.activate) is fail-closed on missing entity/double-freeze
  3. BI-CTRL-003 (override.apply) is fail-closed on missing limit/negative override
  4. Real OperationRegistry dispatch for control operations honors invariant mode
  5. MONITOR mode logs but does not block control operations
  6. STRICT mode blocks on invariant violations
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest


# =============================================================================
# CTRL-DELTA-02: Contract tests — invariant fail-closed behavior
# =============================================================================


class TestControlsInvariantContracts:
    """Prove BI-CTRL-001, BI-CTRL-002, BI-CTRL-003 are fail-closed."""

    # --- BI-CTRL-001 (control.set_threshold) ---

    def test_bi_ctrl_001_rejects_missing_threshold(self):
        """BI-CTRL-001: control.set_threshold with no threshold → FAIL."""
        from app.hoc.cus.hoc_spine.authority.business_invariants import (
            check_all_for_operation,
        )

        results = check_all_for_operation(
            "control.set_threshold",
            {"operation": "control.set_threshold"},
        )
        assert len(results) >= 1
        inv_id, passed, message = results[0]
        assert inv_id == "BI-CTRL-001"
        assert passed is False
        assert "threshold" in message

    def test_bi_ctrl_001_rejects_negative_threshold(self):
        """BI-CTRL-001: control.set_threshold with negative value → FAIL."""
        from app.hoc.cus.hoc_spine.authority.business_invariants import (
            check_all_for_operation,
        )

        results = check_all_for_operation(
            "control.set_threshold",
            {"operation": "control.set_threshold", "threshold": -5.0},
        )
        assert len(results) >= 1
        _, passed, message = results[0]
        assert passed is False
        assert "-5" in message

    def test_bi_ctrl_001_rejects_non_numeric_threshold(self):
        """BI-CTRL-001: control.set_threshold with string value → FAIL."""
        from app.hoc.cus.hoc_spine.authority.business_invariants import (
            check_all_for_operation,
        )

        results = check_all_for_operation(
            "control.set_threshold",
            {"operation": "control.set_threshold", "threshold": "high"},
        )
        assert len(results) >= 1
        _, passed, message = results[0]
        assert passed is False
        assert "numeric" in message

    def test_bi_ctrl_001_accepts_valid_threshold(self):
        """BI-CTRL-001: control.set_threshold with valid value → PASS."""
        from app.hoc.cus.hoc_spine.authority.business_invariants import (
            check_all_for_operation,
        )

        results = check_all_for_operation(
            "control.set_threshold",
            {"operation": "control.set_threshold", "threshold": 75.0},
        )
        assert len(results) >= 1
        _, passed, _ = results[0]
        assert passed is True

    # --- BI-CTRL-002 (killswitch.activate) ---

    def test_bi_ctrl_002_rejects_missing_entity_id(self):
        """BI-CTRL-002: killswitch.activate with no entity_id → FAIL."""
        from app.hoc.cus.hoc_spine.authority.business_invariants import (
            check_all_for_operation,
        )

        results = check_all_for_operation(
            "killswitch.activate",
            {"operation": "killswitch.activate"},
        )
        assert len(results) >= 1
        inv_id, passed, message = results[0]
        assert inv_id == "BI-CTRL-002"
        assert passed is False
        assert "entity_id" in message

    def test_bi_ctrl_002_rejects_already_frozen(self):
        """BI-CTRL-002: killswitch.activate on already-frozen entity → FAIL."""
        from app.hoc.cus.hoc_spine.authority.business_invariants import (
            check_all_for_operation,
        )

        results = check_all_for_operation(
            "killswitch.activate",
            {
                "operation": "killswitch.activate",
                "entity_id": "e-001",
                "entity_frozen": True,
            },
        )
        assert len(results) >= 1
        _, passed, message = results[0]
        assert passed is False
        assert "already frozen" in message

    def test_bi_ctrl_002_accepts_valid_activation(self):
        """BI-CTRL-002: killswitch.activate on unfrozen entity → PASS."""
        from app.hoc.cus.hoc_spine.authority.business_invariants import (
            check_all_for_operation,
        )

        results = check_all_for_operation(
            "killswitch.activate",
            {
                "operation": "killswitch.activate",
                "entity_id": "e-001",
                "entity_frozen": False,
            },
        )
        assert len(results) >= 1
        _, passed, _ = results[0]
        assert passed is True

    # --- BI-CTRL-003 (override.apply) ---

    def test_bi_ctrl_003_rejects_missing_limit_id(self):
        """BI-CTRL-003: override.apply with no limit_id → FAIL."""
        from app.hoc.cus.hoc_spine.authority.business_invariants import (
            check_all_for_operation,
        )

        results = check_all_for_operation(
            "override.apply",
            {"operation": "override.apply", "override_value": 100},
        )
        assert len(results) >= 1
        inv_id, passed, message = results[0]
        assert inv_id == "BI-CTRL-003"
        assert passed is False
        assert "limit_id" in message

    def test_bi_ctrl_003_rejects_non_existent_limit(self):
        """BI-CTRL-003: override.apply on non-existent limit → FAIL."""
        from app.hoc.cus.hoc_spine.authority.business_invariants import (
            check_all_for_operation,
        )

        results = check_all_for_operation(
            "override.apply",
            {
                "operation": "override.apply",
                "limit_id": "lim-001",
                "limit_exists": False,
                "override_value": 100,
            },
        )
        assert len(results) >= 1
        _, passed, message = results[0]
        assert passed is False
        assert "does not exist" in message

    def test_bi_ctrl_003_rejects_negative_override(self):
        """BI-CTRL-003: override.apply with negative value → FAIL."""
        from app.hoc.cus.hoc_spine.authority.business_invariants import (
            check_all_for_operation,
        )

        results = check_all_for_operation(
            "override.apply",
            {
                "operation": "override.apply",
                "limit_id": "lim-001",
                "limit_exists": True,
                "override_value": -10,
            },
        )
        assert len(results) >= 1
        _, passed, message = results[0]
        assert passed is False
        assert "-10" in message

    def test_bi_ctrl_003_accepts_valid_override(self):
        """BI-CTRL-003: override.apply with valid fields → PASS."""
        from app.hoc.cus.hoc_spine.authority.business_invariants import (
            check_all_for_operation,
        )

        results = check_all_for_operation(
            "override.apply",
            {
                "operation": "override.apply",
                "limit_id": "lim-001",
                "limit_exists": True,
                "override_value": 200,
            },
        )
        assert len(results) >= 1
        _, passed, _ = results[0]
        assert passed is True

    # --- STRICT mode escalation ---

    def test_bi_ctrl_002_in_strict_mode_raises(self):
        """BI-CTRL-002 (HIGH severity) in STRICT mode → BusinessInvariantViolation."""
        from app.hoc.cus.hoc_spine.authority.business_invariants import (
            BusinessInvariantViolation,
        )
        from app.hoc.cus.hoc_spine.authority.invariant_evaluator import (
            InvariantMode,
            evaluate_invariants,
        )

        with pytest.raises(BusinessInvariantViolation) as exc_info:
            evaluate_invariants(
                "killswitch.activate",
                {"operation": "killswitch.activate"},
                InvariantMode.STRICT,
            )
        assert "BI-CTRL-002" in exc_info.value.invariant_id

    def test_bi_ctrl_003_in_strict_mode_raises(self):
        """BI-CTRL-003 (HIGH severity) in STRICT mode → BusinessInvariantViolation."""
        from app.hoc.cus.hoc_spine.authority.business_invariants import (
            BusinessInvariantViolation,
        )
        from app.hoc.cus.hoc_spine.authority.invariant_evaluator import (
            InvariantMode,
            evaluate_invariants,
        )

        with pytest.raises(BusinessInvariantViolation) as exc_info:
            evaluate_invariants(
                "override.apply",
                {"operation": "override.apply"},
                InvariantMode.STRICT,
            )
        assert "BI-CTRL-003" in exc_info.value.invariant_id


# =============================================================================
# CTRL-DELTA-03: In-process execution assertions via real OperationRegistry
# =============================================================================


class TestControlsRegistryDispatch:
    """Prove controls operations dispatch through real OperationRegistry."""

    @pytest.fixture
    def registry_with_controls_handlers(self):
        """Create a fresh OperationRegistry with mock controls handlers."""
        from app.hoc.cus.hoc_spine.orchestrator.operation_registry import (
            OperationContext,
            OperationRegistry,
            OperationResult,
        )

        registry = OperationRegistry()

        threshold_handler = MagicMock()
        threshold_handler.execute = AsyncMock(
            return_value=OperationResult.ok(
                {"control_id": "ctrl-001", "threshold": 75.0, "status": "updated"}
            )
        )
        registry.register("control.set_threshold", threshold_handler)

        killswitch_handler = MagicMock()
        killswitch_handler.execute = AsyncMock(
            return_value=OperationResult.ok(
                {"entity_id": "e-001", "frozen": True}
            )
        )
        registry.register("killswitch.activate", killswitch_handler)

        override_handler = MagicMock()
        override_handler.execute = AsyncMock(
            return_value=OperationResult.ok(
                {"limit_id": "lim-001", "override_value": 200, "status": "applied"}
            )
        )
        registry.register("override.apply", override_handler)

        return registry, threshold_handler, killswitch_handler, override_handler

    @pytest.mark.asyncio
    async def test_threshold_dispatch_success(
        self, registry_with_controls_handlers
    ):
        """control.set_threshold dispatches and returns success with valid context."""
        from app.hoc.cus.hoc_spine.orchestrator.operation_registry import (
            OperationContext,
        )

        registry, threshold_handler, _, _ = registry_with_controls_handlers

        ctx = OperationContext(
            session=None,
            tenant_id="t-test",
            params={"threshold": 75.0},
        )
        result = await registry.execute("control.set_threshold", ctx)
        assert result.success is True
        assert result.data["threshold"] == 75.0
        assert threshold_handler.execute.called

    @pytest.mark.asyncio
    async def test_threshold_monitor_mode_allows_bad_context(
        self, registry_with_controls_handlers
    ):
        """In MONITOR mode, missing threshold logs but doesn't block dispatch."""
        from app.hoc.cus.hoc_spine.authority.invariant_evaluator import InvariantMode
        from app.hoc.cus.hoc_spine.orchestrator.operation_registry import (
            OperationContext,
        )

        registry, threshold_handler, _, _ = registry_with_controls_handlers
        registry.set_invariant_mode(InvariantMode.MONITOR)

        ctx = OperationContext(
            session=None,
            tenant_id="t-test",
            params={},  # No threshold — BI-CTRL-001 fails
        )
        result = await registry.execute("control.set_threshold", ctx)
        assert result.success is True  # MONITOR doesn't block
        assert threshold_handler.execute.called

    @pytest.mark.asyncio
    async def test_threshold_strict_blocks_missing(
        self, registry_with_controls_handlers
    ):
        """In STRICT mode, missing threshold triggers BI-CTRL-001 → blocked."""
        from app.hoc.cus.hoc_spine.authority.business_invariants import (
            BusinessInvariantViolation,
        )
        from app.hoc.cus.hoc_spine.authority.invariant_evaluator import InvariantMode
        from app.hoc.cus.hoc_spine.orchestrator.operation_registry import (
            OperationContext,
        )

        registry, _, _, _ = registry_with_controls_handlers
        registry.set_invariant_mode(InvariantMode.STRICT)

        ctx = OperationContext(
            session=None,
            tenant_id="t-test",
            params={},  # No threshold
        )
        with pytest.raises(BusinessInvariantViolation):
            await registry.execute("control.set_threshold", ctx)

    @pytest.mark.asyncio
    async def test_killswitch_dispatch_success(
        self, registry_with_controls_handlers
    ):
        """killswitch.activate dispatches successfully for valid entity."""
        from app.hoc.cus.hoc_spine.orchestrator.operation_registry import (
            OperationContext,
        )

        registry, _, killswitch_handler, _ = registry_with_controls_handlers

        ctx = OperationContext(
            session=None,
            tenant_id="t-test",
            params={"entity_id": "e-001", "entity_frozen": False},
        )
        result = await registry.execute("killswitch.activate", ctx)
        assert result.success is True
        assert result.data["frozen"] is True
        assert killswitch_handler.execute.called

    @pytest.mark.asyncio
    async def test_killswitch_strict_blocks_already_frozen(
        self, registry_with_controls_handlers
    ):
        """In STRICT mode, activating already-frozen killswitch → blocked."""
        from app.hoc.cus.hoc_spine.authority.business_invariants import (
            BusinessInvariantViolation,
        )
        from app.hoc.cus.hoc_spine.authority.invariant_evaluator import InvariantMode
        from app.hoc.cus.hoc_spine.orchestrator.operation_registry import (
            OperationContext,
        )

        registry, _, _, _ = registry_with_controls_handlers
        registry.set_invariant_mode(InvariantMode.STRICT)

        ctx = OperationContext(
            session=None,
            tenant_id="t-test",
            params={"entity_id": "e-001", "entity_frozen": True},
        )
        with pytest.raises(BusinessInvariantViolation):
            await registry.execute("killswitch.activate", ctx)

    @pytest.mark.asyncio
    async def test_override_dispatch_success(
        self, registry_with_controls_handlers
    ):
        """override.apply dispatches successfully with valid limit."""
        from app.hoc.cus.hoc_spine.orchestrator.operation_registry import (
            OperationContext,
        )

        registry, _, _, override_handler = registry_with_controls_handlers

        ctx = OperationContext(
            session=None,
            tenant_id="t-test",
            params={
                "limit_id": "lim-001",
                "limit_exists": True,
                "override_value": 200,
            },
        )
        result = await registry.execute("override.apply", ctx)
        assert result.success is True
        assert result.data["status"] == "applied"
        assert override_handler.execute.called

    @pytest.mark.asyncio
    async def test_override_strict_blocks_missing_limit(
        self, registry_with_controls_handlers
    ):
        """In STRICT mode, overriding non-existent limit → blocked."""
        from app.hoc.cus.hoc_spine.authority.business_invariants import (
            BusinessInvariantViolation,
        )
        from app.hoc.cus.hoc_spine.authority.invariant_evaluator import InvariantMode
        from app.hoc.cus.hoc_spine.orchestrator.operation_registry import (
            OperationContext,
        )

        registry, _, _, _ = registry_with_controls_handlers
        registry.set_invariant_mode(InvariantMode.STRICT)

        ctx = OperationContext(
            session=None,
            tenant_id="t-test",
            params={
                "limit_id": "lim-001",
                "limit_exists": False,
                "override_value": 200,
            },
        )
        with pytest.raises(BusinessInvariantViolation):
            await registry.execute("override.apply", ctx)

    @pytest.mark.asyncio
    async def test_threshold_dispatch_idempotent(
        self, registry_with_controls_handlers
    ):
        """Dispatching control.set_threshold twice is deterministic."""
        from app.hoc.cus.hoc_spine.orchestrator.operation_registry import (
            OperationContext,
        )

        registry, threshold_handler, _, _ = registry_with_controls_handlers

        ctx = OperationContext(
            session=None,
            tenant_id="t-test",
            params={"threshold": 75.0},
        )
        r1 = await registry.execute("control.set_threshold", ctx)
        r2 = await registry.execute("control.set_threshold", ctx)
        assert r1.success == r2.success
        assert r1.data == r2.data
        assert threshold_handler.execute.call_count == 2

    @pytest.mark.asyncio
    async def test_controls_dispatch_result_contains_operation(
        self, registry_with_controls_handlers
    ):
        """Result from controls dispatch carries the operation name."""
        from app.hoc.cus.hoc_spine.orchestrator.operation_registry import (
            OperationContext,
        )

        registry, _, _, _ = registry_with_controls_handlers

        ctx = OperationContext(
            session=None,
            tenant_id="t-test",
            params={"threshold": 50.0},
        )
        result = await registry.execute("control.set_threshold", ctx)
        assert result.operation == "control.set_threshold"
