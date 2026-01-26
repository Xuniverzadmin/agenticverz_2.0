# Layer: L5 — Domain Engine
# AUDIENCE: CUSTOMER
# Product: ai-console
# Temporal:
#   Trigger: api
#   Execution: sync
# Lifecycle:
#   Emits: none
#   Subscribes: none
# Data Access:
#   Reads: none
#   Writes: none
# Role: Severity calculation and escalation decisions for incidents
# Callers: incident_aggregator.py (L6), incident engines
# Allowed Imports: L5, L6
# Forbidden Imports: L1, L2, L3, sqlalchemy (runtime)
# Reference: PIN-470, INCIDENTS_PHASE2.5_IMPLEMENTATION_PLAN.md — Violation I.3

"""
Incident Severity Engine (L4)

Business logic for incident severity decisions:
- Initial severity mapping from trigger type
- Severity calculation from affected calls
- Escalation decisions

Design Rules:
- Pure business logic, no DB access
- Stateless calculations
- No I/O operations
- Returns computed values for drivers to persist

This engine was extracted from incident_aggregator.py per HOC Layer Topology V1.
"""

from dataclasses import dataclass
from typing import Dict, Tuple

from app.models.killswitch import IncidentSeverity


# =============================================================================
# Configuration (Business Rules)
# =============================================================================


@dataclass
class SeverityConfig:
    """Configuration for severity decisions."""

    # Thresholds for severity escalation based on affected calls
    # Business rule: more affected calls = higher severity
    severity_thresholds: Dict[str, int]

    @classmethod
    def default(cls) -> "SeverityConfig":
        """Default severity thresholds."""
        return cls(
            severity_thresholds={
                "low": 1,
                "medium": 10,
                "high": 50,
                "critical": 200,
            }
        )


# =============================================================================
# Initial Severity Mapping (Business Rule)
# =============================================================================


# Trigger type to initial severity mapping
# This is a domain decision: certain trigger types are inherently more severe
TRIGGER_SEVERITY_MAP: Dict[str, str] = {
    "budget_breach": IncidentSeverity.CRITICAL.value,
    "failure_spike": IncidentSeverity.HIGH.value,
    "rate_limit": IncidentSeverity.MEDIUM.value,
    "content_policy": IncidentSeverity.HIGH.value,
    "freeze": IncidentSeverity.CRITICAL.value,
}

DEFAULT_SEVERITY = IncidentSeverity.MEDIUM.value


# =============================================================================
# Incident Severity Engine
# =============================================================================


class IncidentSeverityEngine:
    """
    L4 Engine for incident severity decisions.

    RESPONSIBILITIES:
    - Calculate initial severity from trigger type
    - Calculate severity from affected calls count
    - Determine if severity should escalate

    FORBIDDEN:
    - Database access
    - I/O operations
    - State mutation (stateless calculations only)
    """

    def __init__(self, config: SeverityConfig | None = None):
        self.config = config or SeverityConfig.default()

    def get_initial_severity(self, trigger_type: str) -> str:
        """
        Get initial severity based on trigger type.

        Business rule: certain trigger types have inherent severity levels.

        Args:
            trigger_type: Type of incident trigger (e.g., budget_breach, failure_spike)

        Returns:
            Initial severity value (LOW, MEDIUM, HIGH, CRITICAL)
        """
        return TRIGGER_SEVERITY_MAP.get(trigger_type, DEFAULT_SEVERITY)

    def calculate_severity_for_calls(self, calls_affected: int) -> str:
        """
        Calculate severity based on number of affected calls.

        Business rule: severity increases with impact (more calls = higher severity).

        Args:
            calls_affected: Number of calls affected by the incident

        Returns:
            Severity value (LOW, MEDIUM, HIGH, CRITICAL)
        """
        thresholds = self.config.severity_thresholds

        if calls_affected >= thresholds["critical"]:
            return IncidentSeverity.CRITICAL.value
        elif calls_affected >= thresholds["high"]:
            return IncidentSeverity.HIGH.value
        elif calls_affected >= thresholds["medium"]:
            return IncidentSeverity.MEDIUM.value
        else:
            return IncidentSeverity.LOW.value

    def should_escalate(
        self,
        current_severity: str,
        calls_affected: int,
    ) -> Tuple[bool, str]:
        """
        Determine if an incident should be escalated.

        Business rule: escalate if calculated severity exceeds current severity.

        Args:
            current_severity: Current severity of the incident
            calls_affected: Current number of affected calls

        Returns:
            Tuple of (should_escalate, new_severity)
        """
        new_severity = self.calculate_severity_for_calls(calls_affected)

        # Check if escalation is needed (severity increased)
        if new_severity != current_severity:
            # Only escalate, never de-escalate
            severity_order = [
                IncidentSeverity.LOW.value,
                IncidentSeverity.MEDIUM.value,
                IncidentSeverity.HIGH.value,
                IncidentSeverity.CRITICAL.value,
            ]
            current_idx = severity_order.index(current_severity) if current_severity in severity_order else 0
            new_idx = severity_order.index(new_severity) if new_severity in severity_order else 0

            if new_idx > current_idx:
                return True, new_severity

        return False, current_severity


# =============================================================================
# Title Generation (Presentation Logic)
# =============================================================================


def generate_incident_title(trigger_type: str, trigger_value: str) -> str:
    """
    Generate human-readable incident title.

    This is presentation logic but lives here because it's domain-specific.

    Args:
        trigger_type: Type of incident trigger
        trigger_value: Value/details of the trigger

    Returns:
        Human-readable title string
    """
    titles = {
        "budget_breach": f"Budget limit exceeded: {trigger_value}",
        "failure_spike": f"Failure rate spike detected: {trigger_value}",
        "rate_limit": f"Rate limit triggered: {trigger_value}",
        "content_policy": f"Content policy violation: {trigger_value}",
        "freeze": f"Traffic stopped: {trigger_value}",
        "rate_limit_overflow": "Incident rate limit reached - Events aggregated",
    }
    return titles.get(trigger_type, f"{trigger_type}: {trigger_value}")


__all__ = [
    "IncidentSeverityEngine",
    "SeverityConfig",
    "TRIGGER_SEVERITY_MAP",
    "DEFAULT_SEVERITY",
    "generate_incident_title",
]
