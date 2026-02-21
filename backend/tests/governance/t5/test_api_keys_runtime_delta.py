# Layer: TEST
# AUDIENCE: INTERNAL
# Role: AK-DELTA-01..03 — API keys domain runtime correctness proofs
# artifact_class: TEST


"""
API Keys Domain Runtime Correctness Tests (BI-APIKEY-001)

Proves that:
  1. BI-APIKEY-001 (api_key.create) is fail-closed on missing tenant_id AND
     missing tenant_status (both required)
  2. Positive pass when tenant_id present and tenant_status ACTIVE
  3. MONITOR mode logs but does not block dispatch
  4. STRICT mode blocks on invariant violations
  5. Real OperationRegistry.execute(...) dispatch proof for api_keys.write
     using context enricher (no synthetic tenant_status in params)
  6. api_keys.query does NOT trigger BI-APIKEY-001
  7. Alias mapping api_keys.write → api_key.create is enforced
  8. Without context enricher, STRICT mode blocks (fail-closed on missing
     tenant_status) — proves the pre-corrective gap is closed
  9. Caller-supplied tenant_status cannot bypass authoritative DB lookup
     in the context enricher
 10. STRICT mode does NOT block revoke/list methods (method-aware gating)
 11. Method-aware gate in _default_check passes non-create methods
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest


# =============================================================================
# AK-DELTA-03a: Contract tests — invariant fail-closed behavior
# =============================================================================


class TestApiKeysInvariantContracts:
    """Prove BI-APIKEY-001 is fail-closed on missing/invalid tenant context."""

    # --- Fail-closed negatives ---

    def test_bi_apikey_001_rejects_missing_tenant_id(self):
        """BI-APIKEY-001: api_key.create with no tenant_id → FAIL."""
        from app.hoc.cus.hoc_spine.authority.business_invariants import (
            check_all_for_operation,
        )

        results = check_all_for_operation(
            "api_key.create",
            {"operation": "api_key.create"},
        )
        assert len(results) >= 1
        inv_id, passed, message = results[0]
        assert inv_id == "BI-APIKEY-001"
        assert passed is False
        assert "tenant_id" in message

    def test_bi_apikey_001_rejects_empty_tenant_id(self):
        """BI-APIKEY-001: api_key.create with empty tenant_id → FAIL."""
        from app.hoc.cus.hoc_spine.authority.business_invariants import (
            check_all_for_operation,
        )

        results = check_all_for_operation(
            "api_key.create",
            {"operation": "api_key.create", "tenant_id": ""},
        )
        assert len(results) >= 1
        inv_id, passed, message = results[0]
        assert inv_id == "BI-APIKEY-001"
        assert passed is False

    def test_bi_apikey_001_rejects_missing_tenant_status(self):
        """BI-APIKEY-001: tenant_id present but no tenant_status → FAIL (fail-closed).

        This is the corrective test: pre-fix, this PASSED because the checker
        only validated tenant_status IF it was present. Now it requires
        tenant_status and fails closed when absent.
        """
        from app.hoc.cus.hoc_spine.authority.business_invariants import (
            check_all_for_operation,
        )

        results = check_all_for_operation(
            "api_key.create",
            {"operation": "api_key.create", "tenant_id": "t-no-status"},
        )
        assert len(results) >= 1
        inv_id, passed, message = results[0]
        assert inv_id == "BI-APIKEY-001"
        assert passed is False
        assert "tenant_status" in message

    def test_bi_apikey_001_rejects_suspended_tenant(self):
        """BI-APIKEY-001: api_key.create with SUSPENDED tenant → FAIL."""
        from app.hoc.cus.hoc_spine.authority.business_invariants import (
            check_all_for_operation,
        )

        results = check_all_for_operation(
            "api_key.create",
            {
                "operation": "api_key.create",
                "tenant_id": "t-suspended",
                "tenant_status": "SUSPENDED",
            },
        )
        assert len(results) >= 1
        inv_id, passed, message = results[0]
        assert inv_id == "BI-APIKEY-001"
        assert passed is False
        assert "ACTIVE" in message

    def test_bi_apikey_001_rejects_creating_tenant(self):
        """BI-APIKEY-001: api_key.create with CREATING tenant → FAIL."""
        from app.hoc.cus.hoc_spine.authority.business_invariants import (
            check_all_for_operation,
        )

        results = check_all_for_operation(
            "api_key.create",
            {
                "operation": "api_key.create",
                "tenant_id": "t-creating",
                "tenant_status": "CREATING",
            },
        )
        assert len(results) >= 1
        _, passed, message = results[0]
        assert passed is False
        assert "ACTIVE" in message

    # --- Method-aware gate: non-create methods pass through ---

    def test_bi_apikey_001_passes_revoke_method(self):
        """BI-APIKEY-001: revoke_api_key method passes through (not scoped)."""
        from app.hoc.cus.hoc_spine.authority.business_invariants import (
            check_all_for_operation,
        )

        results = check_all_for_operation(
            "api_keys.write",
            {"operation": "api_keys.write", "method": "revoke_api_key", "tenant_id": "t-any"},
        )
        bi_results = [r for r in results if r[0] == "BI-APIKEY-001"]
        assert len(bi_results) >= 1
        _, passed, message = bi_results[0]
        assert passed is True
        assert "scoped to create only" in message

    def test_bi_apikey_001_passes_list_method(self):
        """BI-APIKEY-001: list_api_keys method passes through (not scoped)."""
        from app.hoc.cus.hoc_spine.authority.business_invariants import (
            check_all_for_operation,
        )

        results = check_all_for_operation(
            "api_keys.write",
            {"operation": "api_keys.write", "method": "list_api_keys", "tenant_id": "t-any"},
        )
        bi_results = [r for r in results if r[0] == "BI-APIKEY-001"]
        assert len(bi_results) >= 1
        _, passed, message = bi_results[0]
        assert passed is True
        assert "scoped to create only" in message

    # --- Positive pass case ---

    def test_bi_apikey_001_passes_active_tenant(self):
        """BI-APIKEY-001: api_key.create with ACTIVE tenant → PASS."""
        from app.hoc.cus.hoc_spine.authority.business_invariants import (
            check_all_for_operation,
        )

        results = check_all_for_operation(
            "api_key.create",
            {
                "operation": "api_key.create",
                "tenant_id": "t-active-001",
                "tenant_status": "ACTIVE",
            },
        )
        assert len(results) >= 1
        inv_id, passed, _ = results[0]
        assert inv_id == "BI-APIKEY-001"
        assert passed is True


# =============================================================================
# AK-DELTA-03b: Alias enforcement — api_keys.write → api_key.create
# =============================================================================


class TestApiKeysInvariantAlias:
    """Prove the alias mapping routes api_keys.write to BI-APIKEY-001."""

    def test_alias_mapping_exists(self):
        """INVARIANT_OPERATION_ALIASES maps api_keys.write → api_key.create."""
        from app.hoc.cus.hoc_spine.authority.business_invariants import (
            INVARIANT_OPERATION_ALIASES,
        )

        assert INVARIANT_OPERATION_ALIASES.get("api_keys.write") == "api_key.create"

    def test_check_all_resolves_alias_for_write(self):
        """check_all_for_operation('api_keys.write') finds BI-APIKEY-001."""
        from app.hoc.cus.hoc_spine.authority.business_invariants import (
            check_all_for_operation,
        )

        results = check_all_for_operation(
            "api_keys.write",
            {"operation": "api_keys.write", "tenant_id": ""},
        )
        inv_ids = [r[0] for r in results]
        assert "BI-APIKEY-001" in inv_ids

    def test_query_does_not_trigger_create_invariant(self):
        """api_keys.query must NOT trigger BI-APIKEY-001."""
        from app.hoc.cus.hoc_spine.authority.business_invariants import (
            check_all_for_operation,
        )

        results = check_all_for_operation(
            "api_keys.query",
            {"operation": "api_keys.query"},
        )
        inv_ids = [r[0] for r in results]
        assert "BI-APIKEY-001" not in inv_ids


# =============================================================================
# AK-DELTA-03c: MONITOR / STRICT mode behavior
# =============================================================================


class TestApiKeysInvariantModes:
    """Prove MONITOR and STRICT modes behave correctly for BI-APIKEY-001."""

    def test_monitor_mode_does_not_raise(self):
        """MONITOR mode: BI-APIKEY-001 fails but no exception raised."""
        from app.hoc.cus.hoc_spine.authority.invariant_evaluator import (
            InvariantMode,
            evaluate_invariants,
        )

        results = evaluate_invariants(
            "api_keys.write",
            {"operation": "api_keys.write", "tenant_id": ""},
            InvariantMode.MONITOR,
        )
        assert len(results) >= 1
        assert any(r.invariant_id == "BI-APIKEY-001" and not r.passed for r in results)

    def test_monitor_mode_returns_failure_details(self):
        """MONITOR mode: returns results with violation details for suspended tenant."""
        from app.hoc.cus.hoc_spine.authority.invariant_evaluator import (
            InvariantMode,
            evaluate_invariants,
        )

        results = evaluate_invariants(
            "api_keys.write",
            {
                "operation": "api_keys.write",
                "tenant_id": "t-suspended",
                "tenant_status": "SUSPENDED",
            },
            InvariantMode.MONITOR,
        )
        failed = [r for r in results if r.invariant_id == "BI-APIKEY-001" and not r.passed]
        assert len(failed) == 1
        assert "ACTIVE" in failed[0].message

    def test_strict_mode_raises_on_missing_tenant(self):
        """STRICT mode: BI-APIKEY-001 with no tenant_id → BusinessInvariantViolation."""
        from app.hoc.cus.hoc_spine.authority.business_invariants import (
            BusinessInvariantViolation,
        )
        from app.hoc.cus.hoc_spine.authority.invariant_evaluator import (
            InvariantMode,
            evaluate_invariants,
        )

        with pytest.raises(BusinessInvariantViolation) as exc_info:
            evaluate_invariants(
                "api_keys.write",
                {"operation": "api_keys.write"},
                InvariantMode.STRICT,
            )
        assert "BI-APIKEY-001" in exc_info.value.invariant_id

    def test_strict_mode_raises_on_suspended_tenant(self):
        """STRICT mode: BI-APIKEY-001 with SUSPENDED tenant → BusinessInvariantViolation."""
        from app.hoc.cus.hoc_spine.authority.business_invariants import (
            BusinessInvariantViolation,
        )
        from app.hoc.cus.hoc_spine.authority.invariant_evaluator import (
            InvariantMode,
            evaluate_invariants,
        )

        with pytest.raises(BusinessInvariantViolation) as exc_info:
            evaluate_invariants(
                "api_keys.write",
                {
                    "operation": "api_keys.write",
                    "tenant_id": "t-suspended",
                    "tenant_status": "SUSPENDED",
                },
                InvariantMode.STRICT,
            )
        assert "BI-APIKEY-001" in exc_info.value.invariant_id

    def test_strict_mode_passes_active_tenant(self):
        """STRICT mode: ACTIVE tenant → no exception."""
        from app.hoc.cus.hoc_spine.authority.invariant_evaluator import (
            InvariantMode,
            evaluate_invariants,
        )

        results = evaluate_invariants(
            "api_keys.write",
            {
                "operation": "api_keys.write",
                "tenant_id": "t-active-001",
                "tenant_status": "ACTIVE",
            },
            InvariantMode.STRICT,
        )
        assert all(r.passed for r in results)


# =============================================================================
# AK-DELTA-03d: Real OperationRegistry dispatch proof
#
# Tests use context enrichers (the runtime mechanism added to close the gap)
# instead of synthetic tenant_status in params. This proves enforcement on
# the real dispatch path where tenant_status comes from the enricher, not
# from the HTTP caller.
# =============================================================================


class TestApiKeysRegistryDispatch:
    """Prove api_keys operations dispatch through real OperationRegistry."""

    @pytest.fixture
    def registry_with_api_keys_handlers(self):
        """Create a fresh OperationRegistry with mock api_keys handlers.

        No enricher is registered — tests that need enrichment register
        it explicitly, proving the mechanism is required.
        """
        from app.hoc.cus.hoc_spine.orchestrator.operation_registry import (
            OperationRegistry,
            OperationResult,
        )

        registry = OperationRegistry()

        query_handler = MagicMock()
        query_handler.execute = AsyncMock(
            return_value=OperationResult.ok({"keys": [], "total": 0})
        )
        registry.register("api_keys.query", query_handler)

        write_handler = MagicMock()
        write_handler.execute = AsyncMock(
            return_value=OperationResult.ok({"full_key": "ak_test_xxx", "api_key": {"id": "k1"}})
        )
        registry.register("api_keys.write", write_handler)

        return registry, query_handler, write_handler

    @pytest.mark.asyncio
    async def test_query_dispatch(self, registry_with_api_keys_handlers):
        """api_keys.query dispatches and returns key list (no invariant trigger)."""
        from app.hoc.cus.hoc_spine.orchestrator.operation_registry import (
            OperationContext,
        )

        registry, query_handler, _ = registry_with_api_keys_handlers

        ctx = OperationContext(
            session=None,
            tenant_id="t-query-001",
            params={"method": "list_api_keys"},
        )
        result = await registry.execute("api_keys.query", ctx)
        assert result.success is True
        assert query_handler.execute.called

    @pytest.mark.asyncio
    async def test_write_dispatch_with_enricher(self, registry_with_api_keys_handlers):
        """api_keys.write dispatches when enricher provides ACTIVE status.

        This is the real-path happy case: the enricher resolves tenant_status
        from the database. Here we simulate it returning ACTIVE.
        """
        from app.hoc.cus.hoc_spine.orchestrator.operation_registry import (
            OperationContext,
        )

        registry, _, write_handler = registry_with_api_keys_handlers
        registry.register_context_enricher(
            "api_keys.write", lambda ctx: {"tenant_status": "ACTIVE"}
        )

        ctx = OperationContext(
            session=None,
            tenant_id="t-write-001",
            params={"method": "create_api_key"},
        )
        result = await registry.execute("api_keys.write", ctx)
        assert result.success is True
        assert result.data["full_key"] == "ak_test_xxx"
        assert write_handler.execute.called

    @pytest.mark.asyncio
    async def test_strict_blocks_write_without_enricher(
        self, registry_with_api_keys_handlers
    ):
        """STRICT mode: api_keys.write WITHOUT enricher → blocked (fail-closed).

        This is the corrective proof: before the fix, this path would PASS
        because the checker did not require tenant_status. Now it FAILS
        because tenant_status is absent from the invariant context.
        """
        from app.hoc.cus.hoc_spine.authority.business_invariants import (
            BusinessInvariantViolation,
        )
        from app.hoc.cus.hoc_spine.authority.invariant_evaluator import InvariantMode
        from app.hoc.cus.hoc_spine.orchestrator.operation_registry import (
            OperationContext,
        )

        registry, _, write_handler = registry_with_api_keys_handlers
        registry.set_invariant_mode(InvariantMode.STRICT)
        # No enricher registered — simulates pre-fix dispatch path

        ctx = OperationContext(
            session=None,
            tenant_id="t-create-001",
            params={"method": "create_api_key"},
        )

        with pytest.raises(BusinessInvariantViolation) as exc_info:
            await registry.execute("api_keys.write", ctx)

        assert "BI-APIKEY-001" in exc_info.value.invariant_id
        # Handler must NOT have been called — invariant blocked pre-dispatch
        assert not write_handler.execute.called

    @pytest.mark.asyncio
    async def test_strict_blocks_write_with_suspended_enricher(
        self, registry_with_api_keys_handlers
    ):
        """STRICT mode: enricher returns SUSPENDED → blocked pre-dispatch."""
        from app.hoc.cus.hoc_spine.authority.business_invariants import (
            BusinessInvariantViolation,
        )
        from app.hoc.cus.hoc_spine.authority.invariant_evaluator import InvariantMode
        from app.hoc.cus.hoc_spine.orchestrator.operation_registry import (
            OperationContext,
        )

        registry, _, write_handler = registry_with_api_keys_handlers
        registry.set_invariant_mode(InvariantMode.STRICT)
        registry.register_context_enricher(
            "api_keys.write", lambda ctx: {"tenant_status": "SUSPENDED"}
        )

        ctx = OperationContext(
            session=None,
            tenant_id="t-bad-001",
            params={"method": "create_api_key"},
        )

        with pytest.raises(BusinessInvariantViolation) as exc_info:
            await registry.execute("api_keys.write", ctx)

        assert "BI-APIKEY-001" in exc_info.value.invariant_id
        assert not write_handler.execute.called

    @pytest.mark.asyncio
    async def test_monitor_allows_write_without_enricher(
        self, registry_with_api_keys_handlers
    ):
        """MONITOR mode: api_keys.write without enricher → dispatches anyway.

        Even though tenant_status is missing (fail-closed invariant violation),
        MONITOR mode logs the violation but does not block dispatch.
        """
        from app.hoc.cus.hoc_spine.authority.invariant_evaluator import InvariantMode
        from app.hoc.cus.hoc_spine.orchestrator.operation_registry import (
            OperationContext,
        )

        registry, _, write_handler = registry_with_api_keys_handlers
        registry.set_invariant_mode(InvariantMode.MONITOR)
        # No enricher — invariant will fail, but MONITOR allows dispatch

        ctx = OperationContext(
            session=None,
            tenant_id="t-monitor-001",
            params={"method": "create_api_key"},
        )

        result = await registry.execute("api_keys.write", ctx)
        assert result.success is True
        assert write_handler.execute.called

    @pytest.mark.asyncio
    async def test_monitor_allows_write_with_suspended_enricher(
        self, registry_with_api_keys_handlers
    ):
        """MONITOR mode: enricher returns SUSPENDED → dispatches anyway."""
        from app.hoc.cus.hoc_spine.authority.invariant_evaluator import InvariantMode
        from app.hoc.cus.hoc_spine.orchestrator.operation_registry import (
            OperationContext,
        )

        registry, _, write_handler = registry_with_api_keys_handlers
        registry.set_invariant_mode(InvariantMode.MONITOR)
        registry.register_context_enricher(
            "api_keys.write", lambda ctx: {"tenant_status": "SUSPENDED"}
        )

        ctx = OperationContext(
            session=None,
            tenant_id="t-bad-002",
            params={"method": "create_api_key"},
        )

        result = await registry.execute("api_keys.write", ctx)
        assert result.success is True
        assert write_handler.execute.called

    @pytest.mark.asyncio
    async def test_unregistered_operation_fails(
        self, registry_with_api_keys_handlers
    ):
        """Unregistered operation name → OperationResult.fail."""
        from app.hoc.cus.hoc_spine.orchestrator.operation_registry import (
            OperationContext,
        )

        registry, _, _ = registry_with_api_keys_handlers

        ctx = OperationContext(
            session=None,
            tenant_id="t-bad-003",
            params={},
        )
        result = await registry.execute("api_keys.nonexistent", ctx)
        assert result.success is False

    @pytest.mark.asyncio
    async def test_real_handler_registration_exists(self):
        """Verify api_keys.* operations and enricher register on a real registry."""
        from app.hoc.cus.hoc_spine.orchestrator.operation_registry import (
            OperationRegistry,
        )
        from app.hoc.cus.hoc_spine.orchestrator.handlers.api_keys_handler import (
            register,
        )

        registry = OperationRegistry()
        register(registry)

        assert "api_keys.query" in registry._handlers
        assert "api_keys.write" in registry._handlers
        assert "api_keys.write" in registry._context_enrichers


# =============================================================================
# AK-DELTA-03e: Caller-supplied tenant_status bypass proof
# =============================================================================


class TestApiKeysEnricherBypassProof:
    """Prove caller-supplied tenant_status in params cannot bypass the
    authoritative DB lookup in the context enricher."""

    def test_enricher_ignores_caller_supplied_tenant_status(self):
        """Enricher queries DB even when ctx.params already has tenant_status.

        This proves the HIGH audit finding is closed: a caller who injects
        tenant_status=ACTIVE in the HTTP request cannot bypass the
        authoritative DB check.
        """
        from unittest.mock import MagicMock as MockClass

        from app.hoc.cus.hoc_spine.orchestrator.handlers.api_keys_handler import (
            _enrich_api_keys_write_context,
        )
        from app.hoc.cus.hoc_spine.orchestrator.operation_registry import (
            OperationContext,
        )

        # Create a mock sync_session that returns SUSPENDED from DB
        mock_session = MockClass()
        mock_row = MockClass()
        mock_row.__getitem__ = lambda self, idx: "SUSPENDED"
        mock_session.execute.return_value.first.return_value = mock_row

        # Caller injects tenant_status=ACTIVE in params — should be ignored
        ctx = OperationContext(
            session=None,
            tenant_id="t-bypass-attempt",
            params={
                "method": "create_api_key",
                "tenant_status": "ACTIVE",  # INJECTED BY CALLER
                "sync_session": mock_session,
                "tenant_id": "t-bypass-attempt",
            },
        )

        result = _enrich_api_keys_write_context(ctx)

        # Enricher MUST have queried DB (session.execute called)
        assert mock_session.execute.called
        # Enricher MUST return the authoritative DB status (SUSPENDED),
        # NOT the caller-supplied ACTIVE
        assert result.get("tenant_status") == "SUSPENDED"

    def test_enricher_skips_non_create_methods(self):
        """Enricher returns empty dict for revoke/list (no DB query needed)."""
        from app.hoc.cus.hoc_spine.orchestrator.handlers.api_keys_handler import (
            _enrich_api_keys_write_context,
        )
        from app.hoc.cus.hoc_spine.orchestrator.operation_registry import (
            OperationContext,
        )

        ctx = OperationContext(
            session=None,
            tenant_id="t-revoke-001",
            params={"method": "revoke_api_key"},
        )
        result = _enrich_api_keys_write_context(ctx)
        assert result == {}


# =============================================================================
# AK-DELTA-03f: STRICT mode method-aware dispatch proof
# =============================================================================


class TestApiKeysMethodAwareDispatch:
    """Prove STRICT mode does NOT block revoke/list methods, but still
    blocks create on non-ACTIVE tenant."""

    @pytest.fixture
    def strict_registry_with_handlers(self):
        """STRICT registry with mock handlers, no enricher."""
        from app.hoc.cus.hoc_spine.authority.invariant_evaluator import InvariantMode
        from app.hoc.cus.hoc_spine.orchestrator.operation_registry import (
            OperationRegistry,
            OperationResult,
        )

        registry = OperationRegistry()
        registry.set_invariant_mode(InvariantMode.STRICT)

        write_handler = MagicMock()
        write_handler.execute = AsyncMock(
            return_value=OperationResult.ok({"revoked": True})
        )
        registry.register("api_keys.write", write_handler)

        return registry, write_handler

    @pytest.mark.asyncio
    async def test_strict_allows_revoke_without_enricher(
        self, strict_registry_with_handlers
    ):
        """STRICT mode: revoke_api_key dispatches even without enricher.

        Method-aware gate in _default_check passes revoke through because
        BI-APIKEY-001 is scoped to create_api_key only.
        """
        from app.hoc.cus.hoc_spine.orchestrator.operation_registry import (
            OperationContext,
        )

        registry, write_handler = strict_registry_with_handlers

        ctx = OperationContext(
            session=None,
            tenant_id="t-revoke-001",
            params={"method": "revoke_api_key", "key_id": "k-123"},
        )

        result = await registry.execute("api_keys.write", ctx)
        assert result.success is True
        assert write_handler.execute.called

    @pytest.mark.asyncio
    async def test_strict_allows_list_without_enricher(
        self, strict_registry_with_handlers
    ):
        """STRICT mode: list_api_keys dispatches even without enricher."""
        from app.hoc.cus.hoc_spine.orchestrator.operation_registry import (
            OperationContext,
        )

        registry, write_handler = strict_registry_with_handlers

        ctx = OperationContext(
            session=None,
            tenant_id="t-list-001",
            params={"method": "list_api_keys"},
        )

        result = await registry.execute("api_keys.write", ctx)
        assert result.success is True
        assert write_handler.execute.called

    @pytest.mark.asyncio
    async def test_strict_still_blocks_create_without_enricher(
        self, strict_registry_with_handlers
    ):
        """STRICT mode: create_api_key still blocked without enricher.

        Confirms that the method-aware gate does NOT weaken create protection.
        """
        from app.hoc.cus.hoc_spine.authority.business_invariants import (
            BusinessInvariantViolation,
        )
        from app.hoc.cus.hoc_spine.orchestrator.operation_registry import (
            OperationContext,
        )

        registry, write_handler = strict_registry_with_handlers

        ctx = OperationContext(
            session=None,
            tenant_id="t-create-blocked",
            params={"method": "create_api_key"},
        )

        with pytest.raises(BusinessInvariantViolation) as exc_info:
            await registry.execute("api_keys.write", ctx)

        assert "BI-APIKEY-001" in exc_info.value.invariant_id
        assert not write_handler.execute.called
