# Layer: TEST
# AUDIENCE: INTERNAL
# Role: ONBOARD-DELTA-01/02 — Account onboarding domain runtime correctness proofs
# artifact_class: TEST


"""
Account Onboarding Domain Runtime Correctness Tests (BI-ONBOARD-001)

Proves that:
  1. BI-ONBOARD-001 (onboarding.activate) is fail-closed on missing predicates
  2. All four predicates are individually required (key_ready, connector_validated,
     sdk_attested, project_ready)
  3. Positive activation passes when all predicates are satisfied
  4. MONITOR mode logs but does not block activation
  5. STRICT mode blocks on invariant violations
  6. Real OperationRegistry.execute(...) dispatch proof for onboarding operations
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest


# =============================================================================
# ONBOARD-DELTA-01: Contract tests — invariant fail-closed behavior
# =============================================================================


class TestOnboardingInvariantContracts:
    """Prove BI-ONBOARD-001 is fail-closed on missing activation predicates."""

    # --- Fail-closed negatives ---

    def test_bi_onboard_001_rejects_empty_predicates(self):
        """BI-ONBOARD-001: onboarding.activate with no predicates → FAIL."""
        from app.hoc.cus.hoc_spine.authority.business_invariants import (
            check_all_for_operation,
        )

        results = check_all_for_operation(
            "onboarding.activate",
            {"operation": "onboarding.activate", "predicates": {}},
        )
        assert len(results) >= 1
        inv_id, passed, message = results[0]
        assert inv_id == "BI-ONBOARD-001"
        assert passed is False
        assert "empty" in message or "missing" in message

    def test_bi_onboard_001_rejects_missing_predicates_key(self):
        """BI-ONBOARD-001: onboarding.activate with no predicates key → FAIL."""
        from app.hoc.cus.hoc_spine.authority.business_invariants import (
            check_all_for_operation,
        )

        results = check_all_for_operation(
            "onboarding.activate",
            {"operation": "onboarding.activate"},
        )
        assert len(results) >= 1
        inv_id, passed, message = results[0]
        assert inv_id == "BI-ONBOARD-001"
        assert passed is False

    def test_bi_onboard_001_rejects_missing_api_key(self):
        """BI-ONBOARD-001: missing key_ready predicate → FAIL."""
        from app.hoc.cus.hoc_spine.authority.business_invariants import (
            check_all_for_operation,
        )

        results = check_all_for_operation(
            "onboarding.activate",
            {
                "operation": "onboarding.activate",
                "predicates": {
                    "project_ready": True,
                    "key_ready": False,
                    "connector_validated": True,
                    "sdk_attested": True,
                },
            },
        )
        assert len(results) >= 1
        inv_id, passed, message = results[0]
        assert inv_id == "BI-ONBOARD-001"
        assert passed is False
        assert "key_ready" in message

    def test_bi_onboard_001_rejects_missing_integration(self):
        """BI-ONBOARD-001: missing connector_validated predicate → FAIL."""
        from app.hoc.cus.hoc_spine.authority.business_invariants import (
            check_all_for_operation,
        )

        results = check_all_for_operation(
            "onboarding.activate",
            {
                "operation": "onboarding.activate",
                "predicates": {
                    "project_ready": True,
                    "key_ready": True,
                    "connector_validated": False,
                    "sdk_attested": True,
                },
            },
        )
        assert len(results) >= 1
        inv_id, passed, message = results[0]
        assert inv_id == "BI-ONBOARD-001"
        assert passed is False
        assert "connector_validated" in message

    def test_bi_onboard_001_rejects_missing_sdk_attestation(self):
        """BI-ONBOARD-001: missing sdk_attested predicate → FAIL."""
        from app.hoc.cus.hoc_spine.authority.business_invariants import (
            check_all_for_operation,
        )

        results = check_all_for_operation(
            "onboarding.activate",
            {
                "operation": "onboarding.activate",
                "predicates": {
                    "project_ready": True,
                    "key_ready": True,
                    "connector_validated": True,
                    "sdk_attested": False,
                },
            },
        )
        assert len(results) >= 1
        inv_id, passed, message = results[0]
        assert inv_id == "BI-ONBOARD-001"
        assert passed is False
        assert "sdk_attested" in message

    def test_bi_onboard_001_rejects_missing_project(self):
        """BI-ONBOARD-001: missing project_ready predicate → FAIL."""
        from app.hoc.cus.hoc_spine.authority.business_invariants import (
            check_all_for_operation,
        )

        results = check_all_for_operation(
            "onboarding.activate",
            {
                "operation": "onboarding.activate",
                "predicates": {
                    "project_ready": False,
                    "key_ready": True,
                    "connector_validated": True,
                    "sdk_attested": True,
                },
            },
        )
        assert len(results) >= 1
        inv_id, passed, message = results[0]
        assert inv_id == "BI-ONBOARD-001"
        assert passed is False
        assert "project_ready" in message

    def test_bi_onboard_001_rejects_all_missing(self):
        """BI-ONBOARD-001: all predicates false → FAIL with all listed."""
        from app.hoc.cus.hoc_spine.authority.business_invariants import (
            check_all_for_operation,
        )

        results = check_all_for_operation(
            "onboarding.activate",
            {
                "operation": "onboarding.activate",
                "predicates": {
                    "project_ready": False,
                    "key_ready": False,
                    "connector_validated": False,
                    "sdk_attested": False,
                },
            },
        )
        assert len(results) >= 1
        _, passed, message = results[0]
        assert passed is False
        # All 4 should be listed as unsatisfied
        for pred in ("project_ready", "key_ready", "connector_validated", "sdk_attested"):
            assert pred in message

    # --- Positive pass case ---

    def test_bi_onboard_001_passes_all_satisfied(self):
        """BI-ONBOARD-001: all predicates true → PASS."""
        from app.hoc.cus.hoc_spine.authority.business_invariants import (
            check_all_for_operation,
        )

        results = check_all_for_operation(
            "onboarding.activate",
            {
                "operation": "onboarding.activate",
                "predicates": {
                    "project_ready": True,
                    "key_ready": True,
                    "connector_validated": True,
                    "sdk_attested": True,
                },
            },
        )
        assert len(results) >= 1
        inv_id, passed, message = results[0]
        assert inv_id == "BI-ONBOARD-001"
        assert passed is True


# =============================================================================
# Activation predicate unit tests (onboarding_policy.check_activation_predicate)
# =============================================================================


class TestActivationPredicate:
    """Unit tests for the pure predicate function."""

    def test_all_satisfied_returns_pass(self):
        """All four predicates True → pass=True, missing=[]."""
        from app.hoc.cus.hoc_spine.authority.onboarding_policy import (
            check_activation_predicate,
        )

        passed, missing = check_activation_predicate(
            has_project=True,
            has_api_key=True,
            has_validated_connector=True,
            has_sdk_attestation=True,
        )
        assert passed is True
        assert missing == []

    def test_missing_api_key(self):
        """Missing API key → fail with key_ready in missing list."""
        from app.hoc.cus.hoc_spine.authority.onboarding_policy import (
            check_activation_predicate,
        )

        passed, missing = check_activation_predicate(
            has_project=True,
            has_api_key=False,
            has_validated_connector=True,
            has_sdk_attestation=True,
        )
        assert passed is False
        assert "key_ready" in missing

    def test_missing_connector(self):
        """Missing connector → fail with connector_validated in missing list."""
        from app.hoc.cus.hoc_spine.authority.onboarding_policy import (
            check_activation_predicate,
        )

        passed, missing = check_activation_predicate(
            has_project=True,
            has_api_key=True,
            has_validated_connector=False,
            has_sdk_attestation=True,
        )
        assert passed is False
        assert "connector_validated" in missing

    def test_missing_sdk_attestation(self):
        """Missing SDK attestation → fail with sdk_attested in missing list."""
        from app.hoc.cus.hoc_spine.authority.onboarding_policy import (
            check_activation_predicate,
        )

        passed, missing = check_activation_predicate(
            has_project=True,
            has_api_key=True,
            has_validated_connector=True,
            has_sdk_attestation=False,
        )
        assert passed is False
        assert "sdk_attested" in missing

    def test_all_missing(self):
        """All predicates False → fail with 4 items in missing list."""
        from app.hoc.cus.hoc_spine.authority.onboarding_policy import (
            check_activation_predicate,
        )

        passed, missing = check_activation_predicate(
            has_project=False,
            has_api_key=False,
            has_validated_connector=False,
            has_sdk_attestation=False,
        )
        assert passed is False
        assert len(missing) == 4


# =============================================================================
# ONBOARD-DELTA-01b: MONITOR / STRICT mode behavior
# =============================================================================


class TestOnboardingInvariantModes:
    """Prove MONITOR and STRICT modes behave correctly for BI-ONBOARD-001."""

    def test_monitor_mode_does_not_raise(self):
        """MONITOR mode: BI-ONBOARD-001 fails but no exception raised."""
        from app.hoc.cus.hoc_spine.authority.invariant_evaluator import (
            InvariantMode,
            evaluate_invariants,
        )

        results = evaluate_invariants(
            "onboarding.activate",
            {"operation": "onboarding.activate", "predicates": {}},
            InvariantMode.MONITOR,
        )
        assert len(results) >= 1
        assert results[0].passed is False
        # No exception raised — MONITOR is non-blocking

    def test_monitor_mode_returns_results(self):
        """MONITOR mode: returns results including failure details."""
        from app.hoc.cus.hoc_spine.authority.invariant_evaluator import (
            InvariantMode,
            evaluate_invariants,
        )

        results = evaluate_invariants(
            "onboarding.activate",
            {
                "operation": "onboarding.activate",
                "predicates": {"key_ready": False, "connector_validated": True,
                               "sdk_attested": True, "project_ready": True},
            },
            InvariantMode.MONITOR,
        )
        assert any(r.invariant_id == "BI-ONBOARD-001" and not r.passed for r in results)

    def test_strict_mode_raises_on_empty_predicates(self):
        """STRICT mode: BI-ONBOARD-001 with empty predicates → BusinessInvariantViolation."""
        from app.hoc.cus.hoc_spine.authority.business_invariants import (
            BusinessInvariantViolation,
        )
        from app.hoc.cus.hoc_spine.authority.invariant_evaluator import (
            InvariantMode,
            evaluate_invariants,
        )

        with pytest.raises(BusinessInvariantViolation) as exc_info:
            evaluate_invariants(
                "onboarding.activate",
                {"operation": "onboarding.activate", "predicates": {}},
                InvariantMode.STRICT,
            )
        assert "BI-ONBOARD-001" in exc_info.value.invariant_id

    def test_strict_mode_raises_on_partial_predicates(self):
        """STRICT mode: BI-ONBOARD-001 with one missing → BusinessInvariantViolation."""
        from app.hoc.cus.hoc_spine.authority.business_invariants import (
            BusinessInvariantViolation,
        )
        from app.hoc.cus.hoc_spine.authority.invariant_evaluator import (
            InvariantMode,
            evaluate_invariants,
        )

        with pytest.raises(BusinessInvariantViolation) as exc_info:
            evaluate_invariants(
                "onboarding.activate",
                {
                    "operation": "onboarding.activate",
                    "predicates": {
                        "project_ready": True,
                        "key_ready": True,
                        "connector_validated": False,
                        "sdk_attested": True,
                    },
                },
                InvariantMode.STRICT,
            )
        assert "BI-ONBOARD-001" in exc_info.value.invariant_id

    def test_strict_mode_passes_all_satisfied(self):
        """STRICT mode: all predicates satisfied → no exception."""
        from app.hoc.cus.hoc_spine.authority.invariant_evaluator import (
            InvariantMode,
            evaluate_invariants,
        )

        results = evaluate_invariants(
            "onboarding.activate",
            {
                "operation": "onboarding.activate",
                "predicates": {
                    "project_ready": True,
                    "key_ready": True,
                    "connector_validated": True,
                    "sdk_attested": True,
                },
            },
            InvariantMode.STRICT,
        )
        assert all(r.passed for r in results)


# =============================================================================
# ONBOARD-DELTA-02: Real OperationRegistry dispatch proof
# =============================================================================


class TestOnboardingRegistryDispatch:
    """Prove onboarding operations dispatch through real OperationRegistry."""

    @pytest.fixture
    def registry_with_onboarding_handlers(self):
        """Create a fresh OperationRegistry with mock onboarding handlers."""
        from app.hoc.cus.hoc_spine.orchestrator.operation_registry import (
            OperationRegistry,
            OperationResult,
        )

        registry = OperationRegistry()

        query_handler = MagicMock()
        query_handler.execute = AsyncMock(
            return_value=OperationResult.ok({
                "tenant_id": "t-onboard-001",
                "state_value": 3,
                "state_name": "SDK_CONNECTED",
                "is_complete": False,
            })
        )
        registry.register("account.onboarding.query", query_handler)

        advance_handler = MagicMock()
        advance_handler.execute = AsyncMock(
            return_value=OperationResult.ok({
                "success": True,
                "from_state": "SDK_CONNECTED",
                "to_state": "COMPLETE",
                "trigger": "auto_promotion",
                "message": "ok",
                "was_no_op": False,
            })
        )
        registry.register("account.onboarding.advance", advance_handler)

        return registry, query_handler, advance_handler

    @pytest.mark.asyncio
    async def test_onboarding_query_dispatch(self, registry_with_onboarding_handlers):
        """account.onboarding.query dispatches and returns state snapshot."""
        from app.hoc.cus.hoc_spine.orchestrator.operation_registry import (
            OperationContext,
        )

        registry, query_handler, _ = registry_with_onboarding_handlers

        ctx = OperationContext(
            session=None,
            tenant_id="t-onboard-001",
            params={},
        )
        result = await registry.execute("account.onboarding.query", ctx)
        assert result.success is True
        assert result.data["state_name"] == "SDK_CONNECTED"
        assert query_handler.execute.called

    @pytest.mark.asyncio
    async def test_onboarding_advance_dispatch(self, registry_with_onboarding_handlers):
        """account.onboarding.advance dispatches and returns transition result."""
        from app.hoc.cus.hoc_spine.orchestrator.operation_registry import (
            OperationContext,
        )

        registry, _, advance_handler = registry_with_onboarding_handlers

        ctx = OperationContext(
            session=None,
            tenant_id="t-onboard-001",
            params={
                "sync_session": MagicMock(),
                "target_state": 4,
                "trigger": "auto_promotion",
            },
        )
        result = await registry.execute("account.onboarding.advance", ctx)
        assert result.success is True
        assert result.data["to_state"] == "COMPLETE"
        assert advance_handler.execute.called

    @pytest.mark.asyncio
    async def test_onboarding_monitor_mode_allows_bad_predicates(
        self, registry_with_onboarding_handlers
    ):
        """In MONITOR mode, bad predicates log but don't block dispatch."""
        from app.hoc.cus.hoc_spine.authority.invariant_evaluator import InvariantMode
        from app.hoc.cus.hoc_spine.orchestrator.operation_registry import (
            OperationContext,
        )

        registry, _, advance_handler = registry_with_onboarding_handlers
        registry.set_invariant_mode(InvariantMode.MONITOR)

        ctx = OperationContext(
            session=None,
            tenant_id="t-onboard-001",
            params={
                "sync_session": MagicMock(),
                "target_state": 4,
                "trigger": "auto_promotion",
                "predicates": {},  # Empty — BI-ONBOARD-001 fails
            },
        )
        result = await registry.execute("account.onboarding.advance", ctx)
        assert result.success is True  # MONITOR doesn't block
        assert advance_handler.execute.called

    @pytest.mark.asyncio
    async def test_onboarding_unregistered_operation_fails(
        self, registry_with_onboarding_handlers
    ):
        """Unregistered operation name → OperationResult.fail."""
        from app.hoc.cus.hoc_spine.orchestrator.operation_registry import (
            OperationContext,
        )

        registry, _, _ = registry_with_onboarding_handlers

        ctx = OperationContext(
            session=None,
            tenant_id="t-onboard-001",
            params={},
        )
        result = await registry.execute("account.onboarding.nonexistent", ctx)
        assert result.success is False

    @pytest.mark.asyncio
    async def test_real_handler_registration_exists(self):
        """Verify account.onboarding.* operations register on a real registry."""
        from app.hoc.cus.hoc_spine.orchestrator.operation_registry import (
            OperationRegistry,
        )
        from app.hoc.cus.hoc_spine.orchestrator.handlers.onboarding_handler import (
            register,
        )

        registry = OperationRegistry()
        register(registry)

        assert "account.onboarding.query" in registry._handlers
        assert "account.onboarding.advance" in registry._handlers


# =============================================================================
# ONBOARD-DELTA-03: Invariant alias enforcement on real dispatch op
# =============================================================================


class TestOnboardingInvariantAlias:
    """Prove BI-ONBOARD-001 fires for the real dispatch op account.onboarding.advance."""

    def test_alias_mapping_exists(self):
        """INVARIANT_OPERATION_ALIASES maps account.onboarding.advance → onboarding.activate."""
        from app.hoc.cus.hoc_spine.authority.business_invariants import (
            INVARIANT_OPERATION_ALIASES,
        )

        assert INVARIANT_OPERATION_ALIASES.get("account.onboarding.advance") == "onboarding.activate"

    def test_check_all_resolves_alias_for_advance(self):
        """check_all_for_operation('account.onboarding.advance') finds BI-ONBOARD-001."""
        from app.hoc.cus.hoc_spine.authority.business_invariants import (
            check_all_for_operation,
        )

        results = check_all_for_operation(
            "account.onboarding.advance",
            {"operation": "account.onboarding.advance", "predicates": {}},
        )
        assert len(results) >= 1
        inv_ids = [r[0] for r in results]
        assert "BI-ONBOARD-001" in inv_ids

    def test_query_does_not_trigger_onboarding_invariant(self):
        """account.onboarding.query must NOT trigger BI-ONBOARD-001."""
        from app.hoc.cus.hoc_spine.authority.business_invariants import (
            check_all_for_operation,
        )

        results = check_all_for_operation(
            "account.onboarding.query",
            {"operation": "account.onboarding.query"},
        )
        inv_ids = [r[0] for r in results]
        assert "BI-ONBOARD-001" not in inv_ids

    def test_strict_mode_blocks_advance_with_bad_predicates(self):
        """STRICT mode: account.onboarding.advance with empty predicates → BusinessInvariantViolation."""
        from app.hoc.cus.hoc_spine.authority.business_invariants import (
            BusinessInvariantViolation,
        )
        from app.hoc.cus.hoc_spine.authority.invariant_evaluator import (
            InvariantMode,
            evaluate_invariants,
        )

        with pytest.raises(BusinessInvariantViolation) as exc_info:
            evaluate_invariants(
                "account.onboarding.advance",
                {"operation": "account.onboarding.advance", "predicates": {}},
                InvariantMode.STRICT,
            )
        assert "BI-ONBOARD-001" in exc_info.value.invariant_id

    def test_monitor_mode_allows_advance_with_bad_predicates(self):
        """MONITOR mode: account.onboarding.advance with empty predicates → no exception."""
        from app.hoc.cus.hoc_spine.authority.invariant_evaluator import (
            InvariantMode,
            evaluate_invariants,
        )

        results = evaluate_invariants(
            "account.onboarding.advance",
            {"operation": "account.onboarding.advance", "predicates": {}},
            InvariantMode.MONITOR,
        )
        assert any(r.invariant_id == "BI-ONBOARD-001" and not r.passed for r in results)

    @pytest.mark.asyncio
    async def test_registry_execute_strict_blocks_advance(self):
        """Real OperationRegistry.execute in STRICT mode blocks account.onboarding.advance."""
        from app.hoc.cus.hoc_spine.authority.business_invariants import (
            BusinessInvariantViolation,
        )
        from app.hoc.cus.hoc_spine.authority.invariant_evaluator import InvariantMode
        from app.hoc.cus.hoc_spine.orchestrator.operation_registry import (
            OperationContext,
            OperationRegistry,
            OperationResult,
        )

        registry = OperationRegistry()
        registry.set_invariant_mode(InvariantMode.STRICT)

        handler = MagicMock()
        handler.execute = AsyncMock(return_value=OperationResult.ok({"ok": True}))
        registry.register("account.onboarding.advance", handler)

        ctx = OperationContext(
            session=None,
            tenant_id="t-alias-001",
            params={"predicates": {}},  # Empty → BI-ONBOARD-001 FAIL
        )

        # STRICT + alias → BusinessInvariantViolation before handler runs
        with pytest.raises(BusinessInvariantViolation) as exc_info:
            await registry.execute("account.onboarding.advance", ctx)

        assert "BI-ONBOARD-001" in exc_info.value.invariant_id
        # Handler must NOT have been called — invariant blocked pre-dispatch
        assert not handler.execute.called

    @pytest.mark.asyncio
    async def test_registry_execute_monitor_allows_advance(self):
        """Real OperationRegistry.execute in MONITOR mode allows account.onboarding.advance."""
        from app.hoc.cus.hoc_spine.authority.invariant_evaluator import InvariantMode
        from app.hoc.cus.hoc_spine.orchestrator.operation_registry import (
            OperationContext,
            OperationRegistry,
            OperationResult,
        )

        registry = OperationRegistry()
        registry.set_invariant_mode(InvariantMode.MONITOR)

        handler = MagicMock()
        handler.execute = AsyncMock(return_value=OperationResult.ok({"ok": True}))
        registry.register("account.onboarding.advance", handler)

        ctx = OperationContext(
            session=None,
            tenant_id="t-alias-002",
            params={"predicates": {}},  # Empty → BI-ONBOARD-001 fails but MONITOR allows
        )

        result = await registry.execute("account.onboarding.advance", ctx)
        assert result.success is True
        assert handler.execute.called
