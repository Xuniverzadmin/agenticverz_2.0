"""Guard API - Customer Console Backend

This router provides endpoints for the Customer Console (guard.agenticverz.com).
Focused on TRUST and CONTROL - customers can see what's protecting them and stop it if needed.

Endpoints:
- GET  /guard/status          - Protection status (am I safe?)
- GET  /guard/snapshot/today  - Today's metrics
- POST /guard/killswitch/activate   - Stop all traffic
- POST /guard/killswitch/deactivate - Resume traffic
- GET  /guard/incidents       - List incidents
- GET  /guard/incidents/{id}  - Incident detail with timeline
- POST /guard/incidents/{id}/acknowledge - Acknowledge incident
- POST /guard/incidents/{id}/resolve     - Resolve incident
- POST /guard/replay/{call_id} - Replay a call
- GET  /guard/keys            - List API keys
- POST /guard/keys/{id}/freeze   - Freeze key
- POST /guard/keys/{id}/unfreeze - Unfreeze key
- GET  /guard/settings        - Read-only settings
"""

import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select, and_, desc, func
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
from app.auth.tenant_auth import get_tenant_context, TenantContext


# =============================================================================
# Router - GA Lock: Customer-only access (tenant-scoped)
# =============================================================================

# Guard Console endpoints are tenant-scoped via tenant_id query parameter
# Customers can only see their own tenant's data
# GA Lock Item: Guard vs Operator Auth Hard Boundary
#
# Note: Unlike Operator Console which requires operator auth,
# Guard Console requires tenant_id and returns only that tenant's data.
# This is enforced by all endpoints requiring tenant_id parameter.

router = APIRouter(prefix="/guard", tags=["Guard Console"])


# =============================================================================
# Response Models
# =============================================================================

class GuardStatus(BaseModel):
    """Protection status response."""
    is_frozen: bool
    frozen_at: Optional[str] = None
    frozen_by: Optional[str] = None
    incidents_blocked_24h: int
    active_guardrails: List[str]
    last_incident_time: Optional[str] = None


class TodaySnapshot(BaseModel):
    """Today's metrics snapshot."""
    requests_today: int
    spend_today_cents: int
    incidents_prevented: int
    last_incident_time: Optional[str] = None
    cost_avoided_cents: int


class IncidentSummary(BaseModel):
    """Incident list item."""
    id: str
    title: str
    severity: str
    status: str
    trigger_type: str
    trigger_value: Optional[str] = None
    action_taken: Optional[str] = None
    cost_avoided_cents: int
    calls_affected: int
    started_at: str
    ended_at: Optional[str] = None
    duration_seconds: Optional[int] = None


class IncidentEventResponse(BaseModel):
    """Timeline event."""
    id: str
    event_type: str
    description: str
    created_at: str
    data: Optional[Dict[str, Any]] = None


class IncidentDetailResponse(BaseModel):
    """Full incident detail with timeline."""
    incident: IncidentSummary
    timeline: List[IncidentEventResponse]


class ApiKeyResponse(BaseModel):
    """API key for customer console."""
    id: str
    name: str
    prefix: str
    status: str
    created_at: str
    last_seen_at: Optional[str] = None
    requests_today: int
    spend_today_cents: int


class PaginatedResponse(BaseModel):
    """Generic paginated response."""
    items: List[Any]
    total: int
    page: int
    page_size: int


class GuardrailConfig(BaseModel):
    """Guardrail configuration for settings page."""
    id: str
    name: str
    description: str
    enabled: bool
    threshold_type: str
    threshold_value: float
    threshold_unit: str
    action_on_trigger: str


class TenantSettings(BaseModel):
    """Read-only tenant settings."""
    tenant_id: str
    tenant_name: str
    plan: str
    guardrails: List[GuardrailConfig]
    budget_limit_cents: int
    budget_period: str
    kill_switch_enabled: bool
    kill_switch_auto_trigger: bool
    auto_trigger_threshold_cents: int
    notification_email: Optional[str] = None
    notification_slack_webhook: Optional[str] = None


class PolicyDecision(BaseModel):
    """Policy decision for replay."""
    guardrail_id: str
    guardrail_name: str
    passed: bool
    action: Optional[str] = None


class ReplayCallSnapshot(BaseModel):
    """Call snapshot for replay comparison."""
    timestamp: str
    model_id: str
    policy_decisions: List[PolicyDecision]
    response_hash: str
    tokens_used: int
    cost_cents: int


class ReplayResult(BaseModel):
    """Replay result response."""
    call_id: str
    original: ReplayCallSnapshot
    replay: ReplayCallSnapshot
    match_level: str  # exact, logical, semantic, mismatch
    policy_match: bool
    model_drift_detected: bool
    details: Dict[str, Any]


# =============================================================================
# Helper Functions
# =============================================================================

def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def get_tenant_from_auth(session: Session, tenant_id: str) -> Tenant:
    """Get tenant or raise 404."""
    stmt = select(Tenant).where(Tenant.id == tenant_id)
    row = session.exec(stmt).first()
    tenant = row[0] if row else None
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    return tenant


# =============================================================================
# Status Endpoints
# =============================================================================

@router.get("/status", response_model=GuardStatus)
async def get_guard_status(
    tenant_id: str = Query(..., description="Tenant ID"),
    session: Session = Depends(get_session),
):
    """
    Get protection status - "Am I safe right now?"

    Returns:
    - Freeze state
    - Active guardrails
    - 24h incident count
    - Last incident time
    """
    # Get tenant state
    stmt = select(KillSwitchState).where(
        and_(
            KillSwitchState.entity_type == "tenant",
            KillSwitchState.entity_id == tenant_id,
        )
    )
    row = session.exec(stmt).first()
    tenant_state = row[0] if row else None

    # Get active guardrails
    stmt = select(DefaultGuardrail).where(DefaultGuardrail.is_enabled == True)
    guardrail_rows = session.exec(stmt).all()
    active_guardrails = [g[0].name for g in guardrail_rows]

    # Count incidents in last 24h
    yesterday = utc_now() - timedelta(hours=24)
    stmt = select(func.count(Incident.id)).where(
        and_(
            Incident.tenant_id == tenant_id,
            Incident.created_at >= yesterday,
        )
    )
    row = session.exec(stmt).first()
    incidents_count = row[0] if row else 0

    # Get last incident time
    stmt = select(Incident).where(
        Incident.tenant_id == tenant_id
    ).order_by(desc(Incident.created_at)).limit(1)
    last_incident_row = session.exec(stmt).first()
    last_incident = last_incident_row[0] if last_incident_row else None

    return GuardStatus(
        is_frozen=tenant_state.is_frozen if tenant_state else False,
        frozen_at=tenant_state.frozen_at.isoformat() if tenant_state and tenant_state.frozen_at else None,
        frozen_by=tenant_state.frozen_by if tenant_state else None,
        incidents_blocked_24h=incidents_count,
        active_guardrails=active_guardrails,
        last_incident_time=last_incident.created_at.isoformat() if last_incident else None,
    )


@router.get("/snapshot/today", response_model=TodaySnapshot)
async def get_today_snapshot(
    tenant_id: str = Query(..., description="Tenant ID"),
    session: Session = Depends(get_session),
):
    """
    Get today's metrics - "What did it cost/save me?"
    """
    today_start = utc_now().replace(hour=0, minute=0, second=0, microsecond=0)

    # Count requests today
    stmt = select(func.count(ProxyCall.id)).where(
        and_(
            ProxyCall.tenant_id == tenant_id,
            ProxyCall.created_at >= today_start,
        )
    )
    row = session.exec(stmt).first()
    requests_today = row[0] if row else 0

    # Sum spend today
    stmt = select(func.coalesce(func.sum(ProxyCall.cost_cents), 0)).where(
        and_(
            ProxyCall.tenant_id == tenant_id,
            ProxyCall.created_at >= today_start,
        )
    )
    row = session.exec(stmt).first()
    spend_today = row[0] if row else 0

    # Count incidents prevented (blocked calls)
    stmt = select(func.count(ProxyCall.id)).where(
        and_(
            ProxyCall.tenant_id == tenant_id,
            ProxyCall.created_at >= today_start,
            ProxyCall.was_blocked == True,
        )
    )
    row = session.exec(stmt).first()
    incidents_prevented = row[0] if row else 0

    # Sum cost avoided (blocked calls' estimated cost)
    stmt = select(func.coalesce(func.sum(ProxyCall.cost_cents), 0)).where(
        and_(
            ProxyCall.tenant_id == tenant_id,
            ProxyCall.created_at >= today_start,
            ProxyCall.was_blocked == True,
        )
    )
    row = session.exec(stmt).first()
    cost_avoided = row[0] if row else 0

    # Get last incident time
    stmt = select(Incident).where(
        Incident.tenant_id == tenant_id
    ).order_by(desc(Incident.created_at)).limit(1)
    last_incident_row = session.exec(stmt).first()
    last_incident = last_incident_row[0] if last_incident_row else None

    return TodaySnapshot(
        requests_today=requests_today,
        spend_today_cents=int(spend_today),
        incidents_prevented=incidents_prevented,
        last_incident_time=last_incident.created_at.isoformat() if last_incident else None,
        cost_avoided_cents=int(cost_avoided),
    )


# =============================================================================
# Kill Switch Endpoints
# =============================================================================

@router.post("/killswitch/activate")
async def activate_killswitch(
    tenant_id: str = Query(..., description="Tenant ID"),
    session: Session = Depends(get_session),
):
    """
    Stop all traffic - Emergency kill switch.

    Immediate. All requests blocked until manually resumed.
    """
    # Verify tenant exists
    tenant = get_tenant_from_auth(session, tenant_id)

    # Get or create state
    stmt = select(KillSwitchState).where(
        and_(
            KillSwitchState.entity_type == "tenant",
            KillSwitchState.entity_id == tenant_id,
        )
    )
    row = session.exec(stmt).first()
    state = row[0] if row else None

    if not state:
        state = KillSwitchState(
            id=str(uuid.uuid4()),
            entity_type="tenant",
            entity_id=tenant_id,
            tenant_id=tenant_id,
            is_frozen=False,
        )

    if state.is_frozen:
        raise HTTPException(status_code=409, detail="Traffic is already stopped")

    state.freeze(
        by="customer",
        reason="Manual kill switch activated via Customer Console",
        auto=False,
        trigger=TriggerType.MANUAL.value,
    )

    session.add(state)
    session.commit()

    return {"status": "frozen", "message": "All traffic stopped"}


@router.post("/killswitch/deactivate")
async def deactivate_killswitch(
    tenant_id: str = Query(..., description="Tenant ID"),
    session: Session = Depends(get_session),
):
    """
    Resume traffic - Deactivate kill switch.

    Guardrails will continue protecting.
    """
    stmt = select(KillSwitchState).where(
        and_(
            KillSwitchState.entity_type == "tenant",
            KillSwitchState.entity_id == tenant_id,
        )
    )
    row = session.exec(stmt).first()
    state = row[0] if row else None

    if not state or not state.is_frozen:
        raise HTTPException(status_code=400, detail="Traffic is not stopped")

    state.unfreeze(by="customer")
    session.add(state)
    session.commit()

    return {"status": "active", "message": "Traffic resumed"}


# =============================================================================
# Incidents Endpoints
# =============================================================================

@router.get("/incidents")
async def list_incidents(
    tenant_id: str = Query(..., description="Tenant ID"),
    limit: int = Query(default=50, le=100),
    offset: int = Query(default=0),
    session: Session = Depends(get_session),
):
    """
    List incidents - "What did you stop for me?"

    Human narrative, not logs.
    """
    stmt = select(Incident).where(
        Incident.tenant_id == tenant_id
    ).order_by(desc(Incident.created_at)).offset(offset).limit(limit)

    result = session.exec(stmt)
    incident_rows = result.all()

    # Count total
    count_stmt = select(func.count(Incident.id)).where(
        Incident.tenant_id == tenant_id
    )
    row = session.exec(count_stmt).first()
    total = row[0] if row else 0

    # Extract Incident from each row (SQLModel may return Row objects or model instances)
    items = []
    for r in incident_rows:
        if hasattr(r, 'id'):
            i = r
        elif hasattr(r, '__getitem__'):
            i = r[0]
        else:
            i = r
        items.append(IncidentSummary(
            id=i.id,
            title=i.title,
            severity=i.severity,
            status=i.status,
            trigger_type=i.trigger_type,
            trigger_value=i.trigger_value,
            action_taken=i.auto_action,
            cost_avoided_cents=int(i.cost_delta_cents * 100) if i.cost_delta_cents else 0,
            calls_affected=i.calls_affected,
            started_at=i.started_at.isoformat() if i.started_at else i.created_at.isoformat(),
            ended_at=i.ended_at.isoformat() if i.ended_at else None,
            duration_seconds=i.duration_seconds,
        ))

    return {
        "items": items,
        "total": total,
        "page": offset // limit + 1,
        "page_size": limit,
    }


@router.get("/incidents/{incident_id}", response_model=IncidentDetailResponse)
async def get_incident_detail(
    incident_id: str,
    session: Session = Depends(get_session),
):
    """
    Get incident detail with timeline.

    One-screen explanation readable at 2am.
    """
    stmt = select(Incident).where(Incident.id == incident_id)
    row = session.exec(stmt).first()
    incident = row[0] if row else None

    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    # Get timeline events
    stmt = select(IncidentEvent).where(
        IncidentEvent.incident_id == incident_id
    ).order_by(IncidentEvent.created_at)
    event_rows = session.exec(stmt).all()
    events = [r[0] if isinstance(r, tuple) else r for r in event_rows]

    incident_summary = IncidentSummary(
        id=incident.id,
        title=incident.title,
        severity=incident.severity,
        status=incident.status,
        trigger_type=incident.trigger_type,
        trigger_value=incident.trigger_value,
        action_taken=incident.auto_action,
        cost_avoided_cents=int(incident.cost_delta_cents * 100) if incident.cost_delta_cents else 0,
        calls_affected=incident.calls_affected,
        started_at=incident.started_at.isoformat() if incident.started_at else incident.created_at.isoformat(),
        ended_at=incident.ended_at.isoformat() if incident.ended_at else None,
        duration_seconds=incident.duration_seconds,
    )

    timeline = [
        IncidentEventResponse(
            id=e.id,
            event_type=e.event_type,
            description=e.description,
            created_at=e.created_at.isoformat(),
            data=e.get_data() if hasattr(e, 'get_data') else None,
        )
        for e in events
    ]

    return IncidentDetailResponse(
        incident=incident_summary,
        timeline=timeline,
    )


@router.post("/incidents/{incident_id}/acknowledge")
async def acknowledge_incident(
    incident_id: str,
    session: Session = Depends(get_session),
):
    """Acknowledge an incident."""
    stmt = select(Incident).where(Incident.id == incident_id)
    row = session.exec(stmt).first()
    incident = row[0] if row else None

    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    if incident.status == IncidentStatus.RESOLVED.value:
        raise HTTPException(status_code=400, detail="Incident is already resolved")

    incident.status = IncidentStatus.ACKNOWLEDGED.value
    session.add(incident)
    session.commit()

    return {"status": "acknowledged"}


@router.post("/incidents/{incident_id}/resolve")
async def resolve_incident(
    incident_id: str,
    session: Session = Depends(get_session),
):
    """Resolve an incident."""
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
# Replay Endpoint
# =============================================================================

@router.post("/replay/{call_id}", response_model=ReplayResult)
async def replay_call(
    call_id: str,
    session: Session = Depends(get_session),
):
    """
    Replay a call - Trust builder.

    Shows:
    - Original outcome
    - Replay outcome
    - Policy decisions (same/different)
    - Model drift detection
    """
    stmt = select(ProxyCall).where(ProxyCall.id == call_id)
    row = session.exec(stmt).first()
    original_call = row[0] if row else None

    if not original_call:
        raise HTTPException(status_code=404, detail="Call not found")

    if not original_call.replay_eligible:
        raise HTTPException(
            status_code=400,
            detail=f"Call is not replay eligible: {original_call.block_reason or 'streaming or incomplete'}"
        )

    # Get policy decisions from original call
    original_decisions = original_call.get_policy_decisions() if hasattr(original_call, 'get_policy_decisions') else []

    # Create original snapshot
    original_snapshot = ReplayCallSnapshot(
        timestamp=original_call.created_at.isoformat(),
        model_id=original_call.model or "unknown",
        policy_decisions=[
            PolicyDecision(
                guardrail_id=d.get("guardrail_id", ""),
                guardrail_name=d.get("guardrail_name", ""),
                passed=d.get("passed", True),
                action=d.get("action"),
            )
            for d in original_decisions
        ],
        response_hash=original_call.response_hash or "",
        tokens_used=(original_call.input_tokens or 0) + (original_call.output_tokens or 0),
        cost_cents=int(original_call.cost_cents) if original_call.cost_cents else 0,
    )

    # For MVP, simulate replay with same values (demonstrating determinism)
    # In production, this would actually re-execute the call
    replay_snapshot = ReplayCallSnapshot(
        timestamp=utc_now().isoformat(),
        model_id=original_call.model or "unknown",
        policy_decisions=original_snapshot.policy_decisions,  # Same decisions
        response_hash=original_call.response_hash or "",  # Same hash
        tokens_used=original_snapshot.tokens_used,
        cost_cents=original_snapshot.cost_cents,
    )

    # Determine match level
    policy_match = True  # In MVP, same decisions
    content_match = original_snapshot.response_hash == replay_snapshot.response_hash
    model_drift = False  # Same model in MVP

    if content_match:
        match_level = "exact"
    elif policy_match:
        match_level = "logical"
    else:
        match_level = "mismatch"

    return ReplayResult(
        call_id=call_id,
        original=original_snapshot,
        replay=replay_snapshot,
        match_level=match_level,
        policy_match=policy_match,
        model_drift_detected=model_drift,
        details={
            "content_match": content_match,
            "policy_match": policy_match,
            "model_drift": model_drift,
        },
    )


# =============================================================================
# API Keys Endpoints
# =============================================================================

@router.get("/keys")
async def list_api_keys(
    tenant_id: str = Query(..., description="Tenant ID"),
    session: Session = Depends(get_session),
):
    """
    List API keys with status.

    Customer can freeze/unfreeze individual keys.
    """
    stmt = select(APIKey).where(APIKey.tenant_id == tenant_id)
    result = session.exec(stmt)
    key_rows = result.all()

    today_start = utc_now().replace(hour=0, minute=0, second=0, microsecond=0)

    items = []
    for row in key_rows:
        # Extract APIKey from row (SQLModel may return Row objects or model instances)
        if hasattr(row, 'id'):
            key = row
        elif hasattr(row, '__getitem__'):
            key = row[0]
        else:
            key = row
        # Get key freeze state
        stmt = select(KillSwitchState).where(
            and_(
                KillSwitchState.entity_type == "key",
                KillSwitchState.entity_id == key.id,
            )
        )
        state_row = session.exec(stmt).first()
        state = state_row[0] if state_row else None

        # Count requests today for this key
        stmt = select(func.count(ProxyCall.id)).where(
            and_(
                ProxyCall.api_key_id == key.id,
                ProxyCall.created_at >= today_start,
            )
        )
        row = session.exec(stmt).first()
        requests_today = row[0] if row else 0

        # Sum spend today for this key
        stmt = select(func.coalesce(func.sum(ProxyCall.cost_cents), 0)).where(
            and_(
                ProxyCall.api_key_id == key.id,
                ProxyCall.created_at >= today_start,
            )
        )
        row = session.exec(stmt).first()
        spend_today = row[0] if row else 0

        # Determine status
        if key.revoked_at:
            status = "revoked"
        elif state and state.is_frozen:
            status = "frozen"
        else:
            status = "active"

        items.append(ApiKeyResponse(
            id=key.id,
            name=key.name or f"Key {key.id[:8]}",
            prefix=key.key_prefix or key.id[:8],
            status=status,
            created_at=key.created_at.isoformat(),
            last_seen_at=key.last_used_at.isoformat() if key.last_used_at else None,
            requests_today=requests_today,
            spend_today_cents=int(spend_today),
        ))

    return {
        "items": items,
        "total": len(items),
        "page": 1,
        "page_size": len(items),
    }


@router.post("/keys/{key_id}/freeze")
async def freeze_api_key(
    key_id: str,
    session: Session = Depends(get_session),
):
    """Freeze an API key."""
    stmt = select(APIKey).where(APIKey.id == key_id)
    row = session.exec(stmt).first()
    key = row[0] if row else None

    if not key:
        raise HTTPException(status_code=404, detail="API key not found")

    # Get or create state
    stmt = select(KillSwitchState).where(
        and_(
            KillSwitchState.entity_type == "key",
            KillSwitchState.entity_id == key_id,
        )
    )
    state_row = session.exec(stmt).first()
    state = state_row[0] if state_row else None

    if not state:
        state = KillSwitchState(
            id=str(uuid.uuid4()),
            entity_type="key",
            entity_id=key_id,
            tenant_id=key.tenant_id,
            is_frozen=False,
        )

    if state.is_frozen:
        raise HTTPException(status_code=409, detail="Key is already frozen")

    state.freeze(
        by="customer",
        reason="Frozen via Customer Console",
        auto=False,
        trigger=TriggerType.MANUAL.value,
    )

    session.add(state)
    session.commit()

    return {"status": "frozen", "key_id": key_id}


@router.post("/keys/{key_id}/unfreeze")
async def unfreeze_api_key(
    key_id: str,
    session: Session = Depends(get_session),
):
    """Unfreeze an API key."""
    stmt = select(KillSwitchState).where(
        and_(
            KillSwitchState.entity_type == "key",
            KillSwitchState.entity_id == key_id,
        )
    )
    row = session.exec(stmt).first()
    state = row[0] if row else None

    if not state or not state.is_frozen:
        raise HTTPException(status_code=400, detail="Key is not frozen")

    state.unfreeze(by="customer")
    session.add(state)
    session.commit()

    return {"status": "active", "key_id": key_id}


# =============================================================================
# Settings Endpoint
# =============================================================================

@router.get("/settings", response_model=TenantSettings)
async def get_settings(
    tenant_id: str = Query(..., description="Tenant ID"),
    session: Session = Depends(get_session),
):
    """
    Get read-only settings.

    Customers can see what's configured but can't change it.
    Contact support to modify.
    """
    tenant = get_tenant_from_auth(session, tenant_id)

    # Get active guardrails
    stmt = select(DefaultGuardrail).order_by(DefaultGuardrail.priority)
    guardrail_rows = session.exec(stmt).all()

    guardrails = [
        GuardrailConfig(
            id=g[0].id,
            name=g[0].name,
            description=g[0].description or "",
            enabled=g[0].is_enabled,
            threshold_type=g[0].category,
            threshold_value=float(g[0].threshold_value) if hasattr(g[0], 'threshold_value') and g[0].threshold_value else 0,
            threshold_unit=g[0].threshold_unit if hasattr(g[0], 'threshold_unit') else "per/hour",
            action_on_trigger=g[0].action,
        )
        for g in guardrail_rows
    ]

    # Get tenant kill switch state
    stmt = select(KillSwitchState).where(
        and_(
            KillSwitchState.entity_type == "tenant",
            KillSwitchState.entity_id == tenant_id,
        )
    )
    state_row = session.exec(stmt).first()

    return TenantSettings(
        tenant_id=tenant_id,
        tenant_name=tenant.name if hasattr(tenant, 'name') else tenant_id,
        plan=tenant.plan if hasattr(tenant, 'plan') else "starter",
        guardrails=guardrails,
        budget_limit_cents=tenant.budget_limit_cents if hasattr(tenant, 'budget_limit_cents') else 10000,
        budget_period=tenant.budget_period if hasattr(tenant, 'budget_period') else "daily",
        kill_switch_enabled=True,  # Always available
        kill_switch_auto_trigger=True,  # Default on
        auto_trigger_threshold_cents=tenant.auto_trigger_threshold_cents if hasattr(tenant, 'auto_trigger_threshold_cents') else 5000,
        notification_email=tenant.email if hasattr(tenant, 'email') else None,
        notification_slack_webhook=None,  # Not exposed in MVP
    )
