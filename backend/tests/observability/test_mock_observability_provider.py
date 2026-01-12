# Layer: L8 — Catalyst / Meta
# Product: system-wide
# Temporal:
#   Trigger: CI
#   Execution: sync
# Role: Phase-8 Observability Provider Tests
# Callers: pytest, CI pipeline
# Allowed Imports: L4 (observability)
# Forbidden Imports: L1, L2, L3, L5, L6
# Reference: PIN-399 Phase-8 (Observability Unification)

"""
Phase-8 Observability Provider Tests

Tests for MockObservabilityProvider and event emission.

Verifies:
- OBSERVE-001: Observability never mutates system state
- OBSERVE-002: Events are immutable once accepted
- OBSERVE-003: All events are tenant-scoped
- OBSERVE-004: Failure to emit must not block execution
- OBSERVE-005: Mock provider must be interface-compatible with real provider
"""

import pytest
from datetime import datetime, timezone, timedelta
import threading
import time

from app.observability import (
    # Core types
    Severity,
    ActorType,
    EventSource,
    Actor,
    EventContext,
    UnifiedEvent,
    # Provider
    MockObservabilityProvider,
    ObservabilityProvider,
    get_observability_provider,
    set_observability_provider,
    # Emitters
    emit_event,
    emit_onboarding_state_transition,
    emit_onboarding_force_complete,
    emit_billing_state_changed,
    emit_billing_limit_evaluated,
    emit_protection_decision,
    emit_protection_anomaly_detected,
    emit_role_violation,
    emit_unauthorized_access,
    # Event type constants
    EVENT_ONBOARDING_STATE_TRANSITION,
    EVENT_ONBOARDING_FORCE_COMPLETE,
    EVENT_BILLING_STATE_CHANGED,
    EVENT_BILLING_LIMIT_EVALUATED,
    EVENT_PROTECTION_DECISION,
    EVENT_PROTECTION_ANOMALY_DETECTED,
    EVENT_ROLE_VIOLATION,
    EVENT_UNAUTHORIZED_ACCESS,
)


class TestUnifiedEvent:
    """Tests for UnifiedEvent dataclass."""

    def test_event_creation_with_required_fields(self):
        """Event can be created with required fields."""
        event = UnifiedEvent(
            event_type="test_event",
            event_source=EventSource.SYSTEM,
            tenant_id="tenant-123",
            severity=Severity.INFO,
        )

        assert event.event_type == "test_event"
        assert event.event_source == EventSource.SYSTEM
        assert event.tenant_id == "tenant-123"
        assert event.severity == Severity.INFO
        assert event.payload == {}
        assert event.actor.type == ActorType.SYSTEM
        assert event.event_id is not None  # Auto-generated
        assert event.timestamp is not None  # Auto-generated

    def test_event_creation_with_all_fields(self):
        """Event can be created with all fields."""
        actor = Actor(type=ActorType.HUMAN, id="user-456")
        context = EventContext(request_id="req-789", trace_id="trace-abc")
        timestamp = datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc)

        event = UnifiedEvent(
            event_type="billing_state_changed",
            event_source=EventSource.BILLING,
            tenant_id="tenant-123",
            severity=Severity.WARN,
            payload={"from_state": "TRIAL", "to_state": "ACTIVE"},
            actor=actor,
            context=context,
            event_id="custom-event-id",
            timestamp=timestamp,
        )

        assert event.event_type == "billing_state_changed"
        assert event.event_source == EventSource.BILLING
        assert event.tenant_id == "tenant-123"
        assert event.severity == Severity.WARN
        assert event.payload == {"from_state": "TRIAL", "to_state": "ACTIVE"}
        assert event.actor.type == ActorType.HUMAN
        assert event.actor.id == "user-456"
        assert event.context.request_id == "req-789"
        assert event.context.trace_id == "trace-abc"
        assert event.event_id == "custom-event-id"
        assert event.timestamp == timestamp

    def test_event_is_immutable(self):
        """OBSERVE-002: Events are immutable once created."""
        event = UnifiedEvent(
            event_type="test_event",
            event_source=EventSource.SYSTEM,
            tenant_id="tenant-123",
            severity=Severity.INFO,
        )

        # Frozen dataclass should raise an error on mutation
        with pytest.raises(Exception):  # FrozenInstanceError
            event.event_type = "modified"  # type: ignore

    def test_event_requires_tenant_id(self):
        """OBSERVE-003: All events are tenant-scoped."""
        with pytest.raises(ValueError, match="tenant_id is required"):
            UnifiedEvent(
                event_type="test_event",
                event_source=EventSource.SYSTEM,
                tenant_id="",  # Empty is invalid
                severity=Severity.INFO,
            )

    def test_event_requires_event_type(self):
        """Event type is required."""
        with pytest.raises(ValueError, match="event_type is required"):
            UnifiedEvent(
                event_type="",  # Empty is invalid
                event_source=EventSource.SYSTEM,
                tenant_id="tenant-123",
                severity=Severity.INFO,
            )

    def test_event_to_dict(self):
        """Event can be serialized to dictionary."""
        timestamp = datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        event = UnifiedEvent(
            event_type="test_event",
            event_source=EventSource.BILLING,
            tenant_id="tenant-123",
            severity=Severity.INFO,
            payload={"key": "value"},
            actor=Actor(type=ActorType.HUMAN, id="user-1"),
            context=EventContext(request_id="req-1"),
            event_id="evt-1",
            timestamp=timestamp,
        )

        result = event.to_dict()

        assert result["event_id"] == "evt-1"
        assert result["event_type"] == "test_event"
        assert result["event_source"] == "billing"
        assert result["tenant_id"] == "tenant-123"
        assert result["timestamp"] == "2026-01-01T12:00:00+00:00"
        assert result["severity"] == "INFO"
        assert result["actor"]["type"] == "human"
        assert result["actor"]["id"] == "user-1"
        assert result["context"]["request_id"] == "req-1"
        assert result["payload"]["key"] == "value"


class TestMockObservabilityProvider:
    """Tests for MockObservabilityProvider."""

    @pytest.fixture
    def provider(self):
        """Fresh provider for each test."""
        provider = MockObservabilityProvider()
        set_observability_provider(provider)
        yield provider
        provider.reset()

    def test_emit_stores_event(self, provider):
        """Emit stores event in memory."""
        event = UnifiedEvent(
            event_type="test_event",
            event_source=EventSource.SYSTEM,
            tenant_id="tenant-123",
            severity=Severity.INFO,
        )

        provider.emit(event)

        assert provider.count() == 1
        stored = provider.get_all_events()[0]
        assert stored.event_type == "test_event"
        assert stored.tenant_id == "tenant-123"

    def test_emit_preserves_immutability(self, provider):
        """OBSERVE-002: Emitted events remain immutable."""
        event = UnifiedEvent(
            event_type="test_event",
            event_source=EventSource.SYSTEM,
            tenant_id="tenant-123",
            severity=Severity.INFO,
        )

        provider.emit(event)
        stored = provider.get_all_events()[0]

        # The stored event should also be immutable
        with pytest.raises(Exception):
            stored.event_type = "modified"  # type: ignore

    def test_query_filters_by_tenant(self, provider):
        """OBSERVE-003: Query only returns events for specified tenant."""
        now = datetime.now(timezone.utc)

        # Emit events for different tenants
        provider.emit(UnifiedEvent(
            event_type="test", event_source=EventSource.SYSTEM,
            tenant_id="tenant-1", severity=Severity.INFO, timestamp=now,
        ))
        provider.emit(UnifiedEvent(
            event_type="test", event_source=EventSource.SYSTEM,
            tenant_id="tenant-2", severity=Severity.INFO, timestamp=now,
        ))
        provider.emit(UnifiedEvent(
            event_type="test", event_source=EventSource.SYSTEM,
            tenant_id="tenant-1", severity=Severity.INFO, timestamp=now,
        ))

        # Query for tenant-1
        start = now - timedelta(hours=1)
        end = now + timedelta(hours=1)
        results = provider.query("tenant-1", start, end)

        assert len(results) == 2
        assert all(e.tenant_id == "tenant-1" for e in results)

    def test_query_filters_by_time_range(self, provider):
        """Query only returns events within time range."""
        base = datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc)

        provider.emit(UnifiedEvent(
            event_type="early", event_source=EventSource.SYSTEM,
            tenant_id="tenant-1", severity=Severity.INFO,
            timestamp=base - timedelta(hours=2),
        ))
        provider.emit(UnifiedEvent(
            event_type="in_range", event_source=EventSource.SYSTEM,
            tenant_id="tenant-1", severity=Severity.INFO,
            timestamp=base,
        ))
        provider.emit(UnifiedEvent(
            event_type="late", event_source=EventSource.SYSTEM,
            tenant_id="tenant-1", severity=Severity.INFO,
            timestamp=base + timedelta(hours=2),
        ))

        # Query for specific range
        start = base - timedelta(hours=1)
        end = base + timedelta(hours=1)
        results = provider.query("tenant-1", start, end)

        assert len(results) == 1
        assert results[0].event_type == "in_range"

    def test_query_filters_by_event_types(self, provider):
        """Query can filter by event types."""
        now = datetime.now(timezone.utc)

        provider.emit(UnifiedEvent(
            event_type="billing_state_changed", event_source=EventSource.BILLING,
            tenant_id="tenant-1", severity=Severity.INFO, timestamp=now,
        ))
        provider.emit(UnifiedEvent(
            event_type="protection_decision", event_source=EventSource.PROTECTION,
            tenant_id="tenant-1", severity=Severity.INFO, timestamp=now,
        ))

        start = now - timedelta(hours=1)
        end = now + timedelta(hours=1)
        results = provider.query(
            "tenant-1", start, end,
            event_types=["billing_state_changed"],
        )

        assert len(results) == 1
        assert results[0].event_type == "billing_state_changed"

    def test_query_filters_by_event_sources(self, provider):
        """Query can filter by event sources."""
        now = datetime.now(timezone.utc)

        provider.emit(UnifiedEvent(
            event_type="event1", event_source=EventSource.BILLING,
            tenant_id="tenant-1", severity=Severity.INFO, timestamp=now,
        ))
        provider.emit(UnifiedEvent(
            event_type="event2", event_source=EventSource.PROTECTION,
            tenant_id="tenant-1", severity=Severity.INFO, timestamp=now,
        ))
        provider.emit(UnifiedEvent(
            event_type="event3", event_source=EventSource.AUTH,
            tenant_id="tenant-1", severity=Severity.INFO, timestamp=now,
        ))

        start = now - timedelta(hours=1)
        end = now + timedelta(hours=1)
        results = provider.query(
            "tenant-1", start, end,
            event_sources=["billing", "protection"],
        )

        assert len(results) == 2
        sources = {e.event_source.value for e in results}
        assert sources == {"billing", "protection"}

    def test_query_returns_ordered_events(self, provider):
        """Query returns events ordered by (timestamp, event_id)."""
        base = datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc)

        # Emit in non-chronological order
        provider.emit(UnifiedEvent(
            event_type="third", event_source=EventSource.SYSTEM,
            tenant_id="tenant-1", severity=Severity.INFO,
            timestamp=base + timedelta(seconds=2), event_id="evt-c",
        ))
        provider.emit(UnifiedEvent(
            event_type="first", event_source=EventSource.SYSTEM,
            tenant_id="tenant-1", severity=Severity.INFO,
            timestamp=base, event_id="evt-a",
        ))
        provider.emit(UnifiedEvent(
            event_type="second", event_source=EventSource.SYSTEM,
            tenant_id="tenant-1", severity=Severity.INFO,
            timestamp=base + timedelta(seconds=1), event_id="evt-b",
        ))

        start = base - timedelta(hours=1)
        end = base + timedelta(hours=1)
        results = provider.query("tenant-1", start, end)

        assert len(results) == 3
        assert results[0].event_type == "first"
        assert results[1].event_type == "second"
        assert results[2].event_type == "third"

    def test_emit_is_thread_safe(self, provider):
        """Emit is thread-safe for concurrent calls."""
        event_count = 100
        thread_count = 10
        errors: list = []

        def emit_events(thread_id: int) -> None:
            try:
                for i in range(event_count):
                    event = UnifiedEvent(
                        event_type=f"event_{thread_id}_{i}",
                        event_source=EventSource.SYSTEM,
                        tenant_id="tenant-1",
                        severity=Severity.INFO,
                    )
                    provider.emit(event)
            except Exception as e:
                errors.append(e)

        threads = [
            threading.Thread(target=emit_events, args=(i,))
            for i in range(thread_count)
        ]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0
        assert provider.count() == event_count * thread_count

    def test_reset_clears_events(self, provider):
        """Reset clears all events from store."""
        provider.emit(UnifiedEvent(
            event_type="test", event_source=EventSource.SYSTEM,
            tenant_id="tenant-1", severity=Severity.INFO,
        ))

        assert provider.count() == 1
        provider.reset()
        assert provider.count() == 0

    def test_get_events_by_tenant(self, provider):
        """Get all events for a specific tenant."""
        provider.emit(UnifiedEvent(
            event_type="event1", event_source=EventSource.SYSTEM,
            tenant_id="tenant-1", severity=Severity.INFO,
        ))
        provider.emit(UnifiedEvent(
            event_type="event2", event_source=EventSource.SYSTEM,
            tenant_id="tenant-2", severity=Severity.INFO,
        ))

        results = provider.get_events_by_tenant("tenant-1")
        assert len(results) == 1
        assert results[0].event_type == "event1"


class TestGlobalProvider:
    """Tests for global provider functions."""

    def test_get_default_provider(self):
        """Default provider is MockObservabilityProvider."""
        provider = get_observability_provider()
        assert isinstance(provider, MockObservabilityProvider)

    def test_set_provider(self):
        """Provider can be changed."""
        original = get_observability_provider()
        new_provider = MockObservabilityProvider()

        set_observability_provider(new_provider)
        assert get_observability_provider() is new_provider

        # Restore original
        set_observability_provider(original)

    def test_provider_satisfies_protocol(self):
        """Mock provider satisfies ObservabilityProvider protocol."""
        provider = MockObservabilityProvider()
        assert isinstance(provider, ObservabilityProvider)


class TestEmitters:
    """Tests for event emitter helper functions."""

    @pytest.fixture
    def provider(self):
        """Fresh provider for each test."""
        provider = MockObservabilityProvider()
        set_observability_provider(provider)
        yield provider
        provider.reset()

    def test_emit_event_basic(self, provider):
        """emit_event creates and emits event."""
        emit_event(
            event_type="test_event",
            event_source=EventSource.SYSTEM,
            tenant_id="tenant-123",
        )

        assert provider.count() == 1
        event = provider.get_all_events()[0]
        assert event.event_type == "test_event"
        assert event.tenant_id == "tenant-123"
        assert event.severity == Severity.INFO  # Default

    def test_emit_onboarding_state_transition(self, provider):
        """Onboarding state transition event is emitted correctly."""
        emit_onboarding_state_transition(
            tenant_id="tenant-1",
            from_state="CREATED",
            to_state="IDENTITY_VERIFIED",
            trigger="clerk_auth",
        )

        event = provider.get_all_events()[0]
        assert event.event_type == EVENT_ONBOARDING_STATE_TRANSITION
        assert event.event_source == EventSource.ONBOARDING
        assert event.payload["from_state"] == "CREATED"
        assert event.payload["to_state"] == "IDENTITY_VERIFIED"
        assert event.payload["trigger"] == "clerk_auth"

    def test_emit_onboarding_force_complete(self, provider):
        """Force-complete event is emitted with WARN severity."""
        actor = Actor(type=ActorType.HUMAN, id="founder-1")
        emit_onboarding_force_complete(
            tenant_id="tenant-1",
            from_state="API_KEY_CREATED",
            reason="Enterprise onboarding",
            justification="Customer requested expedited setup",
            actor=actor,
        )

        event = provider.get_all_events()[0]
        assert event.event_type == EVENT_ONBOARDING_FORCE_COMPLETE
        assert event.event_source == EventSource.FOUNDER
        assert event.severity == Severity.WARN
        assert event.actor.type == ActorType.HUMAN
        assert event.payload["justification"] == "Customer requested expedited setup"

    def test_emit_billing_state_changed(self, provider):
        """Billing state change event is emitted correctly."""
        emit_billing_state_changed(
            tenant_id="tenant-1",
            from_state="TRIAL",
            to_state="ACTIVE",
            plan_id="pro",
        )

        event = provider.get_all_events()[0]
        assert event.event_type == EVENT_BILLING_STATE_CHANGED
        assert event.event_source == EventSource.BILLING
        assert event.payload["plan_id"] == "pro"

    def test_emit_billing_limit_evaluated_exceeded(self, provider):
        """Billing limit exceeded event has WARN severity."""
        emit_billing_limit_evaluated(
            tenant_id="tenant-1",
            limit_name="max_requests_per_day",
            current_value=1500,
            allowed_value=1000,
            exceeded=True,
        )

        event = provider.get_all_events()[0]
        assert event.event_type == EVENT_BILLING_LIMIT_EVALUATED
        assert event.severity == Severity.WARN
        assert event.payload["exceeded"] is True

    def test_emit_billing_limit_evaluated_not_exceeded(self, provider):
        """Billing limit not exceeded event has INFO severity."""
        emit_billing_limit_evaluated(
            tenant_id="tenant-1",
            limit_name="max_requests_per_day",
            current_value=500,
            allowed_value=1000,
            exceeded=False,
        )

        event = provider.get_all_events()[0]
        assert event.severity == Severity.INFO
        assert event.payload["exceeded"] is False

    def test_emit_protection_decision_allow(self, provider):
        """Protection ALLOW decision has INFO severity."""
        emit_protection_decision(
            tenant_id="tenant-1",
            decision="ALLOW",
            dimension="rate",
            endpoint="/api/test",
        )

        event = provider.get_all_events()[0]
        assert event.event_type == EVENT_PROTECTION_DECISION
        assert event.event_source == EventSource.PROTECTION
        assert event.severity == Severity.INFO

    def test_emit_protection_decision_reject(self, provider):
        """Protection REJECT decision has ERROR severity."""
        emit_protection_decision(
            tenant_id="tenant-1",
            decision="REJECT",
            dimension="rate",
            endpoint="/api/test",
            retry_after_ms=60000,
        )

        event = provider.get_all_events()[0]
        assert event.severity == Severity.ERROR
        assert event.payload["retry_after_ms"] == 60000

    def test_emit_protection_decision_throttle(self, provider):
        """Protection THROTTLE decision has WARN severity."""
        emit_protection_decision(
            tenant_id="tenant-1",
            decision="THROTTLE",
            dimension="burst",
            endpoint="/api/test",
        )

        event = provider.get_all_events()[0]
        assert event.severity == Severity.WARN

    def test_emit_protection_anomaly_detected(self, provider):
        """Anomaly detection event is emitted correctly."""
        emit_protection_anomaly_detected(
            tenant_id="tenant-1",
            baseline=100,
            observed=1500,
            window="1min",
            anomaly_severity="critical",
        )

        event = provider.get_all_events()[0]
        assert event.event_type == EVENT_PROTECTION_ANOMALY_DETECTED
        assert event.severity == Severity.ERROR  # critical -> ERROR
        assert event.payload["baseline"] == 100
        assert event.payload["observed"] == 1500

    def test_emit_role_violation(self, provider):
        """Role violation event has ERROR severity."""
        emit_role_violation(
            tenant_id="tenant-1",
            required_role="ADMIN",
            actual_role="VIEWER",
            endpoint="/api/admin/users",
        )

        event = provider.get_all_events()[0]
        assert event.event_type == EVENT_ROLE_VIOLATION
        assert event.event_source == EventSource.AUTH
        assert event.severity == Severity.ERROR

    def test_emit_unauthorized_access(self, provider):
        """Unauthorized access event has ERROR severity."""
        emit_unauthorized_access(
            tenant_id="tenant-1",
            reason="missing_api_key",
            endpoint="/api/runs",
            method="POST",
        )

        event = provider.get_all_events()[0]
        assert event.event_type == EVENT_UNAUTHORIZED_ACCESS
        assert event.severity == Severity.ERROR
        assert event.payload["method"] == "POST"


class TestCorrelationContext:
    """Tests for event correlation via context."""

    @pytest.fixture
    def provider(self):
        """Fresh provider for each test."""
        provider = MockObservabilityProvider()
        set_observability_provider(provider)
        yield provider
        provider.reset()

    def test_events_can_share_request_id(self, provider):
        """Multiple events can be correlated by request_id."""
        context = EventContext(request_id="req-123")

        emit_billing_state_changed(
            tenant_id="tenant-1",
            from_state="TRIAL",
            to_state="ACTIVE",
            plan_id="pro",
            context=context,
        )
        emit_protection_decision(
            tenant_id="tenant-1",
            decision="ALLOW",
            dimension="rate",
            endpoint="/api/upgrade",
            context=context,
        )

        events = provider.get_all_events()
        assert len(events) == 2
        assert events[0].context.request_id == "req-123"
        assert events[1].context.request_id == "req-123"

    def test_events_can_share_trace_id(self, provider):
        """Multiple events can be correlated by trace_id."""
        context = EventContext(trace_id="trace-abc")

        emit_onboarding_state_transition(
            tenant_id="tenant-1",
            from_state="CREATED",
            to_state="IDENTITY_VERIFIED",
            trigger="clerk_auth",
            context=context,
        )
        emit_onboarding_state_transition(
            tenant_id="tenant-1",
            from_state="IDENTITY_VERIFIED",
            to_state="API_KEY_CREATED",
            trigger="api_key_create",
            context=context,
        )

        events = provider.get_all_events()
        assert all(e.context.trace_id == "trace-abc" for e in events)


class TestInvariantCompliance:
    """Tests verifying design invariants from FREEZE.md."""

    def test_observe_001_observability_never_mutates_state(self):
        """OBSERVE-001: Observability never mutates system state."""
        # Observability has no dependencies on billing, protection, or onboarding
        # It only receives events, never sends commands
        from app.observability import emitters

        # Verify emitters module only exports emit_* functions via __all__
        for name in emitters.__all__:
            # All exported names should be emit_* or emit_event
            if name != "emit_event":
                assert name.startswith("emit_"), f"Non-emit export: {name}"

        # Verify no mutation methods exist on the provider
        from app.observability.provider import MockObservabilityProvider
        provider = MockObservabilityProvider()

        # Provider should only have read operations and emit (append-only)
        # No set_*, update_*, delete_* methods that could mutate external state
        public_methods = [m for m in dir(provider) if not m.startswith("_") and callable(getattr(provider, m))]
        mutation_prefixes = ("set_billing", "set_onboarding", "set_role", "update_", "delete_")
        for method in public_methods:
            for prefix in mutation_prefixes:
                assert not method.startswith(prefix), f"Mutation method found: {method}"

    def test_observe_002_events_are_immutable(self):
        """OBSERVE-002: Events are immutable once accepted."""
        event = UnifiedEvent(
            event_type="test",
            event_source=EventSource.SYSTEM,
            tenant_id="tenant-1",
            severity=Severity.INFO,
        )

        # Event is frozen dataclass
        with pytest.raises(Exception):
            event.tenant_id = "modified"  # type: ignore

    def test_observe_003_all_events_tenant_scoped(self):
        """OBSERVE-003: All events are tenant-scoped."""
        # Empty tenant_id should fail validation
        with pytest.raises(ValueError, match="tenant_id is required"):
            UnifiedEvent(
                event_type="test",
                event_source=EventSource.SYSTEM,
                tenant_id="",
                severity=Severity.INFO,
            )

    def test_observe_004_emit_failure_non_blocking(self):
        """OBSERVE-004: Failure to emit must not block execution."""
        # Create a provider that raises on emit
        class FailingProvider:
            def emit(self, event: UnifiedEvent) -> None:
                raise RuntimeError("Storage failure")

            def query(self, *args, **kwargs) -> list:
                return []

        original = get_observability_provider()
        set_observability_provider(FailingProvider())  # type: ignore

        # Emit should not raise, even with failing provider
        try:
            # The emitter catches exceptions internally
            emit_event(
                event_type="test",
                event_source=EventSource.SYSTEM,
                tenant_id="tenant-1",
            )
            # If we get here, the exception was caught (as expected)
        finally:
            set_observability_provider(original)

    def test_observe_005_mock_satisfies_protocol(self):
        """OBSERVE-005: Mock provider must be interface-compatible."""
        provider = MockObservabilityProvider()

        # Check all protocol methods exist
        assert hasattr(provider, "emit")
        assert hasattr(provider, "query")

        # Check method signatures
        assert callable(provider.emit)
        assert callable(provider.query)

        # Verify protocol compliance
        assert isinstance(provider, ObservabilityProvider)
