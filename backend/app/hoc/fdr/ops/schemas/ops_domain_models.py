# Layer: L6 — Driver
# AUDIENCE: CUSTOMER
# Role: Ops domain models for operator intelligence views
# Product: system-wide (ops visibility)
# Temporal:
#   Trigger: api|scheduler
#   Execution: sync
# Callers: L3 adapters, L2 ops APIs
# Allowed Imports: L6 (stdlib only for models)
# Forbidden Imports: L6 infra artifacts (ErrorEnvelope, CorrelationContext)
# Reference: PIN-264 (Phase-S Ops Domain)


"""
Ops Domain Models — L4 Interpreted Meaning

These models represent OPERATOR understanding, NOT infra truth.

Design Principles:
- Derived: Computed from infra data, never raw infra
- Lossy: Intentionally simplified for human consumption
- Opinionated: Contains interpretation and severity judgment
- Role-scoped: Designed for operator visibility, not debugging

Publication Pipeline:
    L6 Infra (ErrorEnvelope, DecisionSnapshot)
        ↓ (translation happens in services)
    L4 Ops Domain Models (THIS FILE)
        ↓
    L3 View Adapters
        ↓
    L2 Ops APIs
        ↓
    L1 Consoles

HARD RULE:
    These models must NEVER import from app.infra.
    Translation from infra → ops happens in L4 services, not here.
    If you need infra types, you're in the wrong layer.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

# =============================================================================
# Enums (Ops-level, NOT infra-level)
# =============================================================================


class OpsSeverity(str, Enum):
    """
    Operator-facing severity levels.

    Distinct from ErrorSeverity (infra) — this is about
    operator action priority, not technical classification.
    """

    INFO = "info"  # Awareness only
    ATTENTION = "attention"  # Should review soon
    ACTION = "action"  # Requires operator action
    URGENT = "urgent"  # Requires immediate attention


class OpsIncidentCategory(str, Enum):
    """
    Operator-facing incident categories.

    These map to OPERATOR questions, not technical taxonomy:
    - "Why did this fail?"
    - "What component is struggling?"
    - "Is this a pattern or one-off?"
    """

    EXECUTION_FAILURE = "execution_failure"  # Run/workflow failed
    BUDGET_EXHAUSTION = "budget_exhaustion"  # Budget limits hit
    POLICY_VIOLATION = "policy_violation"  # Policy rules triggered
    RECOVERY_FAILURE = "recovery_failure"  # Recovery couldn't fix
    EXTERNAL_DEPENDENCY = "external_dependency"  # External service issue
    CONFIGURATION = "configuration"  # Misconfiguration detected
    RATE_LIMIT = "rate_limit"  # Rate limits triggered
    UNKNOWN = "unknown"  # Needs investigation


class OpsHealthStatus(str, Enum):
    """
    System health states for operators.
    """

    HEALTHY = "healthy"  # All good
    DEGRADED = "degraded"  # Partial issues
    UNHEALTHY = "unhealthy"  # Significant problems
    UNKNOWN = "unknown"  # Cannot determine


class OpsRiskLevel(str, Enum):
    """
    Risk levels for preflight findings.
    """

    LOW = "low"  # Minor concern
    MEDIUM = "medium"  # Should address before launch
    HIGH = "high"  # Must address before launch
    CRITICAL = "critical"  # Blocking issue


# =============================================================================
# Core Ops Domain Models
# =============================================================================


@dataclass(frozen=True)
class OpsIncident:
    """
    Aggregated incident for operator visibility.

    Represents a PATTERN of failures, not individual errors.
    Multiple infra errors may roll up into one incident.

    Example:
        "12 budget exhaustion failures in workflow-runner
         between 14:00-15:00, affecting 3 runs"
    """

    incident_id: str  # ops_inc_<uuid>
    category: OpsIncidentCategory
    severity: OpsSeverity
    title: str  # Human-readable summary
    description: str  # What happened

    # Scope
    component: str  # Affected component
    affected_runs: int  # How many runs impacted
    affected_agents: int  # How many agents impacted

    # Time window
    first_seen: datetime
    last_seen: datetime
    occurrence_count: int  # How many times

    # Correlation (opaque to UI)
    sample_correlation_id: Optional[str] = None  # For drill-down

    # Status
    is_resolved: bool = False
    resolved_at: Optional[datetime] = None

    # Additional context (for display only)
    context: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class OpsHealthSignal:
    """
    Current health state of a component or subsystem.

    Operators use this to answer: "Is the system OK right now?"
    """

    signal_id: str  # ops_health_<component>
    component: str  # What component
    status: OpsHealthStatus
    last_checked: datetime

    # Metrics (optional, for context)
    success_rate_pct: Optional[float] = None  # Last hour
    avg_latency_ms: Optional[float] = None
    active_incidents: int = 0

    # Human-readable
    summary: str = ""  # "Budget engine healthy, 99.2% success"

    # Trend
    trend: Optional[str] = None  # "improving" | "stable" | "degrading"


@dataclass(frozen=True)
class OpsRiskFinding:
    """
    Preflight risk finding for launch readiness.

    Operators use this to answer: "What would break if users arrive now?"
    """

    finding_id: str  # ops_risk_<uuid>
    risk_level: OpsRiskLevel
    category: str  # "observability" | "recovery" | "capacity"
    title: str  # "No error persistence configured"
    description: str  # Why this is a risk

    # Impact
    impact: str  # What happens if not addressed
    affected_components: List[str]

    # Recommendation
    recommendation: str  # What to do about it
    documentation_link: Optional[str] = None

    # Status
    acknowledged: bool = False
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[datetime] = None


@dataclass(frozen=True)
class OpsTrendMetric:
    """
    Time-series trend for operator dashboards.

    Not raw metrics — interpreted trends with meaning.
    """

    metric_id: str  # ops_trend_<name>
    name: str  # "Budget Exhaustion Rate"
    description: str

    # Current value
    current_value: float
    unit: str  # "per_hour" | "percentage" | "count"

    # Trend
    trend_direction: str  # "up" | "down" | "stable"
    change_pct: float  # +15.2% from previous period

    # Time context
    period_start: datetime
    period_end: datetime
    comparison_period: str  # "previous_hour" | "previous_day"

    # Thresholds (for alerting context)
    warning_threshold: Optional[float] = None
    critical_threshold: Optional[float] = None
    is_above_warning: bool = False
    is_above_critical: bool = False


@dataclass(frozen=True)
class OpsDecisionOutcome:
    """
    Summary of domain engine decisions for operator review.

    Operators use this to answer: "What decisions did the system make?"
    """

    outcome_id: str  # ops_decision_<uuid>
    decision_type: str  # "budget_halt" | "recovery_action" | "policy_block"
    component: str  # Which engine made it
    timestamp: datetime

    # Decision details (interpreted, not raw)
    summary: str  # "Halted run due to budget exhaustion"
    input_summary: str  # Redacted/summarized input context
    outcome: str  # "halt" | "allow" | "escalate"

    # Impact
    affected_run_id: Optional[str] = None
    affected_agent_id: Optional[str] = None

    # For audit trail
    decision_version: str  # Engine version that made it


@dataclass(frozen=True)
class OpsCorrelatedEvent:
    """
    Cross-component event correlation for incident investigation.

    Shows operators: "These things happened together"
    """

    correlation_id: str  # The correlation ID linking events
    event_count: int  # How many events share this ID
    time_span_seconds: float  # Duration of correlated activity

    # Components involved
    components: List[str]
    layers: List[str]  # ["L2", "L4", "L5"]

    # Timeline
    first_event: datetime
    last_event: datetime

    # Summary
    summary: str  # "Request traversed API → Budget → Worker"

    # Outcome
    final_outcome: str  # "success" | "failure" | "partial"
    failure_point: Optional[str] = None  # Where it broke, if any
