# Layer: TEST
# AUDIENCE: INTERNAL
# Role: POL-DELTA-02/03 — Policies domain runtime correctness proofs
# artifact_class: TEST

"""
Policies Domain Runtime Correctness Tests (POL-DELTA-02, POL-DELTA-03)

Proves that:
  1. BI-POLICY-001 (policy.activate) is fail-closed on missing/malformed schema
  2. BI-POLICY-002 (policy.deactivate) blocks tenant callers on system policies
  3. Real OperationRegistry dispatch for policy.activate honors invariant mode
  4. Real OperationRegistry dispatch for policy.deactivate honors invariant mode
  5. MONITOR mode logs but does not block policy operations
  6. ENFORCE/STRICT modes block on invariant violations
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest


# =============================================================================
# POL-DELTA-02: Contract tests — invariant fail-closed behavior
# =============================================================================


class TestPolicyInvariantContracts:
    """Prove BI-POLICY-001 and BI-POLICY-002 are fail-closed."""

    def test_bi_policy_001_rejects_missing_schema(self):
        """BI-POLICY-001: policy.activate with no schema → FAIL."""
        from app.hoc.cus.hoc_spine.authority.business_invariants import (
            check_all_for_operation,
        )

        results = check_all_for_operation(
            "policy.activate", {"operation": "policy.activate"}
        )
        assert len(results) >= 1
        inv_id, passed, message = results[0]
        assert inv_id == "BI-POLICY-001"
        assert passed is False
        assert "policy_schema" in message

    def test_bi_policy_001_rejects_empty_schema(self):
        """BI-POLICY-001: policy.activate with empty schema → FAIL."""
        from app.hoc.cus.hoc_spine.authority.business_invariants import (
            check_all_for_operation,
        )

        results = check_all_for_operation(
            "policy.activate",
            {"operation": "policy.activate", "policy_schema": ""},
        )
        assert len(results) >= 1
        _, passed, _ = results[0]
        assert passed is False

    def test_bi_policy_001_rejects_non_str_non_dict_schema(self):
        """BI-POLICY-001: policy.activate with int schema → FAIL."""
        from app.hoc.cus.hoc_spine.authority.business_invariants import (
            check_all_for_operation,
        )

        results = check_all_for_operation(
            "policy.activate",
            {"operation": "policy.activate", "policy_schema": 42},
        )
        assert len(results) >= 1
        _, passed, message = results[0]
        assert passed is False
        assert "int" in message

    def test_bi_policy_001_accepts_valid_dict_schema(self):
        """BI-POLICY-001: policy.activate with valid dict schema → PASS."""
        from app.hoc.cus.hoc_spine.authority.business_invariants import (
            check_all_for_operation,
        )

        results = check_all_for_operation(
            "policy.activate",
            {"operation": "policy.activate", "policy_schema": {"rules": []}},
        )
        assert len(results) >= 1
        _, passed, _ = results[0]
        assert passed is True

    def test_bi_policy_001_accepts_valid_str_schema(self):
        """BI-POLICY-001: policy.activate with valid string schema → PASS."""
        from app.hoc.cus.hoc_spine.authority.business_invariants import (
            check_all_for_operation,
        )

        results = check_all_for_operation(
            "policy.activate",
            {"operation": "policy.activate", "policy_schema": '{"rules":[]}'},
        )
        assert len(results) >= 1
        _, passed, _ = results[0]
        assert passed is True

    def test_bi_policy_002_blocks_tenant_on_system_policy(self):
        """BI-POLICY-002: tenant caller deactivating system policy → FAIL."""
        from app.hoc.cus.hoc_spine.authority.business_invariants import (
            check_all_for_operation,
        )

        results = check_all_for_operation(
            "policy.deactivate",
            {
                "operation": "policy.deactivate",
                "is_system_policy": True,
                "actor_type": "user",
            },
        )
        assert len(results) >= 1
        inv_id, passed, message = results[0]
        assert inv_id == "BI-POLICY-002"
        assert passed is False
        assert "system policy" in message

    def test_bi_policy_002_allows_founder_on_system_policy(self):
        """BI-POLICY-002: founder caller deactivating system policy → PASS."""
        from app.hoc.cus.hoc_spine.authority.business_invariants import (
            check_all_for_operation,
        )

        results = check_all_for_operation(
            "policy.deactivate",
            {
                "operation": "policy.deactivate",
                "is_system_policy": True,
                "actor_type": "founder",
            },
        )
        assert len(results) >= 1
        _, passed, _ = results[0]
        assert passed is True

    def test_bi_policy_002_allows_tenant_on_non_system_policy(self):
        """BI-POLICY-002: tenant caller deactivating tenant policy → PASS."""
        from app.hoc.cus.hoc_spine.authority.business_invariants import (
            check_all_for_operation,
        )

        results = check_all_for_operation(
            "policy.deactivate",
            {
                "operation": "policy.deactivate",
                "is_system_policy": False,
                "actor_type": "user",
            },
        )
        assert len(results) >= 1
        _, passed, _ = results[0]
        assert passed is True

    def test_bi_policy_002_default_actor_is_user(self):
        """BI-POLICY-002: missing actor_type defaults to 'user' → blocks system."""
        from app.hoc.cus.hoc_spine.authority.business_invariants import (
            check_all_for_operation,
        )

        results = check_all_for_operation(
            "policy.deactivate",
            {
                "operation": "policy.deactivate",
                "is_system_policy": True,
                # No actor_type → defaults to "user"
            },
        )
        assert len(results) >= 1
        _, passed, _ = results[0]
        assert passed is False

    def test_bi_policy_001_in_strict_mode_raises(self):
        """BI-POLICY-001 (HIGH severity) in STRICT mode → BusinessInvariantViolation."""
        from app.hoc.cus.hoc_spine.authority.business_invariants import (
            BusinessInvariantViolation,
        )
        from app.hoc.cus.hoc_spine.authority.invariant_evaluator import (
            InvariantMode,
            evaluate_invariants,
        )

        with pytest.raises(BusinessInvariantViolation) as exc_info:
            evaluate_invariants(
                "policy.activate",
                {"operation": "policy.activate"},
                InvariantMode.STRICT,
            )
        assert "BI-POLICY-001" in exc_info.value.invariant_id

    def test_bi_policy_002_in_strict_mode_raises(self):
        """BI-POLICY-002 (HIGH severity) in STRICT mode → BusinessInvariantViolation."""
        from app.hoc.cus.hoc_spine.authority.business_invariants import (
            BusinessInvariantViolation,
        )
        from app.hoc.cus.hoc_spine.authority.invariant_evaluator import (
            InvariantMode,
            evaluate_invariants,
        )

        with pytest.raises(BusinessInvariantViolation) as exc_info:
            evaluate_invariants(
                "policy.deactivate",
                {
                    "operation": "policy.deactivate",
                    "is_system_policy": True,
                    "actor_type": "user",
                },
                InvariantMode.STRICT,
            )
        assert "BI-POLICY-002" in exc_info.value.invariant_id


# =============================================================================
# POL-DELTA-03: In-process execution assertions via real OperationRegistry
# =============================================================================


class TestPolicyRegistryDispatch:
    """Prove policy operations dispatch through real OperationRegistry."""

    @pytest.fixture
    def registry_with_policy_handlers(self):
        """Create a fresh OperationRegistry with mock policy handlers."""
        from app.hoc.cus.hoc_spine.orchestrator.operation_registry import (
            OperationContext,
            OperationRegistry,
            OperationResult,
        )

        registry = OperationRegistry()

        activate_handler = MagicMock()
        activate_handler.execute = AsyncMock(
            return_value=OperationResult.ok(
                {"policy_id": "p-001", "status": "active"}
            )
        )
        registry.register("policy.activate", activate_handler)

        deactivate_handler = MagicMock()
        deactivate_handler.execute = AsyncMock(
            return_value=OperationResult.ok(
                {"policy_id": "p-001", "status": "inactive"}
            )
        )
        registry.register("policy.deactivate", deactivate_handler)

        return registry, activate_handler, deactivate_handler

    @pytest.mark.asyncio
    async def test_policy_activate_dispatch_success(
        self, registry_with_policy_handlers
    ):
        """policy.activate dispatches and returns success with valid schema."""
        from app.hoc.cus.hoc_spine.orchestrator.operation_registry import (
            OperationContext,
        )

        registry, activate_handler, _ = registry_with_policy_handlers

        ctx = OperationContext(
            session=None,
            tenant_id="t-test",
            params={"policy_schema": {"rules": ["rule1"]}},
        )
        result = await registry.execute("policy.activate", ctx)
        assert result.success is True
        assert result.data["status"] == "active"
        assert activate_handler.execute.called

    @pytest.mark.asyncio
    async def test_policy_activate_monitor_mode_allows_bad_schema(
        self, registry_with_policy_handlers
    ):
        """In MONITOR mode, bad schema logs but doesn't block dispatch."""
        from app.hoc.cus.hoc_spine.authority.invariant_evaluator import InvariantMode
        from app.hoc.cus.hoc_spine.orchestrator.operation_registry import (
            OperationContext,
        )

        registry, activate_handler, _ = registry_with_policy_handlers
        registry.set_invariant_mode(InvariantMode.MONITOR)

        ctx = OperationContext(
            session=None,
            tenant_id="t-test",
            params={},  # No schema — BI-POLICY-001 fails
        )
        result = await registry.execute("policy.activate", ctx)
        assert result.success is True  # MONITOR doesn't block
        assert activate_handler.execute.called

    @pytest.mark.asyncio
    async def test_policy_activate_strict_blocks_bad_schema(
        self, registry_with_policy_handlers
    ):
        """In STRICT mode, missing schema triggers BI-POLICY-001 (HIGH) → blocked."""
        from app.hoc.cus.hoc_spine.authority.business_invariants import (
            BusinessInvariantViolation,
        )
        from app.hoc.cus.hoc_spine.authority.invariant_evaluator import InvariantMode
        from app.hoc.cus.hoc_spine.orchestrator.operation_registry import (
            OperationContext,
        )

        registry, activate_handler, _ = registry_with_policy_handlers
        registry.set_invariant_mode(InvariantMode.STRICT)

        ctx = OperationContext(
            session=None,
            tenant_id="t-test",
            params={},  # No schema
        )
        with pytest.raises(BusinessInvariantViolation):
            await registry.execute("policy.activate", ctx)

    @pytest.mark.asyncio
    async def test_policy_deactivate_dispatch_success(
        self, registry_with_policy_handlers
    ):
        """policy.deactivate dispatches successfully for tenant policy."""
        from app.hoc.cus.hoc_spine.orchestrator.operation_registry import (
            OperationContext,
        )

        registry, _, deactivate_handler = registry_with_policy_handlers

        ctx = OperationContext(
            session=None,
            tenant_id="t-test",
            params={"is_system_policy": False, "actor_type": "user"},
        )
        result = await registry.execute("policy.deactivate", ctx)
        assert result.success is True
        assert result.data["status"] == "inactive"
        assert deactivate_handler.execute.called

    @pytest.mark.asyncio
    async def test_policy_deactivate_strict_blocks_system_policy(
        self, registry_with_policy_handlers
    ):
        """In STRICT mode, tenant deactivating system policy (HIGH) → blocked."""
        from app.hoc.cus.hoc_spine.authority.business_invariants import (
            BusinessInvariantViolation,
        )
        from app.hoc.cus.hoc_spine.authority.invariant_evaluator import InvariantMode
        from app.hoc.cus.hoc_spine.orchestrator.operation_registry import (
            OperationContext,
        )

        registry, _, _ = registry_with_policy_handlers
        registry.set_invariant_mode(InvariantMode.STRICT)

        ctx = OperationContext(
            session=None,
            tenant_id="t-test",
            params={"is_system_policy": True, "actor_type": "user"},
        )
        with pytest.raises(BusinessInvariantViolation):
            await registry.execute("policy.deactivate", ctx)

    @pytest.mark.asyncio
    async def test_policy_activate_idempotent_dispatch(
        self, registry_with_policy_handlers
    ):
        """Dispatching policy.activate twice with same context is idempotent."""
        from app.hoc.cus.hoc_spine.orchestrator.operation_registry import (
            OperationContext,
        )

        registry, activate_handler, _ = registry_with_policy_handlers

        ctx = OperationContext(
            session=None,
            tenant_id="t-test",
            params={"policy_schema": {"rules": []}},
        )
        r1 = await registry.execute("policy.activate", ctx)
        r2 = await registry.execute("policy.activate", ctx)
        assert r1.success == r2.success
        assert r1.data == r2.data
        assert activate_handler.execute.call_count == 2

    @pytest.mark.asyncio
    async def test_policy_dispatch_result_contains_operation(
        self, registry_with_policy_handlers
    ):
        """Result from policy dispatch carries the operation name."""
        from app.hoc.cus.hoc_spine.orchestrator.operation_registry import (
            OperationContext,
        )

        registry, _, _ = registry_with_policy_handlers

        ctx = OperationContext(
            session=None,
            tenant_id="t-test",
            params={"policy_schema": {"rules": []}},
        )
        result = await registry.execute("policy.activate", ctx)
        assert result.operation == "policy.activate"
