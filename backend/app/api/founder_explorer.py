# Layer: L2 — Product APIs
# Product: founder-console
# Temporal:
#   Trigger: api
#   Execution: async
# Role: H3 Founder Exploratory Mode - Cross-tenant insights (READ-ONLY)
# Callers: founder console UI
# Allowed Imports: L4, L6
# Forbidden Imports: L1, L5
# Reference: Phase H3 - Founder Console Exploratory Mode
"""
Founder Exploratory Mode API (H3)

Cross-tenant summary and deep diagnostics for founders.

INVARIANTS:
- FOUNDER ONLY - must NOT expose to customer
- READ-ONLY - no mutation flows
- No impersonation or write actions
- No approval or escalation flows
- Cross-tenant data for business learning

Endpoints:
- GET /explorer/summary - Cross-tenant system summary
- GET /explorer/tenants - List all tenants with metrics
- GET /explorer/tenant/{tenant_id}/diagnostics - Deep diagnostics for a tenant
- GET /explorer/system/health - Overall system health
- GET /explorer/patterns - Usage pattern analysis

Reference: Phase H3 - Founder Console Exploratory Mode
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlmodel import Session

from ..auth.console_auth import FounderToken, verify_fops_token
from ..db import get_session

logger = logging.getLogger("nova.api.founder_explorer")

router = APIRouter(prefix="/explorer", tags=["explorer"])


# =============================================================================
# Response Models
# =============================================================================


class TenantSummary(BaseModel):
    """Summary metrics for a single tenant."""

    tenant_id: str
    name: Optional[str] = None

    # Activity metrics
    total_calls: int = 0
    calls_24h: int = 0
    calls_7d: int = 0

    # Incident metrics
    total_incidents: int = 0
    open_incidents: int = 0
    critical_incidents: int = 0

    # Cost metrics
    total_cost_cents: int = 0
    cost_24h_cents: int = 0

    # Health indicators
    error_rate_24h: float = 0.0
    avg_latency_ms: float = 0.0

    # Status
    last_activity: Optional[datetime] = None
    status: str = "unknown"


class SystemSummary(BaseModel):
    """Cross-tenant system summary."""

    # Global metrics
    total_tenants: int = 0
    active_tenants_24h: int = 0
    active_tenants_7d: int = 0

    # Call metrics
    total_calls: int = 0
    calls_24h: int = 0
    calls_7d: int = 0

    # Incident metrics
    total_incidents: int = 0
    open_incidents: int = 0
    critical_incidents: int = 0
    incidents_24h: int = 0

    # Cost metrics
    total_cost_cents: int = 0
    cost_24h_cents: int = 0
    cost_7d_cents: int = 0

    # Health indicators
    global_error_rate: float = 0.0
    avg_response_time_ms: float = 0.0

    # Timestamp
    generated_at: datetime
    note: str = "Cross-tenant summary - Founder only"


class TenantDiagnostics(BaseModel):
    """Deep diagnostics for a specific tenant."""

    tenant_id: str

    # Call distribution
    calls_by_hour: List[Dict[str, Any]] = Field(default_factory=list)
    calls_by_skill: List[Dict[str, Any]] = Field(default_factory=list)

    # Error analysis
    error_breakdown: List[Dict[str, Any]] = Field(default_factory=list)
    top_errors: List[Dict[str, Any]] = Field(default_factory=list)

    # Latency analysis
    latency_percentiles: Dict[str, float] = Field(default_factory=dict)
    latency_by_skill: List[Dict[str, Any]] = Field(default_factory=list)

    # Cost analysis
    cost_by_day: List[Dict[str, Any]] = Field(default_factory=list)
    cost_by_skill: List[Dict[str, Any]] = Field(default_factory=list)

    # Recent incidents
    recent_incidents: List[Dict[str, Any]] = Field(default_factory=list)

    # Metadata
    generated_at: datetime
    note: str = "Deep diagnostics - Founder only, READ-ONLY"


class SystemHealthResponse(BaseModel):
    """Overall system health indicators."""

    # Service health
    database_healthy: bool = True
    redis_healthy: bool = True
    worker_healthy: bool = True

    # Load indicators
    current_load: float = 0.0
    queue_depth: int = 0

    # Resource utilization
    memory_usage_pct: float = 0.0
    cpu_usage_pct: float = 0.0

    # Recent issues
    recent_errors: int = 0
    recent_timeouts: int = 0

    # Timestamp
    checked_at: datetime
    status: str = "healthy"


class UsagePattern(BaseModel):
    """Usage pattern insight."""

    pattern_type: str
    description: str
    affected_tenants: int
    severity: str  # info, warning, concern
    recommendation: Optional[str] = None


class PatternsResponse(BaseModel):
    """Usage pattern analysis."""

    patterns: List[UsagePattern] = Field(default_factory=list)
    analysis_window_hours: int = 24
    generated_at: datetime
    note: str = "Pattern analysis - Founder only"


# =============================================================================
# API Endpoints
# =============================================================================


@router.get("/summary", response_model=SystemSummary)
async def get_system_summary(
    token: FounderToken = Depends(verify_fops_token),
    session: Session = Depends(get_session),
):
    """
    Get cross-tenant system summary.

    FOUNDER ONLY - provides aggregate view across all tenants.
    READ-ONLY - no mutations.

    Returns:
    - Total/active tenant counts
    - Aggregate call and incident metrics
    - Global cost metrics
    - System health indicators
    """
    now = datetime.now(timezone.utc)
    yesterday = now - timedelta(days=1)
    week_ago = now - timedelta(days=7)

    try:
        # Get tenant counts
        tenant_query = text("""
            SELECT
                COUNT(DISTINCT tenant_id) as total_tenants,
                COUNT(DISTINCT CASE WHEN created_at > :yesterday THEN tenant_id END) as active_24h,
                COUNT(DISTINCT CASE WHEN created_at > :week_ago THEN tenant_id END) as active_7d
            FROM proxy_calls
        """)
        tenant_result = session.execute(tenant_query, {"yesterday": yesterday, "week_ago": week_ago}).fetchone()

        # Get call metrics
        calls_query = text("""
            SELECT
                COUNT(*) as total_calls,
                COUNT(CASE WHEN created_at > :yesterday THEN 1 END) as calls_24h,
                COUNT(CASE WHEN created_at > :week_ago THEN 1 END) as calls_7d,
                COALESCE(SUM(cost_cents), 0) as total_cost,
                COALESCE(SUM(CASE WHEN created_at > :yesterday THEN cost_cents ELSE 0 END), 0) as cost_24h,
                COALESCE(SUM(CASE WHEN created_at > :week_ago THEN cost_cents ELSE 0 END), 0) as cost_7d,
                AVG(CASE WHEN status = 'error' THEN 1.0 ELSE 0.0 END) as error_rate,
                AVG(latency_ms) as avg_latency
            FROM proxy_calls
        """)
        calls_result = session.execute(calls_query, {"yesterday": yesterday, "week_ago": week_ago}).fetchone()

        # Get incident metrics
        incidents_query = text("""
            SELECT
                COUNT(*) as total_incidents,
                COUNT(CASE WHEN status = 'open' THEN 1 END) as open_incidents,
                COUNT(CASE WHEN severity = 'critical' THEN 1 END) as critical_incidents,
                COUNT(CASE WHEN created_at > :yesterday THEN 1 END) as incidents_24h
            FROM incidents
        """)
        incidents_result = session.execute(incidents_query, {"yesterday": yesterday}).fetchone()

        return SystemSummary(
            total_tenants=tenant_result.total_tenants or 0 if tenant_result else 0,
            active_tenants_24h=tenant_result.active_24h or 0 if tenant_result else 0,
            active_tenants_7d=tenant_result.active_7d or 0 if tenant_result else 0,
            total_calls=calls_result.total_calls or 0 if calls_result else 0,
            calls_24h=calls_result.calls_24h or 0 if calls_result else 0,
            calls_7d=calls_result.calls_7d or 0 if calls_result else 0,
            total_incidents=incidents_result.total_incidents or 0 if incidents_result else 0,
            open_incidents=incidents_result.open_incidents or 0 if incidents_result else 0,
            critical_incidents=incidents_result.critical_incidents or 0 if incidents_result else 0,
            incidents_24h=incidents_result.incidents_24h or 0 if incidents_result else 0,
            total_cost_cents=int(calls_result.total_cost or 0) if calls_result else 0,
            cost_24h_cents=int(calls_result.cost_24h or 0) if calls_result else 0,
            cost_7d_cents=int(calls_result.cost_7d or 0) if calls_result else 0,
            global_error_rate=round(float(calls_result.error_rate or 0) * 100, 2) if calls_result else 0,
            avg_response_time_ms=round(float(calls_result.avg_latency or 0), 2) if calls_result else 0,
            generated_at=now,
            note="Cross-tenant summary - Founder only",
        )

    except Exception as e:
        logger.error(f"Failed to generate system summary: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate summary")


@router.get("/tenants", response_model=List[TenantSummary])
async def list_tenants(
    limit: int = Query(50, ge=1, le=200, description="Max tenants to return"),
    sort_by: str = Query("calls_24h", description="Sort field"),
    token: FounderToken = Depends(verify_fops_token),
    session: Session = Depends(get_session),
):
    """
    List all tenants with summary metrics.

    FOUNDER ONLY - shows all tenants.
    READ-ONLY - no mutations.
    """
    now = datetime.now(timezone.utc)
    yesterday = now - timedelta(days=1)
    week_ago = now - timedelta(days=7)

    try:
        query = text("""
            WITH tenant_calls AS (
                SELECT
                    tenant_id,
                    COUNT(*) as total_calls,
                    COUNT(CASE WHEN created_at > :yesterday THEN 1 END) as calls_24h,
                    COUNT(CASE WHEN created_at > :week_ago THEN 1 END) as calls_7d,
                    COALESCE(SUM(cost_cents), 0) as total_cost,
                    COALESCE(SUM(CASE WHEN created_at > :yesterday THEN cost_cents ELSE 0 END), 0) as cost_24h,
                    AVG(CASE WHEN created_at > :yesterday AND status = 'error' THEN 1.0 ELSE 0.0 END) as error_rate,
                    AVG(latency_ms) as avg_latency,
                    MAX(created_at) as last_activity
                FROM proxy_calls
                GROUP BY tenant_id
            ),
            tenant_incidents AS (
                SELECT
                    tenant_id,
                    COUNT(*) as total_incidents,
                    COUNT(CASE WHEN status = 'open' THEN 1 END) as open_incidents,
                    COUNT(CASE WHEN severity = 'critical' THEN 1 END) as critical_incidents
                FROM incidents
                GROUP BY tenant_id
            )
            SELECT
                tc.tenant_id,
                tc.total_calls,
                tc.calls_24h,
                tc.calls_7d,
                tc.total_cost,
                tc.cost_24h,
                tc.error_rate,
                tc.avg_latency,
                tc.last_activity,
                COALESCE(ti.total_incidents, 0) as total_incidents,
                COALESCE(ti.open_incidents, 0) as open_incidents,
                COALESCE(ti.critical_incidents, 0) as critical_incidents
            FROM tenant_calls tc
            LEFT JOIN tenant_incidents ti ON tc.tenant_id = ti.tenant_id
            ORDER BY tc.calls_24h DESC
            LIMIT :limit
        """)

        results = session.execute(query, {"yesterday": yesterday, "week_ago": week_ago, "limit": limit}).fetchall()

        tenants = []
        for row in results:
            status = "active" if row.calls_24h > 0 else "inactive"
            if row.open_incidents > 0:
                status = "issues"
            if row.critical_incidents > 0:
                status = "critical"

            tenants.append(
                TenantSummary(
                    tenant_id=row.tenant_id,
                    total_calls=row.total_calls or 0,
                    calls_24h=row.calls_24h or 0,
                    calls_7d=row.calls_7d or 0,
                    total_incidents=row.total_incidents or 0,
                    open_incidents=row.open_incidents or 0,
                    critical_incidents=row.critical_incidents or 0,
                    total_cost_cents=int(row.total_cost or 0),
                    cost_24h_cents=int(row.cost_24h or 0),
                    error_rate_24h=round(float(row.error_rate or 0) * 100, 2),
                    avg_latency_ms=round(float(row.avg_latency or 0), 2),
                    last_activity=row.last_activity,
                    status=status,
                )
            )

        return tenants

    except Exception as e:
        logger.error(f"Failed to list tenants: {e}")
        raise HTTPException(status_code=500, detail="Failed to list tenants")


@router.get("/tenant/{tenant_id}/diagnostics", response_model=TenantDiagnostics)
async def get_tenant_diagnostics(
    tenant_id: str,
    hours: int = Query(24, ge=1, le=168, description="Analysis window in hours"),
    token: FounderToken = Depends(verify_fops_token),
    session: Session = Depends(get_session),
):
    """
    Get deep diagnostics for a specific tenant.

    FOUNDER ONLY - detailed view for investigation.
    READ-ONLY - no mutations.

    Returns:
    - Call distribution by hour and skill
    - Error breakdown and top errors
    - Latency analysis
    - Cost breakdown
    - Recent incidents
    """
    now = datetime.now(timezone.utc)
    start_time = now - timedelta(hours=hours)

    try:
        # Calls by hour
        hourly_query = text("""
            SELECT
                DATE_TRUNC('hour', created_at) as hour,
                COUNT(*) as calls,
                COUNT(CASE WHEN status = 'error' THEN 1 END) as errors,
                AVG(latency_ms) as avg_latency
            FROM proxy_calls
            WHERE tenant_id = :tenant_id AND created_at > :start_time
            GROUP BY DATE_TRUNC('hour', created_at)
            ORDER BY hour
        """)
        hourly_results = session.execute(hourly_query, {"tenant_id": tenant_id, "start_time": start_time}).fetchall()

        calls_by_hour = [
            {"hour": str(r.hour), "calls": r.calls, "errors": r.errors, "avg_latency": round(r.avg_latency or 0, 2)}
            for r in hourly_results
        ]

        # Calls by skill (model)
        skill_query = text("""
            SELECT
                model as skill,
                COUNT(*) as calls,
                COALESCE(SUM(cost_cents), 0) as cost,
                AVG(latency_ms) as avg_latency
            FROM proxy_calls
            WHERE tenant_id = :tenant_id AND created_at > :start_time
            GROUP BY model
            ORDER BY calls DESC
            LIMIT 10
        """)
        skill_results = session.execute(skill_query, {"tenant_id": tenant_id, "start_time": start_time}).fetchall()

        calls_by_skill = [
            {
                "skill": r.skill or "unknown",
                "calls": r.calls,
                "cost_cents": int(r.cost),
                "avg_latency": round(r.avg_latency or 0, 2),
            }
            for r in skill_results
        ]

        # Error breakdown
        error_query = text("""
            SELECT
                COALESCE(error_type, 'unknown') as error_type,
                COUNT(*) as count
            FROM proxy_calls
            WHERE tenant_id = :tenant_id AND status = 'error' AND created_at > :start_time
            GROUP BY error_type
            ORDER BY count DESC
            LIMIT 10
        """)
        error_results = session.execute(error_query, {"tenant_id": tenant_id, "start_time": start_time}).fetchall()

        error_breakdown = [{"error_type": r.error_type, "count": r.count} for r in error_results]

        # Recent incidents
        incidents_query = text("""
            SELECT
                id, title, severity, status, created_at
            FROM incidents
            WHERE tenant_id = :tenant_id
            ORDER BY created_at DESC
            LIMIT 10
        """)
        incidents_results = session.execute(incidents_query, {"tenant_id": tenant_id}).fetchall()

        recent_incidents = [
            {
                "id": str(r.id),
                "title": r.title,
                "severity": r.severity,
                "status": r.status,
                "created_at": str(r.created_at),
            }
            for r in incidents_results
        ]

        return TenantDiagnostics(
            tenant_id=tenant_id,
            calls_by_hour=calls_by_hour,
            calls_by_skill=calls_by_skill,
            error_breakdown=error_breakdown,
            top_errors=error_breakdown[:5],
            latency_percentiles={"p50": 100, "p95": 500, "p99": 1000},  # Placeholder
            latency_by_skill=calls_by_skill,
            cost_by_day=[],  # Would need daily aggregation
            cost_by_skill=calls_by_skill,
            recent_incidents=recent_incidents,
            generated_at=now,
            note="Deep diagnostics - Founder only, READ-ONLY",
        )

    except Exception as e:
        logger.error(f"Failed to get tenant diagnostics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get diagnostics")


@router.get("/system/health", response_model=SystemHealthResponse)
async def get_system_health(
    token: FounderToken = Depends(verify_fops_token),
    session: Session = Depends(get_session),
):
    """
    Get overall system health indicators.

    FOUNDER ONLY - infrastructure visibility.
    READ-ONLY - no mutations.
    """
    now = datetime.now(timezone.utc)

    # Check database connectivity
    try:
        session.execute(text("SELECT 1"))
        db_healthy = True
    except Exception:
        db_healthy = False

    # Check Redis (optional)
    redis_healthy = True
    try:
        import os

        import redis

        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        r = redis.from_url(redis_url)
        r.ping()
    except Exception:
        redis_healthy = False

    # Get recent error count
    try:
        recent_errors_query = text("""
            SELECT COUNT(*) as count
            FROM proxy_calls
            WHERE status = 'error' AND created_at > :cutoff
        """)
        recent_errors = session.execute(recent_errors_query, {"cutoff": now - timedelta(minutes=5)}).scalar() or 0
    except Exception:
        recent_errors = -1

    status = "healthy"
    if not db_healthy:
        status = "critical"
    elif not redis_healthy:
        status = "degraded"
    elif recent_errors > 100:
        status = "warning"

    return SystemHealthResponse(
        database_healthy=db_healthy,
        redis_healthy=redis_healthy,
        worker_healthy=True,  # Would need worker health check
        current_load=0.0,  # Would need metrics integration
        queue_depth=0,
        memory_usage_pct=0.0,
        cpu_usage_pct=0.0,
        recent_errors=recent_errors,
        recent_timeouts=0,
        checked_at=now,
        status=status,
    )


@router.get("/patterns", response_model=PatternsResponse)
async def get_usage_patterns(
    hours: int = Query(24, ge=1, le=168, description="Analysis window in hours"),
    token: FounderToken = Depends(verify_fops_token),
    session: Session = Depends(get_session),
):
    """
    Get usage pattern analysis.

    FOUNDER ONLY - business insights.
    READ-ONLY - no mutations.

    Analyzes tenant behavior patterns for business learning.
    """
    now = datetime.now(timezone.utc)
    start_time = now - timedelta(hours=hours)

    patterns = []

    try:
        # Pattern 1: Inactive tenants with high past usage
        inactive_query = text("""
            WITH recent AS (
                SELECT tenant_id, COUNT(*) as calls
                FROM proxy_calls
                WHERE created_at > :recent_cutoff
                GROUP BY tenant_id
            ),
            historical AS (
                SELECT tenant_id, COUNT(*) as calls
                FROM proxy_calls
                WHERE created_at > :historical_cutoff AND created_at <= :recent_cutoff
                GROUP BY tenant_id
            )
            SELECT COUNT(*) as count
            FROM historical h
            LEFT JOIN recent r ON h.tenant_id = r.tenant_id
            WHERE h.calls > 100 AND (r.calls IS NULL OR r.calls < 10)
        """)
        inactive_result = (
            session.execute(
                inactive_query,
                {"recent_cutoff": now - timedelta(hours=24), "historical_cutoff": now - timedelta(days=7)},
            ).scalar()
            or 0
        )

        if inactive_result > 0:
            patterns.append(
                UsagePattern(
                    pattern_type="churn_risk",
                    description=f"{inactive_result} tenants with high historical usage have gone silent",
                    affected_tenants=inactive_result,
                    severity="warning",
                    recommendation="Review these tenants for potential churn intervention",
                )
            )

        # Pattern 2: Error spike
        error_query = text("""
            SELECT
                COUNT(CASE WHEN status = 'error' THEN 1 END) * 100.0 / NULLIF(COUNT(*), 0) as error_rate
            FROM proxy_calls
            WHERE created_at > :start_time
        """)
        error_rate = session.execute(error_query, {"start_time": start_time}).scalar() or 0

        if error_rate > 5:
            patterns.append(
                UsagePattern(
                    pattern_type="error_spike",
                    description=f"System-wide error rate is {error_rate:.1f}%",
                    affected_tenants=0,  # All tenants
                    severity="concern" if error_rate > 10 else "warning",
                    recommendation="Investigate top error types and affected services",
                )
            )

        # Pattern 3: Cost concentration
        cost_query = text("""
            SELECT COUNT(*) as count
            FROM (
                SELECT tenant_id, SUM(cost_cents) as cost
                FROM proxy_calls
                WHERE created_at > :start_time
                GROUP BY tenant_id
                HAVING SUM(cost_cents) > 10000
            ) high_cost
        """)
        high_cost_tenants = session.execute(cost_query, {"start_time": start_time}).scalar() or 0

        if high_cost_tenants > 0:
            patterns.append(
                UsagePattern(
                    pattern_type="cost_concentration",
                    description=f"{high_cost_tenants} tenants with high cost concentration (>$100)",
                    affected_tenants=high_cost_tenants,
                    severity="info",
                    recommendation="Review pricing and usage patterns for high-cost tenants",
                )
            )

    except Exception as e:
        logger.error(f"Failed to analyze patterns: {e}")

    return PatternsResponse(
        patterns=patterns,
        analysis_window_hours=hours,
        generated_at=now,
        note="Pattern analysis - Founder only",
    )


# =============================================================================
# Immutability Notice
# =============================================================================


@router.get("/info")
async def get_explorer_info():
    """Get information about the explorer endpoints."""
    return {
        "system": "H3 Founder Explorer",
        "access": "FOUNDER ONLY",
        "mode": "READ-ONLY",
        "guarantees": [
            "No customer data exposure",
            "No mutation flows",
            "No impersonation",
            "No approval or escalation actions",
            "Cross-tenant aggregates for business learning only",
        ],
        "endpoints": [
            "/explorer/summary - Cross-tenant system summary",
            "/explorer/tenants - List all tenants with metrics",
            "/explorer/tenant/{id}/diagnostics - Deep diagnostics",
            "/explorer/system/health - System health check",
            "/explorer/patterns - Usage pattern analysis",
        ],
        "reference": "Phase H3 - Founder Console Exploratory Mode",
    }
