# Layer: L4 — Domain Engine
# Product: system-wide
# Temporal:
#   Trigger: api
#   Execution: sync
# Role: Guard contract for access control
# Callers: API routes
# Allowed Imports: L6
# Forbidden Imports: L1, L2, L3, L5
# Reference: Contract System

"""
Guard Console Data Contracts - Customer-Facing API

DOMAIN: Customer Console (/guard/*)
AUDIENCE: Customers (tenant-scoped access)
AUTH: aud="console", requires org_id

These contracts are FROZEN as of M29. Changes require:
1. Deprecation annotation
2. 2-version grace period
3. PIN documentation

INVARIANTS:
- All responses are tenant-scoped (no cross-tenant data)
- No founder-only fields (those belong in ops.py)
- Times are ISO8601 strings
- IDs are prefixed strings (inc_, key_, etc.)
"""

from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field

# =============================================================================
# GUARD STATUS - "Am I protected?"
# =============================================================================


class GuardStatusDTO(BaseModel):
    """
    GET /guard/status response.

    Tells customer if their traffic is protected.
    Frozen: 2025-12-23 (M29)
    """

    status: Literal["protected", "attention_needed", "action_required"]
    is_frozen: bool = Field(description="True if killswitch is active")
    frozen_at: Optional[str] = Field(None, description="ISO8601 timestamp when frozen")
    frozen_by: Optional[str] = Field(None, description="Actor who froze (user_id or 'system')")
    incidents_blocked_24h: int = Field(ge=0, description="Incidents blocked in last 24h")
    active_guardrails: List[str] = Field(description="Names of active guardrails")
    last_incident_time: Optional[str] = Field(None, description="ISO8601 of last incident")

    class Config:
        json_schema_extra = {
            "example": {
                "status": "protected",
                "is_frozen": False,
                "frozen_at": None,
                "frozen_by": None,
                "incidents_blocked_24h": 3,
                "active_guardrails": ["cost_limit", "rate_limit"],
                "last_incident_time": "2025-12-23T10:15:00Z",
            }
        }


# =============================================================================
# TODAY SNAPSHOT - "What happened today?"
# =============================================================================


class TodaySnapshotDTO(BaseModel):
    """
    GET /guard/snapshot/today response.

    Today's metrics at a glance.
    Frozen: 2025-12-23 (M29)
    """

    requests_today: int = Field(ge=0)
    spend_today_cents: int = Field(ge=0, description="Spend in cents")
    incidents_prevented: int = Field(ge=0)
    last_incident_time: Optional[str] = None
    cost_avoided_cents: int = Field(ge=0, description="Cost saved by prevention")

    class Config:
        json_schema_extra = {
            "example": {
                "requests_today": 1500,
                "spend_today_cents": 2340,
                "incidents_prevented": 2,
                "last_incident_time": "2025-12-23T09:30:00Z",
                "cost_avoided_cents": 15000,
            }
        }


# =============================================================================
# INCIDENTS - "What went wrong?"
# =============================================================================


class IncidentSummaryDTO(BaseModel):
    """
    Incident list item.

    Used in GET /guard/incidents (list) and detail views.
    Frozen: 2025-12-23 (M29)
    """

    id: str = Field(description="Incident ID (inc_*)")
    title: str = Field(description="Human-readable title")
    severity: Literal["critical", "high", "medium", "low"]
    status: Literal["active", "acknowledged", "resolved", "auto_resolved"]
    trigger_type: str = Field(description="What triggered: cost_spike, rate_limit, etc.")
    trigger_value: Optional[str] = Field(None, description="Trigger threshold value")
    action_taken: Optional[str] = Field(None, description="What system did")
    cost_avoided_cents: int = Field(ge=0)
    calls_affected: int = Field(ge=0)
    started_at: str = Field(description="ISO8601")
    ended_at: Optional[str] = Field(None, description="ISO8601 if resolved")
    duration_seconds: Optional[int] = Field(None, ge=0)
    call_id: Optional[str] = Field(None, description="First related call for replay")


class IncidentEventDTO(BaseModel):
    """Timeline event within an incident."""

    id: str
    event_type: str = Field(description="detection, escalation, action, resolution, etc.")
    description: str
    created_at: str = Field(description="ISO8601")
    data: Optional[Dict[str, Any]] = None


class IncidentDetailDTO(BaseModel):
    """
    GET /guard/incidents/{id} response.

    Full incident with timeline.
    Frozen: 2025-12-23 (M29)
    """

    incident: IncidentSummaryDTO
    timeline: List[IncidentEventDTO]


class IncidentListDTO(BaseModel):
    """
    GET /guard/incidents response (paginated).

    Frozen: 2025-12-23 (M29)
    """

    incidents: List[IncidentSummaryDTO]
    total: int = Field(ge=0)
    page: int = Field(ge=1)
    page_size: int = Field(ge=1, le=100)
    has_more: bool


# =============================================================================
# CUSTOMER INCIDENT DETAIL - "What happened? Should I worry?"
# M29 Category 5: Incident Console Contrast
# Added: 2025-12-24
#
# IMPORTANT: Uses CALM vocabulary only. No internal terminology.
# No policy names, no thresholds, no raw metrics.
# =============================================================================


class CustomerIncidentImpactDTO(BaseModel):
    """
    Impact assessment for customers - calm, explicit.

    Frozen: 2025-12-24 (M29 Category 5)
    """

    requests_affected: Literal["yes", "no", "some"]
    service_interrupted: Literal["yes", "no", "briefly"]
    data_exposed: Literal["no"]  # Always "no" - we never expose data
    cost_impact: Literal["none", "minimal", "higher_than_usual", "significant"]
    cost_impact_message: Optional[str] = Field(None, description="E.g., 'Higher than usual for a short period'")


class CustomerIncidentResolutionDTO(BaseModel):
    """
    Resolution status for customers - reassuring.

    Frozen: 2025-12-24 (M29 Category 5)
    """

    status: Literal["investigating", "mitigating", "resolved", "monitoring"]
    status_message: str = Field(description="E.g., 'The issue was automatically mitigated at 14:32 UTC'")
    resolved_at: Optional[str] = Field(None, description="ISO8601 if resolved")
    requires_action: bool = Field(description="True if customer needs to do something")


class CustomerIncidentActionDTO(BaseModel):
    """
    Customer action item - only if necessary.

    Frozen: 2025-12-24 (M29 Category 5)
    """

    action_type: Literal["review_usage", "adjust_limits", "contact_support", "none"]
    description: str
    urgency: Literal["optional", "recommended", "required"]
    link: Optional[str] = Field(None, description="Deep link to relevant page")


class CustomerIncidentNarrativeDTO(BaseModel):
    """
    GET /guard/incidents/{id} enhanced response.

    Customer-friendly incident detail with calm narrative.
    Answers: What happened? Did it affect me? Is it fixed? Do I need to act?

    Frozen: 2025-12-24 (M29 Category 5)

    IMPORTANT: This is CUSTOMER-ONLY data.
    - Uses calm vocabulary (normal, rising, protected, resolved)
    - No internal terminology (no policy names, no thresholds)
    - No cross-tenant data (no affected_tenants, no percentiles)
    """

    # Identification
    incident_id: str
    title: str = Field(description="Plain language title")

    # Section A: Summary (plain language)
    summary: str = Field(
        description="E.g., 'We detected unusual AI usage that caused higher costs for a short period.'"
    )

    # Section B: Impact Assessment (calm, explicit)
    impact: CustomerIncidentImpactDTO

    # Section C: Resolution Status (reassuring)
    resolution: CustomerIncidentResolutionDTO

    # Section D: What You Can Do (only if necessary)
    customer_actions: List[CustomerIncidentActionDTO] = Field(default_factory=list)

    # Timeline (simplified - outcome focused)
    started_at: str = Field(description="ISO8601")
    ended_at: Optional[str] = Field(None, description="ISO8601 if resolved")

    # Link to cost summary if cost-related
    cost_summary_link: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "incident_id": "inc_abc123",
                "title": "Unusual usage pattern detected and resolved",
                "summary": "We detected unusual AI usage that caused higher costs for a short period. Our systems automatically protected your account.",
                "impact": {
                    "requests_affected": "some",
                    "service_interrupted": "no",
                    "data_exposed": "no",
                    "cost_impact": "higher_than_usual",
                    "cost_impact_message": "Higher than usual for a short period",
                },
                "resolution": {
                    "status": "resolved",
                    "status_message": "The issue was automatically mitigated at 14:32 UTC.",
                    "resolved_at": "2025-12-24T14:32:00Z",
                    "requires_action": False,
                },
                "customer_actions": [
                    {
                        "action_type": "none",
                        "description": "No action is required from you.",
                        "urgency": "optional",
                        "link": None,
                    }
                ],
                "started_at": "2025-12-24T14:00:00Z",
                "ended_at": "2025-12-24T14:32:00Z",
                "cost_summary_link": "/guard/costs/summary",
            }
        }


# =============================================================================
# API KEYS - "Who can access?"
# =============================================================================


class ApiKeyDTO(BaseModel):
    """
    API key response (masked).

    GET /guard/keys response item.
    Frozen: 2025-12-23 (M29)
    """

    id: str = Field(description="Key ID (key_*)")
    name: str
    prefix: str = Field(description="First 8 chars of key")
    is_frozen: bool
    frozen_at: Optional[str] = None
    frozen_by: Optional[str] = None
    created_at: str
    last_used_at: Optional[str] = None
    scopes: List[str] = Field(default_factory=list)


class ApiKeyListDTO(BaseModel):
    """GET /guard/keys response."""

    keys: List[ApiKeyDTO]
    total: int


# =============================================================================
# SETTINGS - "How am I configured?"
# =============================================================================


class GuardrailConfigDTO(BaseModel):
    """Individual guardrail configuration."""

    name: str
    enabled: bool
    threshold: Optional[str] = None
    action: str = Field(description="block, alert, log")


class TenantSettingsDTO(BaseModel):
    """
    GET /guard/settings response.

    Read-only tenant configuration view.
    Frozen: 2025-12-23 (M29)
    """

    tenant_id: str
    tenant_name: str
    guardrails: List[GuardrailConfigDTO]
    notification_email: Optional[str] = None
    notification_slack_webhook: Optional[str] = Field(None, description="Masked webhook URL")
    daily_budget_cents: Optional[int] = None
    rate_limit_rpm: Optional[int] = None


# =============================================================================
# REPLAY - "Can I reproduce this?"
# =============================================================================


class ReplayCallSnapshotDTO(BaseModel):
    """Original call context for replay."""

    call_id: str
    agent_id: str
    input_payload: Dict[str, Any]
    original_output: Dict[str, Any]
    timestamp: str


class ReplayCertificateDTO(BaseModel):
    """Cryptographic proof of replay (M23)."""

    certificate_id: str
    algorithm: str = "sha256"
    original_hash: str
    replay_hash: str
    match: bool
    issued_at: str
    issuer: str = "agenticverz"


class ReplayResultDTO(BaseModel):
    """
    POST /guard/replay/{call_id} response.

    Result of replaying a call with determinism validation.
    Frozen: 2025-12-23 (M29)
    """

    success: bool
    determinism_level: Literal["exact", "semantic", "divergent"]
    original_call: ReplayCallSnapshotDTO
    replay_output: Dict[str, Any]
    differences: List[str] = Field(default_factory=list, description="List of differences if any")
    certificate: Optional[ReplayCertificateDTO] = None


# =============================================================================
# KILLSWITCH ACTIONS
# =============================================================================


class KillSwitchActionDTO(BaseModel):
    """
    POST /guard/killswitch/activate and /deactivate response.

    Frozen: 2025-12-23 (M29)
    """

    success: bool
    action: Literal["activated", "deactivated"]
    frozen_at: Optional[str] = None
    message: str


# =============================================================================
# ONBOARDING
# =============================================================================


class OnboardingVerifyResponseDTO(BaseModel):
    """
    POST /guard/onboarding/verify response.

    Frozen: 2025-12-23 (M29)
    """

    verified: bool
    tenant_id: Optional[str] = None
    message: str


# =============================================================================
# COST VISIBILITY - "What am I spending?"
# Added: 2025-12-23 (M29 Category 4)
# =============================================================================


class CustomerCostSummaryDTO(BaseModel):
    """
    GET /guard/costs/summary response.

    Customer cost summary with trend and projection.
    Frozen: 2025-12-23 (M29 Category 4)

    THE INVARIANT: All values derive from complete snapshots, never live data.
    Customer sees their own tenant data only - no cross-tenant leakage.
    """

    # Current spend
    spend_today_cents: int = Field(ge=0, description="Today's spend so far")
    spend_mtd_cents: int = Field(ge=0, description="Month-to-date spend")
    spend_7d_cents: int = Field(ge=0, description="Last 7 days spend")

    # Budget
    budget_daily_cents: Optional[int] = Field(None, ge=0, description="Daily budget if set")
    budget_monthly_cents: Optional[int] = Field(None, ge=0, description="Monthly budget if set")
    budget_used_daily_pct: Optional[float] = Field(None, ge=0, le=100, description="% of daily budget used")
    budget_used_monthly_pct: Optional[float] = Field(None, ge=0, le=100, description="% of monthly budget used")

    # Projection
    projected_month_end_cents: int = Field(ge=0, description="Projected month-end spend")
    days_until_budget_exhausted: Optional[int] = Field(None, ge=0, description="Days until monthly budget runs out")

    # Trend (customer-friendly vocabulary)
    trend: Literal["normal", "rising", "spike"] = Field(
        description="normal=stable, rising=gradual increase, spike=significant deviation"
    )
    trend_message: Optional[str] = Field(None, description="Human-readable trend explanation")

    # Snapshot freshness
    last_updated: str = Field(description="ISO8601 of last snapshot")

    class Config:
        json_schema_extra = {
            "example": {
                "spend_today_cents": 2340,
                "spend_mtd_cents": 45000,
                "spend_7d_cents": 18000,
                "budget_daily_cents": 10000,
                "budget_monthly_cents": 300000,
                "budget_used_daily_pct": 23.4,
                "budget_used_monthly_pct": 15.0,
                "projected_month_end_cents": 72000,
                "days_until_budget_exhausted": None,
                "trend": "normal",
                "trend_message": "Spending is within normal range",
                "last_updated": "2025-12-23T10:00:00Z",
            }
        }


class CostBreakdownItemDTO(BaseModel):
    """Individual cost breakdown item."""

    name: str = Field(description="Feature tag, model name, or user ID")
    display_name: Optional[str] = Field(None, description="Human-readable name")
    spend_cents: int = Field(ge=0)
    request_count: int = Field(ge=0)
    pct_of_total: float = Field(ge=0, le=100)
    trend: Literal["normal", "rising", "spike"]


class CustomerCostExplainedDTO(BaseModel):
    """
    GET /guard/costs/explained response.

    Explains WHY costs are what they are.
    Frozen: 2025-12-23 (M29 Category 4)

    IMPORTANT: Does not expose founder-only fields like churn_risk or affected_tenants.
    """

    # Period
    period: Literal["today", "7d", "30d"]
    period_start: str = Field(description="ISO8601")
    period_end: str = Field(description="ISO8601")
    total_spend_cents: int = Field(ge=0)

    # Breakdowns
    by_feature: List[CostBreakdownItemDTO] = Field(description="Cost by feature tag")
    by_model: List[CostBreakdownItemDTO] = Field(description="Cost by LLM model")
    by_user: List[CostBreakdownItemDTO] = Field(description="Cost by user (top N)")

    # Biggest driver
    largest_driver_type: Literal["feature", "model", "user"]
    largest_driver_name: str
    largest_driver_pct: float = Field(ge=0, le=100)

    # Simple explanation
    summary: str = Field(description="One-sentence explanation of where money went")

    class Config:
        json_schema_extra = {
            "example": {
                "period": "7d",
                "period_start": "2025-12-16T00:00:00Z",
                "period_end": "2025-12-23T00:00:00Z",
                "total_spend_cents": 18000,
                "by_feature": [
                    {
                        "name": "customer_support.chat",
                        "display_name": "Customer Support Chat",
                        "spend_cents": 12000,
                        "request_count": 500,
                        "pct_of_total": 66.7,
                        "trend": "normal",
                    }
                ],
                "by_model": [
                    {
                        "name": "claude-sonnet-4-20250514",
                        "display_name": "Claude Sonnet",
                        "spend_cents": 15000,
                        "request_count": 800,
                        "pct_of_total": 83.3,
                        "trend": "normal",
                    }
                ],
                "by_user": [
                    {
                        "name": "user_abc123",
                        "display_name": None,
                        "spend_cents": 5000,
                        "request_count": 200,
                        "pct_of_total": 27.8,
                        "trend": "normal",
                    }
                ],
                "largest_driver_type": "model",
                "largest_driver_name": "claude-sonnet-4-20250514",
                "largest_driver_pct": 83.3,
                "summary": "83% of your spend is from Claude Sonnet usage in Customer Support Chat",
            }
        }


class CustomerCostIncidentDTO(BaseModel):
    """
    Cost-related incident visible to customer.

    Used in GET /guard/costs/incidents response.
    Frozen: 2025-12-23 (M29 Category 4)

    IMPORTANT: Uses calm vocabulary (protected, attention_needed).
    Does not expose severity levels - maps internally.
    """

    id: str = Field(description="Incident ID (inc_*)")
    title: str = Field(description="Customer-friendly title")
    status: Literal["protected", "attention_needed", "resolved"] = Field(
        description="protected=blocked, attention_needed=warning, resolved=fixed"
    )
    trigger_type: Literal["cost_spike", "budget_warning", "budget_exceeded"] = Field(description="What triggered this")

    # Cost context
    cost_at_trigger_cents: int = Field(ge=0)
    cost_avoided_cents: int = Field(ge=0)
    threshold_cents: Optional[int] = None

    # Action
    action_taken: str = Field(description="What system did: blocked, alerted, etc.")
    recommendation: Optional[str] = Field(None, description="What customer should do")

    # Cause explanation (M29 Category 4 - calm vocabulary)
    cause_explanation: Optional[str] = Field(None, description="Customer-friendly explanation of why this happened")

    # Times
    detected_at: str = Field(description="ISO8601")
    resolved_at: Optional[str] = None


class CustomerCostIncidentListDTO(BaseModel):
    """GET /guard/costs/incidents response."""

    incidents: List[CustomerCostIncidentDTO]
    total: int
    has_more: bool
