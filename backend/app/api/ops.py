"""Ops Console API - Founder Intelligence System

PIN-105: Ops Console - Founder Intelligence System

This router provides endpoints for the Operator Console (ops.agenticverz.com).
Focused on BEHAVIORAL TRUTH - answer founder questions without customer input.

Modules:
1. System Pulse     - "Is my business healthy right now?"
2. Customer Intel   - "Who is this customer and are they slipping?"
3. Incident Intel   - "What is breaking and is it systemic?"
4. Product Stickiness - "Which feature actually keeps users?"
5. Revenue & Risk   - "Am I making money safely?"
6. Infra & Limits   - "What breaks first if I grow?"
7. Replay Lab       - "Can I reproduce and fix anything?"

All insights are derived from ops_events table (event-sourced).
"""

import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import and_, desc, func, select, text
from sqlalchemy.orm import Session as SASession
from sqlmodel import Session

from app.db import get_session
from app.services.event_emitter import EventType

# =============================================================================
# Router - Operator-only access (requires ops auth)
# =============================================================================

router = APIRouter(prefix="/ops", tags=["Ops Console"])


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

    # Stickiness
    current_stickiness: float
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


class InfraLimits(BaseModel):
    """Infrastructure limits and capacity."""

    # Database
    db_connections_current: int
    db_connections_max: int
    db_storage_used_gb: float
    db_storage_limit_gb: float

    # Redis
    redis_memory_used_mb: float
    redis_memory_limit_mb: float
    redis_keys_count: int

    # API
    requests_per_minute_avg: float
    requests_per_minute_peak: float

    # Warnings
    limit_warnings: List[Dict[str, Any]]


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
    """
    now = utc_now()
    h24_ago = get_window(24)
    h48_ago = get_window(48)

    # Active tenants (current 24h vs previous 24h)
    stmt = text("""
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
    """)

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
            stmt = text("""
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
            """)
            row = exec_sql(session, stmt, {
                "event_type": event_type,
                "h24_ago": h24_ago,
                "h48_ago": h48_ago
            }).first()
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
        stmt = text("""
            SELECT
                COUNT(*) FILTER (WHERE event_type = 'LLM_CALL_MADE') as success,
                COUNT(*) FILTER (WHERE event_type = 'LLM_CALL_FAILED') as failed
            FROM ops_events
            WHERE timestamp > :h24_ago
              AND event_type IN ('LLM_CALL_MADE', 'LLM_CALL_FAILED')
        """)
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
        stmt = text("""
            SELECT COALESCE(SUM(cost_usd), 0)
            FROM ops_events
            WHERE timestamp > :h24_ago AND cost_usd IS NOT NULL
        """)
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

    return SystemPulse(
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
    """
    try:
        stmt = text("""
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
        """)
        rows = exec_sql(session, stmt, {"risk_level": risk_level, "limit": limit}).all()

        return [
            CustomerSegment(
                tenant_id=str(r[0]),
                first_action=r[1],
                first_action_at=r[2].isoformat() if r[2] else None,
                inferred_buyer_type=r[3],
                current_stickiness=float(r[4]) if r[4] else 0.0,
                peak_stickiness=float(r[5]) if r[5] else 0.0,
                stickiness_trend=r[6] or "unknown",
                last_api_call=r[7].isoformat() if r[7] else None,
                last_investigation=r[8].isoformat() if r[8] else None,
                is_silent_churn=bool(r[9]),
                risk_level=r[10] or "low",
                risk_reason=r[11],
                time_to_first_replay_m=r[12],
                time_to_first_export_m=r[13],
            )
            for r in rows
        ]
    except Exception:
        return []


@router.get("/customers/{tenant_id}", response_model=CustomerSegment)
async def get_customer_detail(
    tenant_id: str,
    session: Session = Depends(get_session),
):
    """Get detailed customer profile for a specific tenant."""
    try:
        stmt = text("""
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
        """)
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
            stmt = text("""
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
            """)
            row = exec_sql(session, stmt, {
                "event_type": event_type,
                "h24_ago": h24_ago,
                "h7d_ago": h7d_ago,
            }).first()

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

                patterns.append(IncidentPattern(
                    pattern_type=pattern_name,
                    count_24h=cnt_24h,
                    count_7d=cnt_7d,
                    trend=trend,
                    top_tenants=[t for t in (row[2] or []) if t],
                    sample_ids=[s for s in (row[3] or []) if s],
                ))
        except Exception:
            continue

    return patterns


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
        stmt = text("""
            SELECT COUNT(DISTINCT tenant_id)
            FROM ops_events
            WHERE timestamp > :h30d_ago
        """)
        row = exec_sql(session, stmt, {"h30d_ago": h30d_ago}).first()
        total_active = row[0] if row else 1
    except Exception:
        total_active = 1

    for feature_name, event_type in feature_events:
        try:
            stmt = text("""
                SELECT
                    COUNT(*) as total_actions,
                    COUNT(DISTINCT tenant_id) as unique_tenants
                FROM ops_events
                WHERE event_type = :event_type
                  AND timestamp > :h30d_ago
            """)
            row = exec_sql(session, stmt, {
                "event_type": event_type,
                "h30d_ago": h30d_ago,
            }).first()

            total_actions = row[0] if row else 0
            unique_tenants = row[1] if row else 0
            avg_per_tenant = total_actions / max(unique_tenants, 1)
            pct_of_active = (unique_tenants / max(total_active, 1)) * 100

            features.append(StickinessByFeature(
                feature=feature_name,
                total_actions_30d=total_actions,
                unique_tenants=unique_tenants,
                avg_per_tenant=round(avg_per_tenant, 2),
                pct_of_active_tenants=round(pct_of_active, 1),
            ))
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
        stmt = text("""
            SELECT
                COUNT(*) FILTER (WHERE risk_level = 'critical') as critical,
                COUNT(*) FILTER (WHERE risk_level = 'high') as high,
                COUNT(*) FILTER (WHERE is_silent_churn = true) as silent_churn
            FROM ops_customer_segments
        """)
        row = session.exec(stmt).first()
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
        stmt = text("""
            SELECT COALESCE(SUM(cost_usd), 0)
            FROM ops_events
            WHERE event_type = 'LLM_CALL_MADE'
              AND timestamp > :h24_ago
        """)
        row = exec_sql(session, stmt, {"h24_ago": h24_ago}).first()
        daily_cost = float(row[0]) if row else 0.0
        # Assume 2x markup for revenue
        daily_revenue = daily_cost * 2
    except Exception:
        daily_revenue = 0.0

    # MRR estimate (active tenants * $50 avg plan)
    try:
        stmt = text("""
            SELECT COUNT(DISTINCT tenant_id)
            FROM ops_events
            WHERE timestamp > :h24_ago
        """)
        row = exec_sql(session, stmt, {"h24_ago": h24_ago}).first()
        active_tenants = row[0] if row else 0
        mrr_estimate = active_tenants * 50  # $50 avg plan assumption
    except Exception:
        mrr_estimate = 0.0

    # Revenue alerts
    alerts = []
    if silent_churn > 0:
        alerts.append({
            "type": "warning",
            "message": f"{silent_churn} tenants showing silent churn (API active, no investigation)"
        })
    if critical > 0:
        alerts.append({
            "type": "critical",
            "message": f"{critical} tenants at critical risk level"
        })

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

    Database, Redis, and API capacity metrics.
    """
    warnings = []

    # Database connection check
    try:
        stmt = text("SELECT count(*) FROM pg_stat_activity WHERE state = 'active'")
        row = session.exec(stmt).first()
        db_connections = row[0] if row else 0

        stmt = text("SHOW max_connections")
        row = session.exec(stmt).first()
        db_max = int(row[0]) if row else 100
    except Exception:
        db_connections = 0
        db_max = 100

    # Database size
    try:
        stmt = text("SELECT pg_database_size(current_database()) / 1024 / 1024 / 1024.0")
        row = session.exec(stmt).first()
        db_size_gb = float(row[0]) if row else 0.0
    except Exception:
        db_size_gb = 0.0

    # API request rate (from ops_events)
    h1_ago = get_window(1)
    try:
        stmt = text("""
            SELECT COUNT(*) / 60.0
            FROM ops_events
            WHERE event_type = 'API_CALL_RECEIVED'
              AND timestamp > :h1_ago
        """)
        row = exec_sql(session, stmt, {"h1_ago": h1_ago}).first()
        rpm_avg = float(row[0]) if row else 0.0

        stmt = text("""
            SELECT MAX(cnt) FROM (
                SELECT date_trunc('minute', timestamp) as minute, COUNT(*) as cnt
                FROM ops_events
                WHERE event_type = 'API_CALL_RECEIVED'
                  AND timestamp > :h1_ago
                GROUP BY 1
            ) sub
        """)
        row = exec_sql(session, stmt, {"h1_ago": h1_ago}).first()
        rpm_peak = float(row[0]) if row else 0.0
    except Exception:
        rpm_avg = 0.0
        rpm_peak = 0.0

    # Generate warnings
    if db_connections / max(db_max, 1) > 0.8:
        warnings.append({
            "resource": "db_connections",
            "message": f"Database connections at {(db_connections/db_max)*100:.1f}%",
            "severity": "warning"
        })
    if db_size_gb > 8:  # 80% of 10GB Neon limit
        warnings.append({
            "resource": "db_storage",
            "message": f"Database storage at {db_size_gb:.1f}GB (limit: 10GB)",
            "severity": "warning"
        })

    return InfraLimits(
        db_connections_current=db_connections,
        db_connections_max=db_max,
        db_storage_used_gb=round(db_size_gb, 2),
        db_storage_limit_gb=10.0,  # Neon Pro limit
        redis_memory_used_mb=0.0,  # TODO: Redis metrics
        redis_memory_limit_mb=256.0,  # Upstash limit
        redis_keys_count=0,
        requests_per_minute_avg=round(rpm_avg, 2),
        requests_per_minute_peak=round(rpm_peak, 2),
        limit_warnings=warnings,
    )


# =============================================================================
# Module 7: Replay Lab (Event Stream)
# =============================================================================


@router.get("/events")
async def get_event_stream(
    tenant_id: Optional[str] = Query(None, description="Filter by tenant"),
    event_type: Optional[str] = Query(None, description="Filter by event type"),
    hours: int = Query(24, ge=1, le=168, description="Hours to look back"),
    limit: int = Query(100, ge=1, le=1000),
    session: Session = Depends(get_session),
):
    """
    Event Stream - Raw events for debugging and analysis.

    Use this for Replay Lab functionality.
    """
    window = get_window(hours)

    try:
        stmt = text("""
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
        """)
        rows = exec_sql(session, stmt, {
            "window": window,
            "tenant_id": tenant_id,
            "event_type": event_type,
            "limit": limit,
        }).all()

        return {
            "events": [
                {
                    "event_id": str(r[0]),
                    "timestamp": r[1].isoformat() if r[1] else None,
                    "tenant_id": str(r[2]) if r[2] else None,
                    "user_id": str(r[3]) if r[3] else None,
                    "session_id": str(r[4]) if r[4] else None,
                    "event_type": r[5],
                    "entity_type": r[6],
                    "entity_id": str(r[7]) if r[7] else None,
                    "severity": r[8],
                    "latency_ms": r[9],
                    "cost_usd": float(r[10]) if r[10] else None,
                    "metadata": r[11] or {},
                }
                for r in rows
            ],
            "total": len(rows),
            "window_hours": hours,
        }
    except Exception as e:
        return {"events": [], "total": 0, "window_hours": hours, "error": str(e)}


# =============================================================================
# Silent Churn Detection (Background Job Endpoint)
# =============================================================================


@router.post("/jobs/detect-silent-churn")
async def detect_silent_churn(
    session: Session = Depends(get_session),
):
    """
    Background job to detect silent churn.

    Silent churn = API active but investigation behavior stopped.
    Updates ops_customer_segments table.
    """
    try:
        stmt = text("""
            UPDATE ops_customer_segments
            SET
                is_silent_churn = true,
                risk_level = 'high',
                risk_reason = 'API active but no investigation in 7 days'
            WHERE tenant_id IN (
                SELECT tenant_id
                FROM ops_events
                GROUP BY tenant_id
                HAVING
                    MAX(timestamp) FILTER (WHERE event_type = 'API_CALL_RECEIVED') > now() - interval '48 hours'
                    AND
                    MAX(timestamp) FILTER (WHERE event_type IN ('INCIDENT_VIEWED', 'REPLAY_EXECUTED')) < now() - interval '7 days'
            )
        """)
        session.execute(stmt)
        session.commit()

        return {"status": "completed", "message": "Silent churn detection completed"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


# =============================================================================
# Stickiness Score Computation (Background Job)
# =============================================================================


@router.post("/jobs/compute-stickiness")
async def compute_stickiness(
    session: Session = Depends(get_session),
):
    """
    Background job to compute stickiness scores.

    Stickiness = weighted sum of (incidents * 0.2) + (replays * 0.3) + (exports * 0.5)
    With time decay: recent (7d) actions weighted 2x.
    """
    try:
        stmt = text("""
            WITH actions AS (
                SELECT
                    tenant_id,
                    -- Recent (7 days)
                    COUNT(*) FILTER (WHERE event_type = 'INCIDENT_VIEWED' AND timestamp > now() - interval '7 days') as recent_views,
                    COUNT(*) FILTER (WHERE event_type = 'REPLAY_EXECUTED' AND timestamp > now() - interval '7 days') as recent_replays,
                    COUNT(*) FILTER (WHERE event_type = 'EXPORT_GENERATED' AND timestamp > now() - interval '7 days') as recent_exports,
                    -- Older (7-30 days)
                    COUNT(*) FILTER (WHERE event_type = 'INCIDENT_VIEWED' AND timestamp <= now() - interval '7 days' AND timestamp > now() - interval '30 days') as older_views,
                    COUNT(*) FILTER (WHERE event_type = 'REPLAY_EXECUTED' AND timestamp <= now() - interval '7 days' AND timestamp > now() - interval '30 days') as older_replays,
                    COUNT(*) FILTER (WHERE event_type = 'EXPORT_GENERATED' AND timestamp <= now() - interval '7 days' AND timestamp > now() - interval '30 days') as older_exports
                FROM ops_events
                WHERE timestamp > now() - interval '30 days'
                GROUP BY tenant_id
            )
            INSERT INTO ops_customer_segments (tenant_id, current_stickiness, computed_at)
            SELECT
                tenant_id,
                ROUND(
                    (recent_views * 0.2 + older_views * 0.1) +
                    (recent_replays * 0.3 + older_replays * 0.15) +
                    (recent_exports * 0.5 + older_exports * 0.25),
                    2
                ) as stickiness,
                now()
            FROM actions
            ON CONFLICT (tenant_id) DO UPDATE SET
                current_stickiness = EXCLUDED.current_stickiness,
                peak_stickiness = GREATEST(ops_customer_segments.peak_stickiness, EXCLUDED.current_stickiness),
                stickiness_trend = CASE
                    WHEN EXCLUDED.current_stickiness > ops_customer_segments.current_stickiness * 1.1 THEN 'rising'
                    WHEN EXCLUDED.current_stickiness < ops_customer_segments.current_stickiness * 0.9 THEN 'falling'
                    ELSE 'stable'
                END,
                computed_at = now()
        """)
        session.execute(stmt)
        session.commit()

        return {"status": "completed", "message": "Stickiness computation completed"}
    except Exception as e:
        return {"status": "error", "message": str(e)}
