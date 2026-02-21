# capability_id: CAP-012
# Layer: L6 — Domain Driver
# AUDIENCE: CUSTOMER
# Role: Overview Facade Driver - Pure data access for overview aggregation
# Temporal:
#   Trigger: api (via L5 engine)
#   Execution: async
# Data Access:
#   Reads: Incident, PolicyProposal, Limit, LimitBreach, WorkerRun, AuditLedger
#   Writes: none (read-only projection)
# Database:
#   Scope: cross-domain (reads from multiple domain tables)
#   Models: Incident, PolicyProposal, Limit, LimitBreach, WorkerRun, AuditLedger
# Callers: overview_facade.py (L5)
# Allowed Imports: L6, L7 (models)
# Reference: PIN-470
#
# ARCHITECTURAL RULE:
# This driver ONLY performs data access - NO business logic.
# Returns raw query results as typed snapshots.
# The engine (L5) composes business results from these snapshots.
#
# PHASE 2.5B EXTRACTION (2026-01-24):
# Extracted from overview_facade.py to enforce L5/L6 separation.
# All sqlalchemy runtime imports and model imports are here (L6).

"""
Overview Facade Driver (L6 Data Access)

This driver contains all database queries for the overview domain.
It returns snapshot dataclasses to the facade (L4) for business logic composition.

ARCHITECTURAL RULE:
- This driver ONLY performs data access
- NO business logic (no severity thresholds, no status calculations)
- Returns raw query results as typed snapshots
- The facade composes business results from these snapshots
"""

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, List, Optional

from sqlalchemy import and_, case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

# L7 model imports (allowed in L6)
from app.models.audit_ledger import AuditLedger
from app.models.killswitch import Incident, IncidentLifecycleState
from app.models.policy import PolicyProposal
from app.models.policy_control_plane import Limit, LimitBreach, LimitCategory
from app.models.tenant import WorkerRun

logger = logging.getLogger("nova.hoc.cus.overview.L6_drivers")


# =============================================================================
# Snapshot Dataclasses (Driver Output)
# =============================================================================


@dataclass
class IncidentCountSnapshot:
    """Raw incident count data from DB."""

    total: int
    active: int
    critical: int


@dataclass
class ProposalCountSnapshot:
    """Raw policy proposal count data from DB."""

    total: int
    pending: int


@dataclass
class BreachCountSnapshot:
    """Raw limit breach count data from DB."""

    recent: int


@dataclass
class RunCountSnapshot:
    """Raw worker run count data from DB."""

    total: int
    running: int
    queued: int


@dataclass
class AuditCountSnapshot:
    """Raw audit count data from DB."""

    last_activity_at: Optional[datetime]


@dataclass
class IncidentSnapshot:
    """Snapshot of a single incident for decisions projection."""

    id: str
    title: Optional[str]
    severity: Optional[str]
    lifecycle_state: str
    created_at: Optional[datetime]


@dataclass
class ProposalSnapshot:
    """Snapshot of a single policy proposal for decisions projection."""

    id: str
    proposal_name: str
    status: str
    created_at: Optional[datetime]


@dataclass
class LimitSnapshot:
    """Snapshot of a single limit for cost projection."""

    id: str
    name: str
    limit_category: str
    max_value: float
    status: str


@dataclass
class RunCostSnapshot:
    """Snapshot of run cost data from DB."""

    total_cost_cents: int


@dataclass
class BreachStatsSnapshot:
    """Snapshot of breach statistics from DB."""

    breach_count: int
    total_overage: float


@dataclass
class IncidentDecisionCountSnapshot:
    """Snapshot of incident counts by severity for decisions count."""

    total: int
    critical: int
    high: int
    other: int


@dataclass
class RecoverySnapshot:
    """Snapshot of incident recovery data from DB."""

    total: int
    recovered: int
    pending: int
    failed: int


# =============================================================================
# Driver Implementation
# =============================================================================


class OverviewFacadeDriver:
    """
    Overview Facade Driver - Pure data access layer.

    All methods execute DB queries and return snapshot dataclasses.
    No business logic or status calculations.
    """

    async def fetch_incident_counts(
        self,
        session: AsyncSession,
        tenant_id: str,
    ) -> IncidentCountSnapshot:
        """Fetch incident counts from DB."""
        stmt = select(
            func.count(Incident.id).label("total"),
            func.sum(
                case((Incident.lifecycle_state == IncidentLifecycleState.ACTIVE.value, 1), else_=0)
            ).label("active"),
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

        result = await session.execute(stmt)
        row = result.one()

        return IncidentCountSnapshot(
            total=row.total or 0,
            active=row.active or 0,
            critical=row.critical or 0,
        )

    async def fetch_proposal_counts(
        self,
        session: AsyncSession,
        tenant_id: str,
    ) -> ProposalCountSnapshot:
        """Fetch policy proposal counts from DB."""
        stmt = select(
            func.count(PolicyProposal.id).label("total"),
            func.count(case((PolicyProposal.status == "draft", 1))).label("pending"),
        ).where(PolicyProposal.tenant_id == tenant_id)

        result = await session.execute(stmt)
        row = result.one()

        return ProposalCountSnapshot(
            total=row.total or 0,
            pending=row.pending or 0,
        )

    async def fetch_breach_counts(
        self,
        session: AsyncSession,
        tenant_id: str,
        since: datetime,
    ) -> BreachCountSnapshot:
        """Fetch limit breach counts from DB (defensive query)."""
        try:
            stmt = select(
                func.count(LimitBreach.id).label("recent"),
            ).where(
                LimitBreach.tenant_id == tenant_id,
                LimitBreach.breached_at >= since,
            )
            result = await session.execute(stmt)
            row = result.one()
            return BreachCountSnapshot(recent=row.recent or 0)
        except Exception as err:
            logger.warning(f"[OVERVIEW_DRIVER] limit_breaches query failed (degrading): {err}")
            return BreachCountSnapshot(recent=0)

    async def fetch_run_counts(
        self,
        session: AsyncSession,
        tenant_id: str,
    ) -> RunCountSnapshot:
        """Fetch worker run counts from DB."""
        stmt = select(
            func.count(WorkerRun.id).label("total"),
            func.sum(case((WorkerRun.status == "running", 1), else_=0)).label("running"),
            func.sum(case((WorkerRun.status == "queued", 1), else_=0)).label("queued"),
        ).where(WorkerRun.tenant_id == tenant_id)

        result = await session.execute(stmt)
        row = result.one()

        return RunCountSnapshot(
            total=row.total or 0,
            running=row.running or 0,
            queued=row.queued or 0,
        )

    async def fetch_last_activity(
        self,
        session: AsyncSession,
        tenant_id: str,
    ) -> AuditCountSnapshot:
        """Fetch last activity timestamp from audit ledger."""
        stmt = select(func.max(AuditLedger.created_at)).where(AuditLedger.tenant_id == tenant_id)
        result = await session.execute(stmt)
        last_activity_at = result.scalar()

        return AuditCountSnapshot(last_activity_at=last_activity_at)

    async def fetch_pending_incidents(
        self,
        session: AsyncSession,
        tenant_id: str,
    ) -> List[IncidentSnapshot]:
        """Fetch pending incidents for decisions projection."""
        stmt = (
            select(Incident)
            .where(
                Incident.tenant_id == tenant_id,
                Incident.lifecycle_state == IncidentLifecycleState.ACTIVE.value,
            )
            .order_by(Incident.created_at.desc())
        )
        result = await session.execute(stmt)
        incidents = result.scalars().all()

        return [
            IncidentSnapshot(
                id=str(inc.id),
                title=inc.title,
                severity=inc.severity,
                lifecycle_state=inc.lifecycle_state,
                created_at=inc.created_at,
            )
            for inc in incidents
        ]

    async def fetch_pending_proposals(
        self,
        session: AsyncSession,
        tenant_id: str,
    ) -> List[ProposalSnapshot]:
        """Fetch pending policy proposals for decisions projection."""
        stmt = (
            select(PolicyProposal)
            .where(
                PolicyProposal.tenant_id == tenant_id,
                PolicyProposal.status == "draft",
            )
            .order_by(PolicyProposal.created_at.desc())
        )
        result = await session.execute(stmt)
        proposals = result.scalars().all()

        return [
            ProposalSnapshot(
                id=str(prop.id),
                proposal_name=prop.proposal_name,
                status=prop.status,
                created_at=prop.created_at,
            )
            for prop in proposals
        ]

    async def fetch_run_cost(
        self,
        session: AsyncSession,
        tenant_id: str,
        since: datetime,
    ) -> RunCostSnapshot:
        """Fetch total LLM run cost from worker runs."""
        stmt = select(
            func.coalesce(func.sum(WorkerRun.cost_cents), 0).label("total_cost_cents")
        ).where(
            WorkerRun.tenant_id == tenant_id,
            WorkerRun.created_at >= since,
        )
        result = await session.execute(stmt)
        total_cost_cents = result.scalar() or 0

        return RunCostSnapshot(total_cost_cents=int(total_cost_cents))

    async def fetch_budget_limits(
        self,
        session: AsyncSession,
        tenant_id: str,
    ) -> List[LimitSnapshot]:
        """Fetch active budget limits."""
        stmt = (
            select(Limit)
            .where(
                Limit.tenant_id == tenant_id,
                Limit.limit_category == LimitCategory.BUDGET.value,
                Limit.status == "ACTIVE",
            )
            .order_by(Limit.name)
        )
        result = await session.execute(stmt)
        limits = result.scalars().all()

        return [
            LimitSnapshot(
                id=lim.id,
                name=lim.name,
                limit_category=lim.limit_category,
                max_value=float(lim.max_value),
                status=lim.status,
            )
            for lim in limits
        ]

    async def fetch_breach_stats(
        self,
        session: AsyncSession,
        tenant_id: str,
        since: datetime,
    ) -> BreachStatsSnapshot:
        """Fetch breach statistics (defensive query)."""
        try:
            stmt = select(
                func.count(LimitBreach.id).label("breach_count"),
                func.coalesce(
                    func.sum(LimitBreach.value_at_breach - LimitBreach.limit_value), 0
                ).label("total_overage"),
            ).where(
                LimitBreach.tenant_id == tenant_id,
                LimitBreach.breached_at >= since,
            )
            result = await session.execute(stmt)
            row = result.one()
            return BreachStatsSnapshot(
                breach_count=row.breach_count or 0,
                total_overage=max(0, float(row.total_overage or 0)),
            )
        except Exception as err:
            logger.warning(f"[OVERVIEW_DRIVER] breach stats query failed (degrading): {err}")
            return BreachStatsSnapshot(breach_count=0, total_overage=0.0)

    async def fetch_incident_decision_counts(
        self,
        session: AsyncSession,
        tenant_id: str,
    ) -> IncidentDecisionCountSnapshot:
        """Fetch incident counts by severity for decisions count."""
        stmt = select(
            func.count(Incident.id).label("total"),
            func.sum(case((Incident.severity == "critical", 1), else_=0)).label("critical"),
            func.sum(case((Incident.severity == "high", 1), else_=0)).label("high"),
            func.sum(
                case((Incident.severity.in_(["medium", "low"]), 1), else_=0)
            ).label("other"),
        ).where(
            Incident.tenant_id == tenant_id,
            Incident.lifecycle_state == IncidentLifecycleState.ACTIVE.value,
        )
        result = await session.execute(stmt)
        row = result.one()

        return IncidentDecisionCountSnapshot(
            total=row.total or 0,
            critical=row.critical or 0,
            high=row.high or 0,
            other=row.other or 0,
        )

    async def fetch_proposal_count(
        self,
        session: AsyncSession,
        tenant_id: str,
    ) -> int:
        """Fetch count of pending policy proposals."""
        stmt = select(func.count(PolicyProposal.id).label("total")).where(
            PolicyProposal.tenant_id == tenant_id,
            PolicyProposal.status == "draft",
        )
        result = await session.execute(stmt)
        return result.scalar() or 0

    async def fetch_recovery_stats(
        self,
        session: AsyncSession,
        tenant_id: str,
        since: datetime,
    ) -> RecoverySnapshot:
        """Fetch incident recovery statistics."""
        stmt = select(
            func.count(Incident.id).label("total"),
            func.sum(
                case((Incident.lifecycle_state == IncidentLifecycleState.RESOLVED.value, 1), else_=0)
            ).label("recovered"),
            func.sum(
                case(
                    (
                        Incident.lifecycle_state.in_(
                            [IncidentLifecycleState.ACTIVE.value, "investigating"]
                        ),
                        1,
                    ),
                    else_=0,
                )
            ).label("pending"),
            func.sum(case((Incident.lifecycle_state == "failed", 1), else_=0)).label("failed"),
        ).where(
            Incident.tenant_id == tenant_id,
            Incident.created_at >= since,
        )
        result = await session.execute(stmt)
        row = result.one()

        return RecoverySnapshot(
            total=row.total or 0,
            recovered=row.recovered or 0,
            pending=row.pending or 0,
            failed=row.failed or 0,
        )


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    # Driver
    "OverviewFacadeDriver",
    # Snapshots
    "IncidentCountSnapshot",
    "ProposalCountSnapshot",
    "BreachCountSnapshot",
    "RunCountSnapshot",
    "AuditCountSnapshot",
    "IncidentSnapshot",
    "ProposalSnapshot",
    "LimitSnapshot",
    "RunCostSnapshot",
    "BreachStatsSnapshot",
    "IncidentDecisionCountSnapshot",
    "RecoverySnapshot",
]
