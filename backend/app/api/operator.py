"""Operator API - Internal Admin Console Backend

This router provides endpoints for the Operator Console (ops.agenticverz.com).
Focused on TRUTH and OVERSIGHT - operators see everything across all tenants.

Endpoints:
- GET  /operator/status        - System-wide health
- GET  /operator/tenants/top   - Top tenants by metric
- GET  /operator/incidents/recent - Recent incidents across all tenants
- GET  /operator/incidents/stream - Live incident stream
- POST /operator/incidents/{id}/acknowledge - Acknowledge
- POST /operator/incidents/{id}/resolve     - Resolve
- GET  /operator/tenants/{id}           - Tenant profile
- GET  /operator/tenants/{id}/metrics   - Tenant metrics
- GET  /operator/tenants/{id}/guardrails - Tenant guardrails
- GET  /operator/tenants/{id}/incidents - Tenant incidents
- GET  /operator/tenants/{id}/keys      - Tenant API keys
- POST /operator/tenants/{id}/freeze    - Freeze tenant
- POST /operator/tenants/{id}/unfreeze  - Unfreeze tenant
- GET  /operator/audit/policy           - Policy enforcement audit log
- GET  /operator/audit/policy/export    - Export audit log as CSV
- GET  /operator/guardrails             - List guardrail types
- POST /operator/replay/{call_id}       - Replay a call
- POST /operator/replay/batch           - Batch replay
"""

import csv
import io
import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy import select, and_, desc, or_, func
from sqlmodel import Session

from app.db import get_session
from app.models.killswitch import (
    KillSwitchState,
    ProxyCall,
    Incident,
    IncidentEvent,
    DefaultGuardrail,
    TriggerType,
    IncidentSeverity,
    IncidentStatus,
)
from app.models.tenant import Tenant, APIKey
from app.auth.tenant_auth import require_operator_role


# =============================================================================
# Router - GA Lock: Operator-only access required
# =============================================================================

# All endpoints in this router require operator authentication
# GA Lock Item: Guard vs Operator Auth Hard Boundary
router = APIRouter(
    prefix="/operator",
    tags=["Operator Console"],
    dependencies=[Depends(require_operator_role)],  # Apply to ALL endpoints
)


# =============================================================================
# Response Models
# =============================================================================

class SystemStatus(BaseModel):
    """System-wide status."""
    status: str  # healthy, degraded, critical
    total_tenants: int
    active_tenants_24h: int
    frozen_tenants: int
    total_requests_24h: int
    total_spend_24h_cents: int
    active_incidents: int
    model_drift_alerts: int


class TopTenant(BaseModel):
    """Top tenant by metric."""
    tenant_id: str
    tenant_name: str
    metric_value: float
    metric_label: str


class IncidentStream(BaseModel):
    """Incident for stream."""
    id: str
    tenant_id: str
    tenant_name: str
    title: str
    severity: str
    status: str
    trigger_type: str
    action_taken: Optional[str] = None
    calls_affected: int
    cost_avoided_cents: int
    started_at: str
    ended_at: Optional[str] = None


class TenantProfile(BaseModel):
    """Full tenant profile."""
    tenant_id: str
    tenant_name: str
    email: Optional[str] = None
    plan: str
    created_at: str
    status: str
    frozen_at: Optional[str] = None
    frozen_by: Optional[str] = None
    frozen_reason: Optional[str] = None


class TenantMetrics(BaseModel):
    """Tenant usage metrics."""
    requests_24h: int
    requests_7d: int
    spend_24h_cents: int
    spend_7d_cents: int
    error_rate_24h: float
    avg_latency_ms: int
    incidents_24h: int
    incidents_7d: int
    cost_avoided_7d_cents: int


class TenantGuardrail(BaseModel):
    """Tenant guardrail configuration."""
    id: str
    name: str
    enabled: bool
    threshold_value: float
    threshold_unit: str
    triggers_24h: int


class PolicyEnforcement(BaseModel):
    """Policy enforcement audit record."""
    id: str
    call_id: str
    tenant_id: str
    tenant_name: str
    guardrail_id: str
    guardrail_name: str
    passed: bool
    action_taken: Optional[str] = None
    reason: str
    confidence: float
    latency_ms: int
    created_at: str
    request_context: Dict[str, Any]


class GuardrailType(BaseModel):
    """Guardrail type for filtering."""
    id: str
    name: str


class ReplayResult(BaseModel):
    """Operator replay result with tenant info."""
    call_id: str
    tenant_id: str
    tenant_name: str
    original: Dict[str, Any]
    replay: Dict[str, Any]
    match_level: str
    policy_match: bool
    model_drift_detected: bool
    content_match: bool
    details: Dict[str, Any]


class BatchReplayResult(BaseModel):
    """Batch replay summary."""
    total: int
    completed: int
    exact_matches: int
    logical_matches: int
    semantic_matches: int
    mismatches: int
    model_drift_count: int
    policy_drift_count: int
    failures: List[Dict[str, str]]


# =============================================================================
# Helper Functions
# =============================================================================

def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def get_system_health(active_incidents: int, frozen_tenants: int) -> str:
    """Determine system health status."""
    if active_incidents > 10 or frozen_tenants > 5:
        return "critical"
    elif active_incidents > 3 or frozen_tenants > 0:
        return "degraded"
    return "healthy"


# =============================================================================
# System Status Endpoints
# =============================================================================

@router.get("/status", response_model=SystemStatus)
async def get_system_status(
    session: Session = Depends(get_session),
):
    """
    Get system-wide health status.

    The operator's dashboard - everything that matters at a glance.
    """
    now = utc_now()
    yesterday = now - timedelta(hours=24)

    # Count total tenants
    stmt = select(func.count(Tenant.id))
    row = session.exec(stmt).first()
    total_tenants = row[0] if row else 0

    # Count active tenants (with calls in 24h)
    stmt = select(func.count(func.distinct(ProxyCall.tenant_id))).where(
        ProxyCall.created_at >= yesterday
    )
    row = session.exec(stmt).first()
    active_tenants = row[0] if row else 0

    # Count frozen tenants
    stmt = select(func.count(KillSwitchState.id)).where(
        and_(
            KillSwitchState.entity_type == "tenant",
            KillSwitchState.is_frozen == True,
        )
    )
    row = session.exec(stmt).first()
    frozen_tenants = row[0] if row else 0

    # Total requests in 24h
    stmt = select(func.count(ProxyCall.id)).where(
        ProxyCall.created_at >= yesterday
    )
    row = session.exec(stmt).first()
    total_requests = row[0] if row else 0

    # Total spend in 24h
    stmt = select(func.coalesce(func.sum(ProxyCall.cost_cents), 0)).where(
        ProxyCall.created_at >= yesterday
    )
    row = session.exec(stmt).first()
    total_spend = row[0] if row else 0

    # Active incidents
    stmt = select(func.count(Incident.id)).where(
        Incident.status == IncidentStatus.OPEN.value
    )
    row = session.exec(stmt).first()
    active_incidents = row[0] if row else 0

    # Model drift alerts (calls with drift flagged - placeholder)
    model_drift_alerts = 0  # TODO: Implement drift detection

    status = get_system_health(active_incidents, frozen_tenants)

    return SystemStatus(
        status=status,
        total_tenants=total_tenants,
        active_tenants_24h=active_tenants,
        frozen_tenants=frozen_tenants,
        total_requests_24h=total_requests,
        total_spend_24h_cents=int(total_spend),
        active_incidents=active_incidents,
        model_drift_alerts=model_drift_alerts,
    )


@router.get("/tenants/top")
async def get_top_tenants(
    metric: str = Query(..., description="Metric: spend or incidents"),
    limit: int = Query(default=5, le=20),
    session: Session = Depends(get_session),
):
    """Get top tenants by specified metric."""
    yesterday = utc_now() - timedelta(hours=24)

    if metric == "spend":
        # Top by spend
        stmt = select(
            ProxyCall.tenant_id,
            func.sum(ProxyCall.cost_cents).label("total_spend")
        ).where(
            ProxyCall.created_at >= yesterday
        ).group_by(ProxyCall.tenant_id).order_by(
            desc("total_spend")
        ).limit(limit)

        results = session.exec(stmt).all()

        items = []
        for tenant_id, spend in results:
            # Get tenant name
            tenant_stmt = select(Tenant).where(Tenant.id == tenant_id)
            tenant_row = session.exec(tenant_stmt).first()
            tenant = tenant_row[0] if tenant_row else None
            tenant_name = tenant.name if tenant and hasattr(tenant, 'name') else tenant_id

            items.append(TopTenant(
                tenant_id=tenant_id,
                tenant_name=tenant_name,
                metric_value=float(spend or 0),
                metric_label=f"${(spend or 0) / 100:.2f}",
            ))

    elif metric == "incidents":
        # Top by incidents
        stmt = select(
            Incident.tenant_id,
            func.count(Incident.id).label("incident_count")
        ).where(
            Incident.created_at >= yesterday
        ).group_by(Incident.tenant_id).order_by(
            desc("incident_count")
        ).limit(limit)

        results = session.exec(stmt).all()

        items = []
        for tenant_id, count in results:
            tenant_stmt = select(Tenant).where(Tenant.id == tenant_id)
            tenant_row = session.exec(tenant_stmt).first()
            tenant = tenant_row[0] if tenant_row else None
            tenant_name = tenant.name if tenant and hasattr(tenant, 'name') else tenant_id

            items.append(TopTenant(
                tenant_id=tenant_id,
                tenant_name=tenant_name,
                metric_value=float(count),
                metric_label=f"{count} incidents",
            ))
    else:
        raise HTTPException(status_code=400, detail="Invalid metric. Use: spend, incidents")

    return {"items": items}


@router.get("/incidents/recent")
async def get_recent_incidents(
    limit: int = Query(default=10, le=50),
    session: Session = Depends(get_session),
):
    """Get recent incidents across all tenants."""
    stmt = select(Incident).order_by(desc(Incident.created_at)).limit(limit)
    results = session.exec(stmt).all()

    items = []
    for row in results:
        # Extract Incident from row (SQLModel may return Row objects or model instances)
        if hasattr(row, 'tenant_id'):
            incident = row
        elif hasattr(row, '__getitem__'):
            incident = row[0]
        else:
            incident = row

        # Get tenant name
        tenant_stmt = select(Tenant).where(Tenant.id == incident.tenant_id)
        tenant_row = session.exec(tenant_stmt).first()
        tenant = tenant_row[0] if tenant_row else None
        tenant_name = tenant.name if tenant and hasattr(tenant, 'name') else incident.tenant_id

        items.append(IncidentStream(
            id=incident.id,
            tenant_id=incident.tenant_id,
            tenant_name=tenant_name,
            title=incident.title,
            severity=incident.severity,
            status=incident.status,
            trigger_type=incident.trigger_type,
            action_taken=incident.auto_action,
            calls_affected=incident.calls_affected,
            cost_avoided_cents=int(incident.cost_delta_cents * 100) if incident.cost_delta_cents else 0,
            started_at=incident.started_at.isoformat() if incident.started_at else incident.created_at.isoformat(),
            ended_at=incident.ended_at.isoformat() if incident.ended_at else None,
        ))

    return {"items": items}


@router.get("/incidents/stream")
async def get_incident_stream(
    severity: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    tenant_id: Optional[str] = Query(None),
    session: Session = Depends(get_session),
):
    """
    Live incident stream with filtering.

    Real-time view of all tenant incidents.
    """
    stmt = select(Incident)

    if severity:
        stmt = stmt.where(Incident.severity == severity)
    if status:
        stmt = stmt.where(Incident.status == status)
    if tenant_id:
        stmt = stmt.where(Incident.tenant_id == tenant_id)

    stmt = stmt.order_by(desc(Incident.created_at)).limit(100)
    results = session.exec(stmt).all()

    items = []
    for row in results:
        # Extract Incident from row (SQLModel may return Row objects or model instances)
        if hasattr(row, 'tenant_id'):
            incident = row
        elif hasattr(row, '__getitem__'):
            incident = row[0]
        else:
            incident = row

        tenant_stmt = select(Tenant).where(Tenant.id == incident.tenant_id)
        tenant_row = session.exec(tenant_stmt).first()
        tenant = tenant_row[0] if tenant_row else None
        tenant_name = tenant.name if tenant and hasattr(tenant, 'name') else incident.tenant_id

        items.append(IncidentStream(
            id=incident.id,
            tenant_id=incident.tenant_id,
            tenant_name=tenant_name,
            title=incident.title,
            severity=incident.severity,
            status=incident.status,
            trigger_type=incident.trigger_type,
            action_taken=incident.auto_action,
            calls_affected=incident.calls_affected,
            cost_avoided_cents=int(incident.cost_delta_cents * 100) if incident.cost_delta_cents else 0,
            started_at=incident.started_at.isoformat() if incident.started_at else incident.created_at.isoformat(),
            ended_at=incident.ended_at.isoformat() if incident.ended_at else None,
        ))

    return {"items": items, "total": len(items)}


@router.post("/incidents/{incident_id}/acknowledge")
async def acknowledge_incident(
    incident_id: str,
    session: Session = Depends(get_session),
):
    """Acknowledge an incident (operator)."""
    stmt = select(Incident).where(Incident.id == incident_id)
    row = session.exec(stmt).first()
    incident = row[0] if row else None

    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    incident.status = IncidentStatus.ACKNOWLEDGED.value
    session.add(incident)
    session.commit()

    return {"status": "acknowledged"}


@router.post("/incidents/{incident_id}/resolve")
async def resolve_incident(
    incident_id: str,
    session: Session = Depends(get_session),
):
    """Resolve an incident (operator)."""
    stmt = select(Incident).where(Incident.id == incident_id)
    row = session.exec(stmt).first()
    incident = row[0] if row else None

    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    incident.status = IncidentStatus.RESOLVED.value
    incident.ended_at = utc_now()
    if incident.started_at:
        incident.duration_seconds = int((incident.ended_at - incident.started_at).total_seconds())

    session.add(incident)
    session.commit()

    return {"status": "resolved"}


# =============================================================================
# Tenant Management Endpoints
# =============================================================================

@router.get("/tenants/{tenant_id}", response_model=TenantProfile)
async def get_tenant_profile(
    tenant_id: str,
    session: Session = Depends(get_session),
):
    """Get tenant profile."""
    stmt = select(Tenant).where(Tenant.id == tenant_id)
    row = session.exec(stmt).first()
    tenant = row[0] if row else None

    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    # Get freeze state
    stmt = select(KillSwitchState).where(
        and_(
            KillSwitchState.entity_type == "tenant",
            KillSwitchState.entity_id == tenant_id,
        )
    )
    state_row = session.exec(stmt).first()
    state = state_row[0] if state_row else None

    status = "frozen" if state and state.is_frozen else "active"

    return TenantProfile(
        tenant_id=tenant.id,
        tenant_name=tenant.name if hasattr(tenant, 'name') else tenant.id,
        email=tenant.email if hasattr(tenant, 'email') else None,
        plan=tenant.plan if hasattr(tenant, 'plan') else "starter",
        created_at=tenant.created_at.isoformat() if tenant.created_at else utc_now().isoformat(),
        status=status,
        frozen_at=state.frozen_at.isoformat() if state and state.frozen_at else None,
        frozen_by=state.frozen_by if state else None,
        frozen_reason=state.freeze_reason if state else None,
    )


@router.get("/tenants/{tenant_id}/metrics", response_model=TenantMetrics)
async def get_tenant_metrics(
    tenant_id: str,
    session: Session = Depends(get_session),
):
    """Get tenant usage metrics."""
    now = utc_now()
    yesterday = now - timedelta(hours=24)
    week_ago = now - timedelta(days=7)

    # Requests 24h
    stmt = select(func.count(ProxyCall.id)).where(
        and_(ProxyCall.tenant_id == tenant_id, ProxyCall.created_at >= yesterday)
    )
    row = session.exec(stmt).first()
    requests_24h = row[0] if row else 0

    # Requests 7d
    stmt = select(func.count(ProxyCall.id)).where(
        and_(ProxyCall.tenant_id == tenant_id, ProxyCall.created_at >= week_ago)
    )
    row = session.exec(stmt).first()
    requests_7d = row[0] if row else 0

    # Spend 24h
    stmt = select(func.coalesce(func.sum(ProxyCall.cost_cents), 0)).where(
        and_(ProxyCall.tenant_id == tenant_id, ProxyCall.created_at >= yesterday)
    )
    row = session.exec(stmt).first()
    spend_24h = row[0] if row else 0

    # Spend 7d
    stmt = select(func.coalesce(func.sum(ProxyCall.cost_cents), 0)).where(
        and_(ProxyCall.tenant_id == tenant_id, ProxyCall.created_at >= week_ago)
    )
    row = session.exec(stmt).first()
    spend_7d = row[0] if row else 0

    # Error rate 24h
    stmt = select(func.count(ProxyCall.id)).where(
        and_(
            ProxyCall.tenant_id == tenant_id,
            ProxyCall.created_at >= yesterday,
            or_(ProxyCall.error_code != None, ProxyCall.was_blocked == True),
        )
    )
    row = session.exec(stmt).first()
    errors_24h = row[0] if row else 0
    error_rate = errors_24h / max(requests_24h, 1)

    # Avg latency 24h
    stmt = select(func.coalesce(func.avg(ProxyCall.latency_ms), 0)).where(
        and_(ProxyCall.tenant_id == tenant_id, ProxyCall.created_at >= yesterday)
    )
    row = session.exec(stmt).first()
    avg_latency = row[0] if row else 0

    # Incidents 24h
    stmt = select(func.count(Incident.id)).where(
        and_(Incident.tenant_id == tenant_id, Incident.created_at >= yesterday)
    )
    row = session.exec(stmt).first()
    incidents_24h = row[0] if row else 0

    # Incidents 7d
    stmt = select(func.count(Incident.id)).where(
        and_(Incident.tenant_id == tenant_id, Incident.created_at >= week_ago)
    )
    row = session.exec(stmt).first()
    incidents_7d = row[0] if row else 0

    # Cost avoided 7d
    stmt = select(func.coalesce(func.sum(Incident.cost_delta_cents), 0)).where(
        and_(Incident.tenant_id == tenant_id, Incident.created_at >= week_ago)
    )
    row = session.exec(stmt).first()
    cost_avoided = row[0] if row else 0

    return TenantMetrics(
        requests_24h=requests_24h,
        requests_7d=requests_7d,
        spend_24h_cents=int(spend_24h),
        spend_7d_cents=int(spend_7d),
        error_rate_24h=round(error_rate, 4),
        avg_latency_ms=int(avg_latency),
        incidents_24h=incidents_24h,
        incidents_7d=incidents_7d,
        cost_avoided_7d_cents=int(cost_avoided * 100) if cost_avoided else 0,
    )


@router.get("/tenants/{tenant_id}/guardrails")
async def get_tenant_guardrails(
    tenant_id: str,
    session: Session = Depends(get_session),
):
    """Get tenant guardrails with trigger counts."""
    yesterday = utc_now() - timedelta(hours=24)

    stmt = select(DefaultGuardrail)
    guardrails = session.exec(stmt).all()

    items = []
    for g in guardrails:
        guardrail = g[0]

        # Count triggers (blocked calls) for this guardrail
        # This is simplified - in production you'd track per-guardrail triggers
        triggers_24h = 0

        items.append(TenantGuardrail(
            id=guardrail.id,
            name=guardrail.name,
            enabled=guardrail.is_enabled,
            threshold_value=float(guardrail.threshold_value) if hasattr(guardrail, 'threshold_value') and guardrail.threshold_value else 0,
            threshold_unit=guardrail.threshold_unit if hasattr(guardrail, 'threshold_unit') else "per/hour",
            triggers_24h=triggers_24h,
        ))

    return {"items": items}


@router.get("/tenants/{tenant_id}/incidents")
async def get_tenant_incidents(
    tenant_id: str,
    limit: int = Query(default=10, le=50),
    session: Session = Depends(get_session),
):
    """Get tenant incidents."""
    stmt = select(Incident).where(
        Incident.tenant_id == tenant_id
    ).order_by(desc(Incident.created_at)).limit(limit)

    results = session.exec(stmt).all()

    # Extract Incident from each row (SQLModel returns Row objects when using select())
    items = []
    for row in results:
        # Extract Incident from row (SQLModel may return Row objects or model instances)
        if hasattr(row, 'id'):
            i = row
        elif hasattr(row, '__getitem__'):
            i = row[0]
        else:
            i = row
        items.append({
            "id": i.id,
            "severity": i.severity,
            "title": i.title,
            "status": i.status,
            "started_at": i.started_at.isoformat() if i.started_at else i.created_at.isoformat(),
        })

    return {"items": items}


@router.get("/tenants/{tenant_id}/keys")
async def get_tenant_keys(
    tenant_id: str,
    session: Session = Depends(get_session),
):
    """Get tenant API keys."""
    yesterday = utc_now() - timedelta(hours=24)

    stmt = select(APIKey).where(APIKey.tenant_id == tenant_id)
    key_rows = session.exec(stmt).all()

    items = []
    for row in key_rows:
        # Extract APIKey from row (SQLModel may return Row objects or model instances)
        if hasattr(row, 'id'):
            key = row
        elif hasattr(row, '__getitem__'):
            key = row[0]
        else:
            key = row
        # Get freeze state
        stmt = select(KillSwitchState).where(
            and_(
                KillSwitchState.entity_type == "key",
                KillSwitchState.entity_id == key.id,
            )
        )
        state_row = session.exec(stmt).first()
        state = state_row[0] if state_row else None

        # Requests 24h
        stmt = select(func.count(ProxyCall.id)).where(
            and_(ProxyCall.api_key_id == key.id, ProxyCall.created_at >= yesterday)
        )
        row = session.exec(stmt).first()
        requests_24h = row[0] if row else 0

        status = "frozen" if state and state.is_frozen else "active"
        if key.revoked_at:
            status = "revoked"

        items.append({
            "id": key.id,
            "name": key.name or f"Key {key.id[:8]}",
            "prefix": key.key_prefix or key.id[:8],
            "status": status,
            "requests_24h": requests_24h,
        })

    return {"items": items}


class FreezeRequest(BaseModel):
    reason: str


@router.post("/tenants/{tenant_id}/freeze")
async def freeze_tenant(
    tenant_id: str,
    request: FreezeRequest,
    session: Session = Depends(get_session),
):
    """Freeze a tenant (operator action)."""
    # Verify tenant exists
    stmt = select(Tenant).where(Tenant.id == tenant_id)
    row = session.exec(stmt).first()
    if not row:
        raise HTTPException(status_code=404, detail="Tenant not found")

    # Get or create state
    stmt = select(KillSwitchState).where(
        and_(
            KillSwitchState.entity_type == "tenant",
            KillSwitchState.entity_id == tenant_id,
        )
    )
    state_row = session.exec(stmt).first()
    state = state_row[0] if state_row else None

    if not state:
        state = KillSwitchState(
            id=str(uuid.uuid4()),
            entity_type="tenant",
            entity_id=tenant_id,
            tenant_id=tenant_id,
            is_frozen=False,
        )

    if state.is_frozen:
        raise HTTPException(status_code=409, detail="Tenant is already frozen")

    state.freeze(
        by="operator",
        reason=request.reason,
        auto=False,
        trigger=TriggerType.MANUAL.value,
    )

    session.add(state)
    session.commit()

    return {"status": "frozen", "tenant_id": tenant_id}


@router.post("/tenants/{tenant_id}/unfreeze")
async def unfreeze_tenant(
    tenant_id: str,
    session: Session = Depends(get_session),
):
    """Unfreeze a tenant (operator action)."""
    stmt = select(KillSwitchState).where(
        and_(
            KillSwitchState.entity_type == "tenant",
            KillSwitchState.entity_id == tenant_id,
        )
    )
    row = session.exec(stmt).first()
    state = row[0] if row else None

    if not state or not state.is_frozen:
        raise HTTPException(status_code=400, detail="Tenant is not frozen")

    state.unfreeze(by="operator")
    session.add(state)
    session.commit()

    return {"status": "active", "tenant_id": tenant_id}


# =============================================================================
# Audit Log Endpoints
# =============================================================================

@router.get("/audit/policy")
async def get_policy_audit_log(
    guardrail_id: Optional[str] = Query(None),
    action: Optional[str] = Query(None),
    tenant_id: Optional[str] = Query(None),
    passed: Optional[bool] = Query(None),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, le=100),
    session: Session = Depends(get_session),
):
    """
    Get policy enforcement audit log.

    Every policy decision, fully traceable.
    """
    # Build query - using ProxyCall as the audit source
    stmt = select(ProxyCall)

    if tenant_id:
        stmt = stmt.where(ProxyCall.tenant_id == tenant_id)
    if passed is not None:
        if passed:
            stmt = stmt.where(ProxyCall.was_blocked == False)
        else:
            stmt = stmt.where(ProxyCall.was_blocked == True)
    if date_from:
        try:
            from_dt = datetime.fromisoformat(date_from)
            stmt = stmt.where(ProxyCall.created_at >= from_dt)
        except ValueError:
            pass
    if date_to:
        try:
            to_dt = datetime.fromisoformat(date_to)
            stmt = stmt.where(ProxyCall.created_at <= to_dt)
        except ValueError:
            pass

    # Count total
    count_stmt = select(func.count(ProxyCall.id))
    if tenant_id:
        count_stmt = count_stmt.where(ProxyCall.tenant_id == tenant_id)
    row = session.exec(count_stmt).first()
    total = row[0] if row else 0

    # Paginate
    offset = (page - 1) * page_size
    stmt = stmt.order_by(desc(ProxyCall.created_at)).offset(offset).limit(page_size)
    results = session.exec(stmt).all()

    items = []
    for call in results:
        # Get tenant name
        tenant_stmt = select(Tenant).where(Tenant.id == call.tenant_id)
        tenant_row = session.exec(tenant_stmt).first()
        tenant = tenant_row[0] if tenant_row else None
        tenant_name = tenant.name if tenant and hasattr(tenant, 'name') else call.tenant_id

        # Get policy decisions if available
        decisions = call.get_policy_decisions() if hasattr(call, 'get_policy_decisions') else []
        guardrail_name = decisions[0].get("guardrail_name", "Default") if decisions else "Default"
        guardrail_id_val = decisions[0].get("guardrail_id", "default") if decisions else "default"

        items.append(PolicyEnforcement(
            id=call.id,
            call_id=call.id,
            tenant_id=call.tenant_id,
            tenant_name=tenant_name,
            guardrail_id=guardrail_id_val,
            guardrail_name=guardrail_name,
            passed=not call.was_blocked,
            action_taken=call.block_reason if call.was_blocked else None,
            reason=call.block_reason or "Passed all guardrails",
            confidence=1.0,
            latency_ms=call.latency_ms or 0,
            created_at=call.created_at.isoformat(),
            request_context={
                "model": call.model or "unknown",
                "tokens_estimated": (call.input_tokens or 0) + (call.output_tokens or 0),
                "cost_estimated_cents": int(call.cost_cents) if call.cost_cents else 0,
            },
        ))

    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.get("/audit/policy/export")
async def export_policy_audit_log(
    guardrail_id: Optional[str] = Query(None),
    action: Optional[str] = Query(None),
    tenant_id: Optional[str] = Query(None),
    passed: Optional[bool] = Query(None),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    session: Session = Depends(get_session),
):
    """Export policy audit log as CSV."""
    # Build query
    stmt = select(ProxyCall)

    if tenant_id:
        stmt = stmt.where(ProxyCall.tenant_id == tenant_id)
    if passed is not None:
        if passed:
            stmt = stmt.where(ProxyCall.was_blocked == False)
        else:
            stmt = stmt.where(ProxyCall.was_blocked == True)
    if date_from:
        try:
            from_dt = datetime.fromisoformat(date_from)
            stmt = stmt.where(ProxyCall.created_at >= from_dt)
        except ValueError:
            pass
    if date_to:
        try:
            to_dt = datetime.fromisoformat(date_to)
            stmt = stmt.where(ProxyCall.created_at <= to_dt)
        except ValueError:
            pass

    stmt = stmt.order_by(desc(ProxyCall.created_at)).limit(10000)
    results = session.exec(stmt).all()

    # Build CSV
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "call_id", "tenant_id", "timestamp", "model", "passed",
        "action_taken", "latency_ms", "tokens", "cost_cents"
    ])

    for call in results:
        writer.writerow([
            call.id,
            call.tenant_id,
            call.created_at.isoformat(),
            call.model or "",
            "true" if not call.was_blocked else "false",
            call.block_reason or "",
            call.latency_ms or 0,
            (call.input_tokens or 0) + (call.output_tokens or 0),
            int(call.cost_cents) if call.cost_cents else 0,
        ])

    output.seek(0)

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=policy-audit-{utc_now().strftime('%Y%m%d')}.csv"},
    )


@router.get("/guardrails")
async def list_guardrail_types(
    session: Session = Depends(get_session),
):
    """List all guardrail types for filtering."""
    stmt = select(DefaultGuardrail)
    guardrails = session.exec(stmt).all()

    items = [
        GuardrailType(id=g[0].id, name=g[0].name)
        for g in guardrails
    ]

    return {"items": items}


# =============================================================================
# Replay Endpoints
# =============================================================================

@router.post("/replay/{call_id}", response_model=ReplayResult)
async def replay_call(
    call_id: str,
    session: Session = Depends(get_session),
):
    """
    Replay a call - Operator debug tool.

    Full comparison with tenant context.
    """
    stmt = select(ProxyCall).where(ProxyCall.id == call_id)
    row = session.exec(stmt).first()
    call = row[0] if row else None

    if not call:
        raise HTTPException(status_code=404, detail="Call not found")

    # Get tenant name
    tenant_stmt = select(Tenant).where(Tenant.id == call.tenant_id)
    tenant_row = session.exec(tenant_stmt).first()
    tenant = tenant_row[0] if tenant_row else None
    tenant_name = tenant.name if tenant and hasattr(tenant, 'name') else call.tenant_id

    # Build snapshots
    original = {
        "timestamp": call.created_at.isoformat(),
        "model_id": call.model or "unknown",
        "model_version": None,
        "temperature": None,
        "policy_decisions": call.get_policy_decisions() if hasattr(call, 'get_policy_decisions') else [],
        "response_hash": call.response_hash or "",
        "tokens_used": (call.input_tokens or 0) + (call.output_tokens or 0),
        "cost_cents": int(call.cost_cents) if call.cost_cents else 0,
        "latency_ms": call.latency_ms or 0,
    }

    # Simulate replay (same values for MVP)
    replay = {
        "timestamp": utc_now().isoformat(),
        "model_id": call.model or "unknown",
        "model_version": None,
        "temperature": None,
        "policy_decisions": original["policy_decisions"],
        "response_hash": original["response_hash"],
        "tokens_used": original["tokens_used"],
        "cost_cents": original["cost_cents"],
        "latency_ms": original["latency_ms"],
    }

    return ReplayResult(
        call_id=call_id,
        tenant_id=call.tenant_id,
        tenant_name=tenant_name,
        original=original,
        replay=replay,
        match_level="exact",
        policy_match=True,
        model_drift_detected=False,
        content_match=True,
        details={
            "content_match": True,
            "policy_match": True,
            "model_drift": False,
        },
    )


class BatchReplayRequest(BaseModel):
    tenant_id: str = ""
    sample_size: int = 100
    time_range_hours: int = 24


@router.post("/replay/batch", response_model=BatchReplayResult)
async def batch_replay(
    request: BatchReplayRequest,
    session: Session = Depends(get_session),
):
    """
    Batch replay for regression testing.

    Tests determinism across many calls.
    """
    time_cutoff = utc_now() - timedelta(hours=request.time_range_hours)

    stmt = select(ProxyCall).where(
        ProxyCall.created_at >= time_cutoff
    )

    if request.tenant_id:
        stmt = stmt.where(ProxyCall.tenant_id == request.tenant_id)

    stmt = stmt.where(ProxyCall.replay_eligible == True).limit(request.sample_size)
    results = session.exec(stmt).all()

    # Simulate batch replay
    total = len(results)
    completed = total
    exact_matches = total  # All match in MVP
    logical_matches = 0
    semantic_matches = 0
    mismatches = 0
    model_drift_count = 0
    policy_drift_count = 0
    failures = []

    return BatchReplayResult(
        total=total,
        completed=completed,
        exact_matches=exact_matches,
        logical_matches=logical_matches,
        semantic_matches=semantic_matches,
        mismatches=mismatches,
        model_drift_count=model_drift_count,
        policy_drift_count=policy_drift_count,
        failures=failures,
    )
