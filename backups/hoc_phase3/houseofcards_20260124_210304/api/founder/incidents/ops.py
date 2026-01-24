# Layer: L2 — Product APIs
# AUDIENCE: INTERNAL
# Role: Ops Console API - Founder Intelligence System for behavioral insights
"""Ops Console API - Founder Intelligence System

PIN-105: Ops Console - Founder Intelligence System

This router provides endpoints for the Operator Console (ops.agenticverz.com).
Focused on BEHAVIORAL TRUTH - answer founder questions without customer input.

Modules:
1. System Pulse     - "Is my business healthy right now?"
2. Customer Intel   - "Who is this customer and are they slipping?"
2.5 At-Risk         - "Who should I call today?" (Phase-2)
3. Incident Intel   - "What is breaking and is it systemic?"
4. Product Stickiness - "Which feature actually keeps users?"
5. Revenue & Risk   - "Am I making money safely?"
6. Infra & Limits   - "What breaks first if I grow?"
7. Replay Lab       - "Can I reproduce and fix anything?"

All insights are derived from ops_events table (event-sourced).

ARCHITECTURE NOTES (Phase-2):
==================================

1. SOURCE OF TRUTH: ops_events table
   - Event-sourced design: ops_events is the ONLY authoritative data
   - All metrics are derived from events, never stored directly
   - This enables replay, audit, and recalculation

2. CACHE TABLES (NOT authoritative):
   - ops_customer_segments: Pre-computed customer profiles (cache-only)
   - ops_tenant_metrics: (if exists) Pre-computed metrics (cache-only)
   - These can be DELETED and recomputed from ops_events at any time
   - Never treat cache tables as source of truth
   - Background jobs refresh caches periodically

3. FRICTION EVENTS (Phase-2):
   - *_STARTED vs *_COMPLETED tracks drop-offs
   - *_ABORTED tracks explicit abandonment
   - *_NO_ACTION tracks hesitation
   - These feed into stickiness_delta calculations

4. STICKINESS DECAY:
   - stickiness_7d: Recent engagement (high signal)
   - stickiness_30d: Historical baseline (normalized to weekly)
   - stickiness_delta: Ratio (7d/30d) - <1 means decelerating

5. FOUNDER INTERVENTIONS:
   - Auto-generated action suggestions based on risk signals
   - Priority: immediate > today > this_week
   - Types: call, email, feature_help, pricing, technical

6. FOUNDER PLAYBOOKS (Phase-2.1):
   See PLAYBOOKS constant below for signal → action mappings.
   Use playbooks BEFORE automating - learn what works first.
"""

import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlmodel import Session

# Category 2 Auth: Domain-separated authentication for Founder Ops Console
# Uses verify_fops_token which enforces:
# - aud = "fops" (strict - NOT "console")
# - role in [FOUNDER, OPERATOR]
# - mfa = true (MANDATORY)
# - All rejections logged to audit
# NO SHARED LOGIC with console auth
from app.auth.console_auth import FounderToken, verify_fops_token

# M29 Category 5: Incident Console Contrast - Founder Incident DTOs
from app.contracts.ops import (
    FounderBlastRadiusDTO,
    FounderDecisionTimelineEventDTO,
    FounderIncidentDetailDTO,
    FounderIncidentHeaderDTO,
    FounderIncidentListDTO,
    FounderIncidentListItemDTO,
    FounderRecurrenceRiskDTO,
    FounderRootCauseDTO,
)
from app.db import get_session
from app.schemas.response import wrap_dict

# Incident model for database queries
from app.models.killswitch import Incident, IncidentEvent

# Redis caching for ops endpoints (optional - degrades gracefully)
try:
    import os

    import redis

    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    redis_client = redis.from_url(REDIS_URL, decode_responses=True)
    REDIS_AVAILABLE = True
except Exception:
    redis_client = None
    REDIS_AVAILABLE = False

logger = logging.getLogger("nova.api.ops")

# Cache TTL in seconds (ops data refreshes every 15s, cache for 12s)
OPS_CACHE_TTL = 12


def cache_get(key: str) -> Optional[dict]:
    """Get cached value if Redis is available."""
    if not REDIS_AVAILABLE or not redis_client:
        return None
    try:
        data = redis_client.get(f"ops:{key}")
        if data:
            return json.loads(data)
    except Exception as e:
        logger.debug(f"Redis cache get failed: {e}")
    return None


def cache_set(key: str, value: dict, ttl: int = OPS_CACHE_TTL) -> None:
    """Set cached value if Redis is available."""
    if not REDIS_AVAILABLE or not redis_client:
        return
    try:
        redis_client.setex(f"ops:{key}", ttl, json.dumps(value, default=str))
    except Exception as e:
        logger.debug(f"Redis cache set failed: {e}")


# =============================================================================
# FOUNDER PLAYBOOKS v1 (Phase-2.1)
# Signal → Action Matrix - Use BEFORE automating
# =============================================================================

FOUNDER_PLAYBOOKS = {
    # =========================================================================
    # PLAYBOOK 1: Silent Churn
    # Signal: API active but no investigation in 7+ days
    # =========================================================================
    "silent_churn": {
        "name": "Silent Churn Recovery",
        "trigger_conditions": [
            "API_CALL_RECEIVED in last 48h",
            "NO INCIDENT_VIEWED or REPLAY_EXECUTED in 7+ days",
        ],
        "risk_level": "high",
        "actions": [
            {
                "step": 1,
                "type": "call",
                "action": "Direct founder call - they may have moved on",
                "timing": "within 24h",
                "talk_track": "Hey, noticed you're still integrating but haven't explored incidents. Want me to walk you through the value?",
            },
            {
                "step": 2,
                "type": "email",
                "action": "If no call response, send case study email",
                "timing": "after 48h if no response",
            },
        ],
        "success_metric": "INCIDENT_VIEWED or REPLAY_EXECUTED within 7 days",
        "notes": "Often means they integrated for compliance but don't see value",
    },
    # =========================================================================
    # PLAYBOOK 2: Policy Friction
    # Signal: Repeated POLICY_BLOCK_REPEAT events
    # =========================================================================
    "policy_friction": {
        "name": "Policy Friction Resolution",
        "trigger_conditions": [
            "3+ POLICY_BLOCK_REPEAT events in 7 days",
            "Same policy_id blocking repeatedly",
        ],
        "risk_level": "medium",
        "actions": [
            {
                "step": 1,
                "type": "technical",
                "action": "Review their policy config - likely misconfigured",
                "timing": "same day",
            },
            {
                "step": 2,
                "type": "email",
                "action": "Proactive email with fix suggestion",
                "timing": "same day after review",
                "template": "Hi, noticed your policy {policy_id} is blocking frequently. Here's a suggested adjustment...",
            },
        ],
        "success_metric": "POLICY_BLOCK_REPEAT drops by 80%",
        "notes": "Policy friction often means they don't understand the safety layer",
    },
    # =========================================================================
    # PLAYBOOK 3: Abandonment Pattern
    # Signal: Multiple REPLAY_ABORTED or EXPORT_ABORTED
    # =========================================================================
    "abandonment": {
        "name": "Flow Abandonment Recovery",
        "trigger_conditions": [
            "3+ REPLAY_ABORTED or EXPORT_ABORTED in 7 days",
            "stickiness_delta < 0.7",
        ],
        "risk_level": "high",
        "actions": [
            {
                "step": 1,
                "type": "email",
                "action": "Ask for feedback on what blocked them",
                "timing": "within 24h",
                "template": "We noticed you started a replay/export but didn't complete it. Was something confusing? I'd love to help.",
            },
            {
                "step": 2,
                "type": "feature_help",
                "action": "Send video walkthrough based on friction point",
                "timing": "after email response or 48h",
            },
        ],
        "success_metric": "Completed REPLAY_EXECUTED or EXPORT_GENERATED",
        "notes": "Abandonment often signals UX confusion, not feature rejection",
    },
    # =========================================================================
    # PLAYBOOK 4: Engagement Decay
    # Signal: stickiness_delta < 0.5 (engagement dropped 50%+)
    # =========================================================================
    "engagement_decay": {
        "name": "Engagement Recovery",
        "trigger_conditions": [
            "stickiness_delta < 0.5",
            "Was previously active (stickiness_30d > 3)",
        ],
        "risk_level": "critical",
        "actions": [
            {
                "step": 1,
                "type": "call",
                "action": "Priority call - something changed",
                "timing": "same day",
                "talk_track": "Noticed your usage dropped recently. Did something change on your end, or did we break something?",
            },
            {
                "step": 2,
                "type": "email",
                "action": "If no call, send 'what changed?' email",
                "timing": "after 24h if no call response",
            },
        ],
        "success_metric": "stickiness_delta returns to > 0.8",
        "notes": "Often signals internal priority shift or competitor evaluation",
    },
    # =========================================================================
    # PLAYBOOK 5: Legal/Enterprise-Only Pattern
    # Signal: Only using certs, no investigation
    # =========================================================================
    "legal_only": {
        "name": "Legal-Only Customer Expansion",
        "trigger_conditions": [
            "CERT_VERIFIED events present",
            "NO REPLAY_EXECUTED or EXPORT_GENERATED",
            "Integration older than 14 days",
        ],
        "risk_level": "medium",
        "actions": [
            {
                "step": 1,
                "type": "email",
                "action": "Value expansion email - show other use cases",
                "timing": "within week",
                "template": "You're using certificates for compliance - great! Did you know you can also use replays to debug production issues?",
            },
        ],
        "success_metric": "First REPLAY_EXECUTED or EXPORT_GENERATED",
        "notes": "Legal-only customers have low churn but also low expansion",
    },
}

# =============================================================================
# Router - Operator-only access (requires ops auth)
# =============================================================================

router = APIRouter(
    prefix="/ops",
    tags=["Ops Console"],
    dependencies=[Depends(verify_fops_token)],  # Category 2: Strict fops auth (aud=fops, mfa=true)
)


# =============================================================================
# Response Models
# =============================================================================


class SystemPulse(BaseModel):
    """System health at a glance."""

    # Activity
    active_tenants_24h: int
    active_tenants_delta_pct: float  # vs previous 24h

    incidents_created_24h: int
    incidents_delta_pct: float

    replays_executed_24h: int
    replays_delta_pct: float

    exports_generated_24h: int
    exports_delta_pct: float

    # LLM Health
    llm_calls_24h: int
    llm_failures_24h: int
    llm_failure_rate_pct: float

    # Cost
    total_cost_24h_usd: float

    # System state
    system_state: str  # 'healthy', 'degraded', 'critical'
    alerts: List[Dict[str, Any]]

    computed_at: str


class CustomerSegment(BaseModel):
    """Customer intelligence profile."""

    tenant_id: str
    tenant_name: Optional[str] = None

    # Intent
    first_action: Optional[str] = None
    first_action_at: Optional[str] = None
    inferred_buyer_type: Optional[str] = None

    # Stickiness (with recency decay - Phase-2)
    current_stickiness: float
    stickiness_7d: float = 0.0  # Phase-2: Recent engagement (7 days)
    stickiness_30d: float = 0.0  # Phase-2: Historical engagement (30 days)
    stickiness_delta: float = 0.0  # Phase-2: 7d vs 30d ratio (>1 = accelerating, <1 = decelerating)
    peak_stickiness: float
    stickiness_trend: str  # 'rising', 'stable', 'falling', 'silent'

    # Engagement
    last_api_call: Optional[str] = None
    last_investigation: Optional[str] = None
    is_silent_churn: bool

    # Risk
    risk_level: str
    risk_reason: Optional[str] = None

    # Time-to-value
    time_to_first_replay_m: Optional[int] = None
    time_to_first_export_m: Optional[int] = None

    # Phase-2: Friction signals
    friction_score: float = 0.0  # Aggregate of friction signals
    last_friction_event: Optional[str] = None


class StickinessByFeature(BaseModel):
    """Which feature creates stickiness."""

    feature: str  # 'incidents', 'replays', 'exports', 'certs'
    total_actions_30d: int
    unique_tenants: int
    avg_per_tenant: float
    pct_of_active_tenants: float


class IncidentPattern(BaseModel):
    """Failure pattern analysis."""

    pattern_type: str  # 'policy_block', 'llm_failure', 'rate_limit', 'budget'
    count_24h: int
    count_7d: int
    trend: str  # 'increasing', 'stable', 'decreasing'
    top_tenants: List[str]
    sample_ids: List[str]


class EstimationBasis(BaseModel):
    """
    PIN-254 Phase C Fix (C3 Partial Truth): Explicit disclosure of estimation assumptions.

    Revenue metrics use assumptions that must be visible to consumers.
    """

    mrr_assumption: str = "$50_avg_plan"  # What assumption is used for MRR
    mrr_source: str = "hardcoded"  # hardcoded | billing_system | historical_avg
    revenue_markup: float = 2.0  # Markup applied to LLM costs
    confidence: str = "low"  # low | medium | high
    disclaimer: str = "MRR estimate uses hardcoded $50/tenant assumption. Connect billing system for accurate data."


class RevenueRisk(BaseModel):
    """Revenue and risk metrics."""

    # Revenue
    mrr_estimate_usd: float  # Based on active tenants * avg plan
    daily_api_revenue_usd: float

    # Risk
    at_risk_tenants: int
    silent_churn_count: int
    high_risk_count: int

    # Alerts
    revenue_alerts: List[Dict[str, Any]]

    # PIN-254 Phase C Fix: Estimation transparency
    estimation_basis: EstimationBasis = Field(
        default_factory=EstimationBasis, description="Disclosure of how revenue estimates were derived (PIN-254 C3 fix)"
    )


class FounderIntervention(BaseModel):
    """Phase-2: Suggested founder action for at-risk customer.

    IMPORTANT: Every intervention MUST include explicit triggering_signals.
    This prevents blind trust and enables learning from outcomes.
    """

    intervention_type: str  # 'call', 'email', 'feature_help', 'pricing', 'technical'
    priority: str  # 'immediate', 'today', 'this_week'
    suggested_action: str
    context: str
    expected_outcome: str
    # Phase-2.1: Explicit trigger explainability (mandatory)
    triggering_signals: List[str]  # e.g., ["stickiness_delta < 0.3", "no REPLAY in 9 days"]


class CustomerAtRisk(BaseModel):
    """Phase-2.1: At-risk customer with intervention suggestions.

    NAMING CONVENTION (epistemic honesty):
    - risk_signal_strength: Heuristic attention ranking, NOT prediction
    - Only rename to "risk_score" after validation with 10-20 real churn events
    """

    tenant_id: str
    tenant_name: Optional[str] = None

    # Risk signals (renamed for epistemic honesty)
    risk_level: str  # 'critical', 'high', 'medium'
    risk_signal_strength: float  # 0-100 (heuristic, NOT prediction - treat as attention ranking)
    primary_risk_reason: str
    secondary_signals: List[str]

    # Stickiness context
    stickiness_7d: float
    stickiness_30d: float
    stickiness_delta: float  # Ratio - <1 means decelerating

    # Last activity
    last_investigation: Optional[str] = None
    days_since_investigation: Optional[int] = None
    last_api_call: Optional[str] = None
    days_since_api_call: Optional[int] = None

    # Friction signals (with weighted score)
    friction_events_7d: int = 0
    friction_weighted_score: float = 0.0  # Phase-2.1: Weighted friction (not raw count)
    top_friction_type: Optional[str] = None

    # Phase-2.1: "What changed?" correlation layer
    recent_changes: List[str] = []  # e.g., ["policy_change 3 days ago", "model_switch 5 days ago"]
    decay_correlation: Optional[str] = None  # Best guess at what triggered decay

    # Founder interventions
    interventions: List[FounderIntervention]


class InfraLimits(BaseModel):
    """Infrastructure limits and capacity."""

    # Database
    db_connections_current: int
    db_connections_max: int
    db_storage_used_gb: float
    db_storage_limit_gb: float
    db_storage_days_to_limit: Optional[int] = None  # Phase-2: Projection

    # Redis
    redis_memory_used_mb: float
    redis_memory_limit_mb: float
    redis_keys_count: int
    redis_memory_days_to_limit: Optional[int] = None  # Phase-2: Projection

    # API
    requests_per_minute_avg: float
    requests_per_minute_peak: float

    # Phase-2: Growth-based projections
    db_growth_rate_gb_per_day: float = 0.0
    api_growth_rate_pct_per_week: float = 0.0

    # Warnings
    limit_warnings: List[Dict[str, Any]]


# =============================================================================
# Event Stream Models (Phase 2 normalization)
# =============================================================================


class OpsEvent(BaseModel):
    """Single ops event from event stream."""

    event_id: str
    timestamp: Optional[datetime] = None
    tenant_id: Optional[str] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    event_type: str
    entity_type: Optional[str] = None
    entity_id: Optional[str] = None
    severity: Optional[str] = None
    latency_ms: Optional[int] = None
    cost_usd: Optional[float] = None
    metadata: Dict[str, Any] = {}


class OpsEventListResponse(BaseModel):
    """Response for /ops/events endpoint."""

    events: List[OpsEvent]
    total: int
    window_hours: int


# =============================================================================
# Background Job Models (Phase 2 normalization)
# =============================================================================


class OpsJobResult(BaseModel):
    """Response for /ops/jobs/* background job endpoints."""

    status: Literal["completed", "error"]
    message: str
    affected_count: Optional[int] = None
    job_type: Literal["detect-silent-churn", "compute-stickiness"]


# =============================================================================
# Helper Functions
# =============================================================================


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def get_window(hours: int) -> datetime:
    return utc_now() - timedelta(hours=hours)


def exec_sql(session: Session, stmt, params: dict = None):
    """Execute raw SQL with parameters using SQLAlchemy's execute method."""
    if params:
        return session.execute(stmt, params)
    return session.execute(stmt)


# =============================================================================
# Module 1: System Pulse
# =============================================================================


@router.get("/pulse", response_model=SystemPulse)
async def get_system_pulse(
    session: Session = Depends(get_session),
):
    """
    System Pulse - "Is my business healthy right now?"

    Real-time view of system health with 24h deltas.
    Cached for 12 seconds to reduce DB load.
    """
    # Check cache first
    cached = cache_get("pulse")
    if cached:
        return SystemPulse(**cached)

    now = utc_now()
    h24_ago = get_window(24)
    h48_ago = get_window(48)

    # Active tenants (current 24h vs previous 24h)
    stmt = text(
        """
        WITH current_period AS (
            SELECT COUNT(DISTINCT tenant_id) as cnt
            FROM ops_events
            WHERE timestamp > :h24_ago
        ),
        previous_period AS (
            SELECT COUNT(DISTINCT tenant_id) as cnt
            FROM ops_events
            WHERE timestamp > :h48_ago AND timestamp <= :h24_ago
        )
        SELECT
            COALESCE(c.cnt, 0) as current_cnt,
            COALESCE(p.cnt, 0) as previous_cnt
        FROM current_period c, previous_period p
    """
    )

    try:
        row = exec_sql(session, stmt, {"h24_ago": h24_ago, "h48_ago": h48_ago}).first()
        active_current = row[0] if row else 0
        active_previous = row[1] if row else 0
        active_delta = ((active_current - active_previous) / max(active_previous, 1)) * 100
    except Exception:
        # Table might not exist yet
        active_current = 0
        active_previous = 0
        active_delta = 0.0

    # Event counts by type
    def get_event_counts(event_type: str) -> tuple:
        try:
            stmt = text(
                """
                WITH current_period AS (
                    SELECT COUNT(*) as cnt
                    FROM ops_events
                    WHERE event_type = :event_type AND timestamp > :h24_ago
                ),
                previous_period AS (
                    SELECT COUNT(*) as cnt
                    FROM ops_events
                    WHERE event_type = :event_type AND timestamp > :h48_ago AND timestamp <= :h24_ago
                )
                SELECT
                    COALESCE(c.cnt, 0) as current_cnt,
                    COALESCE(p.cnt, 0) as previous_cnt
                FROM current_period c, previous_period p
            """
            )
            row = exec_sql(session, stmt, {"event_type": event_type, "h24_ago": h24_ago, "h48_ago": h48_ago}).first()
            current = row[0] if row else 0
            previous = row[1] if row else 0
            delta = ((current - previous) / max(previous, 1)) * 100
            return current, delta
        except Exception:
            return 0, 0.0

    incidents_cnt, incidents_delta = get_event_counts("INCIDENT_CREATED")
    replays_cnt, replays_delta = get_event_counts("REPLAY_EXECUTED")
    exports_cnt, exports_delta = get_event_counts("EXPORT_GENERATED")

    # LLM health
    try:
        stmt = text(
            """
            SELECT
                COUNT(*) FILTER (WHERE event_type = 'LLM_CALL_MADE') as success,
                COUNT(*) FILTER (WHERE event_type = 'LLM_CALL_FAILED') as failed
            FROM ops_events
            WHERE timestamp > :h24_ago
              AND event_type IN ('LLM_CALL_MADE', 'LLM_CALL_FAILED')
        """
        )
        row = exec_sql(session, stmt, {"h24_ago": h24_ago}).first()
        llm_success = row[0] if row else 0
        llm_failed = row[1] if row else 0
        llm_total = llm_success + llm_failed
        llm_failure_rate = (llm_failed / max(llm_total, 1)) * 100
    except Exception:
        llm_success = 0
        llm_failed = 0
        llm_failure_rate = 0.0

    # Total cost
    try:
        stmt = text(
            """
            SELECT COALESCE(SUM(cost_usd), 0)
            FROM ops_events
            WHERE timestamp > :h24_ago AND cost_usd IS NOT NULL
        """
        )
        row = exec_sql(session, stmt, {"h24_ago": h24_ago}).first()
        total_cost = float(row[0]) if row else 0.0
    except Exception:
        total_cost = 0.0

    # Determine system state
    alerts = []

    if active_delta < -20:
        alerts.append({"type": "warning", "message": f"Active tenants dropped {abs(active_delta):.1f}%"})
    if replays_delta < -30:
        alerts.append({"type": "critical", "message": f"Replays dropped {abs(replays_delta):.1f}% (stickiness signal)"})
    if exports_delta < -40:
        alerts.append({"type": "critical", "message": f"Exports dropped {abs(exports_delta):.1f}% (value signal)"})
    if llm_failure_rate > 5:
        alerts.append({"type": "critical", "message": f"LLM failure rate {llm_failure_rate:.1f}%"})

    if any(a["type"] == "critical" for a in alerts):
        system_state = "critical"
    elif any(a["type"] == "warning" for a in alerts):
        system_state = "degraded"
    else:
        system_state = "healthy"

    result = SystemPulse(
        active_tenants_24h=active_current,
        active_tenants_delta_pct=round(active_delta, 1),
        incidents_created_24h=incidents_cnt,
        incidents_delta_pct=round(incidents_delta, 1),
        replays_executed_24h=replays_cnt,
        replays_delta_pct=round(replays_delta, 1),
        exports_generated_24h=exports_cnt,
        exports_delta_pct=round(exports_delta, 1),
        llm_calls_24h=llm_success + llm_failed,
        llm_failures_24h=llm_failed,
        llm_failure_rate_pct=round(llm_failure_rate, 2),
        total_cost_24h_usd=round(total_cost, 2),
        system_state=system_state,
        alerts=alerts,
        computed_at=now.isoformat(),
    )
    # Cache the result
    cache_set("pulse", result.model_dump())
    return result


# =============================================================================
# Module 2: Customer Intelligence
# =============================================================================


@router.get("/customers", response_model=List[CustomerSegment])
async def get_customer_segments(
    risk_level: Optional[str] = Query(None, description="Filter by risk level"),
    limit: int = Query(50, ge=1, le=200),
    session: Session = Depends(get_session),
):
    """
    Customer Intelligence - All tenant profiles with stickiness and risk.
    Cached for 12 seconds to reduce DB load.
    """
    # Check cache first (keyed by risk_level and limit)
    cache_key = f"customers:{risk_level or 'all'}:{limit}"
    cached = cache_get(cache_key)
    if cached:
        items = [CustomerSegment(**c) for c in cached]
        return wrap_dict({"items": items, "total": len(items)})

    try:
        stmt = text(
            """
            SELECT
                tenant_id,
                first_action,
                first_action_at,
                inferred_buyer_type,
                current_stickiness,
                stickiness_7d,
                stickiness_30d,
                stickiness_delta,
                peak_stickiness,
                stickiness_trend,
                last_api_call,
                last_investigation,
                is_silent_churn,
                risk_level,
                risk_reason,
                time_to_first_replay_m,
                time_to_first_export_m,
                friction_score,
                last_friction_event
            FROM ops_customer_segments
            WHERE (:risk_level IS NULL OR risk_level = :risk_level)
            ORDER BY
                CASE risk_level
                    WHEN 'critical' THEN 1
                    WHEN 'high' THEN 2
                    WHEN 'medium' THEN 3
                    ELSE 4
                END,
                current_stickiness DESC
            LIMIT :limit
        """
        )
        rows = exec_sql(session, stmt, {"risk_level": risk_level, "limit": limit}).all()

        result = [
            CustomerSegment(
                tenant_id=str(r[0]),
                first_action=r[1],
                first_action_at=r[2].isoformat() if r[2] else None,
                inferred_buyer_type=r[3],
                current_stickiness=float(r[4]) if r[4] else 0.0,
                stickiness_7d=float(r[5]) if r[5] else 0.0,
                stickiness_30d=float(r[6]) if r[6] else 0.0,
                stickiness_delta=float(r[7]) if r[7] else 0.0,
                peak_stickiness=float(r[8]) if r[8] else 0.0,
                stickiness_trend=r[9] or "unknown",
                last_api_call=r[10].isoformat() if r[10] else None,
                last_investigation=r[11].isoformat() if r[11] else None,
                is_silent_churn=bool(r[12]),
                risk_level=r[13] or "low",
                risk_reason=r[14],
                time_to_first_replay_m=r[15],
                time_to_first_export_m=r[16],
                friction_score=float(r[17]) if r[17] else 0.0,
                last_friction_event=r[18].isoformat() if r[18] else None,
            )
            for r in rows
        ]
        # Cache the result
        cache_set(cache_key, [c.model_dump() for c in result])
        return wrap_dict({"items": result, "total": len(result)})
    except Exception:
        return wrap_dict({"items": [], "total": 0})


# =============================================================================
# Module 2.5: Customers At Risk (Phase-2)
# NOTE: This route MUST come before /customers/{tenant_id} to avoid route collision
# =============================================================================


def generate_interventions(
    risk_level: str,
    risk_reason: str,
    stickiness_delta: float,
    days_since_investigation: Optional[int],
    friction_type: Optional[str],
    friction_count: int = 0,
) -> List[FounderIntervention]:
    """Generate founder intervention suggestions based on risk signals.

    Phase-2.1 RULE: Every intervention MUST include explicit triggering_signals.
    This enables:
    - Explainability (founder can see "why")
    - Learning (correlate actions with outcomes)
    - Trust calibration (validate signal quality over time)
    """
    interventions = []

    # Critical risk - immediate action
    if risk_level == "critical":
        interventions.append(
            FounderIntervention(
                intervention_type="call",
                priority="immediate",
                suggested_action="Schedule 15-min call with customer",
                context=f"Critical risk: {risk_reason}",
                expected_outcome="Understand blockers, prevent churn",
                triggering_signals=[
                    "risk_level = 'critical'",
                    f"primary_reason: {risk_reason}",
                ],
            )
        )

    # Decelerating stickiness
    if stickiness_delta < 0.5:
        interventions.append(
            FounderIntervention(
                intervention_type="email",
                priority="today",
                suggested_action="Send personalized check-in email",
                context=f"Engagement dropped {(1 - stickiness_delta) * 100:.0f}% vs last week",
                expected_outcome="Re-engage, identify friction points",
                triggering_signals=[
                    f"stickiness_delta = {stickiness_delta:.2f} (< 0.5 threshold)",
                    f"engagement_drop = {(1 - stickiness_delta) * 100:.0f}%",
                ],
            )
        )

    # Long time since investigation
    if days_since_investigation and days_since_investigation > 7:
        interventions.append(
            FounderIntervention(
                intervention_type="feature_help",
                priority="today",
                suggested_action="Send feature guide or video walkthrough",
                context=f"No investigation in {days_since_investigation} days",
                expected_outcome="Remind value, reduce friction",
                triggering_signals=[
                    f"days_since_investigation = {days_since_investigation} (> 7 day threshold)",
                    "no INCIDENT_VIEWED or REPLAY_EXECUTED events",
                ],
            )
        )

    # Friction-based interventions
    if friction_type:
        if friction_type == "POLICY_BLOCK_REPEAT":
            interventions.append(
                FounderIntervention(
                    intervention_type="technical",
                    priority="this_week",
                    suggested_action="Review and adjust their policy configuration",
                    context="Repeated policy blocks causing friction",
                    expected_outcome="Remove blockers, improve experience",
                    triggering_signals=[
                        "top_friction_type = POLICY_BLOCK_REPEAT",
                        f"friction_events_7d = {friction_count}",
                    ],
                )
            )
        elif friction_type in ("REPLAY_ABORTED", "EXPORT_ABORTED", "SESSION_IDLE_TIMEOUT"):
            interventions.append(
                FounderIntervention(
                    intervention_type="email",
                    priority="today",
                    suggested_action="Ask for feedback on incomplete workflows",
                    context="User abandoning flows mid-way",
                    expected_outcome="Identify UX issues, improve conversion",
                    triggering_signals=[
                        f"top_friction_type = {friction_type}",
                        f"friction_events_7d = {friction_count}",
                        "user abandonment pattern detected",
                    ],
                )
            )

    # Silent churn pattern
    if "silent" in (risk_reason or "").lower():
        interventions.append(
            FounderIntervention(
                intervention_type="call",
                priority="today",
                suggested_action="Direct outreach - they may have moved on",
                context="API active but no human engagement",
                expected_outcome="Win back or understand why they left",
                triggering_signals=[
                    "risk_reason contains 'silent'",
                    "API_CALL_RECEIVED events present",
                    "no INCIDENT_VIEWED or REPLAY_EXECUTED events",
                ],
            )
        )

    # Default intervention if none generated
    if not interventions:
        interventions.append(
            FounderIntervention(
                intervention_type="email",
                priority="this_week",
                suggested_action="Send value reminder with recent improvements",
                context=risk_reason or "Moderate risk signals detected",
                expected_outcome="Maintain engagement, gather feedback",
                triggering_signals=[
                    "no specific high-priority triggers met",
                    f"risk_level = {risk_level}",
                    "proactive outreach recommended",
                ],
            )
        )

    return interventions[:3]  # Max 3 interventions


# Friction event weights (Phase-2.1: Different events have different severity)
FRICTION_WEIGHTS = {
    "REPLAY_ABORTED": 3.0,  # High - user gave up on core feature
    "EXPORT_ABORTED": 2.5,  # High - value extraction abandoned
    "REPLAY_FAILED": 2.0,  # System failure - not user's fault but still friction
    "EXPORT_FAILED": 2.0,
    "INCIDENT_VIEWED_NO_ACTION": 1.0,  # Low - hesitation signal
    "POLICY_BLOCK_REPEAT": 2.0,  # Systemic friction
    "SESSION_IDLE_TIMEOUT": 1.5,  # User went away
}

# Caps per session/day to prevent one bad UX path from dominating
FRICTION_CAP_PER_SESSION = 5
FRICTION_CAP_PER_DAY = 10


@router.get("/customers/at-risk", response_model=List[CustomerAtRisk])
async def get_customers_at_risk(
    limit: int = Query(20, ge=1, le=50),
    session: Session = Depends(get_session),
):
    """
    Customers At Risk - Phase-2 Founder Intelligence.

    Returns at-risk customers with:
    - Risk scores and signals
    - Stickiness decay (7d vs 30d)
    - Friction events
    - Suggested founder interventions

    This is THE endpoint for "who should I call today?"
    Cached for 12 seconds to reduce DB load.
    """
    # Check cache first
    cache_key = f"customers-at-risk:{limit}"
    cached = cache_get(cache_key)
    if cached:
        items = [CustomerAtRisk(**c) for c in cached]
        return wrap_dict({"items": items, "total": len(items)})

    h7d_ago = get_window(168)  # 7 days
    now = utc_now()

    try:
        # Get at-risk customers with detailed metrics
        stmt = text(
            """
            WITH customer_stickiness AS (
                SELECT
                    tenant_id,
                    -- 7-day stickiness (weighted recent)
                    (
                        COUNT(*) FILTER (WHERE event_type = 'INCIDENT_VIEWED' AND timestamp > now() - interval '7 days') * 0.2 +
                        COUNT(*) FILTER (WHERE event_type = 'REPLAY_EXECUTED' AND timestamp > now() - interval '7 days') * 0.3 +
                        COUNT(*) FILTER (WHERE event_type = 'EXPORT_GENERATED' AND timestamp > now() - interval '7 days') * 0.5
                    ) as stickiness_7d,
                    -- 30-day stickiness (normalized to weekly)
                    (
                        COUNT(*) FILTER (WHERE event_type = 'INCIDENT_VIEWED' AND timestamp > now() - interval '30 days') * 0.2 +
                        COUNT(*) FILTER (WHERE event_type = 'REPLAY_EXECUTED' AND timestamp > now() - interval '30 days') * 0.3 +
                        COUNT(*) FILTER (WHERE event_type = 'EXPORT_GENERATED' AND timestamp > now() - interval '30 days') * 0.5
                    ) / 4.3 as stickiness_30d,  -- Normalize to weekly (30/7)
                    -- Friction events
                    COUNT(*) FILTER (
                        WHERE timestamp > now() - interval '7 days'
                        AND event_type IN ('REPLAY_ABORTED', 'EXPORT_ABORTED', 'INCIDENT_VIEWED_NO_ACTION', 'POLICY_BLOCK_REPEAT', 'SESSION_IDLE_TIMEOUT')
                    ) as friction_events_7d,
                    -- Last activity
                    MAX(timestamp) FILTER (WHERE event_type IN ('INCIDENT_VIEWED', 'REPLAY_EXECUTED')) as last_investigation,
                    MAX(timestamp) FILTER (WHERE event_type = 'API_CALL_RECEIVED') as last_api_call
                FROM ops_events
                WHERE timestamp > now() - interval '30 days'
                GROUP BY tenant_id
            ),
            friction_types AS (
                SELECT
                    tenant_id,
                    event_type as top_friction_type,
                    ROW_NUMBER() OVER (PARTITION BY tenant_id ORDER BY COUNT(*) DESC) as rn
                FROM ops_events
                WHERE timestamp > now() - interval '7 days'
                  AND event_type IN ('REPLAY_ABORTED', 'EXPORT_ABORTED', 'INCIDENT_VIEWED_NO_ACTION', 'POLICY_BLOCK_REPEAT', 'SESSION_IDLE_TIMEOUT')
                GROUP BY tenant_id, event_type
            )
            SELECT
                cs.tenant_id,
                cs.stickiness_7d,
                cs.stickiness_30d,
                CASE WHEN cs.stickiness_30d > 0 THEN cs.stickiness_7d / cs.stickiness_30d ELSE 0 END as stickiness_delta,
                cs.friction_events_7d,
                cs.last_investigation,
                cs.last_api_call,
                EXTRACT(DAY FROM now() - cs.last_investigation) as days_since_investigation,
                EXTRACT(DAY FROM now() - cs.last_api_call) as days_since_api,
                ft.top_friction_type,
                seg.risk_level,
                seg.risk_reason
            FROM customer_stickiness cs
            LEFT JOIN friction_types ft ON cs.tenant_id = ft.tenant_id AND ft.rn = 1
            LEFT JOIN ops_customer_segments seg ON cs.tenant_id = seg.tenant_id
            WHERE (
                seg.risk_level IN ('critical', 'high')
                OR cs.stickiness_7d < cs.stickiness_30d * 0.5  -- Dropping fast
                OR cs.friction_events_7d > 3
                OR EXTRACT(DAY FROM now() - cs.last_investigation) > 7
            )
            ORDER BY
                CASE seg.risk_level
                    WHEN 'critical' THEN 1
                    WHEN 'high' THEN 2
                    ELSE 3
                END,
                cs.stickiness_7d / NULLIF(cs.stickiness_30d, 0) ASC,  -- Most dropping first
                cs.friction_events_7d DESC
            LIMIT :limit
        """
        )
        rows = exec_sql(session, stmt, {"limit": limit}).all()

        result = []
        for row in rows:
            tenant_id = str(row[0])
            stickiness_7d = float(row[1]) if row[1] else 0.0
            stickiness_30d = float(row[2]) if row[2] else 0.0
            stickiness_delta = float(row[3]) if row[3] else 0.0
            friction_events = int(row[4]) if row[4] else 0
            last_investigation = row[5]
            last_api_call = row[6]
            days_since_inv = int(row[7]) if row[7] else None
            days_since_api = int(row[8]) if row[8] else None
            friction_type = row[9]
            risk_level = row[10] or "medium"
            risk_reason = row[11] or "Engagement declining"

            # Calculate risk score (0-100)
            risk_score = 0
            secondary_signals = []

            # Stickiness drop contributes up to 40 points
            if stickiness_delta < 0.5:
                risk_score += 40
                secondary_signals.append(f"Engagement dropped {(1 - stickiness_delta) * 100:.0f}%")
            elif stickiness_delta < 0.8:
                risk_score += 20
                secondary_signals.append("Engagement declining")

            # Friction events contribute up to 30 points
            if friction_events > 5:
                risk_score += 30
                secondary_signals.append(f"{friction_events} friction events this week")
            elif friction_events > 2:
                risk_score += 15
                secondary_signals.append("Multiple friction events")

            # Time since investigation contributes up to 30 points
            if days_since_inv and days_since_inv > 14:
                risk_score += 30
                secondary_signals.append(f"No investigation in {days_since_inv} days")
            elif days_since_inv and days_since_inv > 7:
                risk_score += 15
                secondary_signals.append("Disengaged for over a week")

            # Phase-2.1: Calculate weighted friction score
            friction_weight = FRICTION_WEIGHTS.get(friction_type, 1.0) if friction_type else 1.0
            # Cap raw count to prevent one bad UX path from dominating
            capped_friction = min(friction_events, FRICTION_CAP_PER_DAY)
            friction_weighted = round(capped_friction * friction_weight, 2)

            # Phase-2.1: Generate "What changed?" signals
            # In production, this would query policy_changes, model_switches, etc.
            recent_changes = []
            decay_correlation = None

            if stickiness_delta < 0.5:
                # Significant decay detected - note this for correlation tracking
                decay_correlation = "engagement_decay_detected"
                if friction_type:
                    decay_correlation = f"friction_correlation: {friction_type}"

            # Generate interventions with friction count
            interventions = generate_interventions(
                risk_level=risk_level,
                risk_reason=risk_reason,
                stickiness_delta=stickiness_delta,
                days_since_investigation=days_since_inv,
                friction_type=friction_type,
                friction_count=friction_events,
            )

            result.append(
                CustomerAtRisk(
                    tenant_id=tenant_id,
                    risk_level=risk_level,
                    risk_signal_strength=min(risk_score, 100),  # Renamed for epistemic honesty
                    primary_risk_reason=risk_reason,
                    secondary_signals=secondary_signals[:3],
                    stickiness_7d=round(stickiness_7d, 2),
                    stickiness_30d=round(stickiness_30d, 2),
                    stickiness_delta=round(stickiness_delta, 2),
                    last_investigation=last_investigation.isoformat() if last_investigation else None,
                    days_since_investigation=days_since_inv,
                    last_api_call=last_api_call.isoformat() if last_api_call else None,
                    days_since_api_call=days_since_api,
                    friction_events_7d=friction_events,
                    friction_weighted_score=friction_weighted,
                    top_friction_type=friction_type,
                    recent_changes=recent_changes,
                    decay_correlation=decay_correlation,
                    interventions=interventions,
                )
            )

        # Cache the result
        cache_set(cache_key, [c.model_dump() for c in result])
        return wrap_dict({"items": result, "total": len(result)})

    except Exception as e:
        # Return empty list on error, log for debugging
        import logging

        logging.getLogger("nova.api.ops").error(f"at-risk query failed: {e}")
        return wrap_dict({"items": [], "total": 0})


# =============================================================================
# Module 2.5b: Customer Detail (must come AFTER /customers/at-risk)
# =============================================================================


@router.get("/customers/{tenant_id}", response_model=CustomerSegment)
async def get_customer_detail(
    tenant_id: str,
    session: Session = Depends(get_session),
):
    """Get detailed customer profile for a specific tenant."""
    try:
        stmt = text(
            """
            SELECT
                tenant_id,
                first_action,
                first_action_at,
                inferred_buyer_type,
                current_stickiness,
                peak_stickiness,
                stickiness_trend,
                last_api_call,
                last_investigation,
                is_silent_churn,
                risk_level,
                risk_reason,
                time_to_first_replay_m,
                time_to_first_export_m
            FROM ops_customer_segments
            WHERE tenant_id = :tenant_id
        """
        )
        row = exec_sql(session, stmt, {"tenant_id": tenant_id}).first()

        if not row:
            raise HTTPException(status_code=404, detail="Customer not found")

        return CustomerSegment(
            tenant_id=str(row[0]),
            first_action=row[1],
            first_action_at=row[2].isoformat() if row[2] else None,
            inferred_buyer_type=row[3],
            current_stickiness=float(row[4]) if row[4] else 0.0,
            peak_stickiness=float(row[5]) if row[5] else 0.0,
            stickiness_trend=row[6] or "unknown",
            last_api_call=row[7].isoformat() if row[7] else None,
            last_investigation=row[8].isoformat() if row[8] else None,
            is_silent_churn=bool(row[9]),
            risk_level=row[10] or "low",
            risk_reason=row[11],
            time_to_first_replay_m=row[12],
            time_to_first_export_m=row[13],
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# Module 2.6: Founder Playbooks (Phase-2.1)
# =============================================================================


class PlaybookAction(BaseModel):
    """A single step in a founder playbook."""

    step: int
    type: str  # 'call', 'email', 'feature_help', 'technical'
    action: str
    timing: str
    talk_track: Optional[str] = None
    template: Optional[str] = None


class PlaybookDetail(BaseModel):
    """A founder playbook with signal → action mapping."""

    id: str
    name: str
    trigger_conditions: List[str]
    risk_level: str
    actions: List[PlaybookAction]
    success_metric: str
    notes: str


@router.get("/playbooks", response_model=List[PlaybookDetail])
async def get_founder_playbooks():
    """
    Founder Playbooks - Signal → Action Matrix.

    Returns the v1 playbooks for manual founder intervention.
    Use these BEFORE automating - learn what works first.

    Playbooks available:
    - silent_churn: API active but no investigation
    - policy_friction: Repeated policy blocks
    - abandonment: Replay/export abandonment pattern
    - engagement_decay: Stickiness drop >50%
    - legal_only: Using certs but no investigation
    """
    result = []
    for playbook_id, playbook in FOUNDER_PLAYBOOKS.items():
        actions = [
            PlaybookAction(
                step=a["step"],
                type=a["type"],
                action=a["action"],
                timing=a["timing"],
                talk_track=a.get("talk_track"),
                template=a.get("template"),
            )
            for a in playbook["actions"]
        ]
        result.append(
            PlaybookDetail(
                id=playbook_id,
                name=playbook["name"],
                trigger_conditions=playbook["trigger_conditions"],
                risk_level=playbook["risk_level"],
                actions=actions,
                success_metric=playbook["success_metric"],
                notes=playbook["notes"],
            )
        )
    return wrap_dict({"items": [r.model_dump() for r in result], "total": len(result)})


@router.get("/playbooks/{playbook_id}", response_model=PlaybookDetail)
async def get_playbook_detail(playbook_id: str):
    """Get a specific founder playbook by ID."""
    if playbook_id not in FOUNDER_PLAYBOOKS:
        raise HTTPException(status_code=404, detail=f"Playbook '{playbook_id}' not found")

    playbook = FOUNDER_PLAYBOOKS[playbook_id]
    actions = [
        PlaybookAction(
            step=a["step"],
            type=a["type"],
            action=a["action"],
            timing=a["timing"],
            talk_track=a.get("talk_track"),
            template=a.get("template"),
        )
        for a in playbook["actions"]
    ]
    return PlaybookDetail(
        id=playbook_id,
        name=playbook["name"],
        trigger_conditions=playbook["trigger_conditions"],
        risk_level=playbook["risk_level"],
        actions=actions,
        success_metric=playbook["success_metric"],
        notes=playbook["notes"],
    )


# =============================================================================
# Module 3: Incident Intelligence
# =============================================================================


@router.get("/incidents/patterns", response_model=List[IncidentPattern])
async def get_incident_patterns(
    session: Session = Depends(get_session),
):
    """
    Incident Intelligence - What's breaking and is it systemic?

    Groups failures by pattern type with trends.
    """
    h24_ago = get_window(24)
    h7d_ago = get_window(168)  # 7 days

    patterns = []

    pattern_types = [
        ("POLICY_BLOCKED", "policy_block"),
        ("LLM_CALL_FAILED", "llm_failure"),
        ("INFRA_LIMIT_HIT", "infra_limit"),
        ("FREEZE_ACTIVATED", "freeze"),
    ]

    for event_type, pattern_name in pattern_types:
        try:
            stmt = text(
                """
                WITH counts AS (
                    SELECT
                        COUNT(*) FILTER (WHERE timestamp > :h24_ago) as cnt_24h,
                        COUNT(*) FILTER (WHERE timestamp > :h7d_ago) as cnt_7d
                    FROM ops_events
                    WHERE event_type = :event_type
                ),
                top_tenants AS (
                    SELECT tenant_id, COUNT(*) as cnt
                    FROM ops_events
                    WHERE event_type = :event_type AND timestamp > :h7d_ago
                    GROUP BY tenant_id
                    ORDER BY cnt DESC
                    LIMIT 3
                ),
                samples AS (
                    SELECT entity_id
                    FROM ops_events
                    WHERE event_type = :event_type AND timestamp > :h24_ago
                    ORDER BY timestamp DESC
                    LIMIT 5
                )
                SELECT
                    c.cnt_24h,
                    c.cnt_7d,
                    ARRAY_AGG(DISTINCT t.tenant_id::text) as top_tenants,
                    ARRAY_AGG(DISTINCT s.entity_id::text) as samples
                FROM counts c
                LEFT JOIN top_tenants t ON true
                LEFT JOIN samples s ON true
                GROUP BY c.cnt_24h, c.cnt_7d
            """
            )
            row = exec_sql(
                session,
                stmt,
                {
                    "event_type": event_type,
                    "h24_ago": h24_ago,
                    "h7d_ago": h7d_ago,
                },
            ).first()

            if row:
                cnt_24h = row[0] or 0
                cnt_7d = row[1] or 0
                daily_avg_7d = cnt_7d / 7

                if cnt_24h > daily_avg_7d * 1.5:
                    trend = "increasing"
                elif cnt_24h < daily_avg_7d * 0.5:
                    trend = "decreasing"
                else:
                    trend = "stable"

                patterns.append(
                    IncidentPattern(
                        pattern_type=pattern_name,
                        count_24h=cnt_24h,
                        count_7d=cnt_7d,
                        trend=trend,
                        top_tenants=[t for t in (row[2] or []) if t],
                        sample_ids=[s for s in (row[3] or []) if s],
                    )
                )
        except Exception:
            continue

    return wrap_dict({"items": [p.model_dump() for p in patterns], "total": len(patterns)})


# =============================================================================
# Phase-S: Infra Incident Summary (PIN-264)
# =============================================================================


@router.get("/incidents/infra-summary")
async def get_infra_incident_summary(
    hours: int = Query(default=24, ge=1, le=168, description="Lookback window in hours"),
    token: FounderToken = Depends(verify_fops_token),
    session: Session = Depends(get_session),
) -> Dict[str, Any]:
    """
    GET /ops/incidents/infra-summary

    Phase-S Infrastructure Incident Summary.

    This endpoint uses the new L4 OpsIncidentService to query
    infra_error_events and return aggregated OpsIncident data.

    Reference: PIN-264 (Phase-S Track 1.3 + L4 Aggregation)

    Returns:
        Aggregated incident summary from infra persistence layer.
    """
    from datetime import timedelta

    from app.adapters.founder_ops_adapter import FounderOpsAdapter
    from app.services.ops import get_ops_facade

    # Calculate time window
    now = datetime.now(timezone.utc)
    since = now - timedelta(hours=hours)

    # Use OpsFacade for proper encapsulation (API-001 compliance)
    ops_facade = get_ops_facade()

    try:
        # Query L4 for incidents via facade
        incidents = ops_facade.get_active_incidents(since=since, until=now)
        summary = ops_facade.get_incident_summary(since=since, until=now)

        # Adapt to Founder view via L3
        adapter = FounderOpsAdapter()
        response = adapter.to_summary_response(
            incidents=incidents,
            summary_counts=summary,
            window_start=since,
            window_end=now,
            max_recent=10,
        )

        # Return as dict (dataclass to dict conversion)
        return wrap_dict({
            "total_incidents": response.total_incidents,
            "by_severity": response.by_severity,
            "recent_incidents": [
                {
                    "incident_id": inc.incident_id,
                    "title": inc.title,
                    "severity": inc.severity,
                    "component": inc.component,
                    "occurrence_count": inc.occurrence_count,
                    "first_seen": inc.first_seen,
                    "last_seen": inc.last_seen,
                    "affected_runs": inc.affected_runs,
                    "affected_agents": inc.affected_agents,
                    "is_resolved": inc.is_resolved,
                }
                for inc in response.recent_incidents
            ],
            "window_start": response.window_start,
            "window_end": response.window_end,
        })
    except Exception as e:
        # Graceful degradation: return empty summary if infra_error_events not ready
        logging.warning(f"infra-summary query failed (table may not exist yet): {e}")
        return wrap_dict({
            "total_incidents": 0,
            "by_severity": {"urgent": 0, "action": 0, "attention": 0, "info": 0},
            "recent_incidents": [],
            "window_start": since.isoformat(),
            "window_end": now.isoformat(),
            "error": "Infrastructure error table not available",
        })


# =============================================================================
# Module 3.1: Founder Incident Detail (M29 Category 5)
# =============================================================================


@router.get("/incidents/{incident_id}", response_model=FounderIncidentDetailDTO)
async def get_founder_incident_detail(
    incident_id: str,
    token: FounderToken = Depends(verify_fops_token),
    session: Session = Depends(get_session),
) -> FounderIncidentDetailDTO:
    """
    GET /ops/incidents/{incident_id}

    Founder Incident Detail - Full causality and impact analysis.

    M29 Category 5: Incident Console Contrast

    Answers:
    - What failed?
    - Why?
    - What system allowed it?
    - Is it recurring?
    - What do we do next?

    Contains internal terminology, thresholds, and raw metrics.
    NEVER expose to Customer Console.
    """
    from sqlmodel import select

    # Get incident
    stmt = select(Incident).where(Incident.id == incident_id)
    result = session.exec(stmt).first()

    if not result:
        raise HTTPException(status_code=404, detail="Incident not found")

    incident = result[0] if isinstance(result, tuple) else result

    # Get tenant name
    tenant_name = None
    try:
        tenant_result = session.execute(
            text("SELECT name FROM tenants WHERE id = :tenant_id"), {"tenant_id": incident.tenant_id}
        ).first()
        if tenant_result:
            tenant_name = tenant_result[0]
    except Exception:
        pass

    # Map status to lifecycle state
    status_to_state = {
        "open": "DETECTED",
        "acknowledged": "TRIAGED",
        "resolved": "RESOLVED",
        "auto_resolved": "MITIGATED",
    }
    current_state = status_to_state.get(incident.status, "DETECTED")

    # Map trigger_type to incident_type
    trigger_to_type = {
        "cost_spike": "COST",
        "budget_breach": "COST",
        "rate_limit": "RATE_LIMIT",
        "failure_spike": "RELIABILITY",
        "policy_block": "POLICY",
        "safety": "SAFETY",
    }
    incident_type = trigger_to_type.get(incident.trigger_type, "POLICY")

    # Build header
    header = FounderIncidentHeaderDTO(
        incident_id=incident.id,
        incident_type=incident_type,
        severity=incident.severity,
        tenant_id=incident.tenant_id,
        tenant_name=tenant_name,
        current_state=current_state,
        first_detected=(incident.started_at or incident.created_at).isoformat(),
        last_updated=incident.updated_at.isoformat(),
    )

    # Get timeline events
    event_stmt = (
        select(IncidentEvent).where(IncidentEvent.incident_id == incident_id).order_by(IncidentEvent.created_at)
    )
    event_rows = session.exec(event_stmt).all()

    timeline = []
    for row in event_rows:
        event = row[0] if isinstance(row, tuple) else row
        # Map event_type to founder timeline event type
        event_type_map = {
            "detection": "DETECTION_SIGNAL",
            "escalation": "ESCALATION",
            "action": "RECOVERY_ACTION",
            "resolution": "RESOLUTION",
            "policy_evaluated": "POLICY_EVALUATION",
            "cost_anomaly": "COST_ANOMALY",
        }
        mapped_type = event_type_map.get(event.event_type, "DETECTION_SIGNAL")

        timeline.append(
            FounderDecisionTimelineEventDTO(
                timestamp=event.created_at.isoformat(),
                event_type=mapped_type,
                description=event.description,
                data=event.get_data() if hasattr(event, "get_data") else None,
            )
        )

    # Build root cause - derive from trigger type and action details
    derived_cause = "UNKNOWN"
    evidence = f"Triggered by {incident.trigger_type}"
    confidence = "medium"
    baseline_value = None
    actual_value = None
    threshold_breached = None

    if incident.action_details_json:
        try:
            details = json.loads(incident.action_details_json)
            if details.get("retry_ratio"):
                derived_cause = "RETRY_LOOP"
                evidence = f"retry/request +{details.get('retry_ratio', 0) * 100:.0f}% over baseline"
                actual_value = details.get("retry_ratio")
            elif details.get("prompt_growth"):
                derived_cause = "PROMPT_GROWTH"
                evidence = f"prompt tokens +{details.get('prompt_growth', 0) * 100:.0f}% over baseline"
            elif details.get("feature_concentration"):
                derived_cause = "FEATURE_SURGE"
                evidence = f"cost concentrated in {details.get('top_feature', 'unknown')}"
            baseline_value = details.get("baseline_value")
            actual_value = actual_value or details.get("actual_value")
            threshold_breached = details.get("threshold")
        except Exception:
            pass

    if incident.trigger_type == "rate_limit":
        derived_cause = "RATE_LIMIT_BREACH"
        confidence = "high"
    elif incident.trigger_type == "budget_breach":
        derived_cause = "BUDGET_EXCEEDED"
        confidence = "high"
    elif incident.trigger_type == "policy_block":
        derived_cause = "POLICY_VIOLATION"
        confidence = "high"

    root_cause = FounderRootCauseDTO(
        derived_cause=derived_cause,
        evidence=evidence,
        confidence=confidence,
        baseline_value=baseline_value,
        actual_value=actual_value,
        threshold_breached=threshold_breached,
    )

    # Build blast radius
    cost_impact_pct = 0.0
    if incident.cost_delta_cents:
        # Estimate daily baseline (rough)
        cost_impact_pct = float(incident.cost_delta_cents) / 100.0  # Simplified

    blast_radius = FounderBlastRadiusDTO(
        requests_affected=incident.calls_affected or 0,
        requests_blocked=0,  # Would need to calculate from events
        cost_impact_cents=int(incident.cost_delta_cents * 100) if incident.cost_delta_cents else 0,
        cost_impact_pct=cost_impact_pct,
        duration_seconds=incident.duration_seconds or 0,
        customer_visible_degradation=incident.severity in ["critical", "high"],
        users_affected=0,  # Would need to calculate from related calls
        features_affected=[],  # Would need to extract from related calls
    )

    # Check for recurrence
    h7d_ago = datetime.now(timezone.utc) - timedelta(days=7)
    h30d_ago = datetime.now(timezone.utc) - timedelta(days=30)

    similar_7d = 0
    similar_30d = 0
    same_tenant = False
    same_feature = False
    same_cause = False

    try:
        # Count similar incidents (same trigger_type)
        stmt = text(
            """
            SELECT
                COUNT(*) FILTER (WHERE created_at > :h7d_ago) as cnt_7d,
                COUNT(*) FILTER (WHERE created_at > :h30d_ago) as cnt_30d,
                COUNT(*) FILTER (WHERE tenant_id = :tenant_id AND created_at > :h7d_ago) as same_tenant_7d
            FROM incidents
            WHERE trigger_type = :trigger_type
              AND id != :incident_id
        """
        )
        row = session.execute(
            stmt,
            {
                "h7d_ago": h7d_ago,
                "h30d_ago": h30d_ago,
                "tenant_id": incident.tenant_id,
                "trigger_type": incident.trigger_type,
                "incident_id": incident_id,
            },
        ).first()

        if row:
            similar_7d = row[0] or 0
            similar_30d = row[1] or 0
            same_tenant = (row[2] or 0) > 0
    except Exception:
        pass

    risk_level = "low"
    if similar_7d >= 3 or same_tenant:
        risk_level = "high"
    elif similar_7d >= 1:
        risk_level = "medium"

    suggested_prevention = None
    if derived_cause == "RETRY_LOOP":
        suggested_prevention = "Review retry logic and implement exponential backoff"
    elif derived_cause == "PROMPT_GROWTH":
        suggested_prevention = "Audit prompt templates for token efficiency"
    elif derived_cause == "FEATURE_SURGE":
        suggested_prevention = "Investigate feature usage patterns and consider rate limiting"

    recurrence_risk = FounderRecurrenceRiskDTO(
        similar_incidents_7d=similar_7d,
        similar_incidents_30d=similar_30d,
        same_tenant_recurrence=same_tenant,
        same_feature_recurrence=same_feature,
        same_root_cause_recurrence=similar_7d > 0,
        risk_level=risk_level,
        suggested_prevention=suggested_prevention,
    )

    # Get linked call IDs
    linked_calls = incident.get_related_call_ids() if hasattr(incident, "get_related_call_ids") else []

    # Build recommended next steps
    next_steps = []
    if risk_level == "high":
        next_steps.append("Investigate root cause immediately")
        next_steps.append("Review tenant's recent API usage")
    if incident.status == "open":
        next_steps.append("Acknowledge and assign to team member")
    if derived_cause != "UNKNOWN":
        next_steps.append(f"Address {derived_cause} pattern")

    return FounderIncidentDetailDTO(
        header=header,
        timeline=timeline,
        root_cause=root_cause,
        blast_radius=blast_radius,
        recurrence_risk=recurrence_risk,
        related_cost_anomaly_id=None,  # Would link from cost_anomalies table
        related_killswitch_id=incident.killswitch_id,
        linked_call_ids=linked_calls[:10],  # Limit to first 10
        action_taken=incident.auto_action,
        action_details=json.loads(incident.action_details_json) if incident.action_details_json else None,
        recommended_next_steps=next_steps,
    )


@router.get("/incidents", response_model=FounderIncidentListDTO)
async def get_founder_incidents(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    severity: Optional[str] = Query(default=None),
    state: Optional[str] = Query(default=None),
    token: FounderToken = Depends(verify_fops_token),
    session: Session = Depends(get_session),
) -> FounderIncidentListDTO:
    """
    GET /ops/incidents

    Founder Incident List - All incidents with summary stats.

    M29 Category 5: Incident Console Contrast
    """
    from sqlalchemy import desc
    from sqlmodel import select

    # Build query
    stmt = select(Incident).order_by(desc(Incident.created_at))

    if severity:
        stmt = stmt.where(Incident.severity == severity)
    if state:
        status_map = {
            "DETECTED": "open",
            "TRIAGED": "acknowledged",
            "RESOLVED": "resolved",
            "MITIGATED": "auto_resolved",
        }
        if state in status_map:
            stmt = stmt.where(Incident.status == status_map[state])

    # Pagination
    stmt = stmt.offset((page - 1) * page_size).limit(page_size)
    rows = session.exec(stmt).all()

    # Convert to response models
    incidents_list = list(rows)

    # Count total (raw SQL for aggregation - uses execute() not exec())
    count_stmt = text("SELECT COUNT(*) FROM incidents")
    total_row = session.execute(count_stmt).first()
    total = total_row[0] if total_row else 0

    # Count active, critical, high
    counts_stmt = text(
        """
        SELECT
            COUNT(*) FILTER (WHERE status != 'resolved') as active,
            COUNT(*) FILTER (WHERE severity = 'critical') as critical,
            COUNT(*) FILTER (WHERE severity = 'high') as high
        FROM incidents
    """
    )
    counts_row = session.execute(counts_stmt).first()
    active_count = counts_row[0] if counts_row else 0
    critical_count = counts_row[1] if counts_row else 0
    high_count = counts_row[2] if counts_row else 0

    # Map to DTOs
    items = []
    for row in rows:
        incident = row[0] if isinstance(row, tuple) else row

        # Get tenant name
        tenant_name = None
        try:
            tenant_result = session.execute(
                text("SELECT name FROM tenants WHERE id = :tenant_id"), {"tenant_id": incident.tenant_id}
            ).first()
            if tenant_result:
                tenant_name = tenant_result[0]
        except Exception:
            pass

        # Map types
        trigger_to_type = {
            "cost_spike": "COST",
            "budget_breach": "COST",
            "rate_limit": "RATE_LIMIT",
            "failure_spike": "RELIABILITY",
            "policy_block": "POLICY",
            "safety": "SAFETY",
        }
        status_to_state = {
            "open": "DETECTED",
            "acknowledged": "TRIAGED",
            "resolved": "RESOLVED",
            "auto_resolved": "MITIGATED",
        }

        items.append(
            FounderIncidentListItemDTO(
                incident_id=incident.id,
                incident_type=trigger_to_type.get(incident.trigger_type, "POLICY"),
                severity=incident.severity,
                current_state=status_to_state.get(incident.status, "DETECTED"),
                tenant_id=incident.tenant_id,
                tenant_name=tenant_name,
                title=incident.title,
                root_cause=None,  # Would derive from action_details
                requests_affected=incident.calls_affected or 0,
                cost_impact_cents=int(incident.cost_delta_cents * 100) if incident.cost_delta_cents else 0,
                first_detected=(incident.started_at or incident.created_at).isoformat(),
                duration_seconds=incident.duration_seconds,
                is_recurring=False,  # Would need to check recurrence
            )
        )

    return FounderIncidentListDTO(
        incidents=items,
        total=total,
        page=page,
        page_size=page_size,
        active_count=active_count,
        critical_count=critical_count,
        high_count=high_count,
    )


# =============================================================================
# Module 4: Product Stickiness
# =============================================================================


@router.get("/stickiness", response_model=List[StickinessByFeature])
async def get_stickiness_by_feature(
    session: Session = Depends(get_session),
):
    """
    Product Stickiness - Which feature actually keeps users?

    Analyzes 30-day feature usage to identify stickiness drivers.
    """
    h30d_ago = get_window(720)  # 30 days

    features = []
    feature_events = [
        ("incidents", "INCIDENT_VIEWED"),
        ("replays", "REPLAY_EXECUTED"),
        ("exports", "EXPORT_GENERATED"),
        ("certs", "CERT_VERIFIED"),
    ]

    try:
        # Get total active tenants for percentage calc
        stmt = text(
            """
            SELECT COUNT(DISTINCT tenant_id)
            FROM ops_events
            WHERE timestamp > :h30d_ago
        """
        )
        row = exec_sql(session, stmt, {"h30d_ago": h30d_ago}).first()
        total_active = row[0] if row else 1
    except Exception:
        total_active = 1

    for feature_name, event_type in feature_events:
        try:
            stmt = text(
                """
                SELECT
                    COUNT(*) as total_actions,
                    COUNT(DISTINCT tenant_id) as unique_tenants
                FROM ops_events
                WHERE event_type = :event_type
                  AND timestamp > :h30d_ago
            """
            )
            row = exec_sql(
                session,
                stmt,
                {
                    "event_type": event_type,
                    "h30d_ago": h30d_ago,
                },
            ).first()

            total_actions = row[0] if row else 0
            unique_tenants = row[1] if row else 0
            avg_per_tenant = total_actions / max(unique_tenants, 1)
            pct_of_active = (unique_tenants / max(total_active, 1)) * 100

            features.append(
                StickinessByFeature(
                    feature=feature_name,
                    total_actions_30d=total_actions,
                    unique_tenants=unique_tenants,
                    avg_per_tenant=round(avg_per_tenant, 2),
                    pct_of_active_tenants=round(pct_of_active, 1),
                )
            )
        except Exception:
            continue

    return sorted(features, key=lambda x: x.pct_of_active_tenants, reverse=True)


# =============================================================================
# Module 5: Revenue & Risk
# =============================================================================


@router.get("/revenue", response_model=RevenueRisk)
async def get_revenue_risk(
    session: Session = Depends(get_session),
):
    """
    Revenue & Risk - Am I making money safely?

    MRR estimates, at-risk tenants, silent churn detection.
    """
    try:
        # At-risk tenants from customer segments
        stmt = text(
            """
            SELECT
                COUNT(*) FILTER (WHERE risk_level = 'critical') as critical,
                COUNT(*) FILTER (WHERE risk_level = 'high') as high,
                COUNT(*) FILTER (WHERE is_silent_churn = true) as silent_churn
            FROM ops_customer_segments
        """
        )
        row = session.execute(stmt).first()
        critical = row[0] if row else 0
        high = row[1] if row else 0
        silent_churn = row[2] if row else 0
    except Exception:
        critical = 0
        high = 0
        silent_churn = 0

    # Daily revenue from LLM costs (proxy for revenue)
    h24_ago = get_window(24)
    try:
        stmt = text(
            """
            SELECT COALESCE(SUM(cost_usd), 0)
            FROM ops_events
            WHERE event_type = 'LLM_CALL_MADE'
              AND timestamp > :h24_ago
        """
        )
        row = exec_sql(session, stmt, {"h24_ago": h24_ago}).first()
        daily_cost = float(row[0]) if row else 0.0
        # Assume 2x markup for revenue
        daily_revenue = daily_cost * 2
    except Exception:
        daily_revenue = 0.0

    # MRR estimate (active tenants * $50 avg plan)
    try:
        stmt = text(
            """
            SELECT COUNT(DISTINCT tenant_id)
            FROM ops_events
            WHERE timestamp > :h24_ago
        """
        )
        row = exec_sql(session, stmt, {"h24_ago": h24_ago}).first()
        active_tenants = row[0] if row else 0
        mrr_estimate = active_tenants * 50  # $50 avg plan assumption
    except Exception:
        mrr_estimate = 0.0

    # Revenue alerts
    alerts = []
    if silent_churn > 0:
        alerts.append(
            {
                "type": "warning",
                "message": f"{silent_churn} tenants showing silent churn (API active, no investigation)",
            }
        )
    if critical > 0:
        alerts.append({"type": "critical", "message": f"{critical} tenants at critical risk level"})

    return RevenueRisk(
        mrr_estimate_usd=round(mrr_estimate, 2),
        daily_api_revenue_usd=round(daily_revenue, 2),
        at_risk_tenants=critical + high,
        silent_churn_count=silent_churn,
        high_risk_count=critical,
        revenue_alerts=alerts,
    )


# =============================================================================
# Module 6: Infra & Limits
# =============================================================================


@router.get("/infra", response_model=InfraLimits)
async def get_infra_limits(
    session: Session = Depends(get_session),
):
    """
    Infra & Limits - What breaks first if I grow?

    Database, Redis, and API capacity metrics with days-to-limit projections.
    Cached for 30 seconds (infra metrics change slowly).
    """
    # Check cache first (longer TTL for infra)
    cached = cache_get("infra")
    if cached:
        return wrap_dict(InfraLimits(**cached).model_dump())

    warnings = []

    # Database connection check
    try:
        stmt = text("SELECT count(*) FROM pg_stat_activity WHERE state = 'active'")
        row = session.execute(stmt).first()
        db_connections = row[0] if row else 0

        stmt = text("SHOW max_connections")
        row = session.execute(stmt).first()
        db_max = int(row[0]) if row else 100
    except Exception:
        db_connections = 0
        db_max = 100

    # Database size
    try:
        stmt = text("SELECT pg_database_size(current_database()) / 1024 / 1024 / 1024.0")
        row = session.execute(stmt).first()
        db_size_gb = float(row[0]) if row else 0.0
    except Exception:
        db_size_gb = 0.0

    # Phase-2: Calculate DB growth rate from INFRA_LIMIT_HIT events or event volume
    db_growth_rate = 0.0
    db_days_to_limit = None
    try:
        # Estimate growth from event volume (proxy for data growth)
        stmt = text(
            """
            WITH daily_events AS (
                SELECT
                    date_trunc('day', timestamp) as day,
                    COUNT(*) as event_count
                FROM ops_events
                WHERE timestamp > now() - interval '7 days'
                GROUP BY 1
            )
            SELECT
                COALESCE(AVG(event_count), 0) as avg_events_per_day,
                COALESCE(
                    (MAX(event_count) - MIN(event_count)) / NULLIF(COUNT(*), 0),
                    0
                ) as growth_trend
            FROM daily_events
        """
        )
        row = exec_sql(session, stmt, {}).first()
        avg_events = float(row[0]) if row else 0
        # Rough estimate: 1KB per event average
        db_growth_rate = avg_events * 0.000001  # Convert to GB/day

        # Calculate days to limit
        db_limit = 10.0  # Neon Pro limit
        remaining_gb = db_limit - db_size_gb
        if db_growth_rate > 0 and remaining_gb > 0:
            db_days_to_limit = int(remaining_gb / db_growth_rate)
            if db_days_to_limit > 365:
                db_days_to_limit = None  # More than a year, not concerning
    except Exception:
        pass

    # API request rate (from ops_events)
    h1_ago = get_window(1)
    rpm_avg = 0.0
    rpm_peak = 0.0
    api_growth_rate = 0.0
    try:
        stmt = text(
            """
            SELECT COUNT(*) / 60.0
            FROM ops_events
            WHERE event_type = 'API_CALL_RECEIVED'
              AND timestamp > :h1_ago
        """
        )
        row = exec_sql(session, stmt, {"h1_ago": h1_ago}).first()
        rpm_avg = float(row[0]) if row else 0.0

        stmt = text(
            """
            SELECT MAX(cnt) FROM (
                SELECT date_trunc('minute', timestamp) as minute, COUNT(*) as cnt
                FROM ops_events
                WHERE event_type = 'API_CALL_RECEIVED'
                  AND timestamp > :h1_ago
                GROUP BY 1
            ) sub
        """
        )
        row = exec_sql(session, stmt, {"h1_ago": h1_ago}).first()
        rpm_peak = float(row[0]) if row else 0.0

        # Phase-2: Calculate week-over-week API growth
        stmt = text(
            """
            WITH weekly_requests AS (
                SELECT
                    COUNT(*) FILTER (WHERE timestamp > now() - interval '7 days') as this_week,
                    COUNT(*) FILTER (WHERE timestamp <= now() - interval '7 days' AND timestamp > now() - interval '14 days') as last_week
                FROM ops_events
                WHERE event_type = 'API_CALL_RECEIVED'
                  AND timestamp > now() - interval '14 days'
            )
            SELECT
                this_week,
                last_week,
                CASE
                    WHEN last_week > 0 THEN ((this_week - last_week)::float / last_week) * 100
                    ELSE 0
                END as growth_pct
            FROM weekly_requests
        """
        )
        row = exec_sql(session, stmt, {}).first()
        if row:
            api_growth_rate = float(row[2]) if row[2] else 0.0
    except Exception:
        pass

    # Generate warnings with Phase-2 projections
    if db_connections / max(db_max, 1) > 0.8:
        warnings.append(
            {
                "resource": "db_connections",
                "message": f"Database connections at {(db_connections / db_max) * 100:.1f}%",
                "severity": "warning",
            }
        )
    if db_size_gb > 8:  # 80% of 10GB Neon limit
        warnings.append(
            {
                "resource": "db_storage",
                "message": f"Database storage at {db_size_gb:.1f}GB (limit: 10GB)",
                "severity": "warning",
            }
        )

    # Phase-2: Days-to-limit warning
    if db_days_to_limit and db_days_to_limit < 30:
        warnings.append(
            {
                "resource": "db_storage",
                "message": f"At current growth, DB storage limit reached in {db_days_to_limit} days",
                "severity": "critical" if db_days_to_limit < 7 else "warning",
                "days_to_limit": db_days_to_limit,
            }
        )

    # Phase-2: API growth warning
    if api_growth_rate > 50:  # Growing >50% week-over-week
        warnings.append(
            {
                "resource": "api_traffic",
                "message": f"API traffic growing {api_growth_rate:.1f}% week-over-week - review capacity",
                "severity": "warning",
            }
        )

    result = InfraLimits(
        db_connections_current=db_connections,
        db_connections_max=db_max,
        db_storage_used_gb=round(db_size_gb, 2),
        db_storage_limit_gb=10.0,  # Neon Pro limit
        db_storage_days_to_limit=db_days_to_limit,
        redis_memory_used_mb=0.0,  # TODO: Redis metrics via Upstash API
        redis_memory_limit_mb=256.0,  # Upstash limit
        redis_keys_count=0,
        redis_memory_days_to_limit=None,  # TODO: Calculate from Redis metrics
        requests_per_minute_avg=round(rpm_avg, 2),
        requests_per_minute_peak=round(rpm_peak, 2),
        db_growth_rate_gb_per_day=round(db_growth_rate, 6),
        api_growth_rate_pct_per_week=round(api_growth_rate, 1),
        limit_warnings=warnings,
    )
    # Cache with longer TTL (infra metrics change slowly)
    cache_set("infra", result.model_dump(), 30)
    return wrap_dict(result.model_dump())


# =============================================================================
# Module 7: Replay Lab (Event Stream)
# =============================================================================


@router.get("/events", response_model=OpsEventListResponse)
async def get_event_stream(
    tenant_id: Optional[str] = Query(None, description="Filter by tenant"),
    event_type: Optional[str] = Query(None, description="Filter by event type"),
    hours: int = Query(24, ge=1, le=168, description="Hours to look back"),
    limit: int = Query(100, ge=1, le=1000),
    session: Session = Depends(get_session),
) -> OpsEventListResponse:
    """
    Event Stream - Raw events for debugging and analysis.

    Use this for Replay Lab functionality.
    """
    window = get_window(hours)

    try:
        stmt = text(
            """
            SELECT
                event_id,
                timestamp,
                tenant_id,
                user_id,
                session_id,
                event_type,
                entity_type,
                entity_id,
                severity,
                latency_ms,
                cost_usd,
                metadata
            FROM ops_events
            WHERE timestamp > :window
              AND (:tenant_id IS NULL OR tenant_id::text = :tenant_id)
              AND (:event_type IS NULL OR event_type = :event_type)
            ORDER BY timestamp DESC
            LIMIT :limit
        """
        )
        rows = exec_sql(
            session,
            stmt,
            {
                "window": window,
                "tenant_id": tenant_id,
                "event_type": event_type,
                "limit": limit,
            },
        ).all()

        events = [
            OpsEvent(
                event_id=str(r[0]),
                timestamp=r[1],  # datetime, not str - FastAPI handles serialization
                tenant_id=str(r[2]) if r[2] else None,
                user_id=str(r[3]) if r[3] else None,
                session_id=str(r[4]) if r[4] else None,
                event_type=r[5],
                entity_type=r[6],
                entity_id=str(r[7]) if r[7] else None,
                severity=r[8],
                latency_ms=r[9],
                cost_usd=float(r[10]) if r[10] else None,
                metadata=r[11] or {},
            )
            for r in rows
        ]

        return OpsEventListResponse(
            events=events,
            total=len(rows),
            window_hours=hours,
        )
    except Exception as e:
        logger.error(f"Failed to fetch ops events: {e}")
        return OpsEventListResponse(events=[], total=0, window_hours=hours)


# =============================================================================
# REMOVED: Job Endpoints (PIN-254 Phase C Fix - C1 Decorative Violation)
# =============================================================================
#
# Rationale: POST /ops/jobs/detect-silent-churn and POST /ops/jobs/compute-stickiness
# were C1 (Decorative API) violations - they existed in L2 API surface but had no
# real execution path in production (JOB_ENDPOINTS_ENABLED=false by default).
#
# Fix: Removed from L2 API. Job triggers should be invoked via:
#   - L7 systemd timer: /etc/systemd/system/aos-detect-silent-churn.timer
#   - L7 systemd timer: /etc/systemd/system/aos-compute-stickiness.timer
#   - Direct service call: OpsWriteService(session).update_silent_churn()
#   - Direct service call: OpsWriteService(session).compute_stickiness_scores()
#
# Reference: PIN-254 Phase C, LAYERED_SEMANTIC_COMPLETION_CONTRACT.md
# =============================================================================
