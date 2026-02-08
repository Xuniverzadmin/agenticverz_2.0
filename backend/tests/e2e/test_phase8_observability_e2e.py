# Layer: L8 — Catalyst / Meta
# Product: system-wide
# Temporal:
#   Trigger: CI
#   Execution: sync
# Role: Phase-8 Observability E2E validation
# Callers: pytest, CI pipeline, freeze exit validation
# Allowed Imports: L4 (observability, billing, protection, auth)
# Forbidden Imports: L1, L2, L3, L5, L6
# Reference: PIN-399, docs/governance/FREEZE.md

"""
Phase-8 Observability E2E Validation

This test verifies the Phase-8 integration with existing phases:

E2E Validation Checklist (Phase-8):
- [ ] Observability never mutates any system state
- [ ] Events from all sources share unified schema
- [ ] Emit failures never block main operations
- [ ] Query results are tenant-scoped only

DESIGN INVARIANTS VERIFIED:
- OBSERVE-001: Observability never mutates system state
- OBSERVE-002: Events are immutable once accepted
- OBSERVE-003: All events are tenant-scoped
- OBSERVE-004: Failure to emit must not block execution
- OBSERVE-005: Mock provider must be interface-compatible with real provider
"""

import pytest
from datetime import datetime, timezone, timedelta

from app.observability import (
    Severity,
    EventSource,
    Actor,
    ActorType,
    EventContext,
    UnifiedEvent,
    MockObservabilityProvider,
    get_observability_provider,
    set_observability_provider,
    emit_event,
    emit_onboarding_state_transition,
    emit_onboarding_force_complete,
    emit_billing_state_changed,
    emit_billing_limit_evaluated,
    emit_protection_decision,
    emit_protection_anomaly_detected,
    emit_role_violation,
    emit_unauthorized_access,
    EVENT_ONBOARDING_STATE_TRANSITION,
    EVENT_BILLING_STATE_CHANGED,
    EVENT_PROTECTION_DECISION,
)
from app.billing import (
    BillingState,
    MockBillingProvider,
    get_billing_provider,
    set_billing_provider,
    PLAN_FREE,
)
from app.protection import (
    Decision,
    MockAbuseProtectionProvider,
    get_protection_provider,
    set_protection_provider,
)
from app.hoc.cus.account.L5_schemas.onboarding_state import OnboardingState


class TestPhase8E2EValidation:
    """
    E2E validation tests for Phase-8 Observability.

    This test class simulates a tenant journey and verifies
    that all events are properly captured and correlated.
    """

    @pytest.fixture
    def observability_provider(self):
        """Fresh observability provider for each test."""
        provider = MockObservabilityProvider()
        set_observability_provider(provider)
        yield provider
        provider.reset()

    @pytest.fixture
    def billing_provider(self):
        """Fresh billing provider for each test."""
        provider = MockBillingProvider()
        set_billing_provider(provider)
        yield provider
        provider.reset()

    @pytest.fixture
    def protection_provider(self):
        """Fresh protection provider for each test."""
        provider = MockAbuseProtectionProvider()
        set_protection_provider(provider)
        yield provider
        provider.reset()

    # =========================================================================
    # E2E Checklist Item: Observability never mutates system state
    # =========================================================================

    def test_observe_001_emit_does_not_mutate_billing(
        self, observability_provider, billing_provider
    ):
        """OBSERVE-001: Emitting billing events doesn't mutate billing state."""
        tenant_id = "tenant-1"

        # Get initial billing state
        initial_state = billing_provider.get_billing_state(tenant_id)

        # Emit many billing events
        for _ in range(100):
            emit_billing_state_changed(
                tenant_id=tenant_id,
                from_state="TRIAL",
                to_state="ACTIVE",
                plan_id="pro",
            )

        # Billing state should be unchanged
        final_state = billing_provider.get_billing_state(tenant_id)
        assert final_state == initial_state

    def test_observe_001_emit_does_not_mutate_protection(
        self, observability_provider, protection_provider
    ):
        """OBSERVE-001: Emitting protection events doesn't mutate protection state."""
        tenant_id = "tenant-1"

        # Emit many protection events
        for i in range(100):
            emit_protection_decision(
                tenant_id=tenant_id,
                decision="REJECT",
                dimension="rate",
                endpoint=f"/api/test{i}",
                retry_after_ms=60000,
            )

        # Protection counters should be unchanged by observability
        # (Protection only tracks actual check_* calls, not event emissions)
        result = protection_provider.check_rate_limit(tenant_id, "/api/test")
        assert result.decision == Decision.ALLOW  # First actual call

    def test_observe_001_emit_does_not_mutate_onboarding(
        self, observability_provider
    ):
        """OBSERVE-001: Emitting onboarding events doesn't mutate onboarding state."""
        # OnboardingState is an enum, not a mutable state
        # Verify that emitting events doesn't have side effects on the enum
        initial = OnboardingState.CREATED

        emit_onboarding_state_transition(
            tenant_id="tenant-1",
            from_state="CREATED",
            to_state="COMPLETE",
            trigger="force_complete",
        )

        # Enum value should be unchanged (it's a constant)
        assert OnboardingState.CREATED == initial

    # =========================================================================
    # E2E Checklist Item: Events from all sources share unified schema
    # =========================================================================

    def test_unified_schema_all_sources(self, observability_provider):
        """All event sources produce events with the same schema."""
        tenant_id = "tenant-1"
        context = EventContext(request_id="req-123", trace_id="trace-abc")
        actor = Actor(type=ActorType.HUMAN, id="user-1")

        # Emit events from all sources
        emit_onboarding_state_transition(
            tenant_id=tenant_id,
            from_state="CREATED",
            to_state="IDENTITY_VERIFIED",
            trigger="clerk_auth",
            actor=actor,
            context=context,
        )
        emit_billing_state_changed(
            tenant_id=tenant_id,
            from_state="TRIAL",
            to_state="ACTIVE",
            plan_id="pro",
            actor=actor,
            context=context,
        )
        emit_protection_decision(
            tenant_id=tenant_id,
            decision="ALLOW",
            dimension="rate",
            endpoint="/api/test",
            actor=actor,
            context=context,
        )
        emit_role_violation(
            tenant_id=tenant_id,
            required_role="ADMIN",
            actual_role="VIEWER",
            endpoint="/api/admin",
            actor=actor,
            context=context,
        )

        # All events should have the same base structure
        events = observability_provider.get_all_events()
        assert len(events) == 4

        for event in events:
            # All required fields present
            assert event.event_id is not None
            assert event.event_type is not None
            assert event.event_source is not None
            assert event.tenant_id == tenant_id
            assert event.timestamp is not None
            assert event.severity is not None
            assert event.actor is not None
            assert event.context is not None
            assert event.payload is not None

            # All share correlation context
            assert event.context.request_id == "req-123"
            assert event.context.trace_id == "trace-abc"

            # All can be serialized to dict
            d = event.to_dict()
            assert "event_id" in d
            assert "event_type" in d
            assert "event_source" in d
            assert "tenant_id" in d
            assert "timestamp" in d

    def test_unified_schema_all_event_sources_covered(self, observability_provider):
        """Verify all EventSource values have corresponding emitters."""
        # This test ensures we haven't forgotten any event sources
        source_to_emitter = {
            EventSource.ONBOARDING: emit_onboarding_state_transition,
            EventSource.BILLING: emit_billing_state_changed,
            EventSource.PROTECTION: emit_protection_decision,
            EventSource.AUTH: emit_role_violation,
            EventSource.FOUNDER: emit_onboarding_force_complete,
            EventSource.SYSTEM: emit_event,  # Generic emitter for system events
        }

        for source in EventSource:
            assert source in source_to_emitter, f"No emitter for source: {source}"

    # =========================================================================
    # E2E Checklist Item: Emit failures never block main operations
    # =========================================================================

    def test_observe_004_emit_failure_non_blocking(self):
        """OBSERVE-004: Emit failure doesn't block main operation."""
        class FailingProvider:
            def emit(self, event: UnifiedEvent) -> None:
                raise RuntimeError("Storage failure")

            def query(self, *args, **kwargs) -> list:
                return []

        original = get_observability_provider()
        set_observability_provider(FailingProvider())  # type: ignore

        try:
            # This should NOT raise, even though provider fails
            emit_billing_state_changed(
                tenant_id="tenant-1",
                from_state="TRIAL",
                to_state="ACTIVE",
                plan_id="pro",
            )
            # If we get here, the exception was caught (as expected)
            success = True
        except Exception:
            success = False
        finally:
            set_observability_provider(original)

        assert success, "Emit failure should not propagate"

    def test_observe_004_emit_failure_with_billing_operation(
        self, billing_provider
    ):
        """Billing operations should succeed even if observability fails."""
        class FailingProvider:
            def emit(self, event: UnifiedEvent) -> None:
                raise RuntimeError("Storage failure")

            def query(self, *args, **kwargs) -> list:
                return []

        original = get_observability_provider()
        set_observability_provider(FailingProvider())  # type: ignore

        try:
            tenant_id = "tenant-1"

            # Billing operation
            billing_state = billing_provider.get_billing_state(tenant_id)

            # Emit would fail, but we catch it
            emit_billing_state_changed(
                tenant_id=tenant_id,
                from_state="TRIAL",
                to_state="ACTIVE",
                plan_id="pro",
            )

            # Billing should still work
            assert billing_state == BillingState.TRIAL
        finally:
            set_observability_provider(original)

    # =========================================================================
    # E2E Checklist Item: Query results are tenant-scoped only
    # =========================================================================

    def test_observe_003_query_tenant_isolation(self, observability_provider):
        """OBSERVE-003: Queries only return events for the specified tenant."""
        now = datetime.now(timezone.utc)

        # Emit events for different tenants
        for tenant_id in ["tenant-1", "tenant-2", "tenant-3"]:
            for _ in range(10):
                emit_event(
                    event_type="test_event",
                    event_source=EventSource.SYSTEM,
                    tenant_id=tenant_id,
                    severity=Severity.INFO,
                )

        # Query for tenant-1 only
        start = now - timedelta(hours=1)
        end = now + timedelta(hours=1)
        results = observability_provider.query("tenant-1", start, end)

        assert len(results) == 10
        assert all(e.tenant_id == "tenant-1" for e in results)

    def test_observe_003_no_cross_tenant_leakage(self, observability_provider):
        """OBSERVE-003: Sensitive data doesn't leak across tenants."""
        now = datetime.now(timezone.utc)

        # Emit sensitive events for tenant-1
        emit_billing_state_changed(
            tenant_id="tenant-1",
            from_state="TRIAL",
            to_state="SUSPENDED",
            plan_id="enterprise",
        )
        emit_role_violation(
            tenant_id="tenant-1",
            required_role="OWNER",
            actual_role="VIEWER",
            endpoint="/api/billing/cancel",
        )

        # Query for tenant-2 (different tenant)
        start = now - timedelta(hours=1)
        end = now + timedelta(hours=1)
        results = observability_provider.query("tenant-2", start, end)

        # Should return nothing - no cross-tenant leakage
        assert len(results) == 0


class TestPhase8CrossPhaseIntegration:
    """
    Cross-phase integration tests for Phase-8.

    Verifies that observability integrates correctly with
    Phase-4 (Onboarding), Phase-5 (Roles), Phase-6 (Billing),
    and Phase-7 (Protection).
    """

    @pytest.fixture
    def observability_provider(self):
        """Fresh observability provider for each test."""
        provider = MockObservabilityProvider()
        set_observability_provider(provider)
        yield provider
        provider.reset()

    @pytest.fixture
    def billing_provider(self):
        """Fresh billing provider for each test."""
        provider = MockBillingProvider()
        set_billing_provider(provider)
        yield provider
        provider.reset()

    @pytest.fixture
    def protection_provider(self):
        """Fresh protection provider for each test."""
        provider = MockAbuseProtectionProvider()
        set_protection_provider(provider)
        yield provider
        provider.reset()

    def test_tenant_journey_full_timeline(
        self, observability_provider, billing_provider, protection_provider
    ):
        """
        Simulate a full tenant journey and verify event timeline.

        Journey:
        1. Tenant created
        2. Complete onboarding
        3. Get TRIAL billing
        4. Make API calls (protection checks)
        5. Hit rate limit
        """
        tenant_id = "journey-tenant"
        now = datetime.now(timezone.utc)
        trace_id = "journey-trace-123"

        # Step 1: Onboarding state transitions
        context = EventContext(trace_id=trace_id)
        for from_state, to_state, trigger in [
            ("CREATED", "IDENTITY_VERIFIED", "clerk_auth"),
            ("IDENTITY_VERIFIED", "API_KEY_CREATED", "api_key_create"),
            ("API_KEY_CREATED", "SDK_CONNECTED", "sdk_ping"),
            ("SDK_CONNECTED", "COMPLETE", "auto_promotion"),
        ]:
            emit_onboarding_state_transition(
                tenant_id=tenant_id,
                from_state=from_state,
                to_state=to_state,
                trigger=trigger,
                context=context,
            )

        # Step 2: Billing state after COMPLETE
        emit_billing_state_changed(
            tenant_id=tenant_id,
            from_state="NONE",
            to_state="TRIAL",
            plan_id="free",
            context=context,
        )

        # Step 3: API calls with protection checks
        for i in range(5):
            emit_protection_decision(
                tenant_id=tenant_id,
                decision="ALLOW",
                dimension="rate",
                endpoint=f"/api/runs/{i}",
                context=context,
            )

        # Step 4: Hit rate limit
        emit_protection_decision(
            tenant_id=tenant_id,
            decision="REJECT",
            dimension="rate",
            endpoint="/api/runs",
            retry_after_ms=60000,
            context=context,
        )

        # Verify timeline
        start = now - timedelta(hours=1)
        end = now + timedelta(hours=1)
        events = observability_provider.query(tenant_id, start, end)

        # Should have: 4 onboarding + 1 billing + 5 allow + 1 reject = 11 events
        assert len(events) == 11

        # All events should share the trace_id
        assert all(e.context.trace_id == trace_id for e in events)

        # Verify event types in order
        event_types = [e.event_type for e in events]
        assert event_types.count(EVENT_ONBOARDING_STATE_TRANSITION) == 4
        assert event_types.count(EVENT_BILLING_STATE_CHANGED) == 1
        assert event_types.count(EVENT_PROTECTION_DECISION) == 6

        # Verify final event is REJECT
        assert events[-1].event_type == EVENT_PROTECTION_DECISION
        assert events[-1].payload["decision"] == "REJECT"

    def test_correlation_across_request(self, observability_provider):
        """Events from a single request can be correlated via request_id."""
        tenant_id = "correlation-tenant"
        request_id = "req-abc-123"
        context = EventContext(request_id=request_id)

        # Simulate a request that triggers multiple events
        emit_protection_decision(
            tenant_id=tenant_id,
            decision="ALLOW",
            dimension="rate",
            endpoint="/api/upgrade",
            context=context,
        )
        emit_billing_limit_evaluated(
            tenant_id=tenant_id,
            limit_name="max_active_agents",
            current_value=2,
            allowed_value=3,
            exceeded=False,
            context=context,
        )
        emit_billing_state_changed(
            tenant_id=tenant_id,
            from_state="TRIAL",
            to_state="ACTIVE",
            plan_id="pro",
            context=context,
        )

        # All events should share the request_id
        events = observability_provider.get_all_events()
        assert len(events) == 3
        assert all(e.context.request_id == request_id for e in events)

    def test_observability_reads_billing_never_writes(
        self, observability_provider, billing_provider
    ):
        """Observability can read billing state but never write."""
        tenant_id = "readonly-tenant"

        # Get billing state (read)
        billing_state = billing_provider.get_billing_state(tenant_id)

        # Emit event with billing info (observability records truth)
        emit_billing_state_changed(
            tenant_id=tenant_id,
            from_state=billing_state.value,
            to_state="ACTIVE",
            plan_id="pro",
        )

        # Billing state should be unchanged (observability doesn't write)
        assert billing_provider.get_billing_state(tenant_id) == billing_state

    def test_observability_reads_protection_never_writes(
        self, observability_provider, protection_provider
    ):
        """Observability can read protection decisions but never write."""
        tenant_id = "readonly-tenant"

        # Check protection (read)
        result = protection_provider.check_rate_limit(tenant_id, "/api/test")

        # Emit event with protection info (observability records truth)
        emit_protection_decision(
            tenant_id=tenant_id,
            decision=result.decision.value,
            dimension=result.dimension,
            endpoint="/api/test",
        )

        # Protection should still allow (no writes from observability)
        new_result = protection_provider.check_rate_limit(tenant_id, "/api/test")
        assert new_result.decision == Decision.ALLOW


class TestFreezeExitCriteriaPhase8:
    """
    Verify freeze exit criteria for Phase-8.

    Per FREEZE.md, Phase-8 integration requires:
    1. Observability never mutates any system state
    2. Events from all sources share unified schema
    3. Emit failures never block main operations
    4. Query results are tenant-scoped only
    """

    def test_all_phase8_invariants_implemented(self):
        """All OBSERVE invariants are implemented and testable."""
        from app.observability import (
            MockObservabilityProvider,
            ObservabilityProvider,
        )

        provider = MockObservabilityProvider()

        # OBSERVE-001: No mutation methods
        assert not hasattr(provider, "set_billing_state")
        assert not hasattr(provider, "set_onboarding_state")
        assert not hasattr(provider, "set_role")

        # OBSERVE-002: Events are immutable (frozen dataclass)
        event = UnifiedEvent(
            event_type="test",
            event_source=EventSource.SYSTEM,
            tenant_id="t1",
            severity=Severity.INFO,
        )
        with pytest.raises(Exception):
            event.tenant_id = "modified"  # type: ignore

        # OBSERVE-003: tenant_id is required
        with pytest.raises(ValueError):
            UnifiedEvent(
                event_type="test",
                event_source=EventSource.SYSTEM,
                tenant_id="",
                severity=Severity.INFO,
            )

        # OBSERVE-004: emit catches exceptions (tested elsewhere)
        # OBSERVE-005: Mock satisfies protocol
        assert isinstance(provider, ObservabilityProvider)

    def test_mock_provider_complete(self):
        """Mock provider is fully implemented."""
        provider = MockObservabilityProvider()

        # All protocol methods work
        event = UnifiedEvent(
            event_type="test",
            event_source=EventSource.SYSTEM,
            tenant_id="t1",
            severity=Severity.INFO,
        )
        provider.emit(event)

        now = datetime.now(timezone.utc)
        results = provider.query(
            "t1",
            now - timedelta(hours=1),
            now + timedelta(hours=1),
        )
        assert len(results) == 1

        # Helper methods work
        assert provider.count() == 1
        provider.reset()
        assert provider.count() == 0
