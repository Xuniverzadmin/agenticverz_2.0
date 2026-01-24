# Layer: L6 — Platform Substrate
# AUDIENCE: CUSTOMER
# Product: system-wide
# Temporal:
#   Trigger: api
#   Execution: sync
# Role: Incident aggregation persistence - pure data access
# Callers: L2 APIs, L5 workers
# Allowed Imports: sqlmodel, models, L4 engines (for severity)
# Forbidden Imports: L1, L2, L3, L5 (except imported engines)
# Reference: PIN-242 (Baseline Freeze), INCIDENTS_PHASE2.5_IMPLEMENTATION_PLAN.md — Violation I.3
#
# EXTRACTION COMPLETE (2026-01-24):
# Severity logic extracted to incident_severity_engine.py (L4).
# This driver now delegates severity decisions to the engine.

"""Incident Aggregation Driver - Prevents Incident Explosion Under Load

This service implements intelligent incident grouping to prevent thousands of
micro-incidents during large outages. It uses a sliding window approach with
configurable thresholds.

Key Features:
1. Time-window aggregation (default 5 minutes)
2. Tenant + trigger_type grouping key
3. Rate limiting (max 1 incident per key per window)
4. Auto-escalation for high-volume windows
5. Incident merging for related failures

Watchpoint #1: Incident Explosion Under Load
- During a 1000-request outage, we create 1 incident, not 1000
- Related calls are added to the incident's related_call_ids
- Severity auto-escalates based on affected call count

ARCHITECTURE RULE (LESSONS_ENFORCED.md Invariant #10):
- This service MUST be constructed with explicit dependency injection
- NO lazy service resolution (get_incident_aggregator is BANNED)
- All collaborators (clock, uuid_fn) MUST be passed via constructor
- Verification scripts and production MUST use the same constructor pattern
"""

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Any, Callable, Dict, Optional, Tuple, cast

from sqlmodel import Session, and_, select

from app.hoc.cus.incidents.engines.incident_severity_engine import (
    IncidentSeverityEngine,
    SeverityConfig,
    generate_incident_title,
)
from app.models.killswitch import Incident, IncidentEvent, IncidentSeverity, IncidentStatus
from app.utils.runtime import generate_uuid, utc_now

# Type aliases for injected dependencies
ClockFn = Callable[[], datetime]
UuidFn = Callable[[], str]

logger = logging.getLogger(__name__)


# ============== CONFIGURATION ==============


@dataclass
class IncidentAggregatorConfig:
    """Configuration for incident aggregation behavior (L6 persistence config only)."""

    # Time window for grouping incidents (seconds)
    aggregation_window_seconds: int = 300  # 5 minutes

    # Maximum incidents per tenant per hour (hard cap)
    max_incidents_per_tenant_per_hour: int = 20

    # Maximum related calls to store per incident (prevents JSON bloat)
    max_related_calls_per_incident: int = 1000

    # Minimum time between incidents of same type (seconds)
    incident_cooldown_seconds: int = 60

    # Auto-resolve incidents after this duration if no new events (seconds)
    auto_resolve_after_seconds: int = 900  # 15 minutes

    # NOTE: Severity thresholds moved to SeverityConfig in incident_severity_engine.py (L4)


# ============== AGGREGATION KEY ==============


@dataclass
class IncidentKey:
    """
    Grouping key for incident aggregation.

    Incidents are grouped by:
    - tenant_id: Isolation between tenants
    - trigger_type: Type of failure (failure_spike, budget_breach, rate_limit)
    - window_start: 5-minute bucketed window
    """

    tenant_id: str
    trigger_type: str
    window_start: datetime

    def __hash__(self):
        return hash((self.tenant_id, self.trigger_type, self.window_start.isoformat()))

    def __eq__(self, other):
        if not isinstance(other, IncidentKey):
            return False
        return (
            self.tenant_id == other.tenant_id
            and self.trigger_type == other.trigger_type
            and self.window_start == other.window_start
        )

    @classmethod
    def from_event(
        cls, tenant_id: str, trigger_type: str, event_time: datetime, window_seconds: int = 300
    ) -> "IncidentKey":
        """Create an incident key from an event, bucketed to window."""
        # Bucket to nearest window
        epoch = event_time.timestamp()
        window_epoch = int(epoch // window_seconds) * window_seconds
        window_start = datetime.fromtimestamp(window_epoch, tz=timezone.utc)

        return cls(tenant_id=tenant_id, trigger_type=trigger_type, window_start=window_start)


# ============== AGGREGATOR SERVICE ==============


class IncidentAggregator:
    """
    L6 Driver for intelligent incident aggregation.

    Prevents incident explosion by:
    1. Grouping related failures into single incidents
    2. Rate limiting incident creation per tenant
    3. Auto-escalating severity based on impact (delegated to L4 engine)
    4. Merging calls into existing open incidents

    INVARIANT #10: Explicit Dependency Injection Required
    - clock: Function that returns current UTC datetime
    - uuid_fn: Function that generates UUID strings
    - severity_engine: L4 engine for severity decisions (optional, defaults to standard)
    - These MUST be passed explicitly, not resolved lazily

    EXTRACTION NOTE (2026-01-24):
    Severity logic extracted to incident_severity_engine.py (L4).
    This driver delegates severity decisions to the engine.
    """

    def __init__(
        self,
        clock: ClockFn,
        uuid_fn: UuidFn,
        config: Optional[IncidentAggregatorConfig] = None,
        severity_engine: Optional[IncidentSeverityEngine] = None,
    ):
        """
        Construct an IncidentAggregator with explicit dependencies.

        Args:
            clock: Function returning current UTC datetime (use utc_now from app.utils.runtime)
            uuid_fn: Function generating UUID strings (use generate_uuid from app.utils.runtime)
            config: Optional configuration override
            severity_engine: Optional L4 severity engine (defaults to standard engine)

        INVARIANT: Do NOT use get_incident_aggregator(). Always construct explicitly:
            aggregator = IncidentAggregator(
                clock=utc_now,
                uuid_fn=generate_uuid,
            )
        """
        self.clock = clock
        self.uuid_fn = uuid_fn
        self.config = config or IncidentAggregatorConfig()
        self._severity_engine = severity_engine or IncidentSeverityEngine()
        self._incident_cache: Dict[IncidentKey, str] = {}  # Key -> incident_id

    def get_or_create_incident(
        self,
        session: Session,
        tenant_id: str,
        trigger_type: str,
        trigger_value: str,
        call_id: Optional[str] = None,
        cost_delta_cents: Decimal = Decimal("0"),
        auto_action: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Tuple[Incident, bool]:
        """
        Get existing incident or create new one if needed.

        Returns:
            Tuple of (Incident, is_new) where is_new indicates if incident was created
        """
        now = self.clock()
        key = IncidentKey.from_event(
            tenant_id=tenant_id,
            trigger_type=trigger_type,
            event_time=now,
            window_seconds=self.config.aggregation_window_seconds,
        )

        # Check for existing open incident in current window
        existing = self._find_open_incident(session, key, now)

        if existing:
            # Add call to existing incident
            self._add_call_to_incident(
                session=session,
                incident=existing,
                call_id=call_id,
                cost_delta_cents=cost_delta_cents,
                metadata=metadata,
            )
            return existing, False

        # Check rate limiting
        if not self._can_create_incident(session, tenant_id, now):
            logger.warning(
                f"Incident rate limit reached for tenant {tenant_id}. Dropping incident creation for {trigger_type}"
            )
            # Return a synthetic "dropped" incident for tracking
            return self._get_rate_limit_incident(session, tenant_id, now), False

        # Create new incident
        incident = self._create_incident(
            session=session,
            key=key,
            trigger_value=trigger_value,
            call_id=call_id,
            cost_delta_cents=cost_delta_cents,
            auto_action=auto_action,
            metadata=metadata,
        )

        return incident, True

    def _find_open_incident(self, session: Session, key: IncidentKey, now: datetime) -> Optional[Incident]:
        """Find an open incident matching the key within the current window."""
        window_end = key.window_start + timedelta(seconds=self.config.aggregation_window_seconds)

        stmt = (
            select(Incident)
            .where(
                and_(
                    Incident.tenant_id == key.tenant_id,
                    Incident.trigger_type == key.trigger_type,
                    Incident.status != IncidentStatus.RESOLVED.value,
                    Incident.started_at >= key.window_start,
                    Incident.started_at < window_end,
                )
            )
            .order_by(cast(Any, Incident.started_at).desc())
            .limit(1)
        )

        row = session.exec(stmt).first()
        return row[0] if row else None

    def _can_create_incident(self, session: Session, tenant_id: str, now: datetime) -> bool:
        """Check if we can create a new incident (rate limiting)."""
        one_hour_ago = now - timedelta(hours=1)

        from sqlalchemy import func

        stmt = select(func.count(Incident.id)).where(
            and_(Incident.tenant_id == tenant_id, Incident.created_at >= one_hour_ago)
        )

        result = session.exec(stmt).one()
        # func.count returns an int directly, not a tuple
        count = result if isinstance(result, int) else (result[0] if result else 0)

        return count < self.config.max_incidents_per_tenant_per_hour

    def _get_rate_limit_incident(self, session: Session, tenant_id: str, now: datetime) -> Incident:
        """Get or create a rate-limit overflow incident."""
        one_hour_ago = now - timedelta(hours=1)

        # Find existing rate-limit incident
        stmt = (
            select(Incident)
            .where(
                and_(
                    Incident.tenant_id == tenant_id,
                    Incident.trigger_type == "rate_limit_overflow",
                    Incident.status != IncidentStatus.RESOLVED.value,
                    Incident.created_at >= one_hour_ago,
                )
            )
            .order_by(cast(Any, Incident.created_at).desc())
            .limit(1)
        )

        row = session.exec(stmt).first()
        if row:
            incident = row[0]
            incident.calls_affected += 1
            incident.updated_at = now
            session.add(incident)
            session.commit()
            return incident

        # Create new rate-limit overflow incident
        incident = Incident(
            id=self.uuid_fn(),
            tenant_id=tenant_id,
            title="Incident Rate Limit Reached - Events Aggregated",
            severity=IncidentSeverity.HIGH.value,
            status=IncidentStatus.OPEN.value,
            trigger_type="rate_limit_overflow",
            trigger_value=f">{self.config.max_incidents_per_tenant_per_hour} incidents/hour",
            calls_affected=1,
            started_at=now,
            auto_action="aggregate",
        )
        session.add(incident)
        session.commit()
        session.refresh(incident)

        # Safe: session is DI-managed and stays open for caller
        return incident

    def _create_incident(
        self,
        session: Session,
        key: IncidentKey,
        trigger_value: str,
        call_id: Optional[str],
        cost_delta_cents: Decimal,
        auto_action: Optional[str],
        metadata: Optional[Dict[str, Any]],
    ) -> Incident:
        """Create a new incident."""
        now = self.clock()

        # Delegate severity decision to L4 engine
        initial_severity = self._severity_engine.get_initial_severity(key.trigger_type)

        # Delegate title generation to L4 engine
        title = generate_incident_title(key.trigger_type, trigger_value)

        incident = Incident(
            id=self.uuid_fn(),
            tenant_id=key.tenant_id,
            title=title,
            severity=initial_severity,
            status=IncidentStatus.OPEN.value,
            trigger_type=key.trigger_type,
            trigger_value=trigger_value,
            calls_affected=1 if call_id else 0,
            cost_delta_cents=cost_delta_cents,
            auto_action=auto_action,
            started_at=now,
        )

        # Add initial call
        if call_id:
            incident.add_related_call(call_id)

        session.add(incident)
        session.commit()
        session.refresh(incident)

        # Create initial event (session still open, accessing incident is safe)
        self._add_incident_event(
            session=session,
            incident=incident,
            event_type="incident_created",
            description=f"Incident created: {title}",
            data={"trigger_value": trigger_value, **(metadata or {})},
        )

        logger.info(f"Created incident {incident.id} for tenant {key.tenant_id}: {key.trigger_type} - {title}")

        # Safe: session is DI-managed and stays open for caller
        return incident

    def _add_call_to_incident(
        self,
        session: Session,
        incident: Incident,
        call_id: Optional[str],
        cost_delta_cents: Decimal,
        metadata: Optional[Dict[str, Any]],
    ) -> None:
        """Add a call to an existing incident and potentially escalate."""
        now = self.clock()

        # Add call ID if not at limit
        if call_id:
            related_calls = incident.get_related_call_ids()
            if len(related_calls) < self.config.max_related_calls_per_incident:
                incident.add_related_call(call_id)

        # Update cost
        incident.cost_delta_cents += cost_delta_cents
        incident.updated_at = now

        # Delegate escalation decision to L4 engine
        should_escalate, new_severity = self._severity_engine.should_escalate(
            current_severity=incident.severity,
            calls_affected=incident.calls_affected,
        )

        if should_escalate:
            old_severity = incident.severity
            incident.severity = new_severity
            self._add_incident_event(
                session=session,
                incident=incident,
                event_type="severity_escalated",
                description=f"Severity escalated from {old_severity} to {new_severity}",
                data={
                    "old_severity": old_severity,
                    "new_severity": new_severity,
                    "calls_affected": incident.calls_affected,
                },
            )
            logger.warning(
                f"Incident {incident.id} escalated: {old_severity} -> {new_severity} "
                f"(affected calls: {incident.calls_affected})"
            )

        session.add(incident)
        session.commit()

    # NOTE: _calculate_severity, _get_initial_severity, and _generate_title
    # have been extracted to incident_severity_engine.py (L4).
    # This driver now delegates to self._severity_engine for severity decisions.

    def _add_incident_event(
        self,
        session: Session,
        incident: Incident,
        event_type: str,
        description: str,
        data: Optional[Dict[str, Any]] = None,
    ) -> IncidentEvent:
        """Add an event to an incident's timeline."""
        event = IncidentEvent(
            id=self.uuid_fn(),
            incident_id=incident.id,
            event_type=event_type,
            description=description,
        )
        if data:
            event.set_data(data)

        session.add(event)
        session.commit()

        return event

    def resolve_stale_incidents(
        self,
        session: Session,
        tenant_id: Optional[str] = None,
    ) -> int:
        """
        Auto-resolve incidents that have been open without activity.

        Returns number of resolved incidents.
        """
        now = self.clock()
        cutoff = now - timedelta(seconds=self.config.auto_resolve_after_seconds)

        conditions = [Incident.status == IncidentStatus.OPEN.value, Incident.updated_at < cutoff]

        if tenant_id:
            conditions.append(Incident.tenant_id == tenant_id)

        stmt = select(Incident).where(and_(*conditions))
        rows = session.exec(stmt).all()

        resolved_count = 0
        for row in rows:
            incident = row[0]
            incident.resolve("system_auto_resolve")
            session.add(incident)

            self._add_incident_event(
                session=session,
                incident=incident,
                event_type="auto_resolved",
                description=f"Incident auto-resolved after {self.config.auto_resolve_after_seconds}s of inactivity",
                data={"resolved_by": "system", "reason": "inactivity_timeout"},
            )

            resolved_count += 1

        if resolved_count > 0:
            session.commit()
            logger.info(f"Auto-resolved {resolved_count} stale incidents")

        return resolved_count

    def get_incident_stats(
        self,
        session: Session,
        tenant_id: str,
        since: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """Get incident statistics for a tenant."""
        if since is None:
            since = self.clock() - timedelta(hours=24)

        from sqlalchemy import func

        # Total incidents
        total_stmt = select(func.count(Incident.id)).where(
            and_(Incident.tenant_id == tenant_id, Incident.created_at >= since)
        )
        total_result = session.exec(total_stmt).one()
        total_count = total_result[0] if total_result else 0

        # Open incidents
        open_stmt = select(func.count(Incident.id)).where(
            and_(
                Incident.tenant_id == tenant_id,
                Incident.status == IncidentStatus.OPEN.value,
                Incident.created_at >= since,
            )
        )
        open_result = session.exec(open_stmt).one()
        open_count = open_result[0] if open_result else 0

        # Critical incidents
        critical_stmt = select(func.count(Incident.id)).where(
            and_(
                Incident.tenant_id == tenant_id,
                Incident.severity == IncidentSeverity.CRITICAL.value,
                Incident.created_at >= since,
            )
        )
        critical_result = session.exec(critical_stmt).one()
        critical_count = critical_result[0] if critical_result else 0

        # Total calls affected
        calls_stmt = select(func.sum(Incident.calls_affected)).where(
            and_(Incident.tenant_id == tenant_id, Incident.created_at >= since)
        )
        calls_result = session.exec(calls_stmt).one()
        total_calls = calls_result[0] if calls_result else 0

        return {
            "total_incidents": total_count,
            "open_incidents": open_count,
            "critical_incidents": critical_count,
            "total_calls_affected": total_calls or 0,
            "since": since.isoformat(),
            "aggregation_active": True,
            "config": {
                "window_seconds": self.config.aggregation_window_seconds,
                "max_per_hour": self.config.max_incidents_per_tenant_per_hour,
            },
        }


# ============== FACTORY FUNCTION (EXPLICIT DI) ==============
#
# INVARIANT #10: No Lazy Service Resolution
# The get_incident_aggregator() singleton pattern is BANNED.
# Always construct IncidentAggregator explicitly with dependencies:
#
#     from app.utils.runtime import generate_uuid, utc_now
#     aggregator = IncidentAggregator(clock=utc_now, uuid_fn=generate_uuid)
#
# This ensures:
# - Verification scripts and production use the same dependency graph
# - No hidden wiring that only fails at certain execution paths
# - All collaborators are visible and testable
#
# CI Guard enforces this:
#     grep -R "get_incident_aggregator" backend && exit 1


def create_incident_aggregator(
    config: Optional[IncidentAggregatorConfig] = None,
) -> IncidentAggregator:
    """
    Create an IncidentAggregator with canonical dependencies.

    This is the ONLY sanctioned way to create an aggregator.
    Uses generate_uuid and utc_now from app.utils.runtime.

    Usage:
        aggregator = create_incident_aggregator()
        # or with custom config:
        aggregator = create_incident_aggregator(config=IncidentAggregatorConfig(...))
    """
    return IncidentAggregator(
        clock=utc_now,
        uuid_fn=generate_uuid,
        config=config,
    )
