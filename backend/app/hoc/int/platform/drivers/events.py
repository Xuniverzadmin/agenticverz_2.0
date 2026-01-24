# Layer: L4 — Domain Engine
# Product: system-wide
# Temporal:
#   Trigger: import-time
#   Execution: sync
# Role: Phase-8 Unified Event model
# Callers: ObservabilityProvider, event emitters
# Allowed Imports: None (foundational types)
# Forbidden Imports: L1, L2, L3, L5, L6
# Reference: PIN-399 Phase-8 (Observability Unification)

"""
Phase-8 Unified Event Model

PIN-399 Phase-8: Observability answers "what happened?" — never "what should happen?"

DESIGN INVARIANTS (LOCKED):
- OBSERVE-001: Observability never mutates system state
- OBSERVE-002: Events are immutable once accepted
- OBSERVE-003: All events are tenant-scoped
- OBSERVE-004: Failure to emit must not block execution
- OBSERVE-005: Mock provider must be interface-compatible with real provider

CORE CONCEPT:
    Everything becomes an event.
    Events are append-only.
    Events are never mutated.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional
import uuid


class Severity(Enum):
    """
    Event severity levels.

    Used for filtering and prioritization, not enforcement.
    """

    INFO = "INFO"
    WARN = "WARN"
    ERROR = "ERROR"


class ActorType(Enum):
    """
    Type of actor that triggered the event.
    """

    HUMAN = "human"      # Console user action
    MACHINE = "machine"  # SDK/API key action
    SYSTEM = "system"    # Background job, scheduler


class EventSource(Enum):
    """
    Source system that generated the event.
    """

    ONBOARDING = "onboarding"
    BILLING = "billing"
    PROTECTION = "protection"
    FOUNDER = "founder"
    AUTH = "auth"
    SYSTEM = "system"


@dataclass(frozen=True)
class Actor:
    """
    Who triggered the event.

    Attributes:
        type: Actor type (human, machine, system)
        id: Actor identifier (user ID, API key ID, or None for system)
    """

    type: ActorType
    id: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "type": self.type.value,
            "id": self.id,
        }


@dataclass(frozen=True)
class EventContext:
    """
    Correlation context for the event.

    Enables correlation across requests and distributed operations.
    Correlation is opt-in, best-effort, never assumed.

    Attributes:
        request_id: Ties events to a single API request
        trace_id: Ties events across distributed operations
    """

    request_id: Optional[str] = None
    trace_id: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "request_id": self.request_id,
            "trace_id": self.trace_id,
        }


@dataclass(frozen=True)
class UnifiedEvent:
    """
    Phase-8 Unified Event Model (Canonical).

    This is the single canonical event format for all observability data.
    Events are immutable once created (frozen dataclass).

    REQUIRED DIMENSIONS (per design):
    - event_id: Unique identifier
    - tenant_id: Primary query axis
    - timestamp: Ordering
    - event_source: Phase boundary
    - event_type: Semantics
    - severity: Filtering
    - payload: Domain detail

    IMMUTABILITY:
    - Events are append-only
    - No updates, no deletes
    - Order defined by (timestamp, event_id)

    Attributes:
        event_id: UUID string (auto-generated if not provided)
        event_type: Event type string (e.g., "billing_state_changed")
        event_source: Source system (onboarding, billing, protection, etc.)
        tenant_id: Tenant identifier (primary query axis)
        timestamp: UTC timestamp (auto-generated if not provided)
        severity: Event severity (INFO, WARN, ERROR)
        actor: Who triggered the event
        context: Correlation context
        payload: Domain-specific details
    """

    event_type: str
    event_source: EventSource
    tenant_id: str
    severity: Severity
    payload: dict = field(default_factory=dict)
    actor: Actor = field(default_factory=lambda: Actor(type=ActorType.SYSTEM))
    context: EventContext = field(default_factory=EventContext)
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self) -> None:
        """Validate required fields."""
        if not self.event_type:
            raise ValueError("event_type is required")
        if not self.tenant_id:
            raise ValueError("tenant_id is required (OBSERVE-003)")

    def to_dict(self) -> dict:
        """
        Convert to dictionary for serialization.

        Matches the canonical JSON schema from the design document.
        """
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "event_source": self.event_source.value,
            "tenant_id": self.tenant_id,
            "timestamp": self.timestamp.isoformat(),
            "severity": self.severity.value,
            "actor": self.actor.to_dict(),
            "context": self.context.to_dict(),
            "payload": self.payload,
        }


# =============================================================================
# EVENT TYPE CONSTANTS
# =============================================================================

# Onboarding events
EVENT_ONBOARDING_STATE_TRANSITION = "onboarding_state_transition"
EVENT_ONBOARDING_FORCE_COMPLETE = "onboarding_force_complete"

# Billing events
EVENT_BILLING_STATE_CHANGED = "billing_state_changed"
EVENT_BILLING_LIMIT_EVALUATED = "billing_limit_evaluated"

# Protection events
EVENT_PROTECTION_DECISION = "protection_decision"
EVENT_PROTECTION_ANOMALY_DETECTED = "protection_anomaly_detected"

# Auth events
EVENT_ROLE_VIOLATION = "role_violation"
EVENT_UNAUTHORIZED_ACCESS = "unauthorized_access_attempt"


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
]
