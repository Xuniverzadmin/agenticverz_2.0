# Layer: L5 — Domain Engine
# AUDIENCE: CUSTOMER
# Product: system-wide
# Temporal:
#   Trigger: import-time
#   Execution: sync
# Lifecycle:
#   Emits: none
#   Subscribes: none
# Data Access:
#   Reads: none
#   Writes: none
# Role: Phase-7 Decision enum and result types
# Callers: AbuseProtectionProvider, protection middleware
# Allowed Imports: L5, L6
# Forbidden Imports: L1, L2, L3, sqlalchemy (runtime)
# Reference: PIN-470, PIN-399 Phase-7 (Abuse & Protection Layer)

"""
Phase-7 Abuse Protection — Decision Types

PIN-399 Phase-7: Abuse protection constrains behavior, not identity.

DESIGN INVARIANTS (LOCKED):
- ABUSE-001: Protection does not affect onboarding, roles, or billing state
- ABUSE-002: All enforcement outcomes are explicit (no silent failure)
- ABUSE-003: Anomaly detection never blocks user traffic
- ABUSE-004: Protection providers are swappable behind a fixed interface
- ABUSE-005: Mock provider must be behavior-compatible with real provider

DECISION OUTCOMES (Finite, Locked):
- ALLOW: Proceed
- THROTTLE: Delay / slow
- REJECT: Hard stop
- WARN: Allow + emit signal

No silent drops. No implicit retries.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class Decision(Enum):
    """
    Phase-7 Protection Decisions (Finite, Locked).

    Every protection check returns exactly one of these.

    SEMANTICS (LOCKED):
    - ALLOW: Proceed normally
    - THROTTLE: Proceed with delay
    - REJECT: Hard stop, return error
    - WARN: Proceed + emit signal (non-blocking)
    """

    ALLOW = "allow"
    THROTTLE = "throttle"
    REJECT = "reject"
    WARN = "warn"

    def blocks_request(self) -> bool:
        """Check if this decision blocks the request."""
        return self == Decision.REJECT

    def is_warning_only(self) -> bool:
        """Check if this is a non-blocking warning."""
        return self == Decision.WARN


@dataclass(frozen=True)
class ProtectionResult:
    """
    Result of a protection check.

    Attributes:
        decision: The enforcement decision (ALLOW, THROTTLE, REJECT, WARN)
        dimension: Which protection dimension triggered (rate, burst, cost)
        retry_after_ms: Milliseconds to wait before retry (for THROTTLE/REJECT)
        current_value: Current usage value that triggered the check
        allowed_value: The limit that was exceeded
        message: Human-readable explanation
    """

    decision: Decision
    dimension: str
    retry_after_ms: Optional[int] = None
    current_value: Optional[float] = None
    allowed_value: Optional[float] = None
    message: Optional[str] = None

    def to_error_response(self) -> dict:
        """
        Convert to error response format.

        Per PHASE_7_ABUSE_PROTECTION.md Section 7.5.
        """
        if self.decision == Decision.REJECT:
            if self.dimension == "cost":
                return {
                    "error": "cost_limit_exceeded",
                    "limit": self.dimension,
                    "current_value": self.current_value,
                    "allowed_value": self.allowed_value,
                }
            else:
                return {
                    "error": "rate_limited",
                    "dimension": self.dimension,
                    "retry_after_ms": self.retry_after_ms,
                }
        elif self.decision == Decision.THROTTLE:
            return {
                "error": "rate_limited",
                "dimension": self.dimension,
                "retry_after_ms": self.retry_after_ms,
            }
        else:
            return {}


@dataclass(frozen=True)
class AnomalySignal:
    """
    Anomaly detection signal (non-blocking per ABUSE-003).

    Anomaly signals are warnings only, never user-blocking.

    Attributes:
        baseline: Expected baseline value
        observed: Observed value
        window: Time window (e.g., "5m", "1h")
        severity: Severity level (low, medium, high)
    """

    baseline: float
    observed: float
    window: str
    severity: str

    def to_signal_response(self) -> dict:
        """
        Convert to signal format.

        Per PHASE_7_ABUSE_PROTECTION.md Section 7.5.
        """
        return {
            "signal": "usage_anomaly_detected",
            "baseline": self.baseline,
            "observed": self.observed,
            "window": self.window,
        }


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================


def allow() -> ProtectionResult:
    """Create an ALLOW result."""
    return ProtectionResult(decision=Decision.ALLOW, dimension="none")


def reject_rate_limit(
    dimension: str, retry_after_ms: int, message: Optional[str] = None
) -> ProtectionResult:
    """Create a REJECT result for rate limiting."""
    return ProtectionResult(
        decision=Decision.REJECT,
        dimension=dimension,
        retry_after_ms=retry_after_ms,
        message=message or f"Rate limit exceeded for {dimension}",
    )


def reject_cost_limit(
    current_value: float, allowed_value: float, message: Optional[str] = None
) -> ProtectionResult:
    """Create a REJECT result for cost limit."""
    return ProtectionResult(
        decision=Decision.REJECT,
        dimension="cost",
        current_value=current_value,
        allowed_value=allowed_value,
        message=message or "Cost limit exceeded",
    )


def throttle(
    dimension: str, retry_after_ms: int, message: Optional[str] = None
) -> ProtectionResult:
    """Create a THROTTLE result."""
    return ProtectionResult(
        decision=Decision.THROTTLE,
        dimension=dimension,
        retry_after_ms=retry_after_ms,
        message=message or f"Request throttled for {dimension}",
    )


def warn(dimension: str, message: Optional[str] = None) -> ProtectionResult:
    """Create a WARN result (non-blocking)."""
    return ProtectionResult(
        decision=Decision.WARN,
        dimension=dimension,
        message=message,
    )


__all__ = [
    "Decision",
    "ProtectionResult",
    "AnomalySignal",
    "allow",
    "reject_rate_limit",
    "reject_cost_limit",
    "throttle",
    "warn",
]
