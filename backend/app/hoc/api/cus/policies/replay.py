# Layer: L2 — Product APIs
# Product: system-wide
# Temporal:
#   Trigger: api
#   Execution: sync
# Role: Replay UX API - READ-ONLY slice and timeline endpoints
# Authority: READ replay data (no mutations)
# Callers: Customer Console replay viewer
# Allowed Imports: L4
# Forbidden Imports: L1, L3, L5, L6
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
5. All DB access via L4 registry dispatch (L2 first-principles purity)

Reference: Phase H1 - Replay UX Enablement
"""

import json
import logging
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field
from app.auth.authority import AuthorityResult, require_replay_read, verify_tenant_access
from app.schemas.response import wrap_dict
from app.hoc.cus.hoc_spine.orchestrator.operation_registry import (
    get_operation_registry,
    get_sync_session_dep,
    OperationContext,
)

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


def _parse_json_field(value) -> Any:
    """Safely parse a JSON string field, returning empty dict/list on failure."""
    if value is None:
        return {}
    if isinstance(value, (dict, list)):
        return value
    try:
        return json.loads(value)
    except (json.JSONDecodeError, TypeError):
        return {}


def _get_policy_decisions(row: dict) -> list:
    """Extract policy decisions from a proxy call row dict."""
    raw = row.get("policy_decisions_json")
    result = _parse_json_field(raw)
    return result if isinstance(result, list) else []


def _get_related_call_ids(row: dict) -> list:
    """Extract related call IDs from incident metadata."""
    # First check the JSON column
    metadata = row.get("metadata")
    parsed = _parse_json_field(metadata)
    if isinstance(parsed, dict):
        call_ids = parsed.get("related_call_ids", [])
        if isinstance(call_ids, list) and call_ids:
            return call_ids
    # Fall back to related_call_ids_json column
    related_json = row.get("related_call_ids_json")
    if related_json:
        parsed_ids = _parse_json_field(related_json)
        if isinstance(parsed_ids, list):
            return parsed_ids
    return []


def _get_event_data(row: dict) -> dict:
    """Extract data dict from incident event row."""
    raw = row.get("data") or row.get("event_data") or row.get("data_json")
    result = _parse_json_field(raw)
    return result if isinstance(result, dict) else {}


def _categorize_proxy_call_row(row: dict) -> ReplayCategory:
    """
    Categorize a proxy call row into replay category.

    Categories:
    - INPUT: Request data, model selection
    - DECISION: Policy decisions, guardrail evaluations
    - ACTION: Actual API call execution
    - SIDE_EFFECT: Cost tracking, logging, notifications
    """
    if row.get("was_blocked"):
        return ReplayCategory.DECISION
    elif row.get("policy_decisions_json"):
        return ReplayCategory.DECISION
    elif row.get("response_json"):
        return ReplayCategory.ACTION
    else:
        return ReplayCategory.INPUT


def _proxy_call_row_to_replay_item(row: dict) -> ReplayItem:
    """Convert proxy call row dict to ReplayItem for visualization."""
    category = _categorize_proxy_call_row(row)

    # Build summary based on category
    if category == ReplayCategory.DECISION:
        if row.get("was_blocked"):
            summary = f"Blocked: {row.get('block_reason') or 'policy violation'}"
        else:
            decisions = _get_policy_decisions(row)
            passed = sum(1 for d in decisions if d.get("passed", True))
            summary = f"{passed}/{len(decisions)} guardrails passed"
    elif category == ReplayCategory.ACTION:
        summary = f"{row.get('endpoint', '')} -> {row.get('model', '')} ({row.get('status_code') or 'pending'})"
    else:
        summary = f"Request to {row.get('endpoint', '')} using {row.get('model', '')}"

    # Build label
    if row.get("was_blocked"):
        label = "Policy Block"
    elif row.get("error_code"):
        label = f"Error: {row['error_code']}"
    else:
        endpoint = row.get("endpoint", "")
        label = endpoint.replace("/v1/", "").replace("/", " ").title()

    created_at = row.get("created_at")
    timestamp = created_at.isoformat() if hasattr(created_at, "isoformat") else str(created_at)

    cost_cents_val = row.get("cost_cents")
    cost_cents = float(cost_cents_val) if cost_cents_val else None

    return ReplayItem(
        id=row.get("id", ""),
        timestamp=timestamp,
        category=category,
        label=label,
        summary=summary,
        data={
            "endpoint": row.get("endpoint"),
            "model": row.get("model"),
            "status_code": row.get("status_code"),
            "was_blocked": row.get("was_blocked"),
            "block_reason": row.get("block_reason"),
            "input_tokens": row.get("input_tokens"),
            "output_tokens": row.get("output_tokens"),
            "request_hash": row.get("request_hash"),
            "response_hash": row.get("response_hash"),
            # Policy decisions (what the agent saw)
            "policy_decisions": _get_policy_decisions(row),
            # User tracking
            "user_id": row.get("user_id"),
        },
        duration_ms=row.get("latency_ms"),
        cost_cents=cost_cents,
    )


def _incident_event_row_to_replay_item(row: dict) -> ReplayItem:
    """Convert IncidentEvent row dict to ReplayItem for visualization."""
    # Categorize based on event type
    event_type = str(row.get("event_type", "")).lower()

    if "block" in event_type or "deny" in event_type or "policy" in event_type:
        category = ReplayCategory.DECISION
    elif "freeze" in event_type or "notify" in event_type or "alert" in event_type:
        category = ReplayCategory.SIDE_EFFECT
    elif "start" in event_type or "open" in event_type:
        category = ReplayCategory.INPUT
    else:
        category = ReplayCategory.ACTION

    created_at = row.get("created_at")
    timestamp = created_at.isoformat() if hasattr(created_at, "isoformat") else str(created_at)

    return ReplayItem(
        id=row.get("id", ""),
        timestamp=timestamp,
        category=category,
        label=str(row.get("event_type", "")).replace("_", " ").title(),
        summary=row.get("description", ""),
        data=_get_event_data(row),
    )


# =============================================================================
# L4 Registry Dispatch Helpers
# =============================================================================


async def _dispatch_replay(session, method: str, **kwargs) -> Any:
    """Dispatch a replay operation through the L4 registry."""
    registry = get_operation_registry()
    ctx = OperationContext(
        session=session,
        tenant_id=kwargs.get("tenant_id", ""),
        params={"method": method, **kwargs},
    )
    result = await registry.execute("policies.replay", ctx)
    if not result.success:
        raise HTTPException(status_code=500, detail=result.error)
    return result.data


# =============================================================================
# READ-ONLY Endpoints (H1)
# =============================================================================


@router.get("/{incident_id}/slice", response_model=ReplaySliceResponse)
async def get_replay_slice(
    request: Request,
    incident_id: str,
    window: int = Query(30, ge=5, le=300, description="Time window in seconds (+-window from incident)"),
    center_time: Optional[str] = Query(None, description="Center time ISO8601 (default: incident start)"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=10, le=200, description="Items per page"),
    auth: AuthorityResult = Depends(require_replay_read),
    session=Depends(get_sync_session_dep),
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
    # Fetch incident via L4 dispatch
    incident = await _dispatch_replay(
        session,
        "get_incident_no_tenant_check",
        incident_id=incident_id,
    )

    if not incident:
        raise HTTPException(status_code=404, detail=f"Incident {incident_id} not found")

    # Enforce tenant isolation
    verify_tenant_access(auth, incident["tenant_id"])

    # Determine time window
    if center_time:
        try:
            center = datetime.fromisoformat(center_time.replace("Z", "+00:00"))
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid center_time format (use ISO8601)")
    else:
        center = incident["started_at"]

    window_start = center - timedelta(seconds=window)
    window_end = center + timedelta(seconds=window)

    # Get related call IDs
    related_call_ids = _get_related_call_ids(incident)

    # Fetch proxy calls in window via L4 dispatch
    calls = await _dispatch_replay(
        session,
        "get_proxy_calls_in_window",
        call_ids=related_call_ids,
        window_start=window_start,
        window_end=window_end,
    )

    # Fetch incident events in window via L4 dispatch
    events = await _dispatch_replay(
        session,
        "get_incident_events_in_window",
        incident_id=incident_id,
        window_start=window_start,
        window_end=window_end,
    )

    # Convert to replay items
    call_items = [_proxy_call_row_to_replay_item(c) for c in calls]
    event_items = [_incident_event_row_to_replay_item(e) for e in events]

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
        incident_id=incident["id"],
        incident_title=incident["title"],
        incident_severity=incident["severity"],
        incident_status=incident["status"],
        window_start=window_start.isoformat(),
        window_end=window_end.isoformat(),
        window_seconds=window * 2,  # Total window is +/-window
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
    session=Depends(get_sync_session_dep),
):
    """
    Get incident summary for replay context.

    Provides high-level information about an incident before
    diving into detailed replay visualization.

    This endpoint is READ-ONLY.

    RBAC: Requires read:replay permission
    Tenant Isolation: Enforced
    """
    # Fetch incident via L4 dispatch
    incident = await _dispatch_replay(
        session,
        "get_incident_no_tenant_check",
        incident_id=incident_id,
    )

    if not incident:
        raise HTTPException(status_code=404, detail=f"Incident {incident_id} not found")

    # Enforce tenant isolation
    verify_tenant_access(auth, incident["tenant_id"])

    # Check if there's replay data
    related_call_ids = _get_related_call_ids(incident)
    has_replay_data = len(related_call_ids) > 0

    started_at = incident["started_at"]
    ended_at = incident["ended_at"]
    cost_delta = incident["cost_delta_cents"]

    return IncidentSummaryResponse(
        incident_id=incident["id"],
        title=incident["title"],
        severity=incident["severity"],
        status=incident["status"],
        trigger_type=incident["trigger_type"],
        started_at=started_at.isoformat() if hasattr(started_at, "isoformat") else str(started_at),
        ended_at=ended_at.isoformat() if ended_at and hasattr(ended_at, "isoformat") else None,
        duration_seconds=incident["duration_seconds"],
        calls_affected=incident["calls_affected"],
        cost_delta_cents=float(cost_delta) if cost_delta else 0.0,
        has_replay_data=has_replay_data,
    )


@router.get("/{incident_id}/timeline")
async def get_replay_timeline(
    request: Request,
    incident_id: str,
    limit: int = Query(100, ge=10, le=500, description="Maximum items to return"),
    auth: AuthorityResult = Depends(require_replay_read),
    session=Depends(get_sync_session_dep),
):
    """
    Get full timeline for an incident (unpaginated for scrubbing UI).

    Returns all replay items in chronological order for
    timeline scrubbing and playback visualization.

    This endpoint is READ-ONLY.

    RBAC: Requires read:replay permission
    Tenant Isolation: Enforced
    """
    # Fetch incident via L4 dispatch
    incident = await _dispatch_replay(
        session,
        "get_incident_no_tenant_check",
        incident_id=incident_id,
    )

    if not incident:
        raise HTTPException(status_code=404, detail=f"Incident {incident_id} not found")

    # Enforce tenant isolation
    verify_tenant_access(auth, incident["tenant_id"])

    # Get related call IDs
    related_call_ids = _get_related_call_ids(incident)

    # Fetch all proxy calls for incident via L4 dispatch
    calls = await _dispatch_replay(
        session,
        "get_proxy_calls_for_timeline",
        call_ids=related_call_ids,
        limit=limit,
    )

    # Fetch all incident events via L4 dispatch
    events = await _dispatch_replay(
        session,
        "get_all_incident_events",
        incident_id=incident_id,
    )

    # Convert to replay items
    call_items = [_proxy_call_row_to_replay_item(c) for c in calls]
    event_items = [_incident_event_row_to_replay_item(e) for e in events]

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
        started_at = incident["started_at"]
        ended_at = incident["ended_at"] or incident["started_at"]
        start_time = started_at.isoformat() if hasattr(started_at, "isoformat") else str(started_at)
        end_time = ended_at.isoformat() if hasattr(ended_at, "isoformat") else str(ended_at)

    return wrap_dict({
        "incident_id": incident["id"],
        "incident_title": incident["title"],
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
    session=Depends(get_sync_session_dep),
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
    # Fetch incident first (for tenant check) via L4 dispatch
    incident = await _dispatch_replay(
        session,
        "get_incident_no_tenant_check",
        incident_id=incident_id,
    )

    if not incident:
        raise HTTPException(status_code=404, detail=f"Incident {incident_id} not found")

    # Enforce tenant isolation
    verify_tenant_access(auth, incident["tenant_id"])

    # Try to find as ProxyCall via L4 dispatch
    call = await _dispatch_replay(
        session,
        "get_proxy_call_by_id",
        call_id=item_id,
    )

    if call:
        # Verify call belongs to incident
        related_ids = _get_related_call_ids(incident)
        if call["id"] not in related_ids:
            raise HTTPException(status_code=404, detail=f"Item {item_id} not in incident {incident_id}")

        category = _categorize_proxy_call_row(call)
        created_at = call.get("created_at")
        timestamp = created_at.isoformat() if hasattr(created_at, "isoformat") else str(created_at)

        # Build explanation based on category
        if category == ReplayCategory.INPUT:
            explanation = {
                "what_agent_saw": {
                    "endpoint": call.get("endpoint"),
                    "model": call.get("model"),
                    "request_hash": call.get("request_hash"),
                    "note": "The agent received this request from the upstream system.",
                },
                "context": {
                    "user_id": call.get("user_id"),
                    "api_key_id": call.get("api_key_id"),
                    "tenant_id": call.get("tenant_id"),
                },
            }
        elif category == ReplayCategory.DECISION:
            decisions = _get_policy_decisions(call)
            explanation = {
                "why_decision": {
                    "was_blocked": call.get("was_blocked"),
                    "block_reason": call.get("block_reason"),
                    "guardrails_evaluated": len(decisions),
                    "guardrails_passed": sum(1 for d in decisions if d.get("passed", True)),
                },
                "policy_details": decisions,
                "note": "The system evaluated these guardrails before allowing the request.",
            }
        else:  # ACTION
            cost_cents_val = call.get("cost_cents")
            explanation = {
                "what_executed": {
                    "endpoint": call.get("endpoint"),
                    "model": call.get("model"),
                    "status_code": call.get("status_code"),
                    "latency_ms": call.get("latency_ms"),
                },
                "result": {
                    "input_tokens": call.get("input_tokens"),
                    "output_tokens": call.get("output_tokens"),
                    "cost_cents": float(cost_cents_val) if cost_cents_val else 0,
                    "error_code": call.get("error_code"),
                },
                "note": "This is the actual API call that was executed.",
            }

        return wrap_dict({
            "item_id": item_id,
            "item_type": "proxy_call",
            "category": category.value,
            "timestamp": timestamp,
            "explanation": explanation,
            "is_immutable": True,
        })

    # Try to find as IncidentEvent via L4 dispatch
    event = await _dispatch_replay(
        session,
        "get_incident_event_by_id",
        event_id=item_id,
        incident_id=incident_id,
    )

    if event:
        created_at = event.get("created_at")
        timestamp = created_at.isoformat() if hasattr(created_at, "isoformat") else str(created_at)

        return wrap_dict({
            "item_id": item_id,
            "item_type": "incident_event",
            "category": "event",
            "timestamp": timestamp,
            "explanation": {
                "event_type": event.get("event_type"),
                "description": event.get("description"),
                "data": _get_event_data(event),
                "note": "This is an incident timeline event.",
            },
            "is_immutable": True,
        })

    raise HTTPException(status_code=404, detail=f"Item {item_id} not found")
