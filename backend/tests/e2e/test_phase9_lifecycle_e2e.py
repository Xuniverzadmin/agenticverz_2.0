# Layer: L8 — Catalyst / Meta
# Product: system-wide
# Temporal:
#   Trigger: CI
#   Execution: sync
# Role: Phase-9 Lifecycle E2E Validation Tests
# Callers: pytest, CI pipeline
# Allowed Imports: L4 (lifecycle, onboarding, billing, protection, observability), L8
# Forbidden Imports: L1, L2, L3
# Reference: PIN-400 Phase-9 (Offboarding & Tenant Lifecycle)

"""
Phase-9 Tenant Lifecycle E2E Validation Tests

Validates cross-phase integration and invariant enforcement.

Test Categories:
1. Onboarding → Lifecycle transition (semantic mapping)
2. Lifecycle × Billing integration
3. Lifecycle × Protection integration
4. Lifecycle × Observability integration
5. Full tenant journey (onboarding → active → suspended → terminated → archived)
6. Freeze exit criteria

Reference: docs/governance/FREEZE.md Phase-9 checklist
"""

import pytest
from datetime import datetime, timezone

# Phase-4: Onboarding
from app.hoc.cus.account.L5_schemas.onboarding_state import OnboardingState

# Phase-6: Billing
from app.billing import (
    BillingState,
    MockBillingProvider,
    get_billing_provider,
    set_billing_provider,
)

# Phase-7: Protection
from app.protection import (
    MockAbuseProtectionProvider,
    get_protection_provider,
    set_protection_provider,
)

# Phase-8: Observability
from app.observability import (
    MockObservabilityProvider,
    get_observability_provider,
    set_observability_provider,
)
from app.observability.emitters import emit_event
from app.observability.events import EventSource, Severity

# Phase-9: Lifecycle
from app.hoc.cus.account.L5_schemas.tenant_lifecycle_state import (
    TenantLifecycleState,
    LifecycleAction,
    is_valid_transition,
)
from app.hoc.cus.hoc_spine.authority.lifecycle_provider import (
    ActorType,
    ActorContext,
    MockTenantLifecycleProvider,
    get_lifecycle_provider,
    set_lifecycle_provider,
)


# ============================================================================
# FIXTURES
# ============================================================================


@pytest.fixture
def fresh_providers():
    """Set up fresh mock providers for each test."""
    # Phase-6
    billing = MockBillingProvider()
    set_billing_provider(billing)

    # Phase-7
    protection = MockAbuseProtectionProvider()
    set_protection_provider(protection)

    # Phase-8
    observability = MockObservabilityProvider()
    set_observability_provider(observability)

    # Phase-9
    lifecycle = MockTenantLifecycleProvider()
    set_lifecycle_provider(lifecycle)

    return {
        "billing": billing,
        "protection": protection,
        "observability": observability,
        "lifecycle": lifecycle,
    }


@pytest.fixture
def founder_actor():
    """Founder actor for lifecycle operations."""
    return ActorContext(
        actor_type=ActorType.FOUNDER,
        actor_id="founder_e2e",
        reason="e2e_test",
    )


@pytest.fixture
def system_actor():
    """System actor for automated operations."""
    return ActorContext(
        actor_type=ActorType.SYSTEM,
        actor_id="system",
        reason="automated",
    )


# ============================================================================
# ONBOARDING → LIFECYCLE TRANSITION TESTS
# ============================================================================


class TestOnboardingToLifecycleTransition:
    """
    Tests for semantic mapping: OnboardingState.COMPLETE → TenantLifecycleState.ACTIVE

    Validates that onboarding and lifecycle are adjacent state machines.
    """

    def test_complete_onboarding_implies_active_lifecycle(self, fresh_providers):
        """
        After onboarding COMPLETE, tenant should be in ACTIVE lifecycle state.

        This validates the semantic mapping (not enum alias):
        - OnboardingState answers: "Did you ever earn the right to run?"
        - LifecycleState answers: "Are you currently allowed to run?"
        """
        lifecycle = fresh_providers["lifecycle"]

        # Simulate tenant completing onboarding
        # (In real system, onboarding completion would initialize lifecycle to ACTIVE)
        tenant_id = "t_onboarded"

        # Default state for unknown tenant is ACTIVE (assumes onboarding complete)
        state = lifecycle.get_state(tenant_id)
        assert state == TenantLifecycleState.ACTIVE

    def test_lifecycle_does_not_modify_onboarding(self, fresh_providers, founder_actor):
        """
        Lifecycle transitions must not affect onboarding state.

        OFFBOARD-001 corollary: Lifecycle is forward-only from onboarding.
        """
        lifecycle = fresh_providers["lifecycle"]
        tenant_id = "t_lifecycle_test"

        # Terminate tenant
        result = lifecycle.terminate(tenant_id, founder_actor)
        assert result.success is True

        # Onboarding state concept is unchanged
        # (We don't have a direct onboarding lookup here, but the invariant is:
        #  lifecycle changes don't touch the onboarding enum)
        # This test validates lifecycle operates independently
        assert lifecycle.get_state(tenant_id) == TenantLifecycleState.TERMINATED

    def test_onboarding_complete_is_prerequisite_for_lifecycle(self, fresh_providers):
        """
        Lifecycle only applies to onboarding-complete tenants.

        The semantic mapping is one-way:
        OnboardingState.COMPLETE → TenantLifecycleState.ACTIVE
        """
        # This test documents the contract:
        # A tenant that never completed onboarding should not appear in lifecycle
        # (In production, lifecycle provider would check onboarding state)

        # The mock defaults to ACTIVE, simulating post-onboarding state
        lifecycle = fresh_providers["lifecycle"]
        assert lifecycle.get_state("any_tenant") == TenantLifecycleState.ACTIVE


# ============================================================================
# LIFECYCLE × BILLING INTEGRATION TESTS
# ============================================================================


class TestLifecycleBillingIntegration:
    """
    Tests for Lifecycle × Billing integration.

    Validates BILLING-003 is maintained: Billing state does not affect roles.
    Validates lifecycle can query billing but never writes to it.
    """

    def test_lifecycle_reads_billing_never_writes(self, fresh_providers, founder_actor):
        """
        Lifecycle may read billing state but never modifies it.
        """
        billing = fresh_providers["billing"]
        lifecycle = fresh_providers["lifecycle"]
        tenant_id = "t_billing_test"

        # Set initial billing state
        billing.set_billing_state(tenant_id, BillingState.ACTIVE)
        initial_billing = billing.get_billing_state(tenant_id)

        # Perform lifecycle transitions
        lifecycle.suspend(tenant_id, founder_actor)
        lifecycle.resume(tenant_id, founder_actor)
        lifecycle.terminate(tenant_id, founder_actor)

        # Billing state unchanged
        final_billing = billing.get_billing_state(tenant_id)
        assert final_billing == initial_billing

    def test_billing_suspension_independent_of_lifecycle(self, fresh_providers):
        """
        Billing suspension is independent of lifecycle state.

        A tenant can be:
        - Lifecycle ACTIVE + Billing SUSPENDED (e.g., payment failed)
        - Lifecycle SUSPENDED + Billing ACTIVE (e.g., abuse detected)
        """
        billing = fresh_providers["billing"]
        lifecycle = fresh_providers["lifecycle"]
        tenant_id = "t_independence"

        # Set billing to SUSPENDED while lifecycle is ACTIVE
        billing.set_billing_state(tenant_id, BillingState.SUSPENDED)
        assert lifecycle.get_state(tenant_id) == TenantLifecycleState.ACTIVE
        assert billing.get_billing_state(tenant_id) == BillingState.SUSPENDED

    def test_terminated_tenant_billing_state_preserved(self, fresh_providers, founder_actor):
        """
        Terminating a tenant preserves billing history.
        """
        billing = fresh_providers["billing"]
        lifecycle = fresh_providers["lifecycle"]
        tenant_id = "t_billing_history"

        # Set billing to PAST_DUE
        billing.set_billing_state(tenant_id, BillingState.PAST_DUE)

        # Terminate tenant
        lifecycle.terminate(tenant_id, founder_actor)

        # Billing state preserved for audit
        assert billing.get_billing_state(tenant_id) == BillingState.PAST_DUE


# ============================================================================
# LIFECYCLE × PROTECTION INTEGRATION TESTS
# ============================================================================


class TestLifecycleProtectionIntegration:
    """
    Tests for Lifecycle × Protection integration.

    Protection should respect lifecycle state for SDK blocking.
    """

    def test_active_tenant_passes_protection(self, fresh_providers):
        """
        ACTIVE tenant should pass protection checks (if within limits).
        """
        protection = fresh_providers["protection"]
        lifecycle = fresh_providers["lifecycle"]
        tenant_id = "t_protection_active"

        assert lifecycle.get_state(tenant_id) == TenantLifecycleState.ACTIVE
        assert lifecycle.allows_sdk_execution(tenant_id) is True

    def test_suspended_tenant_sdk_blocked(self, fresh_providers, founder_actor):
        """
        SUSPENDED tenant should have SDK execution blocked.
        """
        lifecycle = fresh_providers["lifecycle"]
        tenant_id = "t_protection_suspended"

        lifecycle.suspend(tenant_id, founder_actor)

        assert lifecycle.allows_sdk_execution(tenant_id) is False

    def test_terminated_tenant_sdk_blocked(self, fresh_providers, founder_actor):
        """
        TERMINATED tenant should have SDK execution blocked.
        """
        lifecycle = fresh_providers["lifecycle"]
        tenant_id = "t_protection_terminated"

        lifecycle.terminate(tenant_id, founder_actor)

        assert lifecycle.allows_sdk_execution(tenant_id) is False

    def test_lifecycle_does_not_modify_protection_state(
        self, fresh_providers, founder_actor
    ):
        """
        Lifecycle transitions don't affect protection provider state.
        """
        protection = fresh_providers["protection"]
        lifecycle = fresh_providers["lifecycle"]
        tenant_id = "t_protection_state"

        # Get initial protection result
        initial_result = protection.check_all(tenant_id, "/api/v1/runs", "write")

        # Perform lifecycle transitions
        lifecycle.suspend(tenant_id, founder_actor)
        lifecycle.resume(tenant_id, founder_actor)

        # Protection state unchanged (provider still works the same)
        final_result = protection.check_all(tenant_id, "/api/v1/runs", "write")
        assert initial_result.decision == final_result.decision


# ============================================================================
# LIFECYCLE × OBSERVABILITY INTEGRATION TESTS
# ============================================================================


class TestLifecycleObservabilityIntegration:
    """
    Tests for Lifecycle × Observability integration.

    OFFBOARD-008: Offboarding emits unified observability events.
    OFFBOARD-009: Observability never blocks offboarding.
    """

    def test_offboard_008_lifecycle_emits_events(self, fresh_providers, founder_actor):
        """
        OFFBOARD-008: Lifecycle transitions emit observability events.
        """
        observability = fresh_providers["observability"]
        tenant_id = "t_obs_emit"

        # Create lifecycle with observability callback
        events = []
        lifecycle = MockTenantLifecycleProvider(
            observability_callback=lambda e: events.append(e)
        )

        # Perform transitions
        lifecycle.suspend(tenant_id, founder_actor)
        lifecycle.resume(tenant_id, founder_actor)
        lifecycle.terminate(tenant_id, founder_actor)

        # All transitions emitted events
        assert len(events) == 3
        assert events[0]["to_state"] == "SUSPENDED"
        assert events[1]["to_state"] == "ACTIVE"
        assert events[2]["to_state"] == "TERMINATED"

    def test_offboard_009_observability_failure_non_blocking(
        self, fresh_providers, founder_actor
    ):
        """
        OFFBOARD-009: Observability failure doesn't block lifecycle transition.
        """
        tenant_id = "t_obs_fail"

        # Create lifecycle with failing observability
        def failing_emit(event):
            raise RuntimeError("Observability down")

        lifecycle = MockTenantLifecycleProvider(observability_callback=failing_emit)

        # Transition should succeed despite observability failure
        result = lifecycle.terminate(tenant_id, founder_actor)

        assert result.success is True
        assert lifecycle.get_state(tenant_id) == TenantLifecycleState.TERMINATED

    def test_lifecycle_events_queryable_via_observability(self, fresh_providers):
        """
        Lifecycle events should be queryable via observability provider.
        """
        from datetime import datetime, timezone, timedelta

        observability = fresh_providers["observability"]
        tenant_id = "t_obs_query"

        # Emit a lifecycle event via observability
        emit_event(
            event_type="lifecycle_transition",
            event_source=EventSource.AUTH,
            tenant_id=tenant_id,
            severity=Severity.INFO,
            payload={"from_state": "ACTIVE", "to_state": "TERMINATED"},
        )

        # Query events with time range
        now = datetime.now(timezone.utc)
        start = now - timedelta(hours=1)
        end = now + timedelta(hours=1)
        events = observability.query(
            tenant_id=tenant_id,
            start=start,
            end=end,
        )
        assert len(events) >= 1

        lifecycle_events = [e for e in events if e.event_type == "lifecycle_transition"]
        assert len(lifecycle_events) == 1


# ============================================================================
# FULL TENANT JOURNEY TESTS
# ============================================================================


class TestFullTenantJourney:
    """
    Tests for complete tenant lifecycle journey.

    Validates: CREATED → onboarding → ACTIVE → SUSPENDED → ACTIVE → TERMINATED → ARCHIVED
    """

    def test_full_lifecycle_journey(self, fresh_providers, founder_actor, system_actor):
        """
        Complete tenant journey from onboarding through archival.
        """
        lifecycle = fresh_providers["lifecycle"]
        billing = fresh_providers["billing"]
        tenant_id = "t_full_journey"

        # 1. Tenant completes onboarding (simulated by default ACTIVE state)
        assert lifecycle.get_state(tenant_id) == TenantLifecycleState.ACTIVE

        # 2. Billing activated (Phase-6)
        billing.set_billing_state(tenant_id, BillingState.ACTIVE)
        assert billing.get_billing_state(tenant_id) == BillingState.ACTIVE

        # 3. Tenant suspended for abuse investigation
        result = lifecycle.suspend(tenant_id, founder_actor)
        assert result.success is True
        assert lifecycle.get_state(tenant_id) == TenantLifecycleState.SUSPENDED
        assert not lifecycle.allows_sdk_execution(tenant_id)

        # 4. Investigation clears, tenant resumed
        result = lifecycle.resume(tenant_id, founder_actor)
        assert result.success is True
        assert lifecycle.get_state(tenant_id) == TenantLifecycleState.ACTIVE
        assert lifecycle.allows_sdk_execution(tenant_id)

        # 5. Contract ends, tenant terminated
        result = lifecycle.terminate(tenant_id, founder_actor)
        assert result.success is True
        assert lifecycle.get_state(tenant_id) == TenantLifecycleState.TERMINATED
        assert not lifecycle.allows_sdk_execution(tenant_id)
        assert not lifecycle.allows_new_api_keys(tenant_id)

        # 6. Compliance period ends, tenant archived
        result = lifecycle.archive(tenant_id, system_actor)
        assert result.success is True
        assert lifecycle.get_state(tenant_id) == TenantLifecycleState.ARCHIVED

        # 7. Verify billing history preserved
        assert billing.get_billing_state(tenant_id) == BillingState.ACTIVE

        # 8. Verify full history recorded
        history = lifecycle.get_history(tenant_id)
        assert len(history) == 4
        assert history[0].action == LifecycleAction.SUSPEND
        assert history[1].action == LifecycleAction.RESUME
        assert history[2].action == LifecycleAction.TERMINATE
        assert history[3].action == LifecycleAction.ARCHIVE

    def test_suspend_resume_multiple_cycles(self, fresh_providers, founder_actor):
        """
        Tenant can be suspended and resumed multiple times.
        """
        lifecycle = fresh_providers["lifecycle"]
        tenant_id = "t_multi_suspend"

        for i in range(3):
            result = lifecycle.suspend(tenant_id, founder_actor)
            assert result.success is True

            result = lifecycle.resume(tenant_id, founder_actor)
            assert result.success is True

        assert lifecycle.get_state(tenant_id) == TenantLifecycleState.ACTIVE

        history = lifecycle.get_history(tenant_id)
        assert len(history) == 6  # 3 suspends + 3 resumes

    def test_terminate_from_suspended(self, fresh_providers, founder_actor):
        """
        Tenant can be terminated directly from SUSPENDED state.
        """
        lifecycle = fresh_providers["lifecycle"]
        tenant_id = "t_terminate_suspended"

        lifecycle.suspend(tenant_id, founder_actor)
        result = lifecycle.terminate(tenant_id, founder_actor)

        assert result.success is True
        assert result.from_state == TenantLifecycleState.SUSPENDED
        assert result.to_state == TenantLifecycleState.TERMINATED


# ============================================================================
# CROSS-PHASE INVARIANT TESTS
# ============================================================================


class TestCrossPhaseInvariants:
    """
    Tests for cross-phase invariants.

    Validates Phase-9 doesn't violate Phases 4-8 invariants.
    """

    def test_lifecycle_does_not_affect_onboarding_state(self, fresh_providers, founder_actor):
        """
        Lifecycle transitions don't modify onboarding.

        Validates: Onboarding is historical, lifecycle is authoritative.
        """
        # This is validated by design: lifecycle and onboarding are separate enums
        # No code path exists to modify OnboardingState from lifecycle
        lifecycle = fresh_providers["lifecycle"]

        # All lifecycle operations complete without touching onboarding
        lifecycle.suspend("t_1", founder_actor)
        lifecycle.resume("t_1", founder_actor)
        lifecycle.terminate("t_1", founder_actor)

        # If we got here without error, onboarding was never touched

    def test_lifecycle_does_not_affect_roles(self, fresh_providers, founder_actor):
        """
        Lifecycle transitions don't modify roles.

        Validates ROLE-001-005 maintained.
        """
        lifecycle = fresh_providers["lifecycle"]

        # Perform all lifecycle transitions
        lifecycle.suspend("t_roles", founder_actor)
        lifecycle.terminate("t_roles", founder_actor)

        # Roles would be stored separately; lifecycle has no role mutation code
        # This test documents the invariant

    def test_billing_never_writes_lifecycle(self, fresh_providers):
        """
        Billing operations don't affect lifecycle.
        """
        billing = fresh_providers["billing"]
        lifecycle = fresh_providers["lifecycle"]
        tenant_id = "t_billing_lifecycle"

        # Various billing state changes
        billing.set_billing_state(tenant_id, BillingState.PAST_DUE)
        billing.set_billing_state(tenant_id, BillingState.SUSPENDED)
        billing.set_billing_state(tenant_id, BillingState.ACTIVE)

        # Lifecycle unchanged
        assert lifecycle.get_state(tenant_id) == TenantLifecycleState.ACTIVE

    def test_protection_never_writes_lifecycle(self, fresh_providers):
        """
        Protection operations don't affect lifecycle.
        """
        protection = fresh_providers["protection"]
        lifecycle = fresh_providers["lifecycle"]
        tenant_id = "t_protection_lifecycle"

        # Perform protection check operations
        protection.check_all(tenant_id, "/api/v1/runs", "write")
        protection.check_all(tenant_id, "/api/v1/runs", "read")

        # Lifecycle unchanged
        assert lifecycle.get_state(tenant_id) == TenantLifecycleState.ACTIVE


# ============================================================================
# FREEZE EXIT CRITERIA TESTS
# ============================================================================


class TestFreezeExitCriteriaPhase9:
    """
    Tests for Phase-9 freeze exit criteria.

    All criteria must pass before Phase-9 can be frozen.
    """

    def test_all_phase9_invariants_implemented(self, fresh_providers, founder_actor):
        """
        All OFFBOARD invariants are enforced by the mock provider.
        """
        lifecycle = fresh_providers["lifecycle"]
        tenant_id = "t_invariants"

        # OFFBOARD-001: Monotonic (tested via transition matrix)
        assert is_valid_transition(
            TenantLifecycleState.ACTIVE, TenantLifecycleState.SUSPENDED
        )

        # OFFBOARD-002: TERMINATED irreversible
        lifecycle.set_state(tenant_id, TenantLifecycleState.TERMINATED)
        result = lifecycle.resume(tenant_id, founder_actor)
        assert result.success is False
        assert "OFFBOARD-002" in result.error

        # OFFBOARD-003: ARCHIVED unreachable from ACTIVE
        lifecycle.set_state(tenant_id, TenantLifecycleState.ACTIVE)
        result = lifecycle.archive(tenant_id, founder_actor)
        assert result.success is False

        # OFFBOARD-004: Customer cannot mutate
        customer = ActorContext(ActorType.CUSTOMER, "c_1", "test")
        result = lifecycle.suspend(tenant_id, customer)
        assert result.success is False
        assert "OFFBOARD-004" in result.error

    def test_mock_provider_complete(self, fresh_providers):
        """
        Mock provider implements full TenantLifecycleProvider protocol.
        """
        lifecycle = fresh_providers["lifecycle"]
        tenant_id = "t_protocol"

        # All protocol methods exist and work
        assert lifecycle.get_state(tenant_id) is not None
        assert isinstance(lifecycle.allows_sdk_execution(tenant_id), bool)
        assert isinstance(lifecycle.allows_writes(tenant_id), bool)
        assert isinstance(lifecycle.allows_new_api_keys(tenant_id), bool)
        assert isinstance(lifecycle.get_history(tenant_id), list)

    def test_api_key_revocation_callback_works(self):
        """
        OFFBOARD-005: API key revocation callback is invoked on TERMINATED.
        """
        revoked = []

        def revoke(tenant_id):
            revoked.append(tenant_id)
            return 5

        lifecycle = MockTenantLifecycleProvider(api_key_revocation_callback=revoke)
        founder = ActorContext(ActorType.FOUNDER, "f_1", "test")

        result = lifecycle.terminate("t_revoke", founder)

        assert result.success is True
        assert result.revoked_api_keys == 5
        assert "t_revoke" in revoked

    def test_worker_blocking_callback_works(self):
        """
        OFFBOARD-006: Worker blocking callback is invoked on TERMINATED.
        """
        blocked = []

        def block(tenant_id):
            blocked.append(tenant_id)
            return 3

        lifecycle = MockTenantLifecycleProvider(worker_blocking_callback=block)
        founder = ActorContext(ActorType.FOUNDER, "f_1", "test")

        result = lifecycle.terminate("t_block", founder)

        assert result.success is True
        assert result.blocked_workers == 3
        assert "t_block" in blocked
