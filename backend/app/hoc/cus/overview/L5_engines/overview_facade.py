# Layer: L5 — Domain Engine
# AUDIENCE: CUSTOMER
# Role: Overview Engine - Centralized access to overview domain operations
# Temporal:
#   Trigger: api
#   Execution: async
# Lifecycle:
#   Emits: none
#   Subscribes: none
# Data Access:
#   Reads: incidents, policies, activity, logs (via driver)
#   Writes: none (read-only projection domain)
# Callers: L2 API routes (/api/v1/overview/*)
# Allowed Imports: L5, L6
# Forbidden Imports: L1, L2, L3, sqlalchemy (runtime)
# Reference: PIN-470
#
# ARCHITECTURAL RULE:
# Overview is a PROJECTION domain - it aggregates from other domains.
# It DOES NOT own any tables. All operations are READ-ONLY.
#
# PHASE 2.5B EXTRACTION (2026-01-24):
# All DB operations extracted to overview_facade_driver.py (L6).
# This engine now delegates to driver for data access and composes business results.

"""
Overview Engine (L5 Domain Logic)

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
- All DB access is delegated to overview_facade_driver.py (L6)

L2 API Routes:
- GET /api/v1/overview/highlights      → O1 system pulse & domain counts
- GET /api/v1/overview/decisions       → O2 pending decisions queue
- GET /api/v1/overview/decisions/count → O2 decisions count summary
- GET /api/v1/overview/costs           → O2 cost intelligence summary
- GET /api/v1/overview/recovery-stats  → O3 recovery statistics

Usage:
    from app.hoc.cus.overview.L5_engines.overview_facade import get_overview_facade

    facade = get_overview_facade()

    # Get system highlights
    highlights = await facade.get_highlights(session, tenant_id)
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from app.hoc.cus.hoc_spine.services.time import utc_now
from app.hoc.cus.overview.L6_drivers.overview_facade_driver import (
    OverviewFacadeDriver,
)

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger("nova.hoc.cus.overview.L5_engines")


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

    All DB access is delegated to OverviewFacadeDriver (L6).
    This facade only contains business logic composition.
    """

    def __init__(self) -> None:
        """Initialize the facade with its driver."""
        self._driver = OverviewFacadeDriver()

    async def get_highlights(
        self,
        session: AsyncSession,
        tenant_id: str,
    ) -> HighlightsResult:
        """
        Get system highlights (O1).

        Returns system pulse and domain counts.
        """
        now = utc_now()
        last_24h = now - timedelta(hours=24)

        # Fetch data from driver
        incidents = await self._driver.fetch_incident_counts(session, tenant_id)
        proposals = await self._driver.fetch_proposal_counts(session, tenant_id)
        breaches = await self._driver.fetch_breach_counts(session, tenant_id, last_24h)
        runs = await self._driver.fetch_run_counts(session, tenant_id)
        audit = await self._driver.fetch_last_activity(session, tenant_id)

        # Calculate system pulse (business logic)
        active_incidents = incidents.active
        pending_decisions = incidents.active + proposals.pending
        recent_breaches = breaches.recent

        if incidents.critical > 0:
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
            live_runs=runs.running,
            queued_runs=runs.queued,
        )

        domain_counts = [
            DomainCount(
                domain="Activity",
                total=runs.total,
                pending=runs.queued,
                critical=0,
            ),
            DomainCount(
                domain="Incidents",
                total=incidents.total,
                pending=incidents.active,
                critical=incidents.critical,
            ),
            DomainCount(
                domain="Policies",
                total=proposals.total,
                pending=proposals.pending,
                critical=recent_breaches,
            ),
        ]

        return HighlightsResult(
            pulse=pulse,
            domain_counts=domain_counts,
            last_activity_at=audit.last_activity_at,
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
            incident_snapshots = await self._driver.fetch_pending_incidents(session, tenant_id)

            for inc in incident_snapshots:
                # Business logic: map severity to priority
                inc_priority = (
                    "CRITICAL"
                    if inc.severity in ["critical"]
                    else ("HIGH" if inc.severity in ["high"] else "MEDIUM")
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
                        entity_id=inc.id,
                        decision_type="ACK",
                        priority=inc_priority,
                        summary=inc.title or f"Incident {inc.id}",
                        created_at=inc_created,
                    )
                )

        # 2. Project pending policy proposals (draft = needs approval)
        if source_domain is None or source_domain == "POLICY":
            proposal_snapshots = await self._driver.fetch_pending_proposals(session, tenant_id)

            for prop in proposal_snapshots:
                prop_priority = "MEDIUM"  # Business logic: proposals are always MEDIUM
                if priority is not None and prop_priority != priority:
                    continue

                prop_created = prop.created_at
                if prop_created and prop_created.tzinfo is not None:
                    prop_created = prop_created.replace(tzinfo=None)

                items.append(
                    DecisionItem(
                        source_domain="POLICY",
                        entity_type="POLICY_PROPOSAL",
                        entity_id=prop.id,
                        decision_type="APPROVE",
                        priority=prop_priority,
                        summary=prop.proposal_name,
                        created_at=prop_created,
                    )
                )

        # Sort by created_at descending (business logic)
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
        now = utc_now()
        period_start = now - timedelta(days=period_days)

        # Fetch data from driver
        run_cost = await self._driver.fetch_run_cost(session, tenant_id, period_start)
        limit_snapshots = await self._driver.fetch_budget_limits(session, tenant_id)
        breach_stats = await self._driver.fetch_breach_stats(session, tenant_id, period_start)

        llm_run_cost = float(run_cost.total_cost_cents) / 100.0

        # Build limit items with status calculation (business logic)
        limit_items: List[LimitCostItem] = []
        for lim in limit_snapshots:
            max_val = lim.max_value
            used_val = llm_run_cost
            remaining_val = max(0, max_val - used_val)

            # Business logic: status thresholds
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

        return CostsResult(
            currency="USD",
            period=CostPeriod(start=period_start, end=now),
            llm_run_cost=llm_run_cost,
            limits=limit_items,
            breach_count=breach_stats.breach_count,
            total_overage=breach_stats.total_overage,
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
        # Fetch data from driver
        inc_counts = await self._driver.fetch_incident_decision_counts(session, tenant_id)
        prop_total = await self._driver.fetch_proposal_count(session, tenant_id)

        # Build response (business logic: aggregation)
        incident_total = inc_counts.total
        policy_total = prop_total
        total = incident_total + policy_total

        by_domain = {
            "INCIDENT": incident_total,
            "POLICY": policy_total,
        }

        by_priority = {
            "CRITICAL": inc_counts.critical,
            "HIGH": inc_counts.high,
            "MEDIUM": inc_counts.other + policy_total,  # Proposals are always MEDIUM
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
        now = utc_now()
        period_start = now - timedelta(days=period_days)

        # Fetch data from driver
        recovery = await self._driver.fetch_recovery_stats(session, tenant_id, period_start)

        # Business logic: calculate recovery rate
        recovery_rate = (recovery.recovered / recovery.total * 100.0) if recovery.total > 0 else 0.0

        return RecoveryStatsResult(
            total_incidents=recovery.total,
            recovered=recovery.recovered,
            pending_recovery=recovery.pending,
            failed_recovery=recovery.failed,
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
