# Layer: L4 — Domain Engine
# Product: system-wide
# Temporal:
#   Trigger: import-time
#   Execution: sync
# Role: Phase-8 Observability Package Exports
# Callers: all systems emitting or querying events
# Allowed Imports: L4 (events, provider, emitters)
# Forbidden Imports: L1, L2, L3, L5, L6
# Reference: PIN-399 Phase-8 (Observability Unification)

"""
Phase-8 Observability Package

Unified event model for all observability data.

Usage:
    from app.observability import emit_event, emit_billing_state_changed
    from app.observability import get_observability_provider

    # Emit a billing state change
    emit_billing_state_changed(
        tenant_id="tenant-123",
        from_state="TRIAL",
        to_state="ACTIVE",
        plan_id="pro",
    )

    # Query events
    provider = get_observability_provider()
    events = provider.query(
        tenant_id="tenant-123",
        start=datetime(2026, 1, 1),
        end=datetime.now(timezone.utc),
    )

Design Invariants:
    OBSERVE-001: Observability never mutates system state
    OBSERVE-002: Events are immutable once accepted
    OBSERVE-003: All events are tenant-scoped
    OBSERVE-004: Failure to emit must not block execution
    OBSERVE-005: Mock provider must be interface-compatible with real provider
"""

# Core types
from app.observability.events import (
    Severity,
    ActorType,
    EventSource,
    Actor,
    EventContext,
    UnifiedEvent,
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

# Provider
from app.observability.provider import (
    ObservabilityProvider,
    MockObservabilityProvider,
    get_observability_provider,
    set_observability_provider,
)

# Emitters
from app.observability.emitters import (
    emit_event,
    emit_onboarding_state_transition,
    emit_onboarding_force_complete,
    emit_billing_state_changed,
    emit_billing_limit_evaluated,
    emit_protection_decision,
    emit_protection_anomaly_detected,
    emit_role_violation,
    emit_unauthorized_access,
)


__all__ = [
    # Core types
    "Severity",
    "ActorType",
    "EventSource",
    "Actor",
    "EventContext",
    "UnifiedEvent",
    # Event type constants
    "EVENT_ONBOARDING_STATE_TRANSITION",
    "EVENT_ONBOARDING_FORCE_COMPLETE",
    "EVENT_BILLING_STATE_CHANGED",
    "EVENT_BILLING_LIMIT_EVALUATED",
    "EVENT_PROTECTION_DECISION",
    "EVENT_PROTECTION_ANOMALY_DETECTED",
    "EVENT_ROLE_VIOLATION",
    "EVENT_UNAUTHORIZED_ACCESS",
    # Provider
    "ObservabilityProvider",
    "MockObservabilityProvider",
    "get_observability_provider",
    "set_observability_provider",
    # Emitters
    "emit_event",
    "emit_onboarding_state_transition",
    "emit_onboarding_force_complete",
    "emit_billing_state_changed",
    "emit_billing_limit_evaluated",
    "emit_protection_decision",
    "emit_protection_anomaly_detected",
    "emit_role_violation",
    "emit_unauthorized_access",
]
