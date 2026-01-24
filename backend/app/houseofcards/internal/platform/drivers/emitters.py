# Layer: L4 — Domain Engine
# Product: system-wide
# Temporal:
#   Trigger: runtime
#   Execution: sync
# Role: Phase-8 Event Emitters (helper functions)
# Callers: onboarding, billing, protection, auth, founder ops
# Allowed Imports: L4 (events, provider)
# Forbidden Imports: L1, L2, L3, L5, L6
# Reference: PIN-399 Phase-8 (Observability Unification)

"""
Phase-8 Event Emitters

Convenience functions for emitting events from each system.
All emitters are thin wrappers around the provider's emit() method.

OBSERVE-004: All emitters are non-blocking and fail silently.
"""

import logging
from typing import Optional


logger = logging.getLogger(__name__)

from app.observability.events import (
    UnifiedEvent,
    EventSource,
    Severity,
    Actor,
    ActorType,
    EventContext,
    EVENT_ONBOARDING_STATE_TRANSITION,
    EVENT_ONBOARDING_FORCE_COMPLETE,
    EVENT_BILLING_STATE_CHANGED,
    EVENT_BILLING_LIMIT_EVALUATED,
    EVENT_PROTECTION_DECISION,
    EVENT_PROTECTION_ANOMALY_DETECTED,
    EVENT_ROLE_VIOLATION,
    EVENT_UNAUTHORIZED_ACCESS,
)
from app.observability.provider import get_observability_provider


# =============================================================================
# GENERIC EMIT HELPER
# =============================================================================


def emit_event(
    event_type: str,
    event_source: EventSource,
    tenant_id: str,
    severity: Severity = Severity.INFO,
    payload: Optional[dict] = None,
    actor: Optional[Actor] = None,
    context: Optional[EventContext] = None,
) -> None:
    """
    Emit a unified event to the observability store.

    This is the primary helper function for emitting events.
    OBSERVE-004: Non-blocking, fails silently.

    Args:
        event_type: Event type string (e.g., "billing_state_changed")
        event_source: Source system (onboarding, billing, protection, etc.)
        tenant_id: Tenant identifier (required per OBSERVE-003)
        severity: Event severity (default: INFO)
        payload: Domain-specific details (default: empty dict)
        actor: Who triggered the event (default: SYSTEM)
        context: Correlation context (default: empty)
    """
    try:
        event = UnifiedEvent(
            event_type=event_type,
            event_source=event_source,
            tenant_id=tenant_id,
            severity=severity,
            payload=payload or {},
            actor=actor or Actor(type=ActorType.SYSTEM),
            context=context or EventContext(),
        )
        get_observability_provider().emit(event)
    except Exception as e:
        # OBSERVE-004: Failure to emit must not block execution
        logger.error(f"Observability emit failed: {e}")
        # Operation continues - never propagate


# =============================================================================
# ONBOARDING EMITTERS
# =============================================================================


def emit_onboarding_state_transition(
    tenant_id: str,
    from_state: str,
    to_state: str,
    trigger: str,
    actor: Optional[Actor] = None,
    context: Optional[EventContext] = None,
) -> None:
    """
    Emit an onboarding state transition event.

    Args:
        tenant_id: The tenant undergoing transition
        from_state: Previous onboarding state
        to_state: New onboarding state
        trigger: What caused the transition
        actor: Who triggered the event
        context: Correlation context
    """
    emit_event(
        event_type=EVENT_ONBOARDING_STATE_TRANSITION,
        event_source=EventSource.ONBOARDING,
        tenant_id=tenant_id,
        severity=Severity.INFO,
        payload={
            "from_state": from_state,
            "to_state": to_state,
            "trigger": trigger,
        },
        actor=actor,
        context=context,
    )


def emit_onboarding_force_complete(
    tenant_id: str,
    from_state: str,
    reason: str,
    justification: str,
    actor: Optional[Actor] = None,
    context: Optional[EventContext] = None,
) -> None:
    """
    Emit a force-complete event (founder action).

    Args:
        tenant_id: The tenant being force-completed
        from_state: State before force-complete
        reason: Why force-complete was invoked
        justification: Detailed justification (min 10 chars)
        actor: Who triggered the event (should be founder)
        context: Correlation context
    """
    emit_event(
        event_type=EVENT_ONBOARDING_FORCE_COMPLETE,
        event_source=EventSource.FOUNDER,
        tenant_id=tenant_id,
        severity=Severity.WARN,  # Force-complete is notable
        payload={
            "from_state": from_state,
            "reason": reason,
            "justification": justification,
        },
        actor=actor,
        context=context,
    )


# =============================================================================
# BILLING EMITTERS
# =============================================================================


def emit_billing_state_changed(
    tenant_id: str,
    from_state: str,
    to_state: str,
    plan_id: str,
    actor: Optional[Actor] = None,
    context: Optional[EventContext] = None,
) -> None:
    """
    Emit a billing state change event.

    Args:
        tenant_id: The tenant whose billing state changed
        from_state: Previous billing state
        to_state: New billing state
        plan_id: Current plan ID
        actor: Who triggered the event
        context: Correlation context
    """
    emit_event(
        event_type=EVENT_BILLING_STATE_CHANGED,
        event_source=EventSource.BILLING,
        tenant_id=tenant_id,
        severity=Severity.INFO,
        payload={
            "from_state": from_state,
            "to_state": to_state,
            "plan_id": plan_id,
        },
        actor=actor,
        context=context,
    )


def emit_billing_limit_evaluated(
    tenant_id: str,
    limit_name: str,
    current_value: int,
    allowed_value: int,
    exceeded: bool,
    actor: Optional[Actor] = None,
    context: Optional[EventContext] = None,
) -> None:
    """
    Emit a billing limit evaluation event.

    Args:
        tenant_id: The tenant being evaluated
        limit_name: Name of the limit (e.g., "max_requests_per_day")
        current_value: Current usage value
        allowed_value: Maximum allowed value
        exceeded: Whether the limit was exceeded
        actor: Who triggered the event
        context: Correlation context
    """
    emit_event(
        event_type=EVENT_BILLING_LIMIT_EVALUATED,
        event_source=EventSource.BILLING,
        tenant_id=tenant_id,
        severity=Severity.WARN if exceeded else Severity.INFO,
        payload={
            "limit_name": limit_name,
            "current_value": current_value,
            "allowed_value": allowed_value,
            "exceeded": exceeded,
        },
        actor=actor,
        context=context,
    )


# =============================================================================
# PROTECTION EMITTERS
# =============================================================================


def emit_protection_decision(
    tenant_id: str,
    decision: str,
    dimension: str,
    endpoint: str,
    retry_after_ms: Optional[int] = None,
    actor: Optional[Actor] = None,
    context: Optional[EventContext] = None,
) -> None:
    """
    Emit a protection decision event.

    Args:
        tenant_id: The tenant receiving the decision
        decision: Decision outcome (ALLOW, THROTTLE, REJECT, WARN)
        dimension: Protection dimension (rate, burst, cost)
        endpoint: The endpoint being protected
        retry_after_ms: Retry delay if applicable
        actor: Who triggered the event
        context: Correlation context
    """
    # Determine severity based on decision
    severity = Severity.INFO
    if decision in ("THROTTLE", "WARN"):
        severity = Severity.WARN
    elif decision == "REJECT":
        severity = Severity.ERROR

    payload: dict = {
        "decision": decision,
        "dimension": dimension,
        "endpoint": endpoint,
    }
    if retry_after_ms is not None:
        payload["retry_after_ms"] = retry_after_ms

    emit_event(
        event_type=EVENT_PROTECTION_DECISION,
        event_source=EventSource.PROTECTION,
        tenant_id=tenant_id,
        severity=severity,
        payload=payload,
        actor=actor,
        context=context,
    )


def emit_protection_anomaly_detected(
    tenant_id: str,
    baseline: int,
    observed: int,
    window: str,
    anomaly_severity: str,
    actor: Optional[Actor] = None,
    context: Optional[EventContext] = None,
) -> None:
    """
    Emit an anomaly detection event.

    ABUSE-003: Anomaly detection never blocks user traffic.
    This is informational only.

    Args:
        tenant_id: The tenant with anomalous behavior
        baseline: Expected baseline value
        observed: Actual observed value
        window: Time window (e.g., "1min")
        anomaly_severity: Severity of the anomaly (info, warning, critical)
        actor: Who triggered the event (usually system)
        context: Correlation context
    """
    # Map anomaly severity to event severity
    severity = Severity.INFO
    if anomaly_severity == "warning":
        severity = Severity.WARN
    elif anomaly_severity == "critical":
        severity = Severity.ERROR

    emit_event(
        event_type=EVENT_PROTECTION_ANOMALY_DETECTED,
        event_source=EventSource.PROTECTION,
        tenant_id=tenant_id,
        severity=severity,
        payload={
            "baseline": baseline,
            "observed": observed,
            "window": window,
            "severity": anomaly_severity,
        },
        actor=actor,
        context=context,
    )


# =============================================================================
# AUTH EMITTERS
# =============================================================================


def emit_role_violation(
    tenant_id: str,
    required_role: str,
    actual_role: str,
    endpoint: str,
    actor: Optional[Actor] = None,
    context: Optional[EventContext] = None,
) -> None:
    """
    Emit a role violation event.

    Args:
        tenant_id: The tenant where violation occurred
        required_role: Role required for the endpoint
        actual_role: Role the user actually has
        endpoint: The endpoint that was accessed
        actor: Who triggered the event
        context: Correlation context
    """
    emit_event(
        event_type=EVENT_ROLE_VIOLATION,
        event_source=EventSource.AUTH,
        tenant_id=tenant_id,
        severity=Severity.ERROR,
        payload={
            "required_role": required_role,
            "actual_role": actual_role,
            "endpoint": endpoint,
        },
        actor=actor,
        context=context,
    )


def emit_unauthorized_access(
    tenant_id: str,
    reason: str,
    endpoint: str,
    method: str,
    actor: Optional[Actor] = None,
    context: Optional[EventContext] = None,
) -> None:
    """
    Emit an unauthorized access attempt event.

    Args:
        tenant_id: The tenant where attempt occurred
        reason: Why access was denied
        endpoint: The endpoint that was accessed
        method: HTTP method (GET, POST, etc.)
        actor: Who triggered the event
        context: Correlation context
    """
    emit_event(
        event_type=EVENT_UNAUTHORIZED_ACCESS,
        event_source=EventSource.AUTH,
        tenant_id=tenant_id,
        severity=Severity.ERROR,
        payload={
            "reason": reason,
            "endpoint": endpoint,
            "method": method,
        },
        actor=actor,
        context=context,
    )


__all__ = [
    # Generic emitter
    "emit_event",
    # Onboarding emitters
    "emit_onboarding_state_transition",
    "emit_onboarding_force_complete",
    # Billing emitters
    "emit_billing_state_changed",
    "emit_billing_limit_evaluated",
    # Protection emitters
    "emit_protection_decision",
    "emit_protection_anomaly_detected",
    # Auth emitters
    "emit_role_violation",
    "emit_unauthorized_access",
]
