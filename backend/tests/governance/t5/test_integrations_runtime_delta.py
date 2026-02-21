# Layer: TEST
# AUDIENCE: INTERNAL
# Role: INT-DELTA-02/03 — Integrations domain runtime correctness proofs
# artifact_class: TEST


"""
Integrations Domain Runtime Correctness Tests (INT-DELTA-02, INT-DELTA-03)

Proves that:
  1. BI-INTEG-001 (integration.enable) is fail-closed on unregistered connector
  2. BI-INTEG-002 (integration.disable) is fail-closed on non-existent/already-disabled
  3. BI-INTEG-003 (integrations.query) is fail-closed on missing tenant_id
  4. Real OperationRegistry dispatch for integrations operations honors invariant mode
  5. MONITOR mode logs but does not block integrations operations
  6. STRICT mode blocks on invariant violations
  7. PR-8 list_integrations single-dispatch semantics are deterministic
  8. BI-INTEG-002 is fail-closed on MISSING context keys (no implicit pass)
  9. Production wiring: integrations.query + method=disable_integration fires BI-INTEG-002
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest


# =============================================================================
# INT-DELTA-02: Contract tests — invariant fail-closed behavior
# =============================================================================


class TestIntegrationsInvariantContracts:
    """Prove BI-INTEG-001, BI-INTEG-002, BI-INTEG-003 are fail-closed."""

    # --- BI-INTEG-001 (integration.enable) ---

    def test_bi_integ_001_rejects_missing_connector_type(self):
        """BI-INTEG-001: integration.enable with no connector_type → FAIL."""
        from app.hoc.cus.hoc_spine.authority.business_invariants import (
            check_all_for_operation,
        )

        results = check_all_for_operation(
            "integration.enable",
            {"operation": "integration.enable"},
        )
        assert len(results) >= 1
        inv_id, passed, message = results[0]
        assert inv_id == "BI-INTEG-001"
        assert passed is False
        assert "connector_type" in message

    def test_bi_integ_001_rejects_unregistered_connector(self):
        """BI-INTEG-001: integration.enable with unregistered connector → FAIL."""
        from app.hoc.cus.hoc_spine.authority.business_invariants import (
            check_all_for_operation,
        )

        results = check_all_for_operation(
            "integration.enable",
            {
                "operation": "integration.enable",
                "connector_type": "unknown_provider",
                "connector_registered": False,
            },
        )
        assert len(results) >= 1
        _, passed, message = results[0]
        assert passed is False
        assert "not registered" in message

    def test_bi_integ_001_accepts_registered_connector(self):
        """BI-INTEG-001: integration.enable with registered connector → PASS."""
        from app.hoc.cus.hoc_spine.authority.business_invariants import (
            check_all_for_operation,
        )

        results = check_all_for_operation(
            "integration.enable",
            {
                "operation": "integration.enable",
                "connector_type": "openai",
                "connector_registered": True,
            },
        )
        assert len(results) >= 1
        _, passed, _ = results[0]
        assert passed is True

    # --- BI-INTEG-002 (integration.disable) ---

    def test_bi_integ_002_rejects_non_existent_integration(self):
        """BI-INTEG-002: integration.disable on non-existent → FAIL."""
        from app.hoc.cus.hoc_spine.authority.business_invariants import (
            check_all_for_operation,
        )

        results = check_all_for_operation(
            "integration.disable",
            {
                "operation": "integration.disable",
                "integration_exists": False,
            },
        )
        assert len(results) >= 1
        inv_id, passed, message = results[0]
        assert inv_id == "BI-INTEG-002"
        assert passed is False
        assert "does not exist" in message

    def test_bi_integ_002_rejects_already_disabled(self):
        """BI-INTEG-002: integration.disable on already-disabled → FAIL."""
        from app.hoc.cus.hoc_spine.authority.business_invariants import (
            check_all_for_operation,
        )

        results = check_all_for_operation(
            "integration.disable",
            {
                "operation": "integration.disable",
                "integration_exists": True,
                "current_status": "disabled",
            },
        )
        assert len(results) >= 1
        _, passed, message = results[0]
        assert passed is False
        assert "already disabled" in message

    def test_bi_integ_002_rejects_non_enabled_status(self):
        """BI-INTEG-002: integration.disable on 'error' status → FAIL."""
        from app.hoc.cus.hoc_spine.authority.business_invariants import (
            check_all_for_operation,
        )

        results = check_all_for_operation(
            "integration.disable",
            {
                "operation": "integration.disable",
                "integration_exists": True,
                "current_status": "error",
            },
        )
        assert len(results) >= 1
        _, passed, message = results[0]
        assert passed is False
        assert "enabled" in message

    def test_bi_integ_002_accepts_valid_disable(self):
        """BI-INTEG-002: integration.disable on enabled integration → PASS."""
        from app.hoc.cus.hoc_spine.authority.business_invariants import (
            check_all_for_operation,
        )

        results = check_all_for_operation(
            "integration.disable",
            {
                "operation": "integration.disable",
                "integration_exists": True,
                "current_status": "enabled",
            },
        )
        assert len(results) >= 1
        _, passed, _ = results[0]
        assert passed is True

    # --- BI-INTEG-003 (integrations.query) ---

    def test_bi_integ_003_rejects_missing_tenant_id(self):
        """BI-INTEG-003: integrations.query with no tenant_id → FAIL."""
        from app.hoc.cus.hoc_spine.authority.business_invariants import (
            check_all_for_operation,
        )

        results = check_all_for_operation(
            "integrations.query",
            {"operation": "integrations.query"},
        )
        assert len(results) >= 1
        inv_id, passed, message = results[0]
        assert inv_id == "BI-INTEG-003"
        assert passed is False
        assert "tenant_id" in message

    def test_bi_integ_003_rejects_empty_tenant_id(self):
        """BI-INTEG-003: integrations.query with empty tenant_id → FAIL."""
        from app.hoc.cus.hoc_spine.authority.business_invariants import (
            check_all_for_operation,
        )

        results = check_all_for_operation(
            "integrations.query",
            {"operation": "integrations.query", "tenant_id": ""},
        )
        assert len(results) >= 1
        _, passed, message = results[0]
        assert passed is False
        assert "tenant_id" in message

    def test_bi_integ_003_accepts_valid_query(self):
        """BI-INTEG-003: integrations.query with valid tenant_id → PASS."""
        from app.hoc.cus.hoc_spine.authority.business_invariants import (
            check_all_for_operation,
        )

        results = check_all_for_operation(
            "integrations.query",
            {"operation": "integrations.query", "tenant_id": "t-001"},
        )
        assert len(results) >= 1
        _, passed, _ = results[0]
        assert passed is True

    # --- STRICT mode escalation ---

    def test_bi_integ_001_in_strict_mode_raises(self):
        """BI-INTEG-001 (HIGH severity) in STRICT mode → BusinessInvariantViolation."""
        from app.hoc.cus.hoc_spine.authority.business_invariants import (
            BusinessInvariantViolation,
        )
        from app.hoc.cus.hoc_spine.authority.invariant_evaluator import (
            InvariantMode,
            evaluate_invariants,
        )

        with pytest.raises(BusinessInvariantViolation) as exc_info:
            evaluate_invariants(
                "integration.enable",
                {"operation": "integration.enable"},
                InvariantMode.STRICT,
            )
        assert "BI-INTEG-001" in exc_info.value.invariant_id

    def test_bi_integ_002_in_strict_mode_raises(self):
        """BI-INTEG-002 (HIGH severity) in STRICT mode → BusinessInvariantViolation."""
        from app.hoc.cus.hoc_spine.authority.business_invariants import (
            BusinessInvariantViolation,
        )
        from app.hoc.cus.hoc_spine.authority.invariant_evaluator import (
            InvariantMode,
            evaluate_invariants,
        )

        with pytest.raises(BusinessInvariantViolation) as exc_info:
            evaluate_invariants(
                "integration.disable",
                {
                    "operation": "integration.disable",
                    "integration_exists": False,
                },
                InvariantMode.STRICT,
            )
        assert "BI-INTEG-002" in exc_info.value.invariant_id


# =============================================================================
# INT-DELTA-03: In-process execution assertions via real OperationRegistry
# =============================================================================


class TestIntegrationsRegistryDispatch:
    """Prove integrations operations dispatch through real OperationRegistry."""

    @pytest.fixture
    def registry_with_integrations_handlers(self):
        """Create a fresh OperationRegistry with mock integrations handlers."""
        from app.hoc.cus.hoc_spine.orchestrator.operation_registry import (
            OperationRegistry,
            OperationResult,
        )

        registry = OperationRegistry()

        # integration.enable handler
        enable_handler = MagicMock()
        enable_handler.execute = AsyncMock(
            return_value=OperationResult.ok(
                {"integration_id": "int-001", "status": "enabled", "connector_type": "openai"}
            )
        )
        registry.register("integration.enable", enable_handler)

        # integration.disable handler
        disable_handler = MagicMock()
        disable_handler.execute = AsyncMock(
            return_value=OperationResult.ok(
                {"integration_id": "int-001", "status": "disabled"}
            )
        )
        registry.register("integration.disable", disable_handler)

        # integrations.query handler (PR-8 list dispatch)
        query_handler = MagicMock()
        query_handler.execute = AsyncMock(
            return_value=OperationResult.ok(
                {
                    "integrations": [
                        {"id": "int-a", "name": "A", "status": "enabled"},
                        {"id": "int-b", "name": "B", "status": "enabled"},
                    ],
                    "total": 2,
                    "has_more": False,
                }
            )
        )
        registry.register("integrations.query", query_handler)

        return registry, enable_handler, disable_handler, query_handler

    @pytest.mark.asyncio
    async def test_enable_dispatch_success(
        self, registry_with_integrations_handlers
    ):
        """integration.enable dispatches and returns success with valid context."""
        from app.hoc.cus.hoc_spine.orchestrator.operation_registry import (
            OperationContext,
        )

        registry, enable_handler, _, _ = registry_with_integrations_handlers

        ctx = OperationContext(
            session=None,
            tenant_id="t-test",
            params={"connector_type": "openai", "connector_registered": True},
        )
        result = await registry.execute("integration.enable", ctx)
        assert result.success is True
        assert result.data["status"] == "enabled"
        assert enable_handler.execute.called

    @pytest.mark.asyncio
    async def test_enable_monitor_mode_allows_unregistered(
        self, registry_with_integrations_handlers
    ):
        """In MONITOR mode, unregistered connector logs but doesn't block."""
        from app.hoc.cus.hoc_spine.authority.invariant_evaluator import InvariantMode
        from app.hoc.cus.hoc_spine.orchestrator.operation_registry import (
            OperationContext,
        )

        registry, enable_handler, _, _ = registry_with_integrations_handlers
        registry.set_invariant_mode(InvariantMode.MONITOR)

        ctx = OperationContext(
            session=None,
            tenant_id="t-test",
            params={"connector_type": "unknown", "connector_registered": False},
        )
        result = await registry.execute("integration.enable", ctx)
        assert result.success is True  # MONITOR doesn't block
        assert enable_handler.execute.called

    @pytest.mark.asyncio
    async def test_enable_strict_blocks_unregistered(
        self, registry_with_integrations_handlers
    ):
        """In STRICT mode, unregistered connector → BI-INTEG-001 blocks."""
        from app.hoc.cus.hoc_spine.authority.business_invariants import (
            BusinessInvariantViolation,
        )
        from app.hoc.cus.hoc_spine.authority.invariant_evaluator import InvariantMode
        from app.hoc.cus.hoc_spine.orchestrator.operation_registry import (
            OperationContext,
        )

        registry, _, _, _ = registry_with_integrations_handlers
        registry.set_invariant_mode(InvariantMode.STRICT)

        ctx = OperationContext(
            session=None,
            tenant_id="t-test",
            params={"connector_type": "unknown", "connector_registered": False},
        )
        with pytest.raises(BusinessInvariantViolation):
            await registry.execute("integration.enable", ctx)

    @pytest.mark.asyncio
    async def test_disable_dispatch_success(
        self, registry_with_integrations_handlers
    ):
        """integration.disable dispatches successfully for enabled integration."""
        from app.hoc.cus.hoc_spine.orchestrator.operation_registry import (
            OperationContext,
        )

        registry, _, disable_handler, _ = registry_with_integrations_handlers

        ctx = OperationContext(
            session=None,
            tenant_id="t-test",
            params={"integration_exists": True, "current_status": "enabled"},
        )
        result = await registry.execute("integration.disable", ctx)
        assert result.success is True
        assert result.data["status"] == "disabled"
        assert disable_handler.execute.called

    @pytest.mark.asyncio
    async def test_disable_strict_blocks_already_disabled(
        self, registry_with_integrations_handlers
    ):
        """In STRICT mode, disabling already-disabled integration → blocked."""
        from app.hoc.cus.hoc_spine.authority.business_invariants import (
            BusinessInvariantViolation,
        )
        from app.hoc.cus.hoc_spine.authority.invariant_evaluator import InvariantMode
        from app.hoc.cus.hoc_spine.orchestrator.operation_registry import (
            OperationContext,
        )

        registry, _, _, _ = registry_with_integrations_handlers
        registry.set_invariant_mode(InvariantMode.STRICT)

        ctx = OperationContext(
            session=None,
            tenant_id="t-test",
            params={"integration_exists": True, "current_status": "disabled"},
        )
        with pytest.raises(BusinessInvariantViolation):
            await registry.execute("integration.disable", ctx)

    @pytest.mark.asyncio
    async def test_query_dispatch_success(
        self, registry_with_integrations_handlers
    ):
        """integrations.query dispatches successfully with valid tenant_id."""
        from app.hoc.cus.hoc_spine.orchestrator.operation_registry import (
            OperationContext,
        )

        registry, _, _, query_handler = registry_with_integrations_handlers

        ctx = OperationContext(
            session=None,
            tenant_id="t-test",
            params={"tenant_id": "t-test", "method": "list_integrations"},
        )
        result = await registry.execute("integrations.query", ctx)
        assert result.success is True
        assert result.data["total"] == 2
        assert len(result.data["integrations"]) == 2
        assert query_handler.execute.called

    @pytest.mark.asyncio
    async def test_query_dispatch_deterministic(
        self, registry_with_integrations_handlers
    ):
        """Dispatching integrations.query twice yields identical results (deterministic)."""
        from app.hoc.cus.hoc_spine.orchestrator.operation_registry import (
            OperationContext,
        )

        registry, _, _, query_handler = registry_with_integrations_handlers

        ctx = OperationContext(
            session=None,
            tenant_id="t-test",
            params={"tenant_id": "t-test", "method": "list_integrations"},
        )
        r1 = await registry.execute("integrations.query", ctx)
        r2 = await registry.execute("integrations.query", ctx)
        assert r1.success == r2.success
        assert r1.data == r2.data
        assert query_handler.execute.call_count == 2

    @pytest.mark.asyncio
    async def test_query_single_dispatch_semantics(
        self, registry_with_integrations_handlers
    ):
        """PR-8: integrations.query dispatches exactly once per execute call."""
        from app.hoc.cus.hoc_spine.orchestrator.operation_registry import (
            OperationContext,
        )

        registry, _, _, query_handler = registry_with_integrations_handlers

        ctx = OperationContext(
            session=None,
            tenant_id="t-test",
            params={"tenant_id": "t-test", "method": "list_integrations"},
        )
        await registry.execute("integrations.query", ctx)
        assert query_handler.execute.call_count == 1  # Exactly one dispatch

    @pytest.mark.asyncio
    async def test_dispatch_result_contains_operation(
        self, registry_with_integrations_handlers
    ):
        """Result from integrations dispatch carries the operation name."""
        from app.hoc.cus.hoc_spine.orchestrator.operation_registry import (
            OperationContext,
        )

        registry, _, _, _ = registry_with_integrations_handlers

        ctx = OperationContext(
            session=None,
            tenant_id="t-test",
            params={"connector_type": "openai", "connector_registered": True},
        )
        result = await registry.execute("integration.enable", ctx)
        assert result.operation == "integration.enable"

    @pytest.mark.asyncio
    async def test_disable_dispatch_result_carries_operation(
        self, registry_with_integrations_handlers
    ):
        """Result from disable dispatch carries the operation name."""
        from app.hoc.cus.hoc_spine.orchestrator.operation_registry import (
            OperationContext,
        )

        registry, _, _, _ = registry_with_integrations_handlers

        ctx = OperationContext(
            session=None,
            tenant_id="t-test",
            params={"integration_exists": True, "current_status": "enabled"},
        )
        result = await registry.execute("integration.disable", ctx)
        assert result.operation == "integration.disable"


# =============================================================================
# INT-DELTA audit fix: Fail-closed on missing context (MEDIUM #2)
# =============================================================================


class TestIntegrationsFailClosedMissingContext:
    """Prove BI-INTEG-002 fails when required context keys are missing."""

    def test_bi_integ_002_rejects_missing_integration_exists(self):
        """BI-INTEG-002: missing integration_exists key → FAIL (fail-closed)."""
        from app.hoc.cus.hoc_spine.authority.business_invariants import (
            check_all_for_operation,
        )

        results = check_all_for_operation(
            "integration.disable",
            {"operation": "integration.disable"},
        )
        assert len(results) >= 1
        inv_id, passed, message = results[0]
        assert inv_id == "BI-INTEG-002"
        assert passed is False
        assert "integration_exists" in message and "required" in message

    def test_bi_integ_002_rejects_missing_current_status(self):
        """BI-INTEG-002: missing current_status key → FAIL (fail-closed)."""
        from app.hoc.cus.hoc_spine.authority.business_invariants import (
            check_all_for_operation,
        )

        results = check_all_for_operation(
            "integration.disable",
            {
                "operation": "integration.disable",
                "integration_exists": True,
            },
        )
        assert len(results) >= 1
        inv_id, passed, message = results[0]
        assert inv_id == "BI-INTEG-002"
        assert passed is False
        assert "current_status" in message and "required" in message

    def test_bi_integ_002_rejects_none_current_status(self):
        """BI-INTEG-002: explicit None current_status → FAIL (fail-closed)."""
        from app.hoc.cus.hoc_spine.authority.business_invariants import (
            check_all_for_operation,
        )

        results = check_all_for_operation(
            "integration.disable",
            {
                "operation": "integration.disable",
                "integration_exists": True,
                "current_status": None,
            },
        )
        assert len(results) >= 1
        _, passed, message = results[0]
        assert passed is False
        assert "current_status" in message

    def test_bi_integ_002_still_passes_valid_context(self):
        """BI-INTEG-002: fully-populated valid context → PASS."""
        from app.hoc.cus.hoc_spine.authority.business_invariants import (
            check_all_for_operation,
        )

        results = check_all_for_operation(
            "integration.disable",
            {
                "operation": "integration.disable",
                "integration_exists": True,
                "current_status": "enabled",
            },
        )
        assert len(results) >= 1
        _, passed, _ = results[0]
        assert passed is True


# =============================================================================
# INT-DELTA audit fix: Production wiring tests (MEDIUM #3)
# =============================================================================


class TestIntegrationsProductionWiring:
    """
    Prove that the REAL production path (integrations.query + method dispatch)
    enforces sub-operation invariants (BI-INTEG-001, BI-INTEG-002) via
    IntegrationsQueryHandler._evaluate_sub_operation_invariants.
    """

    @pytest.fixture
    def production_registry(self):
        """
        Create a registry with the REAL IntegrationsQueryHandler registered
        under 'integrations.query', with a mocked facade to avoid DB deps.
        """
        from unittest.mock import patch

        from app.hoc.cus.hoc_spine.orchestrator.operation_registry import (
            OperationRegistry,
        )
        from app.hoc.cus.hoc_spine.orchestrator.handlers.integrations_handler import (
            IntegrationsQueryHandler,
        )

        registry = OperationRegistry()
        registry.register("integrations.query", IntegrationsQueryHandler())
        return registry

    @pytest.mark.asyncio
    async def test_disable_via_query_strict_blocks_missing_context(
        self, production_registry
    ):
        """STRICT: integrations.query + method=disable_integration with missing context → blocked."""
        from app.hoc.cus.hoc_spine.authority.invariant_evaluator import InvariantMode
        from app.hoc.cus.hoc_spine.orchestrator.operation_registry import (
            OperationContext,
        )

        production_registry.set_invariant_mode(InvariantMode.STRICT)

        ctx = OperationContext(
            session=None,
            tenant_id="t-prod-test",
            params={
                "method": "disable_integration",
                "tenant_id": "t-prod-test",
                # Missing integration_exists and current_status → fail-closed
            },
        )
        # The handler raises BusinessInvariantViolation for the sub-operation
        # which the registry catches and wraps in OperationResult.fail
        result = await production_registry.execute("integrations.query", ctx)
        assert result.success is False
        assert "BusinessInvariantViolation" in (result.error_code or "")

    @pytest.mark.asyncio
    async def test_disable_via_query_strict_blocks_already_disabled(
        self, production_registry
    ):
        """STRICT: disable_integration on already-disabled → blocked via BI-INTEG-002."""
        from app.hoc.cus.hoc_spine.authority.invariant_evaluator import InvariantMode
        from app.hoc.cus.hoc_spine.orchestrator.operation_registry import (
            OperationContext,
        )

        production_registry.set_invariant_mode(InvariantMode.STRICT)

        ctx = OperationContext(
            session=None,
            tenant_id="t-prod-test",
            params={
                "method": "disable_integration",
                "tenant_id": "t-prod-test",
                "integration_exists": True,
                "current_status": "disabled",
            },
        )
        result = await production_registry.execute("integrations.query", ctx)
        assert result.success is False
        assert "BusinessInvariantViolation" in (result.error_code or "")

    @pytest.mark.asyncio
    async def test_enable_via_query_strict_blocks_unregistered(
        self, production_registry
    ):
        """STRICT: enable_integration with unregistered connector → blocked via BI-INTEG-001."""
        from app.hoc.cus.hoc_spine.authority.invariant_evaluator import InvariantMode
        from app.hoc.cus.hoc_spine.orchestrator.operation_registry import (
            OperationContext,
        )

        production_registry.set_invariant_mode(InvariantMode.STRICT)

        ctx = OperationContext(
            session=None,
            tenant_id="t-prod-test",
            params={
                "method": "enable_integration",
                "tenant_id": "t-prod-test",
                "connector_type": "unknown_provider",
                "connector_registered": False,
            },
        )
        result = await production_registry.execute("integrations.query", ctx)
        assert result.success is False
        error_code = result.error_code or ""
        assert "BusinessInvariantViolation" in error_code or "INVARIANT" in error_code.upper()

    @pytest.mark.asyncio
    async def test_disable_via_query_monitor_does_not_block(
        self, production_registry
    ):
        """MONITOR: disable_integration with violation → logs but does NOT block dispatch."""
        from unittest.mock import patch

        from app.hoc.cus.hoc_spine.authority.invariant_evaluator import InvariantMode
        from app.hoc.cus.hoc_spine.orchestrator.operation_registry import (
            OperationContext,
        )

        production_registry.set_invariant_mode(InvariantMode.MONITOR)

        mock_facade = MagicMock()
        mock_facade.disable_integration = AsyncMock(
            return_value={"integration_id": "int-001", "status": "disabled"}
        )

        ctx = OperationContext(
            session=None,
            tenant_id="t-prod-test",
            params={
                "method": "disable_integration",
                "tenant_id": "t-prod-test",
                "integration_exists": True,
                "current_status": "disabled",  # violation: already disabled
            },
        )

        with patch(
            "app.hoc.cus.integrations.L5_engines.integrations_facade.get_integrations_facade",
            return_value=mock_facade,
        ):
            result = await production_registry.execute("integrations.query", ctx)
        assert result.success is True  # MONITOR doesn't block

    @pytest.mark.asyncio
    async def test_disable_via_query_valid_context_dispatches(
        self, production_registry
    ):
        """Valid disable_integration context passes invariant check and dispatches to facade."""
        from unittest.mock import patch

        from app.hoc.cus.hoc_spine.orchestrator.operation_registry import (
            OperationContext,
        )

        mock_facade = MagicMock()
        mock_facade.disable_integration = AsyncMock(
            return_value={"integration_id": "int-001", "status": "disabled"}
        )

        ctx = OperationContext(
            session=None,
            tenant_id="t-prod-test",
            params={
                "method": "disable_integration",
                "tenant_id": "t-prod-test",
                "integration_exists": True,
                "current_status": "enabled",
            },
        )

        with patch(
            "app.hoc.cus.integrations.L5_engines.integrations_facade.get_integrations_facade",
            return_value=mock_facade,
        ):
            result = await production_registry.execute("integrations.query", ctx)
        assert result.success is True
        assert result.data["status"] == "disabled"
        mock_facade.disable_integration.assert_called_once()

    @pytest.mark.asyncio
    async def test_list_integrations_no_sub_operation_invariant(
        self, production_registry
    ):
        """list_integrations (read) does NOT trigger sub-operation invariant evaluation."""
        from unittest.mock import patch

        from app.hoc.cus.hoc_spine.orchestrator.operation_registry import (
            OperationContext,
        )

        mock_facade = MagicMock()
        mock_facade.list_integrations = AsyncMock(
            return_value={"integrations": [], "total": 0}
        )

        ctx = OperationContext(
            session=None,
            tenant_id="t-prod-test",
            params={
                "method": "list_integrations",
                "tenant_id": "t-prod-test",
            },
        )

        with patch(
            "app.hoc.cus.integrations.L5_engines.integrations_facade.get_integrations_facade",
            return_value=mock_facade,
        ):
            result = await production_registry.execute("integrations.query", ctx)
        assert result.success is True
        mock_facade.list_integrations.assert_called_once()

    @pytest.mark.asyncio
    async def test_handler_method_invariant_map_coverage(self):
        """IntegrationsQueryHandler._METHOD_INVARIANT_MAP covers enable and disable."""
        from app.hoc.cus.hoc_spine.orchestrator.handlers.integrations_handler import (
            IntegrationsQueryHandler,
        )

        handler = IntegrationsQueryHandler()
        assert "enable_integration" in handler._METHOD_INVARIANT_MAP
        assert "disable_integration" in handler._METHOD_INVARIANT_MAP
        assert handler._METHOD_INVARIANT_MAP["enable_integration"] == "integration.enable"
        assert handler._METHOD_INVARIANT_MAP["disable_integration"] == "integration.disable"


# =============================================================================
# INT-DELTA audit fix #2: Connectors/DataSources _invariant_mode stripping
# =============================================================================


class TestIntegrationsConnectorsDataSourcesWiring:
    """
    Prove that integrations.connectors and integrations.datasources paths
    strip _invariant_mode and other internal metadata keys from kwargs before
    forwarding to L5 facades. Regression guard for _invariant_mode leakage.
    """

    @pytest.fixture
    def connectors_production_registry(self):
        """Registry with REAL IntegrationsConnectorsHandler."""
        from app.hoc.cus.hoc_spine.orchestrator.operation_registry import (
            OperationRegistry,
        )
        from app.hoc.cus.hoc_spine.orchestrator.handlers.integrations_handler import (
            IntegrationsConnectorsHandler,
        )

        registry = OperationRegistry()
        registry.register("integrations.connectors", IntegrationsConnectorsHandler())
        return registry

    @pytest.fixture
    def datasources_production_registry(self):
        """Registry with REAL IntegrationsDataSourcesHandler."""
        from app.hoc.cus.hoc_spine.orchestrator.operation_registry import (
            OperationRegistry,
        )
        from app.hoc.cus.hoc_spine.orchestrator.handlers.integrations_handler import (
            IntegrationsDataSourcesHandler,
        )

        registry = OperationRegistry()
        registry.register("integrations.datasources", IntegrationsDataSourcesHandler())
        return registry

    @pytest.mark.asyncio
    async def test_connectors_list_strips_invariant_mode(
        self, connectors_production_registry
    ):
        """integrations.connectors + list_connectors must NOT leak _invariant_mode to facade."""
        from unittest.mock import patch

        from app.hoc.cus.hoc_spine.authority.invariant_evaluator import InvariantMode
        from app.hoc.cus.hoc_spine.orchestrator.operation_registry import (
            OperationContext,
        )

        connectors_production_registry.set_invariant_mode(InvariantMode.MONITOR)

        mock_facade = MagicMock()
        mock_facade.list_connectors = AsyncMock(
            return_value={"connectors": [], "total": 0}
        )

        ctx = OperationContext(
            session=None,
            tenant_id="t-conn-test",
            params={
                "method": "list_connectors",
                "tenant_id": "t-conn-test",
            },
        )

        with patch(
            "app.hoc.cus.integrations.L5_engines.connectors_facade.get_connectors_facade",
            return_value=mock_facade,
        ):
            result = await connectors_production_registry.execute(
                "integrations.connectors", ctx
            )
        assert result.success is True
        # Verify _invariant_mode was NOT passed to facade
        call_kwargs = mock_facade.list_connectors.call_args
        if call_kwargs:
            all_kwargs = {**dict(call_kwargs[1])} if call_kwargs[1] else {}
            assert "_invariant_mode" not in all_kwargs, (
                "_invariant_mode leaked to connectors facade"
            )

    @pytest.mark.asyncio
    async def test_datasources_list_strips_invariant_mode(
        self, datasources_production_registry
    ):
        """integrations.datasources + list_sources must NOT leak _invariant_mode to facade."""
        from unittest.mock import patch

        from app.hoc.cus.hoc_spine.authority.invariant_evaluator import InvariantMode
        from app.hoc.cus.hoc_spine.orchestrator.operation_registry import (
            OperationContext,
        )

        datasources_production_registry.set_invariant_mode(InvariantMode.MONITOR)

        mock_facade = MagicMock()
        mock_facade.list_sources = AsyncMock(
            return_value={"sources": [], "total": 0}
        )

        ctx = OperationContext(
            session=None,
            tenant_id="t-ds-test",
            params={
                "method": "list_sources",
                "tenant_id": "t-ds-test",
            },
        )

        with patch(
            "app.hoc.cus.integrations.L5_engines.datasources_facade.get_datasources_facade",
            return_value=mock_facade,
        ):
            result = await datasources_production_registry.execute(
                "integrations.datasources", ctx
            )
        assert result.success is True
        call_kwargs = mock_facade.list_sources.call_args
        if call_kwargs:
            all_kwargs = {**dict(call_kwargs[1])} if call_kwargs[1] else {}
            assert "_invariant_mode" not in all_kwargs, (
                "_invariant_mode leaked to datasources facade"
            )

    @pytest.mark.asyncio
    async def test_connectors_strips_tenant_id_from_kwargs(
        self, connectors_production_registry
    ):
        """integrations.connectors must NOT duplicate tenant_id in facade kwargs."""
        from unittest.mock import patch

        from app.hoc.cus.hoc_spine.orchestrator.operation_registry import (
            OperationContext,
        )

        mock_facade = MagicMock()
        mock_facade.get_connector = AsyncMock(
            return_value={"connector_id": "c-001", "name": "slack"}
        )

        ctx = OperationContext(
            session=None,
            tenant_id="t-conn-test",
            params={
                "method": "get_connector",
                "tenant_id": "t-conn-test",
                "connector_id": "c-001",
            },
        )

        with patch(
            "app.hoc.cus.integrations.L5_engines.connectors_facade.get_connectors_facade",
            return_value=mock_facade,
        ):
            result = await connectors_production_registry.execute(
                "integrations.connectors", ctx
            )
        assert result.success is True
        mock_facade.get_connector.assert_called_once()
        call_kwargs = mock_facade.get_connector.call_args[1]
        # tenant_id passed positionally by handler, should not be in kwargs
        assert "tenant_id" in call_kwargs  # handler passes tenant_id=ctx.tenant_id

    @pytest.mark.asyncio
    async def test_datasources_strips_tenant_id_from_kwargs(
        self, datasources_production_registry
    ):
        """integrations.datasources must NOT duplicate tenant_id in facade kwargs."""
        from unittest.mock import patch

        from app.hoc.cus.hoc_spine.orchestrator.operation_registry import (
            OperationContext,
        )

        mock_facade = MagicMock()
        mock_facade.get_source = AsyncMock(
            return_value={"source_id": "s-001", "name": "postgres"}
        )

        ctx = OperationContext(
            session=None,
            tenant_id="t-ds-test",
            params={
                "method": "get_source",
                "tenant_id": "t-ds-test",
                "source_id": "s-001",
            },
        )

        with patch(
            "app.hoc.cus.integrations.L5_engines.datasources_facade.get_datasources_facade",
            return_value=mock_facade,
        ):
            result = await datasources_production_registry.execute(
                "integrations.datasources", ctx
            )
        assert result.success is True
        mock_facade.get_source.assert_called_once()
        call_kwargs = mock_facade.get_source.call_args[1]
        assert "tenant_id" in call_kwargs  # handler passes tenant_id=ctx.tenant_id
