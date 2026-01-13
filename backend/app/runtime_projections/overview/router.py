# Layer: L2 — Product APIs
# Product: ai-console
# Temporal:
#   Trigger: HTTP request
#   Execution: async
# Role: Overview O2 Runtime Projection API — PROJECTION-ONLY (OVW-RT-O2)
# Callers: Customer Console Overview Views
# Allowed Imports: L3, L4, L6
# Forbidden Imports: L1, L5
# Reference: PIN-413 Domain Design — Overview & Logs (CORRECTED)

"""
OVW-RT-O2 — Overview Runtime Projection Contract (PROJECTION-ONLY)

ARCHITECTURAL RULE:
- Overview DOES NOT own any tables
- Overview aggregates/projects from existing domains
- All endpoints are READ-ONLY

Data Sources (existing tables — not owned by Overview):
- incidents: For active incident counts, pending acknowledgments
- policy_proposals: For draft proposals pending approval
- limit_breaches: For recent breach events
- audit_ledger: For recent governance actions

Contract Rules:
- Tenant isolation is mandatory (from auth_context)
- All queries are READ-ONLY
- No write paths, no queues, no state transitions
- If an action exists, it must already exist elsewhere
"""

from datetime import datetime, timedelta, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import select, func, case, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_async_session_dep
from app.auth.tenant_auth import TenantContext, get_tenant_context

# Import existing domain models (Overview does NOT own these)
from app.models.killswitch import Incident, IncidentLifecycleState
from app.models.policy import PolicyProposal
from app.models.policy_control_plane import Limit, LimitBreach, LimitCategory
from app.models.audit_ledger import AuditLedger
from app.models.tenant import WorkerRun

router = APIRouter(prefix="/overview", tags=["runtime-overview"])


# =============================================================================
# Response Models — Cross-Domain Highlights (OVW-RT-O2-HIGHLIGHTS)
# =============================================================================


class DomainCount(BaseModel):
    """Count for a specific domain."""
    domain: str
    total: int
    pending: int  # Items requiring human action
    critical: int  # High-priority items


class SystemPulse(BaseModel):
    """System health pulse summary."""
    status: str  # HEALTHY, ATTENTION_NEEDED, CRITICAL
    active_incidents: int
    pending_decisions: int
    recent_breaches: int  # Last 24h


class CrossDomainHighlightsResponse(BaseModel):
    """Response envelope for cross-domain highlights (O1)."""
    pulse: SystemPulse
    domain_counts: List[DomainCount]
    last_activity_at: Optional[datetime]


# =============================================================================
# Response Models — Decisions Queue (OVW-RT-O2-DECISIONS)
# =============================================================================


class DecisionItem(BaseModel):
    """A pending decision requiring human action (projection)."""
    source_domain: str  # INCIDENT, POLICY, LIMIT
    entity_type: str
    entity_id: str
    decision_type: str  # ACK, APPROVE, OVERRIDE
    priority: str  # CRITICAL, HIGH, MEDIUM, LOW
    summary: str
    created_at: datetime


class DecisionsQueueResponse(BaseModel):
    """Response envelope for decisions queue (O2)."""
    items: List[DecisionItem]
    total: int
    has_more: bool


# =============================================================================
# Response Models — Cost Intelligence (OVW-RT-O2-COSTS)
# =============================================================================


class CostPeriod(BaseModel):
    """Time period for cost calculation."""
    start: datetime
    end: datetime


class CostActuals(BaseModel):
    """Actual costs incurred."""
    llm_run_cost: float  # USD


class LimitCostItem(BaseModel):
    """Single limit with cost status."""
    limit_id: str
    name: str
    category: str  # BUDGET
    max_value: float
    used_value: float
    remaining_value: float
    status: str  # OK, NEAR_THRESHOLD, BREACHED


class CostViolations(BaseModel):
    """Cost violation summary."""
    breach_count: int
    total_overage: float  # USD


class CostIntelligenceResponse(BaseModel):
    """
    Response envelope for cost intelligence (O2).

    Cost Intelligence v2 may include policy-prevented cost attribution
    once enforcement → cost mapping is deterministic.
    """
    currency: str  # Always "USD" in v1
    period: CostPeriod
    actuals: CostActuals
    limits: List[LimitCostItem]
    violations: CostViolations


# =============================================================================
# Cross-Domain Highlights O1 Endpoint (OVW-RT-O2-HIGHLIGHTS)
# =============================================================================


@router.get("/highlights", response_model=CrossDomainHighlightsResponse)
async def get_cross_domain_highlights(
    tenant: TenantContext = Depends(get_tenant_context),
    session: AsyncSession = Depends(get_async_session_dep),
):
    """
    GET /api/v1/runtime/overview/highlights

    Cross-Domain Highlights: System pulse and domain counts.

    PROJECTION-ONLY: Aggregates from existing domain tables.
    No owned state. Read-only.
    """
    # Use naive datetime for TIMESTAMP WITHOUT TIME ZONE columns
    now = datetime.utcnow()
    last_24h = now - timedelta(hours=24)

    # Incident counts (from incidents table)
    incident_stmt = select(
        func.count(Incident.id).label("total"),
        func.sum(case(
            (Incident.lifecycle_state == IncidentLifecycleState.ACTIVE.value, 1),
            else_=0
        )).label("pending"),
        func.sum(case(
            (and_(
                Incident.lifecycle_state == IncidentLifecycleState.ACTIVE.value,
                Incident.severity.in_(["critical", "high"])
            ), 1),
            else_=0
        )).label("critical"),
    ).where(
        Incident.tenant_id == tenant.tenant_id
    )
    incident_result = await session.execute(incident_stmt)
    incident_row = incident_result.one()

    # Policy proposal counts (from policy_proposals table)
    proposal_stmt = select(
        func.count(PolicyProposal.id).label("total"),
        func.count(case(
            (PolicyProposal.status == "draft", 1)
        )).label("pending"),
    ).where(
        PolicyProposal.tenant_id == tenant.tenant_id
    )
    proposal_result = await session.execute(proposal_stmt)
    proposal_row = proposal_result.one()

    # Limit breach counts (from limit_breaches table) - last 24h
    breach_stmt = select(
        func.count(LimitBreach.id).label("recent"),
    ).where(
        LimitBreach.tenant_id == tenant.tenant_id,
        LimitBreach.breached_at >= last_24h,
    )
    breach_result = await session.execute(breach_stmt)
    breach_row = breach_result.one()

    # Last activity (most recent audit ledger entry)
    last_activity_stmt = select(
        func.max(AuditLedger.created_at)
    ).where(
        AuditLedger.tenant_id == tenant.tenant_id
    )
    last_activity_result = await session.execute(last_activity_stmt)
    last_activity_at = last_activity_result.scalar()

    # Calculate system pulse
    active_incidents = incident_row.pending or 0
    pending_decisions = (incident_row.pending or 0) + (proposal_row.pending or 0)
    recent_breaches = breach_row.recent or 0

    if incident_row.critical and incident_row.critical > 0:
        pulse_status = "CRITICAL"
    elif pending_decisions > 0 or recent_breaches > 0:
        pulse_status = "ATTENTION_NEEDED"
    else:
        pulse_status = "HEALTHY"

    pulse = SystemPulse(
        status=pulse_status,
        active_incidents=active_incidents,
        pending_decisions=pending_decisions,
        recent_breaches=recent_breaches,
    )

    domain_counts = [
        DomainCount(
            domain="Incidents",
            total=incident_row.total or 0,
            pending=incident_row.pending or 0,
            critical=incident_row.critical or 0,
        ),
        DomainCount(
            domain="Policies",
            total=proposal_row.total or 0,
            pending=proposal_row.pending or 0,
            critical=0,  # Policies don't have critical flag
        ),
    ]

    return CrossDomainHighlightsResponse(
        pulse=pulse,
        domain_counts=domain_counts,
        last_activity_at=last_activity_at,
    )


# =============================================================================
# Decisions Queue O2 Endpoint (OVW-RT-O2-DECISIONS)
# =============================================================================


@router.get("/decisions", response_model=DecisionsQueueResponse)
async def get_decisions_queue(
    source_domain: Optional[str] = Query(
        None,
        description="Filter by source domain: INCIDENT, POLICY",
        regex="^(INCIDENT|POLICY)$",
    ),
    priority: Optional[str] = Query(
        None,
        description="Filter by priority: CRITICAL, HIGH, MEDIUM, LOW",
        regex="^(CRITICAL|HIGH|MEDIUM|LOW)$",
    ),
    limit: int = Query(50, ge=1, le=100, description="Max items to return"),
    offset: int = Query(0, ge=0, description="Rows to skip"),
    tenant: TenantContext = Depends(get_tenant_context),
    session: AsyncSession = Depends(get_async_session_dep),
):
    """
    GET /api/v1/runtime/overview/decisions

    Decisions Queue: Pending items requiring human action.

    PROJECTION-ONLY: Aggregates from incidents (pending ACK) and
    policy_proposals (pending approval). Does NOT create or own
    decision state — only projects existing pending items.
    """
    items: List[DecisionItem] = []

    # 1. Project pending incidents (ACTIVE = needs ACK)
    if source_domain is None or source_domain == "INCIDENT":
        incident_stmt = (
            select(Incident)
            .where(
                Incident.tenant_id == tenant.tenant_id,
                Incident.lifecycle_state == IncidentLifecycleState.ACTIVE.value,
            )
            .order_by(Incident.created_at.desc())
        )

        incident_result = await session.execute(incident_stmt)
        incidents = incident_result.scalars().all()

        for inc in incidents:
            # Map severity to priority
            inc_priority = "CRITICAL" if inc.severity in ["critical"] else (
                "HIGH" if inc.severity in ["high"] else "MEDIUM"
            )

            # Apply priority filter if specified
            if priority is not None and inc_priority != priority:
                continue

            # Normalize datetime to naive UTC for consistent sorting
            inc_created = inc.created_at
            if inc_created and inc_created.tzinfo is not None:
                inc_created = inc_created.replace(tzinfo=None)

            items.append(DecisionItem(
                source_domain="INCIDENT",
                entity_type="INCIDENT",
                entity_id=str(inc.id),
                decision_type="ACK",
                priority=inc_priority,
                summary=inc.title or f"Incident {inc.id}",
                created_at=inc_created,
            ))

    # 2. Project pending policy proposals (draft = needs approval)
    if source_domain is None or source_domain == "POLICY":
        proposal_stmt = (
            select(PolicyProposal)
            .where(
                PolicyProposal.tenant_id == tenant.tenant_id,
                PolicyProposal.status == "draft",
            )
            .order_by(PolicyProposal.created_at.desc())
        )

        proposal_result = await session.execute(proposal_stmt)
        proposals = proposal_result.scalars().all()

        for prop in proposals:
            # Proposals default to MEDIUM priority
            prop_priority = "MEDIUM"

            # Apply priority filter if specified
            if priority is not None and prop_priority != priority:
                continue

            # Normalize datetime to naive UTC for consistent sorting
            prop_created = prop.created_at
            if prop_created and prop_created.tzinfo is not None:
                prop_created = prop_created.replace(tzinfo=None)

            items.append(DecisionItem(
                source_domain="POLICY",
                entity_type="POLICY_PROPOSAL",
                entity_id=str(prop.id),
                decision_type="APPROVE",
                priority=prop_priority,
                summary=prop.proposal_name,
                created_at=prop_created,
            ))

    # Sort by created_at descending
    items.sort(key=lambda x: x.created_at, reverse=True)

    # Apply pagination
    total = len(items)
    paginated = items[offset:offset + limit]

    return DecisionsQueueResponse(
        items=paginated,
        total=total,
        has_more=(offset + len(paginated)) < total,
    )


# =============================================================================
# Cost Intelligence O2 Endpoint (OVW-RT-O2-COSTS)
# =============================================================================


@router.get("/costs", response_model=CostIntelligenceResponse)
async def get_cost_intelligence(
    period_days: int = Query(30, ge=1, le=365, description="Period in days to calculate costs"),
    tenant: TenantContext = Depends(get_tenant_context),
    session: AsyncSession = Depends(get_async_session_dep),
):
    """
    GET /api/v1/runtime/overview/costs

    Cost Intelligence: Realized and constrained costs.

    PROJECTION-ONLY: Aggregates from limits, limit_breaches, and worker_runs.
    No owned state. Read-only. No speculation.

    V1 SCOPE:
    - Actual LLM spend (from worker_runs.cost_cents)
    - Budget limits (from limits where category=BUDGET)
    - Breach counts and overage (from limit_breaches)

    EXPLICITLY EXCLUDED (v2+):
    - "Saved cost" / policy-prevented attribution
    - Forecasts or projections
    - Synthetic attribution
    """
    # Use naive datetime for TIMESTAMP WITHOUT TIME ZONE columns
    now = datetime.utcnow()
    period_start = now - timedelta(days=period_days)

    # 1. Calculate actual LLM cost from worker_runs
    cost_stmt = select(
        func.coalesce(func.sum(WorkerRun.cost_cents), 0).label("total_cost_cents")
    ).where(
        WorkerRun.tenant_id == tenant.tenant_id,
        WorkerRun.created_at >= period_start,
    )
    cost_result = await session.execute(cost_stmt)
    total_cost_cents = cost_result.scalar() or 0
    llm_run_cost = float(total_cost_cents) / 100.0  # cents to USD

    # 2. Get budget limits with used values
    limits_stmt = (
        select(Limit)
        .where(
            Limit.tenant_id == tenant.tenant_id,
            Limit.limit_category == LimitCategory.BUDGET.value,
            Limit.status == "ACTIVE",
        )
        .order_by(Limit.name)
    )
    limits_result = await session.execute(limits_stmt)
    limits = limits_result.scalars().all()

    limit_items: List[LimitCostItem] = []
    for lim in limits:
        max_val = float(lim.max_value)
        # For budget limits, used_value is derived from actual cost
        # In v1, we use the total LLM cost as a proxy for budget usage
        used_val = llm_run_cost  # Simplified: all cost counts toward all budget limits
        remaining_val = max(0, max_val - used_val)

        # Calculate status
        if used_val >= max_val:
            status = "BREACHED"
        elif used_val >= max_val * 0.8:
            status = "NEAR_THRESHOLD"
        else:
            status = "OK"

        limit_items.append(LimitCostItem(
            limit_id=lim.id,
            name=lim.name,
            category=lim.limit_category,
            max_value=max_val,
            used_value=used_val,
            remaining_value=remaining_val,
            status=status,
        ))

    # 3. Get breach statistics from limit_breaches
    breach_stmt = select(
        func.count(LimitBreach.id).label("breach_count"),
        func.coalesce(
            func.sum(LimitBreach.value_at_breach - LimitBreach.limit_value),
            0
        ).label("total_overage"),
    ).where(
        LimitBreach.tenant_id == tenant.tenant_id,
        LimitBreach.breached_at >= period_start,
    )
    breach_result = await session.execute(breach_stmt)
    breach_row = breach_result.one()

    breach_count = breach_row.breach_count or 0
    # Overage is stored in the same unit as limit_value (could be USD, tokens, etc.)
    # For budget limits, treat as USD
    total_overage = float(breach_row.total_overage or 0)

    return CostIntelligenceResponse(
        currency="USD",
        period=CostPeriod(
            start=period_start,
            end=now,
        ),
        actuals=CostActuals(
            llm_run_cost=llm_run_cost,
        ),
        limits=limit_items,
        violations=CostViolations(
            breach_count=breach_count,
            total_overage=max(0, total_overage),  # Ensure non-negative
        ),
    )
