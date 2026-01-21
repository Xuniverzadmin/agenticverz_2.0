# Layer: L4 — Domain Engines
# Product: system-wide
# Reference: GAP-070 (Governance Degraded Mode)
"""
Governance Degraded Mode Services (GAP-070)

Provides services for governance degraded mode with incident response
integration. When governance systems are unavailable, the system enters
a DEGRADED state that properly surfaces to incident response.

This module provides:
    - GovernanceDegradedModeChecker: Validates and manages degraded state
    - DegradedModeIncidentCreator: Creates incidents for degraded mode
    - DegradedModeState: State tracking for degraded mode
    - Helper functions for degraded mode operations
"""

from app.services.governance.degraded.degraded_mode_checker import (
    DegradedModeCheckResponse,
    DegradedModeCheckResult,
    DegradedModeIncidentCreator,
    DegradedModeState,
    GovernanceDegradedModeChecker,
    GovernanceDegradedModeError,
    check_degraded_mode,
    enter_degraded_with_incident,
    ensure_not_degraded,
)

__all__ = [
    "DegradedModeCheckResponse",
    "DegradedModeCheckResult",
    "DegradedModeIncidentCreator",
    "DegradedModeState",
    "GovernanceDegradedModeChecker",
    "GovernanceDegradedModeError",
    "check_degraded_mode",
    "enter_degraded_with_incident",
    "ensure_not_degraded",
]
