# Layer: L2 — Product APIs
# Product: system-wide
# Temporal:
#   Trigger: api
#   Execution: sync
# Role: Replay UX API - READ-ONLY slice and timeline endpoints
# Authority: READ replay data (no mutations)
# Callers: Customer Console replay viewer
# Allowed Imports: L4, L6
# Forbidden Imports: L1, L3, L5
# Reference: PIN-309 (Phase G Governance Freeze), H1 Replay UX
# capability_id: CAP-001

"""
Replay UX API (H1)

Provides READ-ONLY endpoints for replay visualization:
- Time-windowed slice of incident data
- Grouped view: inputs, decisions, actions, side-effects
- Immutable, paginated responses

INVARIANTS:
1. All endpoints are READ-ONLY (no mutations)
2. Uses existing RBAC v2 enforcement (require_replay_read)
3. Tenant isolation enforced
4. No execution or write capabilities

Reference: Phase H1 - Replay UX Enablement
"""

import logging
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field
from sqlalchemy import and_, select
from sqlmodel import Session

from ..auth.authority import AuthorityResult, require_replay_read, verify_tenant_access
from ..db import get_session as get_db_session
from ..schemas.response import wrap_dict
from ..models.killswitch import Incident, IncidentEvent, ProxyCall

logger = logging.getLogger("nova.api.replay")

router = APIRouter(prefix="/replay", tags=["replay"])


# =============================================================================
# Response Models (Immutable Views)
# =============================================================================


class ReplayCategory(str, Enum):
    """Categories for replay data grouping."""

    INPUT = "input"
    DECISION = "decision"
    ACTION = "action"
    SIDE_EFFECT = "side_effect"


class ReplayItem(BaseModel):
    """Single item in replay timeline."""

    id: str
    timestamp: str
    category: ReplayCategory
    label: str
    summary: str
    data: Dict[str, Any] = Field(default_factory=dict)
    duration_ms: Optional[int] = None
    cost_cents: Optional[float] = None


class ReplaySliceResponse(BaseModel):
    """Paginated, grouped replay slice response."""

    incident_id: str
    incident_title: str
    incident_severity: str
    incident_status: str

    # Time window
    window_start: str
    window_end: str
    window_seconds: int

    # Grouped data (immutable)
    inputs: List[ReplayItem] = Field(default_factory=list)
    decisions: List[ReplayItem] = Field(default_factory=list)
    actions: List[ReplayItem] = Field(default_factory=list)
    side_effects: List[ReplayItem] = Field(default_factory=list)

    # Timeline (all items in chronological order)
    timeline: List[ReplayItem] = Field(default_factory=list)

    # Pagination
    total_items: int
    page: int
    page_size: int
    has_more: bool

    # Metadata (read-only indicators)
    is_immutable: bool = True
    replay_version: str = "1.0"


class IncidentSummaryResponse(BaseModel):
    """Summary of incident for replay context."""

    incident_id: str
    title: str
    severity: str
    status: str
    trigger_type: str
    started_at: str
    ended_at: Optional[str]
    duration_seconds: Optional[int]
    calls_affected: int
    cost_delta_cents: float
    has_replay_data: bool


# =============================================================================
# Helper Functions
# =============================================================================


def _categorize_proxy_call(call: ProxyCall) -> ReplayCategory:
    """
    Categorize a proxy call into replay category.

    Categories:
    - INPUT: Request data, model selection
    - DECISION: Policy decisions, guardrail evaluations
    - ACTION: Actual API call execution
    - SIDE_EFFECT: Cost tracking, logging, notifications
    """
    if call.was_blocked:
        return ReplayCategory.DECISION
    elif call.policy_decisions_json:
        return ReplayCategory.DECISION
    elif call.response_json:
        return ReplayCategory.ACTION
    else:
        return ReplayCategory.INPUT


def _proxy_call_to_replay_item(call: ProxyCall) -> ReplayItem:
    """Convert ProxyCall to ReplayItem for visualization."""
    category = _categorize_proxy_call(call)

    # Build summary based on category
    if category == ReplayCategory.DECISION:
        if call.was_blocked:
            summary = f"Blocked: {call.block_reason or 'policy violation'}"
        else:
            decisions = call.get_policy_decisions()
            passed = sum(1 for d in decisions if d.get("passed", True))
            summary = f"{passed}/{len(decisions)} guardrails passed"
    elif category == ReplayCategory.ACTION:
        summary = f"{call.endpoint} → {call.model} ({call.status_code or 'pending'})"
    else:
        summary = f"Request to {call.endpoint} using {call.model}"

    # Build label
    if call.was_blocked:
        label = "Policy Block"
    elif call.error_code:
        label = f"Error: {call.error_code}"
    else:
        label = call.endpoint.replace("/v1/", "").replace("/", " ").title()

    return ReplayItem(
        id=call.id,
        timestamp=call.created_at.isoformat(),
        category=category,
        label=label,
        summary=summary,
        data={
            "endpoint": call.endpoint,
            "model": call.model,
            "status_code": call.status_code,
            "was_blocked": call.was_blocked,
            "block_reason": call.block_reason,
            "input_tokens": call.input_tokens,
            "output_tokens": call.output_tokens,
            "request_hash": call.request_hash,
            "response_hash": call.response_hash,
            # Policy decisions (what the agent saw)
            "policy_decisions": call.get_policy_decisions(),
            # User tracking
            "user_id": call.user_id,
        },
        duration_ms=call.latency_ms,
        cost_cents=float(call.cost_cents) if call.cost_cents else None,
    )


def _incident_event_to_replay_item(event: IncidentEvent) -> ReplayItem:
    """Convert IncidentEvent to ReplayItem for visualization."""
    # Categorize based on event type
    event_type = event.event_type.lower()

    if "block" in event_type or "deny" in event_type or "policy" in event_type:
        category = ReplayCategory.DECISION
    elif "freeze" in event_type or "notify" in event_type or "alert" in event_type:
        category = ReplayCategory.SIDE_EFFECT
    elif "start" in event_type or "open" in event_type:
        category = ReplayCategory.INPUT
    else:
        category = ReplayCategory.ACTION

    return ReplayItem(
        id=event.id,
        timestamp=event.created_at.isoformat(),
        category=category,
        label=event.event_type.replace("_", " ").title(),
        summary=event.description,
        data=event.get_data(),
    )


# =============================================================================
# READ-ONLY Endpoints (H1)
# =============================================================================


@router.get("/{incident_id}/slice", response_model=ReplaySliceResponse)
async def get_replay_slice(
    request: Request,
    incident_id: str,
    window: int = Query(30, ge=5, le=300, description="Time window in seconds (±window from incident)"),
    center_time: Optional[str] = Query(None, description="Center time ISO8601 (default: incident start)"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=10, le=200, description="Items per page"),
    auth: AuthorityResult = Depends(require_replay_read),
    session: Session = Depends(get_db_session),
):
    """
    Get time-windowed replay slice of an incident.

    Returns grouped, immutable data for replay visualization:
    - inputs: What the agent saw (requests, context)
    - decisions: Policy evaluations, guardrail checks
    - actions: Actual executions, API calls
    - side_effects: Cost tracking, notifications, logging

    This endpoint is READ-ONLY and does not modify any data.

    RBAC: Requires read:replay permission
    Tenant Isolation: Enforced
    """
    # Fetch incident
    stmt = select(Incident).where(Incident.id == incident_id)
    incident = session.exec(stmt).first()

    if not incident:
        raise HTTPException(status_code=404, detail=f"Incident {incident_id} not found")

    # Enforce tenant isolation
    verify_tenant_access(auth, incident.tenant_id)

    # Determine time window
    if center_time:
        try:
            center = datetime.fromisoformat(center_time.replace("Z", "+00:00"))
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid center_time format (use ISO8601)")
    else:
        center = incident.started_at

    window_start = center - timedelta(seconds=window)
    window_end = center + timedelta(seconds=window)

    # Get related call IDs
    related_call_ids = incident.get_related_call_ids()

    # Fetch proxy calls in window
    if related_call_ids:
        stmt = (
            select(ProxyCall)
            .where(
                and_(
                    ProxyCall.id.in_(related_call_ids),
                    ProxyCall.created_at >= window_start,
                    ProxyCall.created_at <= window_end,
                )
            )
            .order_by(ProxyCall.created_at)
        )
        calls = list(session.exec(stmt).all())
    else:
        calls = []

    # Fetch incident events in window
    stmt = (
        select(IncidentEvent)
        .where(
            and_(
                IncidentEvent.incident_id == incident_id,
                IncidentEvent.created_at >= window_start,
                IncidentEvent.created_at <= window_end,
            )
        )
        .order_by(IncidentEvent.created_at)
    )
    events = list(session.exec(stmt).all())

    # Convert to replay items
    call_items = [_proxy_call_to_replay_item(c) for c in calls]
    event_items = [_incident_event_to_replay_item(e) for e in events]

    # Combine and sort timeline
    all_items = call_items + event_items
    all_items.sort(key=lambda x: x.timestamp)

    # Pagination
    total_items = len(all_items)
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    paginated_items = all_items[start_idx:end_idx]

    # Group by category
    inputs = [i for i in paginated_items if i.category == ReplayCategory.INPUT]
    decisions = [i for i in paginated_items if i.category == ReplayCategory.DECISION]
    actions = [i for i in paginated_items if i.category == ReplayCategory.ACTION]
    side_effects = [i for i in paginated_items if i.category == ReplayCategory.SIDE_EFFECT]

    logger.info(
        "replay_slice_read",
        extra={
            "incident_id": incident_id,
            "window_seconds": window,
            "total_items": total_items,
            "page": page,
            "actor_id": auth.actor.actor_id,
        },
    )

    return ReplaySliceResponse(
        incident_id=incident.id,
        incident_title=incident.title,
        incident_severity=incident.severity,
        incident_status=incident.status,
        window_start=window_start.isoformat(),
        window_end=window_end.isoformat(),
        window_seconds=window * 2,  # Total window is ±window
        inputs=inputs,
        decisions=decisions,
        actions=actions,
        side_effects=side_effects,
        timeline=paginated_items,
        total_items=total_items,
        page=page,
        page_size=page_size,
        has_more=end_idx < total_items,
    )


@router.get("/{incident_id}/summary", response_model=IncidentSummaryResponse)
async def get_incident_summary(
    request: Request,
    incident_id: str,
    auth: AuthorityResult = Depends(require_replay_read),
    session: Session = Depends(get_db_session),
):
    """
    Get incident summary for replay context.

    Provides high-level information about an incident before
    diving into detailed replay visualization.

    This endpoint is READ-ONLY.

    RBAC: Requires read:replay permission
    Tenant Isolation: Enforced
    """
    # Fetch incident
    stmt = select(Incident).where(Incident.id == incident_id)
    incident = session.exec(stmt).first()

    if not incident:
        raise HTTPException(status_code=404, detail=f"Incident {incident_id} not found")

    # Enforce tenant isolation
    verify_tenant_access(auth, incident.tenant_id)

    # Check if there's replay data
    related_call_ids = incident.get_related_call_ids()
    has_replay_data = len(related_call_ids) > 0

    return IncidentSummaryResponse(
        incident_id=incident.id,
        title=incident.title,
        severity=incident.severity,
        status=incident.status,
        trigger_type=incident.trigger_type,
        started_at=incident.started_at.isoformat(),
        ended_at=incident.ended_at.isoformat() if incident.ended_at else None,
        duration_seconds=incident.duration_seconds,
        calls_affected=incident.calls_affected,
        cost_delta_cents=float(incident.cost_delta_cents) if incident.cost_delta_cents else 0.0,
        has_replay_data=has_replay_data,
    )


@router.get("/{incident_id}/timeline")
async def get_replay_timeline(
    request: Request,
    incident_id: str,
    limit: int = Query(100, ge=10, le=500, description="Maximum items to return"),
    auth: AuthorityResult = Depends(require_replay_read),
    session: Session = Depends(get_db_session),
):
    """
    Get full timeline for an incident (unpaginated for scrubbing UI).

    Returns all replay items in chronological order for
    timeline scrubbing and playback visualization.

    This endpoint is READ-ONLY.

    RBAC: Requires read:replay permission
    Tenant Isolation: Enforced
    """
    # Fetch incident
    stmt = select(Incident).where(Incident.id == incident_id)
    incident = session.exec(stmt).first()

    if not incident:
        raise HTTPException(status_code=404, detail=f"Incident {incident_id} not found")

    # Enforce tenant isolation
    verify_tenant_access(auth, incident.tenant_id)

    # Get related call IDs
    related_call_ids = incident.get_related_call_ids()

    # Fetch all proxy calls for incident
    if related_call_ids:
        stmt = select(ProxyCall).where(ProxyCall.id.in_(related_call_ids)).order_by(ProxyCall.created_at).limit(limit)
        calls = list(session.exec(stmt).all())
    else:
        calls = []

    # Fetch all incident events
    stmt = select(IncidentEvent).where(IncidentEvent.incident_id == incident_id).order_by(IncidentEvent.created_at)
    events = list(session.exec(stmt).all())

    # Convert to replay items
    call_items = [_proxy_call_to_replay_item(c) for c in calls]
    event_items = [_incident_event_to_replay_item(e) for e in events]

    # Combine and sort
    all_items = call_items + event_items
    all_items.sort(key=lambda x: x.timestamp)

    # Limit total items
    all_items = all_items[:limit]

    # Calculate timeline bounds
    if all_items:
        start_time = all_items[0].timestamp
        end_time = all_items[-1].timestamp
    else:
        start_time = incident.started_at.isoformat()
        end_time = (incident.ended_at or incident.started_at).isoformat()

    return wrap_dict({
        "incident_id": incident.id,
        "incident_title": incident.title,
        "timeline_start": start_time,
        "timeline_end": end_time,
        "total_items": len(all_items),
        "items": [item.model_dump() for item in all_items],
        "is_immutable": True,
        "note": "Timeline data is read-only. No mutations are possible.",
    })


# =============================================================================
# UX Helper Endpoints
# =============================================================================


@router.get("/{incident_id}/explain/{item_id}")
async def explain_replay_item(
    request: Request,
    incident_id: str,
    item_id: str,
    auth: AuthorityResult = Depends(require_replay_read),
    session: Session = Depends(get_db_session),
):
    """
    Get detailed explanation for a single replay item.

    Provides expanded context for:
    - What the agent saw (inputs)
    - Why it decided (decision rationale)
    - What it executed (action details)

    This endpoint is READ-ONLY.

    RBAC: Requires read:replay permission
    Tenant Isolation: Enforced via incident
    """
    # Fetch incident first (for tenant check)
    stmt = select(Incident).where(Incident.id == incident_id)
    incident = session.exec(stmt).first()

    if not incident:
        raise HTTPException(status_code=404, detail=f"Incident {incident_id} not found")

    # Enforce tenant isolation
    verify_tenant_access(auth, incident.tenant_id)

    # Try to find as ProxyCall
    stmt = select(ProxyCall).where(ProxyCall.id == item_id)
    call = session.exec(stmt).first()

    if call:
        # Verify call belongs to incident
        related_ids = incident.get_related_call_ids()
        if call.id not in related_ids:
            raise HTTPException(status_code=404, detail=f"Item {item_id} not in incident {incident_id}")

        category = _categorize_proxy_call(call)

        # Build explanation based on category
        if category == ReplayCategory.INPUT:
            explanation = {
                "what_agent_saw": {
                    "endpoint": call.endpoint,
                    "model": call.model,
                    "request_hash": call.request_hash,
                    "note": "The agent received this request from the upstream system.",
                },
                "context": {
                    "user_id": call.user_id,
                    "api_key_id": call.api_key_id,
                    "tenant_id": call.tenant_id,
                },
            }
        elif category == ReplayCategory.DECISION:
            decisions = call.get_policy_decisions()
            explanation = {
                "why_decision": {
                    "was_blocked": call.was_blocked,
                    "block_reason": call.block_reason,
                    "guardrails_evaluated": len(decisions),
                    "guardrails_passed": sum(1 for d in decisions if d.get("passed", True)),
                },
                "policy_details": decisions,
                "note": "The system evaluated these guardrails before allowing the request.",
            }
        else:  # ACTION
            explanation = {
                "what_executed": {
                    "endpoint": call.endpoint,
                    "model": call.model,
                    "status_code": call.status_code,
                    "latency_ms": call.latency_ms,
                },
                "result": {
                    "input_tokens": call.input_tokens,
                    "output_tokens": call.output_tokens,
                    "cost_cents": float(call.cost_cents) if call.cost_cents else 0,
                    "error_code": call.error_code,
                },
                "note": "This is the actual API call that was executed.",
            }

        return wrap_dict({
            "item_id": item_id,
            "item_type": "proxy_call",
            "category": category.value,
            "timestamp": call.created_at.isoformat(),
            "explanation": explanation,
            "is_immutable": True,
        })

    # Try to find as IncidentEvent
    stmt = select(IncidentEvent).where(
        and_(
            IncidentEvent.id == item_id,
            IncidentEvent.incident_id == incident_id,
        )
    )
    event = session.exec(stmt).first()

    if event:
        return wrap_dict({
            "item_id": item_id,
            "item_type": "incident_event",
            "category": "event",
            "timestamp": event.created_at.isoformat(),
            "explanation": {
                "event_type": event.event_type,
                "description": event.description,
                "data": event.get_data(),
                "note": "This is an incident timeline event.",
            },
            "is_immutable": True,
        })

    raise HTTPException(status_code=404, detail=f"Item {item_id} not found")
