# Layer: TEST
# AUDIENCE: INTERNAL
# Role: TEN-DELTA-02/03 — Tenant domain runtime correctness proofs
# artifact_class: TEST


"""
Tenant Domain Runtime Correctness Tests (TEN-DELTA-02, TEN-DELTA-03)

Proves that:
  1. BI-TENANT-001 (project.create) is fail-closed on non-ACTIVE tenant
  2. BI-TENANT-002 (tenant.create) is fail-closed on missing org_id/tenant_name
  3. BI-TENANT-003 (tenant.delete) blocks on non-existent or CREATING tenant
  4. Real OperationRegistry dispatch for tenant operations honors invariant mode
  5. MONITOR mode logs but does not block tenant operations
  6. STRICT mode blocks on invariant violations
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest


# =============================================================================
# TEN-DELTA-02: Contract tests — invariant fail-closed behavior
# =============================================================================


class TestTenantInvariantContracts:
    """Prove BI-TENANT-001, BI-TENANT-002, BI-TENANT-003 are fail-closed."""

    # --- BI-TENANT-001 (project.create anchor) ---

    def test_bi_tenant_001_blocks_non_active_tenant(self):
        """BI-TENANT-001: project.create with SUSPENDED tenant → FAIL."""
        from app.hoc.cus.hoc_spine.authority.business_invariants import (
            check_all_for_operation,
        )

        results = check_all_for_operation(
            "project.create",
            {
                "operation": "project.create",
                "tenant_id": "t-test",
                "tenant_status": "SUSPENDED",
            },
        )
        assert len(results) >= 1
        inv_id, passed, message = results[0]
        assert inv_id == "BI-TENANT-001"
        assert passed is False
        assert "ACTIVE" in message

    def test_bi_tenant_001_allows_active_tenant(self):
        """BI-TENANT-001: project.create with ACTIVE tenant → PASS."""
        from app.hoc.cus.hoc_spine.authority.business_invariants import (
            check_all_for_operation,
        )

        results = check_all_for_operation(
            "project.create",
            {
                "operation": "project.create",
                "tenant_id": "t-test",
                "tenant_status": "ACTIVE",
            },
        )
        assert len(results) >= 1
        _, passed, _ = results[0]
        assert passed is True

    # --- BI-TENANT-002 (tenant.create) ---

    def test_bi_tenant_002_rejects_missing_org_id(self):
        """BI-TENANT-002: tenant.create with no org_id → FAIL."""
        from app.hoc.cus.hoc_spine.authority.business_invariants import (
            check_all_for_operation,
        )

        results = check_all_for_operation(
            "tenant.create",
            {"operation": "tenant.create", "tenant_name": "Test Tenant"},
        )
        assert len(results) >= 1
        inv_id, passed, message = results[0]
        assert inv_id == "BI-TENANT-002"
        assert passed is False
        assert "org_id" in message

    def test_bi_tenant_002_rejects_missing_tenant_name(self):
        """BI-TENANT-002: tenant.create with no tenant_name → FAIL."""
        from app.hoc.cus.hoc_spine.authority.business_invariants import (
            check_all_for_operation,
        )

        results = check_all_for_operation(
            "tenant.create",
            {"operation": "tenant.create", "org_id": "org-001"},
        )
        assert len(results) >= 1
        _, passed, message = results[0]
        assert passed is False
        assert "tenant_name" in message

    def test_bi_tenant_002_rejects_empty_tenant_name(self):
        """BI-TENANT-002: tenant.create with whitespace-only tenant_name → FAIL."""
        from app.hoc.cus.hoc_spine.authority.business_invariants import (
            check_all_for_operation,
        )

        results = check_all_for_operation(
            "tenant.create",
            {
                "operation": "tenant.create",
                "org_id": "org-001",
                "tenant_name": "   ",
            },
        )
        assert len(results) >= 1
        _, passed, message = results[0]
        assert passed is False
        assert "tenant_name" in message

    def test_bi_tenant_002_accepts_valid_create(self):
        """BI-TENANT-002: tenant.create with valid fields → PASS."""
        from app.hoc.cus.hoc_spine.authority.business_invariants import (
            check_all_for_operation,
        )

        results = check_all_for_operation(
            "tenant.create",
            {
                "operation": "tenant.create",
                "org_id": "org-001",
                "tenant_name": "Test Tenant",
            },
        )
        assert len(results) >= 1
        _, passed, _ = results[0]
        assert passed is True

    # --- BI-TENANT-003 (tenant.delete) ---

    def test_bi_tenant_003_blocks_non_existent_tenant(self):
        """BI-TENANT-003: tenant.delete on non-existent tenant → FAIL."""
        from app.hoc.cus.hoc_spine.authority.business_invariants import (
            check_all_for_operation,
        )

        results = check_all_for_operation(
            "tenant.delete",
            {
                "operation": "tenant.delete",
                "tenant_exists": False,
                "tenant_status": "ACTIVE",
            },
        )
        assert len(results) >= 1
        inv_id, passed, message = results[0]
        assert inv_id == "BI-TENANT-003"
        assert passed is False
        assert "does not exist" in message

    def test_bi_tenant_003_blocks_creating_tenant(self):
        """BI-TENANT-003: tenant.delete on CREATING tenant → FAIL."""
        from app.hoc.cus.hoc_spine.authority.business_invariants import (
            check_all_for_operation,
        )

        results = check_all_for_operation(
            "tenant.delete",
            {
                "operation": "tenant.delete",
                "tenant_exists": True,
                "tenant_status": "CREATING",
            },
        )
        assert len(results) >= 1
        _, passed, message = results[0]
        assert passed is False
        assert "CREATING" in message

    def test_bi_tenant_003_allows_valid_delete(self):
        """BI-TENANT-003: tenant.delete on ACTIVE tenant → PASS."""
        from app.hoc.cus.hoc_spine.authority.business_invariants import (
            check_all_for_operation,
        )

        results = check_all_for_operation(
            "tenant.delete",
            {
                "operation": "tenant.delete",
                "tenant_exists": True,
                "tenant_status": "ACTIVE",
            },
        )
        assert len(results) >= 1
        _, passed, _ = results[0]
        assert passed is True

    # --- STRICT mode escalation ---

    def test_bi_tenant_002_in_strict_mode_raises(self):
        """BI-TENANT-002 (HIGH severity) in STRICT mode → BusinessInvariantViolation."""
        from app.hoc.cus.hoc_spine.authority.business_invariants import (
            BusinessInvariantViolation,
        )
        from app.hoc.cus.hoc_spine.authority.invariant_evaluator import (
            InvariantMode,
            evaluate_invariants,
        )

        with pytest.raises(BusinessInvariantViolation) as exc_info:
            evaluate_invariants(
                "tenant.create",
                {"operation": "tenant.create"},
                InvariantMode.STRICT,
            )
        assert "BI-TENANT-002" in exc_info.value.invariant_id

    def test_bi_tenant_003_in_strict_mode_raises(self):
        """BI-TENANT-003 (HIGH severity) in STRICT mode → BusinessInvariantViolation."""
        from app.hoc.cus.hoc_spine.authority.business_invariants import (
            BusinessInvariantViolation,
        )
        from app.hoc.cus.hoc_spine.authority.invariant_evaluator import (
            InvariantMode,
            evaluate_invariants,
        )

        with pytest.raises(BusinessInvariantViolation) as exc_info:
            evaluate_invariants(
                "tenant.delete",
                {
                    "operation": "tenant.delete",
                    "tenant_exists": False,
                    "tenant_status": "ACTIVE",
                },
                InvariantMode.STRICT,
            )
        assert "BI-TENANT-003" in exc_info.value.invariant_id


# =============================================================================
# TEN-DELTA-03: In-process execution assertions via real OperationRegistry
# =============================================================================


class TestTenantRegistryDispatch:
    """Prove tenant operations dispatch through real OperationRegistry."""

    @pytest.fixture
    def registry_with_tenant_handlers(self):
        """Create a fresh OperationRegistry with mock tenant handlers."""
        from app.hoc.cus.hoc_spine.orchestrator.operation_registry import (
            OperationContext,
            OperationRegistry,
            OperationResult,
        )

        registry = OperationRegistry()

        create_handler = MagicMock()
        create_handler.execute = AsyncMock(
            return_value=OperationResult.ok(
                {"tenant_id": "t-new-001", "status": "CREATING", "org_id": "org-001"}
            )
        )
        registry.register("tenant.create", create_handler)

        delete_handler = MagicMock()
        delete_handler.execute = AsyncMock(
            return_value=OperationResult.ok(
                {"tenant_id": "t-del-001", "status": "DELETED"}
            )
        )
        registry.register("tenant.delete", delete_handler)

        project_handler = MagicMock()
        project_handler.execute = AsyncMock(
            return_value=OperationResult.ok(
                {"project_id": "p-001", "tenant_id": "t-test"}
            )
        )
        registry.register("project.create", project_handler)

        return registry, create_handler, delete_handler, project_handler

    @pytest.mark.asyncio
    async def test_tenant_create_dispatch_success(
        self, registry_with_tenant_handlers
    ):
        """tenant.create dispatches and returns success with valid context."""
        from app.hoc.cus.hoc_spine.orchestrator.operation_registry import (
            OperationContext,
        )

        registry, create_handler, _, _ = registry_with_tenant_handlers

        ctx = OperationContext(
            session=None,
            tenant_id="t-test",
            params={"org_id": "org-001", "tenant_name": "Test Tenant"},
        )
        result = await registry.execute("tenant.create", ctx)
        assert result.success is True
        assert result.data["status"] == "CREATING"
        assert create_handler.execute.called

    @pytest.mark.asyncio
    async def test_tenant_create_monitor_mode_allows_bad_context(
        self, registry_with_tenant_handlers
    ):
        """In MONITOR mode, missing org_id logs but doesn't block dispatch."""
        from app.hoc.cus.hoc_spine.authority.invariant_evaluator import InvariantMode
        from app.hoc.cus.hoc_spine.orchestrator.operation_registry import (
            OperationContext,
        )

        registry, create_handler, _, _ = registry_with_tenant_handlers
        registry.set_invariant_mode(InvariantMode.MONITOR)

        ctx = OperationContext(
            session=None,
            tenant_id="t-test",
            params={},  # No org_id/tenant_name — BI-TENANT-002 fails
        )
        result = await registry.execute("tenant.create", ctx)
        assert result.success is True  # MONITOR doesn't block
        assert create_handler.execute.called

    @pytest.mark.asyncio
    async def test_tenant_create_strict_blocks_missing_fields(
        self, registry_with_tenant_handlers
    ):
        """In STRICT mode, missing org_id triggers BI-TENANT-002 → blocked."""
        from app.hoc.cus.hoc_spine.authority.business_invariants import (
            BusinessInvariantViolation,
        )
        from app.hoc.cus.hoc_spine.authority.invariant_evaluator import InvariantMode
        from app.hoc.cus.hoc_spine.orchestrator.operation_registry import (
            OperationContext,
        )

        registry, _, _, _ = registry_with_tenant_handlers
        registry.set_invariant_mode(InvariantMode.STRICT)

        ctx = OperationContext(
            session=None,
            tenant_id="t-test",
            params={},  # No org_id/tenant_name
        )
        with pytest.raises(BusinessInvariantViolation):
            await registry.execute("tenant.create", ctx)

    @pytest.mark.asyncio
    async def test_tenant_delete_dispatch_success(
        self, registry_with_tenant_handlers
    ):
        """tenant.delete dispatches successfully for valid tenant."""
        from app.hoc.cus.hoc_spine.orchestrator.operation_registry import (
            OperationContext,
        )

        registry, _, delete_handler, _ = registry_with_tenant_handlers

        ctx = OperationContext(
            session=None,
            tenant_id="t-test",
            params={"tenant_exists": True, "tenant_status": "ACTIVE"},
        )
        result = await registry.execute("tenant.delete", ctx)
        assert result.success is True
        assert result.data["status"] == "DELETED"
        assert delete_handler.execute.called

    @pytest.mark.asyncio
    async def test_tenant_delete_strict_blocks_non_existent(
        self, registry_with_tenant_handlers
    ):
        """In STRICT mode, deleting non-existent tenant → blocked."""
        from app.hoc.cus.hoc_spine.authority.business_invariants import (
            BusinessInvariantViolation,
        )
        from app.hoc.cus.hoc_spine.authority.invariant_evaluator import InvariantMode
        from app.hoc.cus.hoc_spine.orchestrator.operation_registry import (
            OperationContext,
        )

        registry, _, _, _ = registry_with_tenant_handlers
        registry.set_invariant_mode(InvariantMode.STRICT)

        ctx = OperationContext(
            session=None,
            tenant_id="t-test",
            params={"tenant_exists": False, "tenant_status": "ACTIVE"},
        )
        with pytest.raises(BusinessInvariantViolation):
            await registry.execute("tenant.delete", ctx)

    @pytest.mark.asyncio
    async def test_project_create_dispatch_success(
        self, registry_with_tenant_handlers
    ):
        """project.create dispatches successfully with ACTIVE tenant."""
        from app.hoc.cus.hoc_spine.orchestrator.operation_registry import (
            OperationContext,
        )

        registry, _, _, project_handler = registry_with_tenant_handlers

        ctx = OperationContext(
            session=None,
            tenant_id="t-test",
            params={"tenant_id": "t-test", "tenant_status": "ACTIVE"},
        )
        result = await registry.execute("project.create", ctx)
        assert result.success is True
        assert result.data["project_id"] == "p-001"
        assert project_handler.execute.called

    @pytest.mark.asyncio
    async def test_tenant_create_idempotent_dispatch(
        self, registry_with_tenant_handlers
    ):
        """Dispatching tenant.create twice with same context is deterministic."""
        from app.hoc.cus.hoc_spine.orchestrator.operation_registry import (
            OperationContext,
        )

        registry, create_handler, _, _ = registry_with_tenant_handlers

        ctx = OperationContext(
            session=None,
            tenant_id="t-test",
            params={"org_id": "org-001", "tenant_name": "Test Tenant"},
        )
        r1 = await registry.execute("tenant.create", ctx)
        r2 = await registry.execute("tenant.create", ctx)
        assert r1.success == r2.success
        assert r1.data == r2.data
        assert create_handler.execute.call_count == 2

    @pytest.mark.asyncio
    async def test_tenant_dispatch_result_contains_operation(
        self, registry_with_tenant_handlers
    ):
        """Result from tenant dispatch carries the operation name."""
        from app.hoc.cus.hoc_spine.orchestrator.operation_registry import (
            OperationContext,
        )

        registry, _, _, _ = registry_with_tenant_handlers

        ctx = OperationContext(
            session=None,
            tenant_id="t-test",
            params={"org_id": "org-001", "tenant_name": "Test Tenant"},
        )
        result = await registry.execute("tenant.create", ctx)
        assert result.operation == "tenant.create"
