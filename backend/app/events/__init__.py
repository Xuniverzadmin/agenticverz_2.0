# Layer: L6 — Platform Substrate
# Product: system-wide
# Temporal:
#   Trigger: import-time
#   Execution: sync
# Role: Event system package marker
# Callers: Event imports
# Allowed Imports: None
# Forbidden Imports: None
# Reference: Package Structure, PIN-454 Phase 5

# NOVA Events Package
# Event publishing adapters and subscribers

from .publisher import BasePublisher, LoggingPublisher, get_publisher

# PIN-454 Phase 5: Event Reactor (Subscribers)
from .subscribers import (
    EVENT_REACTOR_ENABLED,
    EventEnvelope,
    EventReactor,
    EventReactorStats,
    ReactorState,
    get_event_reactor,
    reset_event_reactor,
)

# PIN-454 Phase 5: Audit Event Handlers
from .audit_handlers import (
    AUDIT_ALERTS_ENABLED,
    AlertSeverity,
    AuditAlert,
    AuditAlertType,
    register_audit_handlers,
)

__all__ = [
    # Publisher (existing)
    "get_publisher",
    "BasePublisher",
    "LoggingPublisher",
    # Reactor (PIN-454 Phase 5)
    "EventReactor",
    "get_event_reactor",
    "reset_event_reactor",
    "EventEnvelope",
    "EventReactorStats",
    "ReactorState",
    "EVENT_REACTOR_ENABLED",
    # Audit Handlers (PIN-454 Phase 5)
    "register_audit_handlers",
    "AuditAlert",
    "AuditAlertType",
    "AlertSeverity",
    "AUDIT_ALERTS_ENABLED",
]
