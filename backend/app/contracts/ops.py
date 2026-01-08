# Layer: L4 — Domain Engine
# Product: system-wide
# Temporal:
#   Trigger: api
#   Execution: sync
# Role: Ops contract definitions
# Callers: Ops console API
# Allowed Imports: L6
# Forbidden Imports: L1, L2, L3, L5
# Reference: Contract System

"""
Ops Console Data Contracts - Founder-Facing API

DOMAIN: Founder Ops Console (/ops/*)
AUDIENCE: Founders/Operators (global view)
AUTH: aud="fops", requires mfa=true

These contracts are FROZEN as of M29. Changes require:
1. Deprecation annotation
2. 2-version grace period
3. PIN documentation

INVARIANTS:
- All responses are GLOBAL (cross-tenant aggregation allowed)
- Contains founder-only intelligence (not for customers)
- Times are ISO8601 strings
- IDs are prefixed strings (tenant_*, etc.)

CRITICAL: These contracts MUST NOT be exposed to Customer Console.
"""

from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field

# =============================================================================
# SYSTEM PULSE - "Is my business healthy?"
# =============================================================================


class SystemPulseDTO(BaseModel):
    """
    GET /ops/pulse response.

    Real-time system health for founders.
    Frozen: 2025-12-23 (M29)
    """

    status: Literal["stable", "elevated", "degraded", "critical"]
    active_customers: int = Field(ge=0, description="Customers with activity in last 24h")
    incidents_24h: int = Field(ge=0)
    incidents_7d: int = Field(ge=0)
    revenue_today_cents: int = Field(ge=0)
    revenue_7d_cents: int = Field(ge=0)
    error_rate_percent: float = Field(ge=0, le=100)
    p99_latency_ms: int = Field(ge=0)
    customers_at_risk: int = Field(ge=0, description="Customers showing churn signals")
    last_updated: str = Field(description="ISO8601")

    class Config:
        json_schema_extra = {
            "example": {
                "status": "stable",
                "active_customers": 42,
                "incidents_24h": 3,
                "incidents_7d": 15,
                "revenue_today_cents": 125000,
                "revenue_7d_cents": 875000,
                "error_rate_percent": 0.02,
                "p99_latency_ms": 145,
                "customers_at_risk": 2,
                "last_updated": "2025-12-23T10:15:00Z",
            }
        }


# =============================================================================
# CUSTOMER INTEL - "Who is this customer?"
# =============================================================================


class CustomerSegmentDTO(BaseModel):
    """
    Customer profile with engagement metrics.

    GET /ops/customers and GET /ops/customers/{id} response.
    Frozen: 2025-12-23 (M29)
    """

    tenant_id: str
    tenant_name: str
    segment: Literal["enterprise", "growth", "starter", "trial", "churned"]
    status: Literal["healthy", "declining", "at_risk", "churned"]

    # Engagement metrics
    stickiness_7d: float = Field(ge=0, description="7-day engagement score")
    stickiness_30d: float = Field(ge=0, description="30-day baseline")
    stickiness_delta: float = Field(description="7d/30d ratio, <1 means declining")

    # Activity
    api_calls_7d: int = Field(ge=0)
    incidents_7d: int = Field(ge=0)
    last_activity: Optional[str] = Field(None, description="ISO8601")
    days_since_last_login: Optional[int] = Field(None, ge=0)

    # Revenue
    mrr_cents: int = Field(ge=0, description="Monthly recurring revenue")
    ltv_cents: int = Field(ge=0, description="Lifetime value")

    # Signals
    churn_risk_score: float = Field(ge=0, le=1, description="0-1 churn probability")
    top_features_used: List[str] = Field(default_factory=list)


class CustomerAtRiskDTO(BaseModel):
    """
    Customer at risk of churning.

    GET /ops/customers/at-risk response item.
    Frozen: 2025-12-23 (M29)
    """

    tenant_id: str
    tenant_name: str
    risk_level: Literal["critical", "high", "medium"]
    risk_signals: List[str] = Field(description="Why they're at risk")
    days_at_risk: int = Field(ge=0)
    last_activity: Optional[str] = None
    suggested_action: str = Field(description="call, email, feature_help, pricing")
    mrr_cents: int = Field(ge=0)
    stickiness_delta: float


class CustomerListDTO(BaseModel):
    """GET /ops/customers response."""

    customers: List[CustomerSegmentDTO]
    total: int
    page: int
    page_size: int


# =============================================================================
# INCIDENT PATTERNS - "What is breaking systemically?"
# =============================================================================


class IncidentPatternDTO(BaseModel):
    """
    Aggregated incident pattern across all tenants.

    GET /ops/incidents/patterns response item.
    Frozen: 2025-12-23 (M29)

    IMPORTANT: This is FOUNDER-ONLY data (cross-tenant aggregation).
    NEVER expose individual tenant patterns to Customer Console.
    """

    pattern_type: str = Field(description="cost_spike, rate_limit, policy_violation, etc.")
    occurrence_count: int = Field(ge=0)
    affected_tenants: int = Field(ge=0)
    first_seen: str = Field(description="ISO8601")
    last_seen: str = Field(description="ISO8601")
    is_systemic: bool = Field(description="True if affects >10% of active tenants")
    severity: Literal["critical", "high", "medium", "low"]
    trend: Literal["increasing", "stable", "decreasing"]
    total_cost_impact_cents: int = Field(ge=0)
    suggested_fix: Optional[str] = None


# =============================================================================
# FOUNDER INCIDENT DETAIL - "What failed? Why? What do we do?"
# M29 Category 5: Incident Console Contrast
# Added: 2025-12-24
# =============================================================================


class FounderIncidentHeaderDTO(BaseModel):
    """
    Incident header - dense, no prose, just facts.

    Part of GET /ops/incidents/{id} response.
    Frozen: 2025-12-24 (M29 Category 5)
    """

    incident_id: str
    incident_type: Literal["POLICY", "COST", "RELIABILITY", "RATE_LIMIT", "SAFETY"]
    severity: Literal["critical", "high", "medium", "low"]
    tenant_id: str
    tenant_name: Optional[str] = None
    current_state: Literal["DETECTED", "TRIAGED", "MITIGATED", "RESOLVED"]
    first_detected: str = Field(description="ISO8601")
    last_updated: str = Field(description="ISO8601")


class FounderDecisionTimelineEventDTO(BaseModel):
    """
    Single event in the decision timeline - raw truth, append-only.

    Frozen: 2025-12-24 (M29 Category 5)
    """

    timestamp: str = Field(description="ISO8601")
    event_type: Literal[
        "DETECTION_SIGNAL",
        "TRIGGER_CONDITION",
        "POLICY_EVALUATION",
        "COST_ANOMALY",
        "RECOVERY_ACTION",
        "RESOLUTION",
        "ESCALATION",
        "OPERATOR_ACTION",
    ]
    description: str
    data: Optional[Dict[str, Any]] = None


class FounderRootCauseDTO(BaseModel):
    """
    Root cause analysis - explicit, no hedging.

    Frozen: 2025-12-24 (M29 Category 5)
    """

    derived_cause: Literal[
        "RETRY_LOOP",
        "PROMPT_GROWTH",
        "FEATURE_SURGE",
        "TRAFFIC_GROWTH",
        "RATE_LIMIT_BREACH",
        "POLICY_VIOLATION",
        "BUDGET_EXCEEDED",
        "UNKNOWN",
    ]
    evidence: str = Field(description="E.g., 'retry/request +92% over baseline'")
    confidence: Literal["high", "medium", "low"]
    baseline_value: Optional[float] = None
    actual_value: Optional[float] = None
    threshold_breached: Optional[float] = None


class FounderBlastRadiusDTO(BaseModel):
    """
    Impact assessment - helps founders judge seriousness.

    Frozen: 2025-12-24 (M29 Category 5)
    """

    requests_affected: int = Field(ge=0)
    requests_blocked: int = Field(ge=0)
    cost_impact_cents: int = Field(description="Absolute cost impact")
    cost_impact_pct: float = Field(description="% of daily baseline")
    duration_seconds: int = Field(ge=0)
    customer_visible_degradation: bool = Field(description="True if customer experienced service degradation")
    users_affected: int = Field(ge=0)
    features_affected: List[str] = Field(default_factory=list)


class FounderRecurrenceRiskDTO(BaseModel):
    """
    Recurrence risk analysis - strategic, not operational.

    Frozen: 2025-12-24 (M29 Category 5)
    """

    similar_incidents_7d: int = Field(ge=0)
    similar_incidents_30d: int = Field(ge=0)
    same_tenant_recurrence: bool
    same_feature_recurrence: bool
    same_root_cause_recurrence: bool
    risk_level: Literal["high", "medium", "low"]
    suggested_prevention: Optional[str] = None


class FounderIncidentDetailDTO(BaseModel):
    """
    GET /ops/incidents/{id} response.

    Full incident with causality and impact analysis.
    Answers: What failed? Why? What do we do next?

    Frozen: 2025-12-24 (M29 Category 5)

    IMPORTANT: This is FOUNDER-ONLY data.
    Contains internal terminology, thresholds, and cross-tenant context.
    NEVER expose to Customer Console.
    """

    # Section A: Header (dense facts)
    header: FounderIncidentHeaderDTO

    # Section B: Full Decision Timeline (raw truth)
    timeline: List[FounderDecisionTimelineEventDTO]

    # Section C: Root Cause (explicit)
    root_cause: FounderRootCauseDTO

    # Section D: Blast Radius (impact)
    blast_radius: FounderBlastRadiusDTO

    # Section E: Recurrence Risk (strategic)
    recurrence_risk: FounderRecurrenceRiskDTO

    # Related data
    related_cost_anomaly_id: Optional[str] = None
    related_killswitch_id: Optional[str] = None
    linked_call_ids: List[str] = Field(default_factory=list)

    # Actions
    action_taken: Optional[str] = None
    action_details: Optional[Dict[str, Any]] = None
    recommended_next_steps: List[str] = Field(default_factory=list)

    class Config:
        json_schema_extra = {
            "example": {
                "header": {
                    "incident_id": "inc_abc123",
                    "incident_type": "COST",
                    "severity": "high",
                    "tenant_id": "tenant_xyz",
                    "tenant_name": "Acme Corp",
                    "current_state": "MITIGATED",
                    "first_detected": "2025-12-24T10:00:00Z",
                    "last_updated": "2025-12-24T10:15:00Z",
                },
                "timeline": [
                    {
                        "timestamp": "2025-12-24T10:00:00Z",
                        "event_type": "DETECTION_SIGNAL",
                        "description": "Cost anomaly detected: 40% above baseline",
                        "data": {"deviation_pct": 40.0},
                    }
                ],
                "root_cause": {
                    "derived_cause": "RETRY_LOOP",
                    "evidence": "retry/request +92% over baseline",
                    "confidence": "high",
                    "baseline_value": 0.05,
                    "actual_value": 0.48,
                    "threshold_breached": 0.40,
                },
                "blast_radius": {
                    "requests_affected": 1500,
                    "requests_blocked": 200,
                    "cost_impact_cents": 5000,
                    "cost_impact_pct": 45.0,
                    "duration_seconds": 900,
                    "customer_visible_degradation": False,
                    "users_affected": 12,
                    "features_affected": ["customer_support.chat"],
                },
                "recurrence_risk": {
                    "similar_incidents_7d": 1,
                    "similar_incidents_30d": 3,
                    "same_tenant_recurrence": True,
                    "same_feature_recurrence": True,
                    "same_root_cause_recurrence": True,
                    "risk_level": "high",
                    "suggested_prevention": "Review retry logic in customer_support.chat feature",
                },
            }
        }


class FounderIncidentListItemDTO(BaseModel):
    """
    Incident list item for founder console.

    Used in GET /ops/incidents response.
    Frozen: 2025-12-24 (M29 Category 5)
    """

    incident_id: str
    incident_type: Literal["POLICY", "COST", "RELIABILITY", "RATE_LIMIT", "SAFETY"]
    severity: Literal["critical", "high", "medium", "low"]
    current_state: Literal["DETECTED", "TRIAGED", "MITIGATED", "RESOLVED"]
    tenant_id: str
    tenant_name: Optional[str] = None
    title: str
    root_cause: Optional[str] = None
    requests_affected: int = Field(ge=0)
    cost_impact_cents: int = Field(ge=0)
    first_detected: str
    duration_seconds: Optional[int] = None
    is_recurring: bool = Field(description="True if similar incident in last 7 days")


class FounderIncidentListDTO(BaseModel):
    """
    GET /ops/incidents response (paginated).

    Frozen: 2025-12-24 (M29 Category 5)
    """

    incidents: List[FounderIncidentListItemDTO]
    total: int = Field(ge=0)
    page: int = Field(ge=1)
    page_size: int = Field(ge=1, le=100)
    # Summary stats
    active_count: int = Field(ge=0, description="Non-resolved incidents")
    critical_count: int = Field(ge=0)
    high_count: int = Field(ge=0)


# =============================================================================
# STICKINESS - "Which features keep users?"
# =============================================================================


class StickinessByFeatureDTO(BaseModel):
    """
    Feature engagement metrics.

    GET /ops/stickiness response item.
    Frozen: 2025-12-23 (M29)
    """

    feature_name: str
    usage_count_7d: int = Field(ge=0)
    unique_tenants: int = Field(ge=0)
    retention_correlation: float = Field(ge=-1, le=1, description="Correlation with retention, 1 = strongly predictive")
    avg_session_depth: float = Field(ge=0, description="Avg actions per session")
    is_sticky: bool = Field(description="True if retention_correlation > 0.5")


# =============================================================================
# REVENUE & RISK - "Am I making money safely?"
# =============================================================================


class RevenueRiskDTO(BaseModel):
    """
    GET /ops/revenue response.

    Revenue metrics with risk indicators.
    Frozen: 2025-12-23 (M29)
    """

    mrr_cents: int = Field(ge=0, description="Monthly recurring revenue")
    arr_cents: int = Field(ge=0, description="Annual run rate")
    revenue_7d_cents: int = Field(ge=0)
    revenue_30d_cents: int = Field(ge=0)

    # Concentration risk
    top_customer_percent: float = Field(ge=0, le=100, description="% of revenue from top customer")
    top_3_customers_percent: float = Field(ge=0, le=100)
    concentration_risk: Literal["low", "medium", "high", "critical"]

    # Churn exposure
    at_risk_mrr_cents: int = Field(ge=0, description="MRR from at-risk customers")
    churn_rate_30d: float = Field(ge=0, le=100, description="% customers churned")

    # Growth
    net_revenue_retention: float = Field(description="NRR %, >100 is expansion")
    new_mrr_cents: int = Field(ge=0, description="New MRR this month")


# =============================================================================
# INFRA LIMITS - "What breaks first if I grow?"
# =============================================================================


class InfraLimitsDTO(BaseModel):
    """
    GET /ops/infra response.

    Infrastructure capacity and limits.
    Frozen: 2025-12-23 (M29)
    """

    # Database
    db_connections_used: int = Field(ge=0)
    db_connections_max: int = Field(ge=0)
    db_connections_percent: float = Field(ge=0, le=100)

    # Redis
    redis_memory_used_mb: int = Field(ge=0)
    redis_memory_max_mb: int = Field(ge=0)
    redis_memory_percent: float = Field(ge=0, le=100)

    # Workers
    worker_queue_depth: int = Field(ge=0)
    worker_concurrency: int = Field(ge=0)
    worker_utilization_percent: float = Field(ge=0, le=100)

    # API
    api_rate_current_rpm: int = Field(ge=0)
    api_rate_limit_rpm: int = Field(ge=0)
    api_rate_percent: float = Field(ge=0, le=100)

    # Bottleneck
    bottleneck: Optional[str] = Field(None, description="First limit to hit")
    headroom_percent: float = Field(ge=0, description="Capacity remaining")
    scale_trigger: Optional[str] = Field(None, description="What to scale first")


# =============================================================================
# PLAYBOOKS - "What actions should I take?"
# =============================================================================


class PlaybookActionDTO(BaseModel):
    """Individual action in a playbook."""

    step: int = Field(ge=1)
    action_type: Literal["call", "email", "feature_help", "pricing", "technical", "escalate"]
    description: str
    timing: str = Field(description="when to execute: immediately, within_24h, etc.")
    talk_track: Optional[str] = Field(None, description="Suggested script")


class PlaybookDTO(BaseModel):
    """
    GET /ops/playbooks and GET /ops/playbooks/{id} response.

    Founder playbook with actions.
    Frozen: 2025-12-23 (M29)
    """

    id: str = Field(description="Playbook ID (playbook_*)")
    name: str
    trigger_conditions: List[str] = Field(description="What triggers this playbook")
    risk_level: Literal["critical", "high", "medium", "low"]
    applicable_count: int = Field(ge=0, description="Customers matching this playbook")
    actions: List[PlaybookActionDTO]


# =============================================================================
# OPS EVENTS - Event sourcing
# =============================================================================


class OpsEventDTO(BaseModel):
    """
    Raw ops event.

    GET /ops/events response item.
    Frozen: 2025-12-23 (M29)
    """

    id: str
    tenant_id: str
    event_type: str
    event_data: Dict[str, Any]
    created_at: str


class OpsEventListDTO(BaseModel):
    """GET /ops/events response."""

    events: List[OpsEventDTO]
    total: int
    has_more: bool
    cursor: Optional[str] = None


# =============================================================================
# JOBS
# =============================================================================


class OpsJobResultDTO(BaseModel):
    """
    POST /ops/jobs/* response.

    Result of running an ops job.
    Frozen: 2025-12-23 (M29)
    """

    job_id: str
    job_type: str
    status: Literal["completed", "failed", "queued"]
    processed_count: int = Field(ge=0)
    affected_tenants: int = Field(ge=0)
    duration_ms: int = Field(ge=0)
    message: str


# =============================================================================
# COST INTELLIGENCE - "Where is money going?"
# Added: 2025-12-23 (M29 Category 4)
# =============================================================================


class FounderCostOverviewDTO(BaseModel):
    """
    GET /ops/cost/overview response.

    Global cost view for founders - deterministic from snapshots only.
    Frozen: 2025-12-23 (M29 Category 4)

    THE INVARIANT: All values derive from complete snapshots, never live data.
    """

    # Spend metrics
    spend_today_cents: int = Field(ge=0, description="Total spend today across all tenants")
    spend_mtd_cents: int = Field(ge=0, description="Month-to-date spend")
    spend_7d_cents: int = Field(ge=0, description="Last 7 days spend")

    # Anomaly summary
    tenants_with_anomalies: int = Field(ge=0, description="Tenants with active cost anomalies")
    total_anomalies_24h: int = Field(ge=0, description="Anomalies detected in last 24h")

    # Largest deviation
    largest_deviation_tenant_id: Optional[str] = Field(None, description="Tenant with biggest deviation")
    largest_deviation_pct: Optional[float] = Field(None, description="Deviation % from baseline")
    largest_deviation_type: Optional[str] = Field(None, description="user_spike, feature_spike, etc.")

    # Snapshot freshness
    last_snapshot_at: Optional[str] = Field(None, description="ISO8601 of last complete snapshot")
    snapshot_freshness_minutes: int = Field(ge=0, description="Minutes since last snapshot")
    snapshot_status: Literal["fresh", "stale", "missing"] = Field(description="fresh=<60min, stale=<24h, missing=>24h")

    # Trend
    trend_7d: Literal["increasing", "stable", "decreasing"] = Field(description="7-day cost trend")

    class Config:
        json_schema_extra = {
            "example": {
                "spend_today_cents": 125000,
                "spend_mtd_cents": 2500000,
                "spend_7d_cents": 875000,
                "tenants_with_anomalies": 3,
                "total_anomalies_24h": 5,
                "largest_deviation_tenant_id": "tenant_abc",
                "largest_deviation_pct": 450.0,
                "largest_deviation_type": "user_spike",
                "last_snapshot_at": "2025-12-23T10:00:00Z",
                "snapshot_freshness_minutes": 15,
                "snapshot_status": "fresh",
                "trend_7d": "stable",
            }
        }


class FounderCostAnomalyDTO(BaseModel):
    """
    Cost anomaly aggregation for founders.

    GET /ops/cost/anomalies response item.
    Frozen: 2025-12-23 (M29 Category 4)

    IMPORTANT: This is FOUNDER-ONLY cross-tenant aggregation.
    NEVER expose to Customer Console.
    """

    id: str = Field(description="Anomaly ID (anom_*)")
    anomaly_type: str = Field(description="user_spike, feature_spike, model_spike, tenant_spike")
    severity: Literal["critical", "high", "medium", "low"]

    # Entity
    entity_type: str = Field(description="user, feature, model, tenant")
    entity_id: Optional[str] = None

    # Values
    current_value_cents: float = Field(ge=0)
    expected_value_cents: float = Field(ge=0)
    deviation_pct: float = Field(description="% deviation from baseline")
    threshold_pct: float = Field(description="Threshold that was exceeded")

    # Cross-tenant (FOUNDER ONLY)
    affected_tenants: int = Field(ge=1, description="Number of tenants affected by similar pattern")
    is_systemic: bool = Field(description="True if affects >3 tenants")

    # Cause analysis (M29 Category 4)
    derived_cause: Optional[str] = Field(
        None, description="Root cause: RETRY_LOOP, PROMPT_GROWTH, FEATURE_SURGE, TRAFFIC_GROWTH, UNKNOWN"
    )
    breach_count: int = Field(
        default=1, ge=1, description="Consecutive intervals that breached threshold (2+ = confirmed spike)"
    )

    # Status
    message: str
    incident_id: Optional[str] = Field(None, description="Linked incident if escalated")
    action_taken: Optional[str] = None
    resolved: bool = False
    detected_at: str = Field(description="ISO8601")
    snapshot_id: Optional[str] = Field(None, description="Source snapshot ID")


class FounderCostAnomalyListDTO(BaseModel):
    """GET /ops/cost/anomalies response."""

    anomalies: List[FounderCostAnomalyDTO]
    total: int = Field(ge=0)
    tenants_affected: int = Field(ge=0, description="Unique tenants with anomalies")
    systemic_count: int = Field(ge=0, description="Cross-tenant systemic issues")


class FounderCostTenantDTO(BaseModel):
    """
    Per-tenant cost drilldown for founders.

    GET /ops/cost/tenants response item.
    Frozen: 2025-12-23 (M29 Category 4)
    """

    tenant_id: str
    tenant_name: str

    # Spend
    spend_today_cents: int = Field(ge=0)
    spend_mtd_cents: int = Field(ge=0)
    spend_7d_cents: int = Field(ge=0)

    # Deviation
    deviation_from_baseline_pct: Optional[float] = Field(None, description="% deviation from 7-day avg")
    baseline_7d_avg_cents: Optional[float] = None

    # Budget
    budget_monthly_cents: Optional[int] = Field(None, ge=0)
    budget_used_pct: Optional[float] = Field(None, ge=0, le=100)

    # Status
    has_anomaly: bool = Field(description="Has active cost anomaly")
    anomaly_count_24h: int = Field(ge=0)
    trend: Literal["increasing", "stable", "decreasing"]
    last_activity: Optional[str] = None


class FounderCostTenantListDTO(BaseModel):
    """GET /ops/cost/tenants response."""

    tenants: List[FounderCostTenantDTO]
    total: int
    page: int
    page_size: int


# =============================================================================
# CUSTOMER COST DRILLDOWN - "Why is this customer spending so much?"
# Added: 2025-12-24 (M29 Category 4 Enhancement)
# =============================================================================


class CostDailyBreakdownDTO(BaseModel):
    """Daily cost data point."""

    date: str = Field(description="ISO8601 date (YYYY-MM-DD)")
    spend_cents: int = Field(ge=0)
    request_count: int = Field(ge=0)
    avg_cost_per_request_cents: float = Field(ge=0)


class CostByFeatureDTO(BaseModel):
    """Cost attribution by feature."""

    feature_tag: str
    display_name: Optional[str] = None
    spend_cents: int = Field(ge=0)
    request_count: int = Field(ge=0)
    pct_of_total: float = Field(ge=0, le=100)
    trend: Literal["increasing", "stable", "decreasing"]


class CostByUserDTO(BaseModel):
    """Cost attribution by user (top N)."""

    user_id: str
    spend_cents: int = Field(ge=0)
    request_count: int = Field(ge=0)
    pct_of_total: float = Field(ge=0, le=100)
    is_anomalous: bool = Field(description="True if user has active anomaly")


class CostByModelDTO(BaseModel):
    """Cost attribution by LLM model."""

    model: str
    spend_cents: int = Field(ge=0)
    input_tokens: int = Field(ge=0)
    output_tokens: int = Field(ge=0)
    request_count: int = Field(ge=0)
    pct_of_total: float = Field(ge=0, le=100)


class CustomerAnomalyHistoryDTO(BaseModel):
    """Recent anomaly for this customer."""

    id: str
    anomaly_type: str
    severity: Literal["critical", "high", "medium", "low"]
    detected_at: str
    resolved: bool
    deviation_pct: float
    derived_cause: Optional[str] = None
    message: str


class FounderCustomerCostDrilldownDTO(BaseModel):
    """
    GET /ops/cost/customers/{id} response.

    Deep-dive cost analysis for a single customer.
    Frozen: 2025-12-24 (M29 Category 4 Enhancement)

    IMPORTANT: This is FOUNDER-ONLY data.
    Provides granular cost attribution to answer "why is this customer spending so much?"
    """

    # Customer identification
    tenant_id: str
    tenant_name: str

    # Summary
    spend_today_cents: int = Field(ge=0)
    spend_mtd_cents: int = Field(ge=0)
    spend_7d_cents: int = Field(ge=0)
    spend_30d_cents: int = Field(ge=0)

    # Baseline comparison
    baseline_7d_avg_cents: Optional[float] = None
    deviation_from_baseline_pct: Optional[float] = None

    # Budget status
    budget_monthly_cents: Optional[int] = Field(None, ge=0)
    budget_used_pct: Optional[float] = Field(None, ge=0, le=100)
    projected_month_end_cents: Optional[int] = Field(None, ge=0)
    days_until_budget_exhausted: Optional[int] = Field(None, ge=0)

    # Daily breakdown (last 7 days)
    daily_breakdown: List[CostDailyBreakdownDTO] = Field(description="Last 7 days")

    # Cost attribution
    by_feature: List[CostByFeatureDTO] = Field(description="Top features by cost")
    by_user: List[CostByUserDTO] = Field(description="Top 10 users by cost")
    by_model: List[CostByModelDTO] = Field(description="Cost by LLM model")

    # Largest cost driver
    largest_driver_type: Literal["feature", "user", "model"]
    largest_driver_name: str
    largest_driver_pct: float = Field(ge=0, le=100)

    # Anomaly history
    active_anomalies: int = Field(ge=0)
    recent_anomalies: List[CustomerAnomalyHistoryDTO] = Field(description="Last 5 anomalies for this customer")

    # Trend
    trend_7d: Literal["increasing", "stable", "decreasing"]
    trend_message: Optional[str] = None

    # Metadata
    last_activity: Optional[str] = None
    last_updated: str = Field(description="ISO8601 of data freshness")

    class Config:
        json_schema_extra = {
            "example": {
                "tenant_id": "tenant_abc123",
                "tenant_name": "Acme Corp",
                "spend_today_cents": 2500,
                "spend_mtd_cents": 45000,
                "spend_7d_cents": 18000,
                "spend_30d_cents": 72000,
                "baseline_7d_avg_cents": 2000.0,
                "deviation_from_baseline_pct": 25.0,
                "budget_monthly_cents": 100000,
                "budget_used_pct": 45.0,
                "projected_month_end_cents": 90000,
                "days_until_budget_exhausted": None,
                "daily_breakdown": [
                    {
                        "date": "2025-12-23",
                        "spend_cents": 2500,
                        "request_count": 150,
                        "avg_cost_per_request_cents": 16.67,
                    },
                    {
                        "date": "2025-12-22",
                        "spend_cents": 2300,
                        "request_count": 140,
                        "avg_cost_per_request_cents": 16.43,
                    },
                ],
                "by_feature": [
                    {
                        "feature_tag": "customer_support.chat",
                        "display_name": "Customer Support",
                        "spend_cents": 12000,
                        "request_count": 500,
                        "pct_of_total": 66.7,
                        "trend": "stable",
                    }
                ],
                "by_user": [
                    {
                        "user_id": "user_xyz",
                        "spend_cents": 5000,
                        "request_count": 200,
                        "pct_of_total": 27.8,
                        "is_anomalous": False,
                    }
                ],
                "by_model": [
                    {
                        "model": "claude-sonnet-4-20250514",
                        "spend_cents": 15000,
                        "input_tokens": 500000,
                        "output_tokens": 100000,
                        "request_count": 600,
                        "pct_of_total": 83.3,
                    }
                ],
                "largest_driver_type": "feature",
                "largest_driver_name": "customer_support.chat",
                "largest_driver_pct": 66.7,
                "active_anomalies": 0,
                "recent_anomalies": [],
                "trend_7d": "stable",
                "trend_message": "Cost is within normal range for this customer",
                "last_activity": "2025-12-23T15:30:00Z",
                "last_updated": "2025-12-23T16:00:00Z",
            }
        }


# =============================================================================
# CATEGORY 6: FOUNDER ACTION PATH DTOs
# =============================================================================
# These DTOs define the command/response structure for founder actions.
# Invariant: Every action is audited, reversible (except OVERRIDE_INCIDENT),
# and rate-limited. Customer tokens are rejected.


class FounderActionTargetDTO(BaseModel):
    """Target of a founder action."""

    type: Literal["TENANT", "API_KEY", "INCIDENT"] = Field(description="Type of target being acted upon")
    id: str = Field(description="Target identifier (tenant_id, api_key_id, or incident_id)")


class FounderActionReasonDTO(BaseModel):
    """Reason for a founder action - required for audit trail."""

    code: Literal["COST_ANOMALY", "POLICY_VIOLATION", "RETRY_LOOP", "ABUSE_SUSPECTED", "FALSE_POSITIVE", "OTHER"] = (
        Field(description="Reason code for the action")
    )
    note: Optional[str] = Field(
        default=None, max_length=500, description="Optional free-text explanation (max 500 chars)"
    )


class FounderActionRequestDTO(BaseModel):
    """
    Unified command model for all founder actions.

    Actions:
    - FREEZE_TENANT: Immediately block all API calls for tenant
    - THROTTLE_TENANT: Reduce tenant rate limit to 10% of normal
    - FREEZE_API_KEY: Immediately revoke specific API key
    - OVERRIDE_INCIDENT: Mark incident as false positive (closes it)
    """

    action: Literal["FREEZE_TENANT", "THROTTLE_TENANT", "FREEZE_API_KEY", "OVERRIDE_INCIDENT"] = Field(
        description="Action to perform"
    )
    target: FounderActionTargetDTO = Field(description="Target of the action")
    reason: FounderActionReasonDTO = Field(description="Reason for the action")
    source_incident_id: Optional[str] = Field(
        default=None, description="Optional incident ID that triggered this action"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "action": "FREEZE_TENANT",
                "target": {"type": "TENANT", "id": "tenant_abc123"},
                "reason": {"code": "COST_ANOMALY", "note": "Spending 40% above baseline, possible retry loop"},
                "source_incident_id": "inc_xyz789",
            }
        }


class FounderActionResponseDTO(BaseModel):
    """
    Unified response for all founder actions.

    Status codes:
    - APPLIED: Action was successfully applied
    - REJECTED: Action was rejected (validation failed, target not found)
    - RATE_LIMITED: Too many actions in time window
    - CONFLICT: Conflicting action already active (e.g., freeze + throttle)
    """

    status: Literal["APPLIED", "REJECTED", "RATE_LIMITED", "CONFLICT"] = Field(
        description="Result status of the action"
    )
    action_id: str = Field(description="Unique identifier for this action")
    applied_at: str = Field(description="ISO8601 timestamp when action was applied")
    reversible: bool = Field(description="Whether this action can be undone (OVERRIDE_INCIDENT is not reversible)")
    undo_hint: Optional[str] = Field(
        default=None, description="Hint for how to reverse this action (null if not reversible)"
    )
    message: Optional[str] = Field(
        default=None, description="Human-readable message (especially for REJECTED/CONFLICT)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "status": "APPLIED",
                "action_id": "action_abc123def456",
                "applied_at": "2025-12-24T10:30:00Z",
                "reversible": True,
                "undo_hint": "Use POST /ops/actions/unfreeze-tenant with action_id",
                "message": None,
            }
        }


class FounderAuditRecordDTO(BaseModel):
    """
    Immutable audit record for founder actions.

    Invariant: Every action MUST write an audit record.
    No audit record → API must fail.
    """

    audit_id: str = Field(description="Unique audit record ID")
    action_id: str = Field(description="ID of the action that was taken")
    action_type: Literal[
        "FREEZE_TENANT",
        "THROTTLE_TENANT",
        "FREEZE_API_KEY",
        "OVERRIDE_INCIDENT",
        "UNFREEZE_TENANT",
        "UNTHROTTLE_TENANT",
        "UNFREEZE_API_KEY",
    ] = Field(description="Type of action taken")
    target_type: Literal["TENANT", "API_KEY", "INCIDENT"] = Field(description="Type of target")
    target_id: str = Field(description="ID of the target")
    reason_code: str = Field(description="Reason code for the action")
    reason_note: Optional[str] = Field(default=None, description="Optional reason note")
    source_incident_id: Optional[str] = Field(default=None, description="Incident that triggered this action")
    founder_id: str = Field(description="ID of the founder who took the action")
    founder_email: str = Field(description="Email of the founder")
    mfa_verified: bool = Field(description="Whether MFA was verified for this action")
    applied_at: str = Field(description="ISO8601 timestamp")
    reversed_at: Optional[str] = Field(default=None, description="ISO8601 timestamp if action was reversed")
    reversed_by_action_id: Optional[str] = Field(default=None, description="ID of the reversal action")

    class Config:
        json_schema_extra = {
            "example": {
                "audit_id": "audit_xyz123",
                "action_id": "action_abc123def456",
                "action_type": "FREEZE_TENANT",
                "target_type": "TENANT",
                "target_id": "tenant_abc123",
                "reason_code": "COST_ANOMALY",
                "reason_note": "Spending 40% above baseline",
                "source_incident_id": "inc_xyz789",
                "founder_id": "founder_001",
                "founder_email": "admin@company.com",
                "mfa_verified": True,
                "applied_at": "2025-12-24T10:30:00Z",
                "reversed_at": None,
                "reversed_by_action_id": None,
            }
        }


class FounderReversalRequestDTO(BaseModel):
    """Request to reverse a previous action."""

    action_id: str = Field(description="ID of the action to reverse")
    reason: Optional[str] = Field(default=None, max_length=500, description="Optional reason for reversal")

    class Config:
        json_schema_extra = {
            "example": {"action_id": "action_abc123def456", "reason": "False positive confirmed - customer was testing"}
        }


class FounderActionSummaryDTO(BaseModel):
    """Summary of a founder action for list views."""

    action_id: str = Field(description="Unique action ID")
    action_type: str = Field(description="Type of action")
    target_type: str = Field(description="Type of target")
    target_id: str = Field(description="ID of target")
    target_name: Optional[str] = Field(default=None, description="Display name of target")
    reason_code: str = Field(description="Reason code")
    founder_email: str = Field(description="Who took the action")
    applied_at: str = Field(description="When action was taken")
    is_reversed: bool = Field(description="Whether action was reversed")
    is_active: bool = Field(description="Whether action is currently active")


class FounderActionListDTO(BaseModel):
    """List of recent founder actions for audit trail."""

    actions: List[FounderActionSummaryDTO] = Field(description="List of recent actions")
    total_count: int = Field(description="Total number of actions matching filter")
    page: int = Field(default=1, description="Current page number")
    page_size: int = Field(default=50, description="Items per page")


# =============================================================================
# AUTO_EXECUTE REVIEW - PIN-333
# Evidence-only review of SUB-019 auto-execution decisions
# =============================================================================


class AutoExecuteReviewItemDTO(BaseModel):
    """
    Single AUTO_EXECUTE decision evidence record.

    PIN-333: Evidence-only, no control, no behavior change.

    Maps 1:1 to ExecutionEnvelope (SUB-019) + InvocationSafetyFlags.
    No derived fields. No computed judgments. No inferred risk scores.

    Frozen: 2026-01-06 (PIN-333)
    """

    # Core identifiers
    invocation_id: str = Field(description="Unique invocation ID from envelope")
    envelope_id: str = Field(description="Execution envelope ID")
    timestamp: str = Field(description="ISO8601 timestamp of decision")

    # Tenant context (for cross-tenant founder view)
    tenant_id: str = Field(description="Tenant ID from envelope")
    account_id: Optional[str] = Field(default=None, description="Account ID if available")
    project_id: Optional[str] = Field(default=None, description="Project ID if available")

    # Capability attribution
    capability_id: Literal["SUB-019"] = Field(default="SUB-019", description="Always SUB-019")
    execution_vector: Literal["AUTO_EXEC"] = Field(default="AUTO_EXEC", description="Always AUTO_EXEC")

    # Decision evidence
    confidence_score: float = Field(ge=0.0, le=1.0, description="Confidence score from envelope")
    threshold: float = Field(ge=0.0, le=1.0, description="Threshold used for decision")
    decision: Literal["EXECUTED", "SKIPPED"] = Field(description="Whether auto-execute triggered")
    recovery_action: Optional[str] = Field(default=None, description="Action taken (if executed)")

    # Recovery context
    recovery_candidate_id: Optional[str] = Field(default=None, description="Recovery candidate ID")
    incident_id: Optional[str] = Field(default=None, description="Related incident ID if known")

    # Execution result (if available)
    execution_result: Optional[Literal["SUCCESS", "FAILED", "PENDING", "UNKNOWN"]] = Field(
        default=None, description="Result of execution if completed"
    )

    # Plan integrity evidence
    input_hash: str = Field(description="Hash of input from envelope")
    plan_hash: str = Field(description="Hash of resolved plan from envelope")
    plan_mutation_detected: bool = Field(default=False, description="Whether plan was mutated")

    # Worker attribution
    worker_identity: str = Field(default="recovery_claim_worker", description="Worker identity from envelope")

    # Safety flags (from InvocationSafetyFlags)
    safety_checked: bool = Field(default=False, description="Whether safety checks ran")
    safety_passed: bool = Field(default=True, description="Whether safety checks passed")
    safety_flags: List[str] = Field(default_factory=list, description="Safety flag values")
    safety_warnings: List[str] = Field(default_factory=list, description="Safety warning messages")

    class Config:
        json_schema_extra = {
            "example": {
                "invocation_id": "abc123-def456-ghi789",
                "envelope_id": "env_001",
                "timestamp": "2026-01-06T10:30:00Z",
                "tenant_id": "tenant_xyz",
                "account_id": None,
                "project_id": None,
                "capability_id": "SUB-019",
                "execution_vector": "AUTO_EXEC",
                "confidence_score": 0.92,
                "threshold": 0.80,
                "decision": "EXECUTED",
                "recovery_action": "retry_with_backoff",
                "recovery_candidate_id": "rc_123",
                "incident_id": "inc_456",
                "execution_result": "SUCCESS",
                "input_hash": "a1b2c3d4...",
                "plan_hash": "e5f6g7h8...",
                "plan_mutation_detected": False,
                "worker_identity": "recovery_claim_worker",
                "safety_checked": True,
                "safety_passed": True,
                "safety_flags": [],
                "safety_warnings": [],
            }
        }


class AutoExecuteReviewListDTO(BaseModel):
    """
    List of AUTO_EXECUTE decisions for founder review.

    PIN-333: Evidence-only, read-only.
    """

    items: List[AutoExecuteReviewItemDTO] = Field(description="List of AUTO_EXECUTE decisions")
    total_count: int = Field(ge=0, description="Total matching items")
    page: int = Field(default=1, ge=1, description="Current page")
    page_size: int = Field(default=50, ge=1, le=100, description="Items per page")

    # Summary stats (from existing stored data, not computed)
    executed_count: int = Field(ge=0, description="Count of EXECUTED decisions in result set")
    skipped_count: int = Field(ge=0, description="Count of SKIPPED decisions in result set")
    flagged_count: int = Field(ge=0, description="Count of decisions with safety flags")


class AutoExecuteReviewFilterDTO(BaseModel):
    """
    Filter parameters for AUTO_EXECUTE review queries.

    All filters are optional. Defaults to last 7 days.
    """

    # Time window
    start_time: Optional[str] = Field(default=None, description="ISO8601 start time (default: 7 days ago)")
    end_time: Optional[str] = Field(default=None, description="ISO8601 end time (default: now)")

    # Tenant filter (optional - founders can see all tenants)
    tenant_id: Optional[str] = Field(default=None, description="Filter by specific tenant")

    # Decision filter
    decision: Optional[Literal["EXECUTED", "SKIPPED"]] = Field(default=None, description="Filter by decision type")

    # Confidence range
    min_confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0, description="Minimum confidence score")
    max_confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0, description="Maximum confidence score")

    # Safety flag presence
    has_safety_flags: Optional[bool] = Field(default=None, description="Filter for items with safety flags")

    # Pagination
    page: int = Field(default=1, ge=1, description="Page number")
    page_size: int = Field(default=50, ge=1, le=100, description="Items per page")


class AutoExecuteReviewStatsDTO(BaseModel):
    """
    Aggregate statistics for AUTO_EXECUTE review charts.

    PIN-333: Charts reflect stored evidence only. No predictive analytics.
    """

    # Time window
    start_time: str = Field(description="ISO8601 start of aggregation window")
    end_time: str = Field(description="ISO8601 end of aggregation window")

    # Counts
    total_decisions: int = Field(ge=0, description="Total AUTO_EXECUTE decisions in window")
    executed_count: int = Field(ge=0, description="Decisions where execution triggered")
    skipped_count: int = Field(ge=0, description="Decisions where execution was skipped")

    # Confidence distribution (for histogram)
    confidence_distribution: Dict[str, int] = Field(
        description="Confidence score buckets (0.0-0.5, 0.5-0.6, ..., 0.9-1.0)"
    )

    # Safety flag summary
    flagged_count: int = Field(ge=0, description="Decisions with at least one safety flag")
    flag_counts: Dict[str, int] = Field(default_factory=dict, description="Count per safety flag type")

    # Time series (for trend chart)
    daily_counts: List[Dict[str, Any]] = Field(default_factory=list, description="Daily counts for trend chart")

    class Config:
        json_schema_extra = {
            "example": {
                "start_time": "2025-12-30T00:00:00Z",
                "end_time": "2026-01-06T00:00:00Z",
                "total_decisions": 150,
                "executed_count": 120,
                "skipped_count": 30,
                "confidence_distribution": {
                    "0.8-0.85": 25,
                    "0.85-0.9": 45,
                    "0.9-0.95": 35,
                    "0.95-1.0": 15,
                },
                "flagged_count": 8,
                "flag_counts": {
                    "ownership_violation": 3,
                    "rate_threshold_exceeded": 5,
                },
                "daily_counts": [
                    {"date": "2025-12-30", "executed": 18, "skipped": 4},
                    {"date": "2025-12-31", "executed": 15, "skipped": 5},
                ],
            }
        }
