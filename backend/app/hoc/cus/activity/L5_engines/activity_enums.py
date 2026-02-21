# capability_id: CAP-012
# Layer: L5 — Domain Engine
# AUDIENCE: CUSTOMER
# Product: ai-console
# Temporal:
#   Trigger: N/A (static definitions)
#   Execution: N/A
# Lifecycle:
#   Emits: none
#   Subscribes: none
# Data Access:
#   Reads: none (pure definitions)
#   Writes: none
# Role: Canonical enums for activity domain - owned by engines
# Callers: activity_facade.py, signal engines
# Allowed Imports: none (pure enums)
# Forbidden Imports: all (pure enums, no imports needed)
# Reference: PIN-470, ACT-DUP-006, ACTIVITY_DTO_RULES.md
# NOTE: Reclassified L6→L5 (2026-01-24) - pure enum definitions, no DB ops
"""
Activity Domain Enums

Canonical enum definitions for the activity domain.
These are the single source of truth for categorical fields.

Rules (per ACT-DUP-006, ACTIVITY_DTO_RULES.md):
- No free-text categorical fields in Activity
- Signals are governance inputs - they must be enumerable
- Engines own canonical enums, facades import them
"""

from enum import Enum


class SignalType(str, Enum):
    """
    Canonical signal types for activity domain.

    Signals are governance inputs and must be enumerable.
    No free-text signal types allowed.
    """

    COST_RISK = "cost_risk"
    TIME_RISK = "time_risk"
    TOKEN_RISK = "token_risk"
    RATE_RISK = "rate_risk"
    POLICY_BREACH = "policy_breach"
    EVIDENCE_DEGRADED = "evidence_degraded"
    RELIABILITY = "reliability"
    SECURITY = "security"
    THRESHOLD_PROXIMITY = "threshold_proximity"


class SeverityLevel(str, Enum):
    """
    Canonical severity levels for display/UI.

    Rule (per ACT-DUP-005):
    - Engines speak numbers (severity_score: float 0.0-1.0)
    - Facades render labels (severity_level: SeverityLevel)

    Conversion:
    - HIGH: score >= 0.7
    - MEDIUM: score >= 0.4
    - LOW: score < 0.4
    """

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

    @classmethod
    def from_score(cls, score: float) -> "SeverityLevel":
        """Convert numeric severity score (0.0-1.0) to level."""
        if score >= 0.7:
            return cls.HIGH
        elif score >= 0.4:
            return cls.MEDIUM
        return cls.LOW

    @classmethod
    def from_risk_level(cls, risk_level: str) -> "SeverityLevel":
        """Convert risk level string to severity level."""
        if risk_level == "VIOLATED":
            return cls.HIGH
        elif risk_level == "AT_RISK":
            return cls.MEDIUM
        return cls.LOW


class RunState(str, Enum):
    """Run lifecycle state."""

    LIVE = "LIVE"
    COMPLETED = "COMPLETED"


class RiskType(str, Enum):
    """Types of risk for threshold signals."""

    COST = "COST"
    TIME = "TIME"
    TOKENS = "TOKENS"
    RATE = "RATE"


class EvidenceHealth(str, Enum):
    """Evidence health status."""

    FLOWING = "FLOWING"
    DEGRADED = "DEGRADED"
    MISSING = "MISSING"


__all__ = [
    "SignalType",
    "SeverityLevel",
    "RunState",
    "RiskType",
    "EvidenceHealth",
]
