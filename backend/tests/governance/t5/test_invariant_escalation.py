# Layer: L8 — Test
# AUDIENCE: INTERNAL
# Role: Validates BA-N6-02 — invariant mode escalation (MONITOR → ENFORCE → STRICT)
# artifact_class: TEST

"""
Invariant Escalation Path Tests (BA-N6-02)

Proves that:
  1. MONITOR mode logs without blocking
  2. ENFORCE mode blocks on CRITICAL invariant violations
  3. STRICT mode blocks on ANY invariant violation
  4. Default mode remains MONITOR unless explicitly configured
  5. Mode configuration is wired through OperationRegistry
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# =============================================================================
# Unit tests: invariant_evaluator modes
# =============================================================================


class TestInvariantModeEscalation:
    """Prove MONITOR/ENFORCE/STRICT behavior in invariant_evaluator."""

    def test_monitor_mode_does_not_raise_on_critical(self):
        """MONITOR mode logs but never raises, even for CRITICAL violations."""
        from app.hoc.cus.hoc_spine.authority.invariant_evaluator import (
            InvariantMode,
            evaluate_invariants,
        )

        # project.create with missing tenant_id → BI-TENANT-001 CRITICAL failure
        context = {"operation": "project.create"}
        results = evaluate_invariants("project.create", context, InvariantMode.MONITOR)

        # Should return results, not raise
        assert isinstance(results, list)
        assert len(results) >= 1
        # At least one failure
        failed = [r for r in results if not r.passed]
        assert len(failed) >= 1
        assert failed[0].severity == "CRITICAL"

    def test_enforce_mode_raises_on_critical(self):
        """ENFORCE mode raises BusinessInvariantViolation on CRITICAL failure."""
        from app.hoc.cus.hoc_spine.authority.business_invariants import (
            BusinessInvariantViolation,
        )
        from app.hoc.cus.hoc_spine.authority.invariant_evaluator import (
            InvariantMode,
            evaluate_invariants,
        )

        context = {"operation": "project.create"}  # missing tenant_id → CRITICAL

        with pytest.raises(BusinessInvariantViolation) as exc_info:
            evaluate_invariants("project.create", context, InvariantMode.ENFORCE)

        assert exc_info.value.severity == "CRITICAL"
        assert "BI-TENANT-001" in exc_info.value.invariant_id

    def test_enforce_mode_does_not_raise_on_medium(self):
        """ENFORCE mode does NOT raise for MEDIUM violations."""
        from app.hoc.cus.hoc_spine.authority.invariant_evaluator import (
            InvariantMode,
            evaluate_invariants,
        )

        # incident.transition with RESOLVED→ACTIVE → BI-INCIDENT-001 MEDIUM failure
        context = {
            "operation": "incident.transition",
            "current_status": "RESOLVED",
            "target_status": "ACTIVE",
        }

        # Should NOT raise (MEDIUM severity, ENFORCE only blocks CRITICAL)
        results = evaluate_invariants("incident.transition", context, InvariantMode.ENFORCE)
        assert isinstance(results, list)
        failed = [r for r in results if not r.passed]
        assert len(failed) >= 1
        assert failed[0].severity == "MEDIUM"

    def test_strict_mode_raises_on_any_failure(self):
        """STRICT mode raises on ANY invariant failure, even MEDIUM."""
        from app.hoc.cus.hoc_spine.authority.business_invariants import (
            BusinessInvariantViolation,
        )
        from app.hoc.cus.hoc_spine.authority.invariant_evaluator import (
            InvariantMode,
            evaluate_invariants,
        )

        # incident.transition MEDIUM failure
        context = {
            "operation": "incident.transition",
            "current_status": "RESOLVED",
            "target_status": "ACTIVE",
        }

        with pytest.raises(BusinessInvariantViolation):
            evaluate_invariants("incident.transition", context, InvariantMode.STRICT)

    def test_strict_mode_passes_when_all_pass(self):
        """STRICT mode returns normally when all invariants pass."""
        from app.hoc.cus.hoc_spine.authority.invariant_evaluator import (
            InvariantMode,
            evaluate_invariants,
        )

        # project.create with valid tenant → should pass
        context = {
            "operation": "project.create",
            "tenant_id": "t-valid",
            "tenant_status": "ACTIVE",
        }

        results = evaluate_invariants("project.create", context, InvariantMode.STRICT)
        assert isinstance(results, list)
        assert all(r.passed for r in results)

    def test_monitor_is_default_mode(self):
        """InvariantMode default in evaluate_invariants signature is MONITOR."""
        from app.hoc.cus.hoc_spine.authority.invariant_evaluator import (
            evaluate_invariants,
        )
        import inspect

        sig = inspect.signature(evaluate_invariants)
        mode_param = sig.parameters["mode"]
        assert "MONITOR" in str(mode_param.default)


# =============================================================================
# Integration tests: OperationRegistry mode wiring
# =============================================================================


class TestRegistryInvariantModeWiring:
    """Prove OperationRegistry honors configured invariant mode."""

    @pytest.fixture
    def registry_with_handler(self):
        """Create a fresh OperationRegistry with a mock handler."""
        from app.hoc.cus.hoc_spine.orchestrator.operation_registry import (
            OperationRegistry,
            OperationContext,
            OperationResult,
        )

        registry = OperationRegistry()

        handler = MagicMock()
        handler.execute = AsyncMock(return_value=OperationResult.ok({"key": "value"}))
        registry.register("project.create", handler)

        return registry, handler

    def test_default_mode_is_monitor(self, registry_with_handler):
        """Registry defaults to MONITOR mode (None → resolved as MONITOR)."""
        registry, _ = registry_with_handler
        assert registry._invariant_mode is None  # None = defaults to MONITOR

    def test_set_invariant_mode_stores_mode(self, registry_with_handler):
        """set_invariant_mode() stores the mode on the registry."""
        from app.hoc.cus.hoc_spine.authority.invariant_evaluator import InvariantMode

        registry, _ = registry_with_handler
        registry.set_invariant_mode(InvariantMode.ENFORCE)
        assert registry._invariant_mode is InvariantMode.ENFORCE

    @pytest.mark.asyncio
    async def test_monitor_mode_does_not_block_dispatch(self, registry_with_handler):
        """In MONITOR mode, dispatch succeeds even with invariant failures."""
        from app.hoc.cus.hoc_spine.authority.invariant_evaluator import InvariantMode
        from app.hoc.cus.hoc_spine.orchestrator.operation_registry import (
            OperationContext,
        )

        registry, handler = registry_with_handler
        registry.set_invariant_mode(InvariantMode.MONITOR)

        # Missing tenant_id → BI-TENANT-001 CRITICAL failure, but MONITOR won't block
        ctx = OperationContext(session=None, tenant_id="", params={})
        result = await registry.execute("project.create", ctx)
        assert result.success is True
        assert handler.execute.called

    @pytest.mark.asyncio
    async def test_enforce_mode_blocks_critical_violation(self, registry_with_handler):
        """In ENFORCE mode, CRITICAL invariant failure blocks dispatch."""
        from app.hoc.cus.hoc_spine.authority.business_invariants import (
            BusinessInvariantViolation,
        )
        from app.hoc.cus.hoc_spine.authority.invariant_evaluator import InvariantMode
        from app.hoc.cus.hoc_spine.orchestrator.operation_registry import (
            OperationContext,
        )

        registry, handler = registry_with_handler
        registry.set_invariant_mode(InvariantMode.ENFORCE)

        # Missing tenant_id → BI-TENANT-001 CRITICAL failure
        ctx = OperationContext(session=None, tenant_id="", params={})

        with pytest.raises(BusinessInvariantViolation):
            await registry.execute("project.create", ctx)

    @pytest.mark.asyncio
    async def test_strict_mode_blocks_any_violation(self, registry_with_handler):
        """In STRICT mode, any invariant failure blocks dispatch."""
        from app.hoc.cus.hoc_spine.authority.business_invariants import (
            BusinessInvariantViolation,
        )
        from app.hoc.cus.hoc_spine.authority.invariant_evaluator import InvariantMode
        from app.hoc.cus.hoc_spine.orchestrator.operation_registry import (
            OperationContext,
        )

        registry, handler = registry_with_handler

        # Register a handler for incident.transition
        handler2 = MagicMock()
        from app.hoc.cus.hoc_spine.orchestrator.operation_registry import OperationResult
        handler2.execute = AsyncMock(return_value=OperationResult.ok({}))
        registry.register("incident.transition", handler2)

        registry.set_invariant_mode(InvariantMode.STRICT)

        # RESOLVED→ACTIVE → BI-INCIDENT-001 MEDIUM failure → STRICT blocks
        ctx = OperationContext(
            session=None,
            tenant_id="t-test",
            params={"current_status": "RESOLVED", "target_status": "ACTIVE"},
        )

        with pytest.raises(BusinessInvariantViolation):
            await registry.execute("incident.transition", ctx)
