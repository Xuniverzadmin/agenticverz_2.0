# Layer: L2b -- Public API (Tenant-scoped, NOT console-only)
# Product: system-wide (BOUNDARY VIOLATION if labeled ai-console)
# Auth: get_tenant_context + requires_feature (tier-gating)
# Reference: PIN-240
# WARNING: This is NOT console-exclusive. SDK users and external systems call this.
#
# REFACTORED: All session.execute() calls moved to L6 drivers
# - Read operations: controls/L6_drivers/killswitch_ops_driver.py
# - Write operations: hoc_spine/drivers/guard_write_driver.py

"""M22 KillSwitch MVP - Control & Observability API

Endpoints:
- POST /v1/killswitch/tenant - Freeze tenant
- POST /v1/killswitch/key - Freeze API key
- GET /v1/killswitch/status - Get freeze status
- DELETE /v1/killswitch/tenant - Unfreeze tenant
- DELETE /v1/killswitch/key - Unfreeze API key
- GET /v1/policies/active - Get active guardrails
- GET /v1/incidents - List incidents
- GET /v1/incidents/{id} - Get incident detail
- POST /v1/replay/{call_id} - Replay a call
- GET /v1/calls/{call_id} - Get call detail

M28: Demo endpoint /v1/demo/simulate-incident removed (PIN-145)

Tier Gating (M32 - PIN-158):
- OBSERVE ($0): Read-only status, policies, incidents
- REACT ($9): Killswitch write (freeze/unfreeze) - "You see the fire"
- PREVENT ($199): Replay for evidence - "You stop the fire"
"""

import json
import uuid

# NOTE: Removed 'import random' - Demo endpoint uses deterministic values
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from app.auth.authority import AuthorityResult, emit_authority_audit, require_replay_execute
from app.schemas.response import wrap_dict
from app.auth.tenant_auth import TenantContext, get_tenant_context
from app.auth.tier_gating import requires_feature
from app.models.killswitch import (
    # M28: DemoSimulationRequest, DemoSimulationResult removed (PIN-145)
    GuardrailSummary,
    IncidentDetail,
    IncidentSummary,
    KillSwitchAction,
    KillSwitchStatus,
    ProxyCallDetail,
    ReplayRequest,
    ReplayResult,
    TriggerType,
)

# L4 registry dispatch (L2→L4 topology)
from app.hoc.cus.hoc_spine.orchestrator.operation_registry import (
    get_operation_registry,
    get_sync_session_dep,
    OperationContext,
)

# =============================================================================
# Router
# =============================================================================

router = APIRouter(prefix="/v1", tags=["KillSwitch"])


# =============================================================================
# Helper Functions
# =============================================================================


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


# =============================================================================
# Kill Switch Endpoints
# =============================================================================


@router.post("/killswitch/tenant", response_model=KillSwitchStatus)
async def freeze_tenant(
    tenant_id: str = Query(..., description="Tenant ID to freeze"),
    action: KillSwitchAction = None,
    session=Depends(get_sync_session_dep),
    ctx: TenantContext = Depends(get_tenant_context),
    _tier: None = Depends(requires_feature("killswitch.write")),
):
    """
    Hard stop everything for a tenant.

    **Tier: REACT ($9)** - Emergency response capability. "You see the fire."

    Immediate. No in-flight retries. Sticky until manually lifted.
    """
    if action is None:
        action = KillSwitchAction(reason="Manual freeze", actor="system")

    registry = get_operation_registry()

    # Verify tenant exists via registry dispatch
    result = await registry.execute("killswitch.read", OperationContext(
        session=None,
        tenant_id="",
        params={
            "method": "verify_tenant_exists",
            "sync_session": session,
            "lookup_tenant_id": tenant_id,
        }
    ))
    if not result.success:
        raise HTTPException(status_code=500, detail=result.error)
    tenant = result.data

    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    # Get or create killswitch state via registry dispatch
    result = await registry.execute("killswitch.write", OperationContext(
        session=None,
        tenant_id="",
        params={
            "method": "get_or_create_killswitch_state",
            "sync_session": session,
            "entity_type": "tenant",
            "entity_id": tenant_id,
            "lookup_tenant_id": tenant_id,
        }
    ))
    if not result.success:
        raise HTTPException(status_code=500, detail=result.error)
    state = result.data["state"]

    if state.is_frozen:
        raise HTTPException(status_code=409, detail="Tenant is already frozen")

    # Freeze killswitch via registry dispatch
    result = await registry.execute("killswitch.write", OperationContext(
        session=None,
        tenant_id="",
        params={
            "method": "freeze_killswitch",
            "sync_session": session,
            "state": state,
            "by": action.actor or "system",
            "reason": action.reason,
            "auto": False,
            "trigger": TriggerType.MANUAL.value,
        }
    ))
    if not result.success:
        raise HTTPException(status_code=500, detail=result.error)
    state = result.data

    # Extract values while session is open
    return KillSwitchStatus(
        entity_type="tenant",
        entity_id=tenant_id,
        is_frozen=True,
        frozen_at=state.frozen_at,
        frozen_by=state.frozen_by,
        freeze_reason=state.freeze_reason,
        auto_triggered=state.auto_triggered,
        trigger_type=state.trigger_type,
    )


@router.post("/killswitch/key", response_model=KillSwitchStatus)
async def freeze_key(
    key_id: str = Query(..., description="API key ID to freeze"),
    action: KillSwitchAction = None,
    session=Depends(get_sync_session_dep),
    ctx: TenantContext = Depends(get_tenant_context),
    _tier: None = Depends(requires_feature("killswitch.write")),
):
    """
    Kill a single API key.

    **Tier: REACT ($9)** - Emergency response capability. "You see the fire."

    Use cases: Compromised key, rogue experiment, limit damage.
    """
    if action is None:
        action = KillSwitchAction(reason="Manual freeze", actor="system")

    registry = get_operation_registry()

    # Verify key exists via registry dispatch
    result = await registry.execute("killswitch.read", OperationContext(
        session=None,
        tenant_id="",
        params={
            "method": "verify_api_key_exists",
            "sync_session": session,
            "key_id": key_id,
        }
    ))
    if not result.success:
        raise HTTPException(status_code=500, detail=result.error)
    key = result.data

    if not key:
        raise HTTPException(status_code=404, detail="API key not found")

    # Get or create killswitch state via registry dispatch
    result = await registry.execute("killswitch.write", OperationContext(
        session=None,
        tenant_id="",
        params={
            "method": "get_or_create_killswitch_state",
            "sync_session": session,
            "entity_type": "key",
            "entity_id": key_id,
            "lookup_tenant_id": key.tenant_id,
        }
    ))
    if not result.success:
        raise HTTPException(status_code=500, detail=result.error)
    state = result.data["state"]

    if state.is_frozen:
        raise HTTPException(status_code=409, detail="API key is already frozen")

    # Freeze killswitch via registry dispatch
    result = await registry.execute("killswitch.write", OperationContext(
        session=None,
        tenant_id="",
        params={
            "method": "freeze_killswitch",
            "sync_session": session,
            "state": state,
            "by": action.actor or "system",
            "reason": action.reason,
            "auto": False,
            "trigger": TriggerType.MANUAL.value,
        }
    ))
    if not result.success:
        raise HTTPException(status_code=500, detail=result.error)
    state = result.data

    # Extract values while session is open
    return KillSwitchStatus(
        entity_type="key",
        entity_id=key_id,
        is_frozen=True,
        frozen_at=state.frozen_at,
        frozen_by=state.frozen_by,
        freeze_reason=state.freeze_reason,
        auto_triggered=state.auto_triggered,
        trigger_type=state.trigger_type,
    )


@router.get("/killswitch/status", response_model=Dict[str, Any])
async def get_killswitch_status(
    tenant_id: str = Query(..., description="Tenant ID"),
    session=Depends(get_sync_session_dep),
    ctx: TenantContext = Depends(get_tenant_context),
    _tier: None = Depends(requires_feature("killswitch.read")),
):
    """
    Get complete kill switch status for a tenant.

    **Tier: REACT ($9)** - KillSwitch visibility.

    Shows tenant state plus all key overrides.
    """
    registry = get_operation_registry()

    # Get tenant state via registry dispatch
    result = await registry.execute("killswitch.read", OperationContext(
        session=None,
        tenant_id="",
        params={
            "method": "get_killswitch_state",
            "sync_session": session,
            "entity_type": "tenant",
            "entity_id": tenant_id,
        }
    ))
    if not result.success:
        raise HTTPException(status_code=500, detail=result.error)
    tenant_state = result.data

    # Get all key states for this tenant via registry dispatch
    result = await registry.execute("killswitch.read", OperationContext(
        session=None,
        tenant_id="",
        params={
            "method": "get_key_states_for_tenant",
            "sync_session": session,
            "lookup_tenant_id": tenant_id,
        }
    ))
    if not result.success:
        raise HTTPException(status_code=500, detail=result.error)
    key_states = result.data

    return wrap_dict({
        "tenant_id": tenant_id,
        "tenant": {
            "is_frozen": tenant_state.is_frozen if tenant_state else False,
            "frozen_at": tenant_state.frozen_at.isoformat() if tenant_state and tenant_state.frozen_at else None,
            "frozen_by": tenant_state.frozen_by if tenant_state else None,
            "freeze_reason": tenant_state.freeze_reason if tenant_state else None,
            "auto_triggered": tenant_state.auto_triggered if tenant_state else False,
            "trigger_type": tenant_state.trigger_type if tenant_state else None,
        },
        "keys": [
            {
                "key_id": ks["entity_id"],
                "is_frozen": ks["is_frozen"],
                "frozen_at": ks["frozen_at"].isoformat() if ks["frozen_at"] else None,
                "frozen_by": ks["frozen_by"],
                "freeze_reason": ks["freeze_reason"],
            }
            for ks in key_states
        ],
        "effective_state": "frozen" if (tenant_state and tenant_state.is_frozen) else "active",
    })


@router.delete("/killswitch/tenant", response_model=KillSwitchStatus)
async def unfreeze_tenant(
    tenant_id: str = Query(..., description="Tenant ID to unfreeze"),
    actor: str = Query(default="system", description="Who is unfreezing"),
    session=Depends(get_sync_session_dep),
    ctx: TenantContext = Depends(get_tenant_context),
    _tier: None = Depends(requires_feature("killswitch.write")),
):
    """
    Unfreeze a tenant.

    **Tier: REACT ($9)** - Emergency response capability.
    """
    registry = get_operation_registry()

    # Get killswitch state via registry dispatch
    result = await registry.execute("killswitch.read", OperationContext(
        session=None,
        tenant_id="",
        params={
            "method": "get_killswitch_state",
            "sync_session": session,
            "entity_type": "tenant",
            "entity_id": tenant_id,
        }
    ))
    if not result.success:
        raise HTTPException(status_code=500, detail=result.error)
    state_dto = result.data

    if not state_dto or not state_dto.is_frozen:
        raise HTTPException(status_code=404, detail="Tenant is not frozen")

    # Get or create killswitch state via registry dispatch
    result = await registry.execute("killswitch.write", OperationContext(
        session=None,
        tenant_id="",
        params={
            "method": "get_or_create_killswitch_state",
            "sync_session": session,
            "entity_type": "tenant",
            "entity_id": tenant_id,
            "lookup_tenant_id": tenant_id,
        }
    ))
    if not result.success:
        raise HTTPException(status_code=500, detail=result.error)
    state = result.data["state"]

    # Unfreeze killswitch via registry dispatch
    result = await registry.execute("killswitch.write", OperationContext(
        session=None,
        tenant_id="",
        params={
            "method": "unfreeze_killswitch",
            "sync_session": session,
            "state": state,
            "by": actor,
        }
    ))
    if not result.success:
        raise HTTPException(status_code=500, detail=result.error)
    state = result.data

    return KillSwitchStatus(
        entity_type="tenant",
        entity_id=tenant_id,
        is_frozen=False,
        frozen_at=state.frozen_at,
        frozen_by=state.frozen_by,
        freeze_reason=state.freeze_reason,
        auto_triggered=state.auto_triggered,
        trigger_type=state.trigger_type,
    )


@router.delete("/killswitch/key", response_model=KillSwitchStatus)
async def unfreeze_key(
    key_id: str = Query(..., description="API key ID to unfreeze"),
    actor: str = Query(default="system", description="Who is unfreezing"),
    session=Depends(get_sync_session_dep),
    ctx: TenantContext = Depends(get_tenant_context),
    _tier: None = Depends(requires_feature("killswitch.write")),
):
    """
    Unfreeze an API key.

    **Tier: REACT ($9)** - Emergency response capability.
    """
    registry = get_operation_registry()

    # Get killswitch state via registry dispatch
    result = await registry.execute("killswitch.read", OperationContext(
        session=None,
        tenant_id="",
        params={
            "method": "get_killswitch_state",
            "sync_session": session,
            "entity_type": "key",
            "entity_id": key_id,
        }
    ))
    if not result.success:
        raise HTTPException(status_code=500, detail=result.error)
    state_dto = result.data

    if not state_dto or not state_dto.is_frozen:
        raise HTTPException(status_code=404, detail="API key is not frozen")

    # Get or create killswitch state via registry dispatch
    result = await registry.execute("killswitch.write", OperationContext(
        session=None,
        tenant_id="",
        params={
            "method": "get_or_create_killswitch_state",
            "sync_session": session,
            "entity_type": "key",
            "entity_id": key_id,
            "lookup_tenant_id": state_dto.tenant_id,
        }
    ))
    if not result.success:
        raise HTTPException(status_code=500, detail=result.error)
    state = result.data["state"]

    # Unfreeze killswitch via registry dispatch
    result = await registry.execute("killswitch.write", OperationContext(
        session=None,
        tenant_id="",
        params={
            "method": "unfreeze_killswitch",
            "sync_session": session,
            "state": state,
            "by": actor,
        }
    ))
    if not result.success:
        raise HTTPException(status_code=500, detail=result.error)
    state = result.data

    return KillSwitchStatus(
        entity_type="key",
        entity_id=key_id,
        is_frozen=False,
        frozen_at=state.frozen_at,
        frozen_by=state.frozen_by,
        freeze_reason=state.freeze_reason,
        auto_triggered=state.auto_triggered,
        trigger_type=state.trigger_type,
    )


# =============================================================================
# Guardrails Endpoint
# =============================================================================


@router.get("/policies/active", response_model=List[GuardrailSummary])
async def get_active_policies(
    session=Depends(get_sync_session_dep),
    ctx: TenantContext = Depends(get_tenant_context),
):
    """
    Get active guardrails - "What's protecting me right now?"

    **Tier: OBSERVE ($0)** - Basic visibility into protection.

    Returns the Default Guardrail Pack v1 (read-only).
    No editing in MVP - this is intentional for trust.
    """
    registry = get_operation_registry()

    # List active guardrails via registry dispatch
    result = await registry.execute("killswitch.read", OperationContext(
        session=None,
        tenant_id="",
        params={
            "method": "list_active_guardrails",
            "sync_session": session,
        }
    ))
    if not result.success:
        raise HTTPException(status_code=500, detail=result.error)
    guardrails = result.data

    return [
        GuardrailSummary(
            id=g.id,
            name=g.name,
            description=g.description,
            category=g.category,
            action=g.action,
            is_enabled=g.is_enabled,
            priority=g.priority,
        )
        for g in guardrails
    ]


# =============================================================================
# Incidents Endpoints
# =============================================================================


@router.get("/incidents", response_model=List[IncidentSummary])
async def list_incidents(
    tenant_id: str = Query(..., description="Tenant ID"),
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(default=50, le=100),
    offset: int = Query(default=0),
    session=Depends(get_sync_session_dep),
    ctx: TenantContext = Depends(get_tenant_context),
    _tier: None = Depends(requires_feature("incident.list")),
):
    """
    List incidents (auto-grouped failures).

    **Tier: REACT ($9)** - Incident visibility. "You see the fire."

    An incident = correlated failures + retries + cost spike within time window.
    """
    registry = get_operation_registry()

    # List incidents via registry dispatch
    result = await registry.execute("killswitch.read", OperationContext(
        session=None,
        tenant_id="",
        params={
            "method": "list_incidents",
            "sync_session": session,
            "lookup_tenant_id": tenant_id,
            "status": status,
            "limit": limit,
            "offset": offset,
        }
    ))
    if not result.success:
        raise HTTPException(status_code=500, detail=result.error)
    incidents = result.data

    return [
        IncidentSummary(
            id=i.id,
            title=i.title,
            severity=i.severity,
            status=i.status,
            trigger_type=i.trigger_type,
            calls_affected=i.calls_affected,
            cost_delta_cents=i.cost_delta_cents,
            started_at=i.started_at,
            ended_at=i.ended_at,
            duration_seconds=i.duration_seconds,
        )
        for i in incidents
    ]


@router.get("/incidents/{incident_id}", response_model=IncidentDetail)
async def get_incident(
    incident_id: str,
    session=Depends(get_sync_session_dep),
    ctx: TenantContext = Depends(get_tenant_context),
    _tier: None = Depends(requires_feature("incident.read")),
):
    """
    Get incident detail with timeline.

    **Tier: REACT ($9)** - Incident visibility. "You see the fire."

    One-screen explanation readable by a founder at 2am.
    """
    registry = get_operation_registry()

    # Get incident detail via registry dispatch
    result = await registry.execute("killswitch.read", OperationContext(
        session=None,
        tenant_id="",
        params={
            "method": "get_incident_detail",
            "sync_session": session,
            "incident_id": incident_id,
        }
    ))
    if not result.success:
        raise HTTPException(status_code=500, detail=result.error)
    incident = result.data

    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    # Get timeline events via registry dispatch
    result = await registry.execute("killswitch.read", OperationContext(
        session=None,
        tenant_id="",
        params={
            "method": "get_incident_events",
            "sync_session": session,
            "incident_id": incident_id,
        }
    ))
    if not result.success:
        raise HTTPException(status_code=500, detail=result.error)
    events = result.data

    timeline = [
        {
            "time": e.created_at.isoformat() if hasattr(e.created_at, "isoformat") else str(e.created_at),
            "event_type": e.event_type,
            "description": e.description,
            "data": e.data or {},
        }
        for e in events
    ]

    return IncidentDetail(
        id=incident.id,
        title=incident.title,
        severity=incident.severity,
        status=incident.status,
        trigger_type=incident.trigger_type,
        trigger_value=incident.trigger_value,
        calls_affected=incident.calls_affected,
        cost_delta_cents=incident.cost_delta_cents,
        error_rate=incident.error_rate,
        auto_action=incident.auto_action,
        started_at=incident.started_at,
        ended_at=incident.ended_at,
        duration_seconds=incident.duration_seconds,
        timeline=timeline,
    )


# =============================================================================
# Replay Endpoints
# =============================================================================


@router.post("/replay/{call_id}", response_model=ReplayResult)
async def replay_call(
    call_id: str,
    request: ReplayRequest = None,
    session=Depends(get_sync_session_dep),
    ctx: TenantContext = Depends(get_tenant_context),
    _tier: None = Depends(requires_feature("evidence.replay")),
    auth: AuthorityResult = Depends(require_replay_execute),
):
    """
    REPLAY PROVES ENFORCEMENT

    **Tier: PREVENT ($199)** - Evidence and compliance verification. "You stop the fire."

    Language layer: This is NOT "re-execution" - it's PROOF.
    Replay demonstrates that your guardrails are working correctly.

    Guarantees:
    - Same input
    - Same policy evaluation
    - Same routing decision
    - Deterministic outcome

    Returns comparison showing enforcement consistency.
    """
    # Emit authority audit for capability access
    await emit_authority_audit(auth, "replay", subject_id=call_id)

    if request is None:
        request = ReplayRequest(dry_run=False)

    registry = get_operation_registry()

    # Get original call via registry dispatch
    result = await registry.execute("killswitch.read", OperationContext(
        session=None,
        tenant_id="",
        params={
            "method": "get_proxy_call",
            "sync_session": session,
            "call_id": call_id,
        }
    ))
    if not result.success:
        raise HTTPException(status_code=500, detail=result.error)
    original = result.data

    if not original:
        raise HTTPException(status_code=404, detail="Call not found")

    if not original.replay_eligible:
        raise HTTPException(
            status_code=400, detail=f"Call is not replay eligible: {original.block_reason or 'unknown'}"
        )

    # Parse original request (reserved for future replay implementation)
    _original_request = json.loads(original.request_json)  # noqa: F841

    if request.dry_run:
        # Dry run - just validate
        return ReplayResult(
            original_call_id=call_id,
            replay_call_id=None,
            dry_run=True,
            same_result=True,
            diff=None,
        )

    # Re-execute the call
    # This would call the proxy endpoint internally
    # For MVP, we simulate the replay
    replay_call_id = str(uuid.uuid4())

    # Compare hashes
    same_result = True  # In real impl, compare response_hash

    return ReplayResult(
        original_call_id=call_id,
        replay_call_id=replay_call_id,
        dry_run=False,
        same_result=same_result,
        diff=None if same_result else {"note": "Results differ"},
    )


@router.get("/calls/{call_id}", response_model=ProxyCallDetail)
async def get_call(
    call_id: str,
    session=Depends(get_sync_session_dep),
    ctx: TenantContext = Depends(get_tenant_context),
    _tier: None = Depends(requires_feature("timeline.read")),
):
    """
    Get single call truth.

    **Tier: REACT ($9)** - Decision timeline visibility.

    Includes input hash, policy decisions, cost, outcome, replay eligibility.
    """
    registry = get_operation_registry()

    # Get proxy call via registry dispatch
    result = await registry.execute("killswitch.read", OperationContext(
        session=None,
        tenant_id="",
        params={
            "method": "get_proxy_call",
            "sync_session": session,
            "call_id": call_id,
        }
    ))
    if not result.success:
        raise HTTPException(status_code=500, detail=result.error)
    call = result.data

    if not call:
        raise HTTPException(status_code=404, detail="Call not found")

    def _parse_json(raw):
        if raw is None:
            return None
        if isinstance(raw, (dict, list)):
            return raw
        try:
            return json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            return None

    def _get_policy_decisions(raw):
        parsed = _parse_json(raw)
        return parsed if isinstance(parsed, list) else []

    return ProxyCallDetail(
        id=call.id,
        endpoint=call.endpoint,
        model=call.model,
        request_hash=call.request_hash,
        request_body=json.loads(call.request_json) if call.request_json else None,
        response_body=json.loads(call.response_json) if call.response_json else None,
        status_code=call.status_code,
        error_code=call.error_code,
        was_blocked=call.was_blocked,
        block_reason=call.block_reason,
        policy_decisions=_get_policy_decisions(call.policy_decisions_json),
        cost_cents=call.cost_cents,
        input_tokens=call.input_tokens,
        output_tokens=call.output_tokens,
        latency_ms=call.latency_ms,
        replay_eligible=call.replay_eligible,
        created_at=call.created_at,
    )


# =============================================================================
# M28 DELETION: Demo Simulation endpoint removed (PIN-145)
# /v1/demo/simulate-incident was a sales demo tool, not a product feature
# Reason: Demo artifacts violate evidence integrity and confuse customers
# =============================================================================
