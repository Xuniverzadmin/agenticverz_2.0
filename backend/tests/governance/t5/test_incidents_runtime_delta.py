# Layer: TEST
# AUDIENCE: INTERNAL
# Role: INC-DELTA-02/03 — Incidents domain runtime correctness proofs
# artifact_class: TEST


"""
Incidents Domain Runtime Correctness Tests (INC-DELTA-02, INC-DELTA-03)

Proves that:
  1. BI-INCIDENT-001 (incident.transition) is fail-closed on RESOLVED→ACTIVE
  2. BI-INCIDENT-002 (incident.create) is fail-closed on missing tenant/severity
  3. BI-INCIDENT-003 (incident.resolve) blocks on non-existent or already-resolved
  4. Real OperationRegistry dispatch for incident operations honors invariant mode
  5. MONITOR mode logs but does not block incident operations
  6. STRICT mode blocks on invariant violations
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest


# =============================================================================
# INC-DELTA-02: Contract tests — invariant fail-closed behavior
# =============================================================================


class TestIncidentInvariantContracts:
    """Prove BI-INCIDENT-001, BI-INCIDENT-002, BI-INCIDENT-003 are fail-closed."""

    # --- BI-INCIDENT-001 (transition) ---

    def test_bi_incident_001_blocks_resolved_to_active(self):
        """BI-INCIDENT-001: RESOLVED→ACTIVE transition → FAIL."""
        from app.hoc.cus.hoc_spine.authority.business_invariants import (
            check_all_for_operation,
        )

        results = check_all_for_operation(
            "incident.transition",
            {
                "operation": "incident.transition",
                "current_status": "RESOLVED",
                "target_status": "ACTIVE",
            },
        )
        assert len(results) >= 1
        inv_id, passed, message = results[0]
        assert inv_id == "BI-INCIDENT-001"
        assert passed is False
        assert "reopen" in message

    def test_bi_incident_001_allows_valid_transition(self):
        """BI-INCIDENT-001: OPEN→INVESTIGATING transition → PASS."""
        from app.hoc.cus.hoc_spine.authority.business_invariants import (
            check_all_for_operation,
        )

        results = check_all_for_operation(
            "incident.transition",
            {
                "operation": "incident.transition",
                "current_status": "OPEN",
                "target_status": "INVESTIGATING",
            },
        )
        assert len(results) >= 1
        _, passed, _ = results[0]
        assert passed is True

    # --- BI-INCIDENT-002 (create) ---

    def test_bi_incident_002_rejects_missing_tenant_id(self):
        """BI-INCIDENT-002: incident.create with no tenant_id → FAIL."""
        from app.hoc.cus.hoc_spine.authority.business_invariants import (
            check_all_for_operation,
        )

        results = check_all_for_operation(
            "incident.create",
            {"operation": "incident.create", "severity": "HIGH"},
        )
        assert len(results) >= 1
        inv_id, passed, message = results[0]
        assert inv_id == "BI-INCIDENT-002"
        assert passed is False
        assert "tenant_id" in message

    def test_bi_incident_002_rejects_missing_severity(self):
        """BI-INCIDENT-002: incident.create with no severity → FAIL."""
        from app.hoc.cus.hoc_spine.authority.business_invariants import (
            check_all_for_operation,
        )

        results = check_all_for_operation(
            "incident.create",
            {"operation": "incident.create", "tenant_id": "t-test"},
        )
        assert len(results) >= 1
        _, passed, message = results[0]
        assert passed is False
        assert "severity" in message

    def test_bi_incident_002_rejects_invalid_severity(self):
        """BI-INCIDENT-002: incident.create with invalid severity → FAIL."""
        from app.hoc.cus.hoc_spine.authority.business_invariants import (
            check_all_for_operation,
        )

        results = check_all_for_operation(
            "incident.create",
            {
                "operation": "incident.create",
                "tenant_id": "t-test",
                "severity": "EXTREME",
            },
        )
        assert len(results) >= 1
        _, passed, message = results[0]
        assert passed is False
        assert "EXTREME" in message

    def test_bi_incident_002_accepts_valid_create(self):
        """BI-INCIDENT-002: incident.create with valid fields → PASS."""
        from app.hoc.cus.hoc_spine.authority.business_invariants import (
            check_all_for_operation,
        )

        results = check_all_for_operation(
            "incident.create",
            {
                "operation": "incident.create",
                "tenant_id": "t-test",
                "severity": "HIGH",
            },
        )
        assert len(results) >= 1
        _, passed, _ = results[0]
        assert passed is True

    # --- BI-INCIDENT-003 (resolve) ---

    def test_bi_incident_003_blocks_non_existent_incident(self):
        """BI-INCIDENT-003: incident.resolve on non-existent → FAIL."""
        from app.hoc.cus.hoc_spine.authority.business_invariants import (
            check_all_for_operation,
        )

        results = check_all_for_operation(
            "incident.resolve",
            {
                "operation": "incident.resolve",
                "incident_exists": False,
                "current_status": "OPEN",
            },
        )
        assert len(results) >= 1
        inv_id, passed, message = results[0]
        assert inv_id == "BI-INCIDENT-003"
        assert passed is False
        assert "does not exist" in message

    def test_bi_incident_003_blocks_already_resolved(self):
        """BI-INCIDENT-003: incident.resolve on already-resolved → FAIL."""
        from app.hoc.cus.hoc_spine.authority.business_invariants import (
            check_all_for_operation,
        )

        results = check_all_for_operation(
            "incident.resolve",
            {
                "operation": "incident.resolve",
                "incident_exists": True,
                "current_status": "RESOLVED",
            },
        )
        assert len(results) >= 1
        _, passed, message = results[0]
        assert passed is False
        assert "already resolved" in message

    def test_bi_incident_003_allows_valid_resolve(self):
        """BI-INCIDENT-003: incident.resolve on OPEN incident → PASS."""
        from app.hoc.cus.hoc_spine.authority.business_invariants import (
            check_all_for_operation,
        )

        results = check_all_for_operation(
            "incident.resolve",
            {
                "operation": "incident.resolve",
                "incident_exists": True,
                "current_status": "INVESTIGATING",
            },
        )
        assert len(results) >= 1
        _, passed, _ = results[0]
        assert passed is True

    # --- STRICT mode escalation ---

    def test_bi_incident_002_in_strict_mode_raises(self):
        """BI-INCIDENT-002 (HIGH severity) in STRICT mode → BusinessInvariantViolation."""
        from app.hoc.cus.hoc_spine.authority.business_invariants import (
            BusinessInvariantViolation,
        )
        from app.hoc.cus.hoc_spine.authority.invariant_evaluator import (
            InvariantMode,
            evaluate_invariants,
        )

        with pytest.raises(BusinessInvariantViolation) as exc_info:
            evaluate_invariants(
                "incident.create",
                {"operation": "incident.create"},
                InvariantMode.STRICT,
            )
        assert "BI-INCIDENT-002" in exc_info.value.invariant_id

    def test_bi_incident_003_in_strict_mode_raises(self):
        """BI-INCIDENT-003 (HIGH severity) in STRICT mode → BusinessInvariantViolation."""
        from app.hoc.cus.hoc_spine.authority.business_invariants import (
            BusinessInvariantViolation,
        )
        from app.hoc.cus.hoc_spine.authority.invariant_evaluator import (
            InvariantMode,
            evaluate_invariants,
        )

        with pytest.raises(BusinessInvariantViolation) as exc_info:
            evaluate_invariants(
                "incident.resolve",
                {
                    "operation": "incident.resolve",
                    "incident_exists": True,
                    "current_status": "RESOLVED",
                },
                InvariantMode.STRICT,
            )
        assert "BI-INCIDENT-003" in exc_info.value.invariant_id


# =============================================================================
# INC-DELTA-03: In-process execution assertions via real OperationRegistry
# =============================================================================


class TestIncidentRegistryDispatch:
    """Prove incident operations dispatch through real OperationRegistry."""

    @pytest.fixture
    def registry_with_incident_handlers(self):
        """Create a fresh OperationRegistry with mock incident handlers."""
        from app.hoc.cus.hoc_spine.orchestrator.operation_registry import (
            OperationContext,
            OperationRegistry,
            OperationResult,
        )

        registry = OperationRegistry()

        create_handler = MagicMock()
        create_handler.execute = AsyncMock(
            return_value=OperationResult.ok(
                {"incident_id": "inc-001", "status": "open", "severity": "HIGH"}
            )
        )
        registry.register("incident.create", create_handler)

        resolve_handler = MagicMock()
        resolve_handler.execute = AsyncMock(
            return_value=OperationResult.ok(
                {"incident_id": "inc-001", "status": "resolved"}
            )
        )
        registry.register("incident.resolve", resolve_handler)

        return registry, create_handler, resolve_handler

    @pytest.mark.asyncio
    async def test_incident_create_dispatch_success(
        self, registry_with_incident_handlers
    ):
        """incident.create dispatches and returns success with valid context."""
        from app.hoc.cus.hoc_spine.orchestrator.operation_registry import (
            OperationContext,
        )

        registry, create_handler, _ = registry_with_incident_handlers

        ctx = OperationContext(
            session=None,
            tenant_id="t-test",
            params={"tenant_id": "t-test", "severity": "HIGH"},
        )
        result = await registry.execute("incident.create", ctx)
        assert result.success is True
        assert result.data["status"] == "open"
        assert create_handler.execute.called

    @pytest.mark.asyncio
    async def test_incident_create_monitor_mode_allows_bad_context(
        self, registry_with_incident_handlers
    ):
        """In MONITOR mode, missing tenant_id logs but doesn't block dispatch."""
        from app.hoc.cus.hoc_spine.authority.invariant_evaluator import InvariantMode
        from app.hoc.cus.hoc_spine.orchestrator.operation_registry import (
            OperationContext,
        )

        registry, create_handler, _ = registry_with_incident_handlers
        registry.set_invariant_mode(InvariantMode.MONITOR)

        ctx = OperationContext(
            session=None,
            tenant_id="t-test",
            params={},  # No tenant_id/severity — BI-INCIDENT-002 fails
        )
        result = await registry.execute("incident.create", ctx)
        assert result.success is True  # MONITOR doesn't block
        assert create_handler.execute.called

    @pytest.mark.asyncio
    async def test_incident_create_strict_blocks_missing_fields(
        self, registry_with_incident_handlers
    ):
        """In STRICT mode, missing tenant_id triggers BI-INCIDENT-002 → blocked."""
        from app.hoc.cus.hoc_spine.authority.business_invariants import (
            BusinessInvariantViolation,
        )
        from app.hoc.cus.hoc_spine.authority.invariant_evaluator import InvariantMode
        from app.hoc.cus.hoc_spine.orchestrator.operation_registry import (
            OperationContext,
        )

        registry, _, _ = registry_with_incident_handlers
        registry.set_invariant_mode(InvariantMode.STRICT)

        ctx = OperationContext(
            session=None,
            tenant_id="t-test",
            params={},  # No tenant_id/severity
        )
        with pytest.raises(BusinessInvariantViolation):
            await registry.execute("incident.create", ctx)

    @pytest.mark.asyncio
    async def test_incident_resolve_dispatch_success(
        self, registry_with_incident_handlers
    ):
        """incident.resolve dispatches successfully for valid incident."""
        from app.hoc.cus.hoc_spine.orchestrator.operation_registry import (
            OperationContext,
        )

        registry, _, resolve_handler = registry_with_incident_handlers

        ctx = OperationContext(
            session=None,
            tenant_id="t-test",
            params={"incident_exists": True, "current_status": "INVESTIGATING"},
        )
        result = await registry.execute("incident.resolve", ctx)
        assert result.success is True
        assert result.data["status"] == "resolved"
        assert resolve_handler.execute.called

    @pytest.mark.asyncio
    async def test_incident_resolve_strict_blocks_already_resolved(
        self, registry_with_incident_handlers
    ):
        """In STRICT mode, resolving already-resolved incident → blocked."""
        from app.hoc.cus.hoc_spine.authority.business_invariants import (
            BusinessInvariantViolation,
        )
        from app.hoc.cus.hoc_spine.authority.invariant_evaluator import InvariantMode
        from app.hoc.cus.hoc_spine.orchestrator.operation_registry import (
            OperationContext,
        )

        registry, _, _ = registry_with_incident_handlers
        registry.set_invariant_mode(InvariantMode.STRICT)

        ctx = OperationContext(
            session=None,
            tenant_id="t-test",
            params={"incident_exists": True, "current_status": "RESOLVED"},
        )
        with pytest.raises(BusinessInvariantViolation):
            await registry.execute("incident.resolve", ctx)

    @pytest.mark.asyncio
    async def test_incident_create_idempotent_dispatch(
        self, registry_with_incident_handlers
    ):
        """Dispatching incident.create twice with same context is deterministic."""
        from app.hoc.cus.hoc_spine.orchestrator.operation_registry import (
            OperationContext,
        )

        registry, create_handler, _ = registry_with_incident_handlers

        ctx = OperationContext(
            session=None,
            tenant_id="t-test",
            params={"tenant_id": "t-test", "severity": "HIGH"},
        )
        r1 = await registry.execute("incident.create", ctx)
        r2 = await registry.execute("incident.create", ctx)
        assert r1.success == r2.success
        assert r1.data == r2.data
        assert create_handler.execute.call_count == 2

    @pytest.mark.asyncio
    async def test_incident_dispatch_result_contains_operation(
        self, registry_with_incident_handlers
    ):
        """Result from incident dispatch carries the operation name."""
        from app.hoc.cus.hoc_spine.orchestrator.operation_registry import (
            OperationContext,
        )

        registry, _, _ = registry_with_incident_handlers

        ctx = OperationContext(
            session=None,
            tenant_id="t-test",
            params={"tenant_id": "t-test", "severity": "HIGH"},
        )
        result = await registry.execute("incident.create", ctx)
        assert result.operation == "incident.create"
