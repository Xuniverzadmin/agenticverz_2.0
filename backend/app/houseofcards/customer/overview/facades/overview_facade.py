# Layer: L4 — Domain Services
# AUDIENCE: CUSTOMER
# Role: Overview Facade - Centralized access to overview domain operations
# Pattern: app/houseofcards/customer/overview/facades/overview_facade.py
# Reference: DIRECTORY_REORGANIZATION_PLAN.md

"""
Overview Facade (L4 Domain Logic)

This facade provides the external interface for overview operations.
All overview APIs MUST use this facade instead of directly importing
models or executing queries in L2.

Why This Facade Exists:
- Prevents L2→L6 layer violations (direct model imports)
- Centralizes overview aggregation logic
- Single point for tenant-scoped queries
- Maintains projection-only architecture

ARCHITECTURAL RULE:
- Overview DOES NOT own any tables
- Overview aggregates/projects from existing domains
- All operations are READ-ONLY

L2 API Routes:
- GET /api/v1/overview/highlights      → O1 system pulse & domain counts
- GET /api/v1/overview/decisions       → O2 pending decisions queue
- GET /api/v1/overview/decisions/count → O2 decisions count summary
- GET /api/v1/overview/costs           → O2 cost intelligence summary
- GET /api/v1/overview/recovery-stats  → O3 recovery statistics

Usage:
    from app.houseofcards.customer.overview.facades.overview_facade import get_overview_facade

    facade = get_overview_facade()

    # Get system highlights
    highlights = await facade.get_highlights(session, tenant_id)
"""

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

# L6 model imports (allowed for L4)
from app.models.audit_ledger import AuditLedger
from app.models.killswitch import Incident, IncidentLifecycleState
from app.models.policy import PolicyProposal
from app.models.policy_control_plane import Limit, LimitBreach, LimitCategory
from app.models.tenant import WorkerRun

logger = logging.getLogger("nova.houseofcards.customer.overview.facades")


# =============================================================================
# Data Classes
# =============================================================================


@dataclass
class SystemPulse:
    """System health pulse summary."""
    status: str  # HEALTHY, ATTENTION_NEEDED, CRITICAL
    active_incidents: int
    pending_decisions: int
    recent_breaches: int
    live_runs: int
    queued_runs: int

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "active_incidents": self.active_incidents,
            "pending_decisions": self.pending_decisions,
            "recent_breaches": self.recent_breaches,
            "live_runs": self.live_runs,
            "queued_runs": self.queued_runs,
        }


@dataclass
class DomainCount:
    """Count for a specific domain."""
    domain: str
    total: int
    pending: int
    critical: int

    def to_dict(self) -> Dict[str, Any]:
        return {
            "domain": self.domain,
            "total": self.total,
            "pending": self.pending,
            "critical": self.critical,
        }


@dataclass
class HighlightsResult:
    """Result from get_highlights."""
    pulse: SystemPulse
    domain_counts: List[DomainCount]
    last_activity_at: Optional[datetime]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "pulse": self.pulse.to_dict(),
            "domain_counts": [dc.to_dict() for dc in self.domain_counts],
            "last_activity_at": self.last_activity_at.isoformat() if self.last_activity_at else None,
        }


@dataclass
class DecisionItem:
    """A pending decision requiring human action."""
    source_domain: str
    entity_type: str
    entity_id: str
    decision_type: str
    priority: str
    summary: str
    created_at: datetime

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source_domain": self.source_domain,
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "decision_type": self.decision_type,
            "priority": self.priority,
            "summary": self.summary,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


@dataclass
class DecisionsResult:
    """Result from get_decisions."""
    items: List[DecisionItem]
    total: int
    has_more: bool
    filters_applied: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "items": [item.to_dict() for item in self.items],
            "total": self.total,
            "has_more": self.has_more,
            "filters_applied": self.filters_applied,
        }


@dataclass
class CostPeriod:
    """Time period for cost calculation."""
    start: datetime
    end: datetime

    def to_dict(self) -> Dict[str, Any]:
        return {
            "start": self.start.isoformat(),
            "end": self.end.isoformat(),
        }


@dataclass
class LimitCostItem:
    """Single limit with cost status."""
    limit_id: str
    name: str
    category: str
    max_value: float
    used_value: float
    remaining_value: float
    status: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "limit_id": self.limit_id,
            "name": self.name,
            "category": self.category,
            "max_value": self.max_value,
            "used_value": self.used_value,
            "remaining_value": self.remaining_value,
            "status": self.status,
        }


@dataclass
class CostsResult:
    """Result from get_costs."""
    currency: str
    period: CostPeriod
    llm_run_cost: float
    limits: List[LimitCostItem]
    breach_count: int
    total_overage: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "currency": self.currency,
            "period": self.period.to_dict(),
            "actuals": {"llm_run_cost": self.llm_run_cost},
            "limits": [lim.to_dict() for lim in self.limits],
            "violations": {
                "breach_count": self.breach_count,
                "total_overage": self.total_overage,
            },
        }


@dataclass
class DecisionsCountResult:
    """Result from get_decisions_count."""
    total: int
    by_domain: Dict[str, int]
    by_priority: Dict[str, int]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total": self.total,
            "by_domain": self.by_domain,
            "by_priority": self.by_priority,
        }


@dataclass
class RecoveryStatsResult:
    """Result from get_recovery_stats."""
    total_incidents: int
    recovered: int
    pending_recovery: int
    failed_recovery: int
    recovery_rate_pct: float
    period: CostPeriod

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_incidents": self.total_incidents,
            "recovered": self.recovered,
            "pending_recovery": self.pending_recovery,
            "failed_recovery": self.failed_recovery,
            "recovery_rate_pct": self.recovery_rate_pct,
            "period": self.period.to_dict(),
        }


# =============================================================================
# Facade Implementation
# =============================================================================


class OverviewFacade:
    """
    Overview Facade - Centralized access to overview domain operations.

    This facade aggregates data from multiple domains:
    - Activity (WorkerRun)
    - Incidents (Incident)
    - Policies (PolicyProposal, Limit, LimitBreach)
    - Logs (AuditLedger)
    """

    async def get_highlights(
        self,
        session: AsyncSession,
        tenant_id: str,
    ) -> HighlightsResult:
        """
        Get system highlights (O1).

        Returns system pulse and domain counts.
        """
        now = datetime.utcnow()
        last_24h = now - timedelta(hours=24)

        # Incident counts
        incident_stmt = select(
            func.count(Incident.id).label("total"),
            func.sum(case((Incident.lifecycle_state == IncidentLifecycleState.ACTIVE.value, 1), else_=0)).label("pending"),
            func.sum(
                case(
                    (
                        and_(
                            Incident.lifecycle_state == IncidentLifecycleState.ACTIVE.value,
                            Incident.severity.in_(["critical", "high"]),
                        ),
                        1,
                    ),
                    else_=0,
                )
            ).label("critical"),
        ).where(Incident.tenant_id == tenant_id)
        incident_result = await session.execute(incident_stmt)
        incident_row = incident_result.one()

        # Policy proposal counts
        proposal_stmt = select(
            func.count(PolicyProposal.id).label("total"),
            func.count(case((PolicyProposal.status == "draft", 1))).label("pending"),
        ).where(PolicyProposal.tenant_id == tenant_id)
        proposal_result = await session.execute(proposal_stmt)
        proposal_row = proposal_result.one()

        # Limit breach counts (last 24h) - DEFENSIVE QUERY
        try:
            breach_stmt = select(
                func.count(LimitBreach.id).label("recent"),
            ).where(
                LimitBreach.tenant_id == tenant_id,
                LimitBreach.breached_at >= last_24h,
            )
            breach_result = await session.execute(breach_stmt)
            breach_row = breach_result.one()
            recent_breach_count = breach_row.recent or 0
        except Exception as breach_err:
            logger.warning(f"[OVERVIEW] limit_breaches query failed (degrading): {breach_err}")
            recent_breach_count = 0

        # Last activity
        last_activity_stmt = select(func.max(AuditLedger.created_at)).where(AuditLedger.tenant_id == tenant_id)
        last_activity_result = await session.execute(last_activity_stmt)
        last_activity_at = last_activity_result.scalar()

        # Activity metrics: live and queued runs
        activity_stmt = select(
            func.sum(case((WorkerRun.status == "running", 1), else_=0)).label("live"),
            func.sum(case((WorkerRun.status == "queued", 1), else_=0)).label("queued"),
            func.count(WorkerRun.id).label("total"),
        ).where(WorkerRun.tenant_id == tenant_id)
        activity_result = await session.execute(activity_stmt)
        activity_row = activity_result.one()
        live_runs = activity_row.live or 0
        queued_runs = activity_row.queued or 0

        # Calculate system pulse
        active_incidents = incident_row.pending or 0
        pending_decisions = (incident_row.pending or 0) + (proposal_row.pending or 0)
        recent_breaches = recent_breach_count

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
            live_runs=live_runs,
            queued_runs=queued_runs,
        )

        domain_counts = [
            DomainCount(
                domain="Activity",
                total=activity_row.total or 0,
                pending=queued_runs,
                critical=0,
            ),
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
                critical=recent_breaches,
            ),
        ]

        return HighlightsResult(
            pulse=pulse,
            domain_counts=domain_counts,
            last_activity_at=last_activity_at,
        )

    async def get_decisions(
        self,
        session: AsyncSession,
        tenant_id: str,
        source_domain: Optional[str] = None,
        priority: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> DecisionsResult:
        """
        Get pending decisions (O2).

        Returns decisions queue from incidents and policy proposals.
        """
        filters_applied: Dict[str, Any] = {"tenant_id": tenant_id}
        if source_domain:
            filters_applied["source_domain"] = source_domain
        if priority:
            filters_applied["priority"] = priority

        items: List[DecisionItem] = []

        # 1. Project pending incidents (ACTIVE = needs ACK)
        if source_domain is None or source_domain == "INCIDENT":
            incident_stmt = (
                select(Incident)
                .where(
                    Incident.tenant_id == tenant_id,
                    Incident.lifecycle_state == IncidentLifecycleState.ACTIVE.value,
                )
                .order_by(Incident.created_at.desc())
            )
            incident_result = await session.execute(incident_stmt)
            incidents = incident_result.scalars().all()

            for inc in incidents:
                inc_priority = (
                    "CRITICAL" if inc.severity in ["critical"] else ("HIGH" if inc.severity in ["high"] else "MEDIUM")
                )
                if priority is not None and inc_priority != priority:
                    continue

                inc_created = inc.created_at
                if inc_created and inc_created.tzinfo is not None:
                    inc_created = inc_created.replace(tzinfo=None)

                items.append(
                    DecisionItem(
                        source_domain="INCIDENT",
                        entity_type="INCIDENT",
                        entity_id=str(inc.id),
                        decision_type="ACK",
                        priority=inc_priority,
                        summary=inc.title or f"Incident {inc.id}",
                        created_at=inc_created,
                    )
                )

        # 2. Project pending policy proposals (draft = needs approval)
        if source_domain is None or source_domain == "POLICY":
            proposal_stmt = (
                select(PolicyProposal)
                .where(
                    PolicyProposal.tenant_id == tenant_id,
                    PolicyProposal.status == "draft",
                )
                .order_by(PolicyProposal.created_at.desc())
            )
            proposal_result = await session.execute(proposal_stmt)
            proposals = proposal_result.scalars().all()

            for prop in proposals:
                prop_priority = "MEDIUM"
                if priority is not None and prop_priority != priority:
                    continue

                prop_created = prop.created_at
                if prop_created and prop_created.tzinfo is not None:
                    prop_created = prop_created.replace(tzinfo=None)

                items.append(
                    DecisionItem(
                        source_domain="POLICY",
                        entity_type="POLICY_PROPOSAL",
                        entity_id=str(prop.id),
                        decision_type="APPROVE",
                        priority=prop_priority,
                        summary=prop.proposal_name,
                        created_at=prop_created,
                    )
                )

        # Sort by created_at descending
        items.sort(key=lambda x: x.created_at, reverse=True)

        # Apply pagination
        total = len(items)
        paginated = items[offset : offset + limit]
        has_more = offset + len(paginated) < total

        return DecisionsResult(
            items=paginated,
            total=total,
            has_more=has_more,
            filters_applied=filters_applied,
        )

    async def get_costs(
        self,
        session: AsyncSession,
        tenant_id: str,
        period_days: int = 30,
    ) -> CostsResult:
        """
        Get cost intelligence (O2).

        Returns realized costs and budget status.
        """
        now = datetime.utcnow()
        period_start = now - timedelta(days=period_days)

        # 1. Calculate actual LLM cost from worker_runs
        cost_stmt = select(func.coalesce(func.sum(WorkerRun.cost_cents), 0).label("total_cost_cents")).where(
            WorkerRun.tenant_id == tenant_id,
            WorkerRun.created_at >= period_start,
        )
        cost_result = await session.execute(cost_stmt)
        total_cost_cents = cost_result.scalar() or 0
        llm_run_cost = float(total_cost_cents) / 100.0

        # 2. Get budget limits
        limits_stmt = (
            select(Limit)
            .where(
                Limit.tenant_id == tenant_id,
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
            used_val = llm_run_cost
            remaining_val = max(0, max_val - used_val)

            if used_val >= max_val:
                status = "BREACHED"
            elif used_val >= max_val * 0.8:
                status = "NEAR_THRESHOLD"
            else:
                status = "OK"

            limit_items.append(
                LimitCostItem(
                    limit_id=lim.id,
                    name=lim.name,
                    category=lim.limit_category,
                    max_value=max_val,
                    used_value=used_val,
                    remaining_value=remaining_val,
                    status=status,
                )
            )

        # 3. Get breach statistics - DEFENSIVE QUERY
        try:
            breach_stmt = select(
                func.count(LimitBreach.id).label("breach_count"),
                func.coalesce(func.sum(LimitBreach.value_at_breach - LimitBreach.limit_value), 0).label("total_overage"),
            ).where(
                LimitBreach.tenant_id == tenant_id,
                LimitBreach.breached_at >= period_start,
            )
            breach_result = await session.execute(breach_stmt)
            breach_row = breach_result.one()
            breach_count = breach_row.breach_count or 0
            total_overage = max(0, float(breach_row.total_overage or 0))
        except Exception as breach_err:
            logger.warning(f"[OVERVIEW] limit_breaches cost query failed (degrading): {breach_err}")
            breach_count = 0
            total_overage = 0.0

        return CostsResult(
            currency="USD",
            period=CostPeriod(start=period_start, end=now),
            llm_run_cost=llm_run_cost,
            limits=limit_items,
            breach_count=breach_count,
            total_overage=total_overage,
        )

    async def get_decisions_count(
        self,
        session: AsyncSession,
        tenant_id: str,
    ) -> DecisionsCountResult:
        """
        Get decisions count summary (O2).

        Returns count of pending decisions by domain and priority.
        """
        # Count incidents by severity
        incident_stmt = select(
            func.count(Incident.id).label("total"),
            func.sum(case((Incident.severity == "critical", 1), else_=0)).label("critical"),
            func.sum(case((Incident.severity == "high", 1), else_=0)).label("high"),
            func.sum(case((Incident.severity.in_(["medium", "low"]), 1), else_=0)).label("other"),
        ).where(
            Incident.tenant_id == tenant_id,
            Incident.lifecycle_state == IncidentLifecycleState.ACTIVE.value,
        )
        incident_result = await session.execute(incident_stmt)
        inc_row = incident_result.one()

        # Count policy proposals (all draft = MEDIUM priority)
        proposal_stmt = select(func.count(PolicyProposal.id).label("total")).where(
            PolicyProposal.tenant_id == tenant_id,
            PolicyProposal.status == "draft",
        )
        proposal_result = await session.execute(proposal_stmt)
        prop_total = proposal_result.scalar() or 0

        # Build response
        incident_total = inc_row.total or 0
        policy_total = prop_total
        total = incident_total + policy_total

        by_domain = {
            "INCIDENT": incident_total,
            "POLICY": policy_total,
        }

        by_priority = {
            "CRITICAL": inc_row.critical or 0,
            "HIGH": inc_row.high or 0,
            "MEDIUM": (inc_row.other or 0) + policy_total,
            "LOW": 0,
        }

        return DecisionsCountResult(
            total=total,
            by_domain=by_domain,
            by_priority=by_priority,
        )

    async def get_recovery_stats(
        self,
        session: AsyncSession,
        tenant_id: str,
        period_days: int = 30,
    ) -> RecoveryStatsResult:
        """
        Get recovery statistics (O3).

        Returns recovery statistics from incident lifecycle.
        """
        now = datetime.utcnow()
        period_start = now - timedelta(days=period_days)

        # Count incidents by lifecycle state
        stmt = select(
            func.count(Incident.id).label("total"),
            func.sum(case((Incident.lifecycle_state == IncidentLifecycleState.RESOLVED.value, 1), else_=0)).label("recovered"),
            func.sum(
                case(
                    (Incident.lifecycle_state.in_([IncidentLifecycleState.ACTIVE.value, "investigating"]), 1), else_=0
                )
            ).label("pending"),
            func.sum(case((Incident.lifecycle_state == "failed", 1), else_=0)).label("failed"),
        ).where(
            Incident.tenant_id == tenant_id,
            Incident.created_at >= period_start,
        )
        result = await session.execute(stmt)
        row = result.one()

        total = row.total or 0
        recovered = row.recovered or 0
        pending = row.pending or 0
        failed = row.failed or 0

        recovery_rate = (recovered / total * 100.0) if total > 0 else 0.0

        return RecoveryStatsResult(
            total_incidents=total,
            recovered=recovered,
            pending_recovery=pending,
            failed_recovery=failed,
            recovery_rate_pct=round(recovery_rate, 2),
            period=CostPeriod(start=period_start, end=now),
        )


# =============================================================================
# Singleton Instance
# =============================================================================

_overview_facade: Optional[OverviewFacade] = None


def get_overview_facade() -> OverviewFacade:
    """Get the singleton OverviewFacade instance."""
    global _overview_facade
    if _overview_facade is None:
        _overview_facade = OverviewFacade()
    return _overview_facade


__all__ = [
    # Facade
    "OverviewFacade",
    "get_overview_facade",
    # Result types
    "SystemPulse",
    "DomainCount",
    "HighlightsResult",
    "DecisionItem",
    "DecisionsResult",
    "CostPeriod",
    "LimitCostItem",
    "CostsResult",
    "DecisionsCountResult",
    "RecoveryStatsResult",
]
