"""Incident Aggregation Service - Prevents Incident Explosion Under Load

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
"""

import json
import logging
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass, field
from enum import Enum

from sqlmodel import Session, select, and_

from app.models.killswitch import (
    Incident,
    IncidentEvent,
    IncidentSeverity,
    IncidentStatus
)
from app.utils.deterministic import generate_uuid, utc_now

logger = logging.getLogger(__name__)


# ============== CONFIGURATION ==============

@dataclass
class IncidentAggregatorConfig:
    """Configuration for incident aggregation behavior."""

    # Time window for grouping incidents (seconds)
    aggregation_window_seconds: int = 300  # 5 minutes

    # Maximum incidents per tenant per hour (hard cap)
    max_incidents_per_tenant_per_hour: int = 20

    # Thresholds for severity escalation based on affected calls
    severity_thresholds: Dict[str, int] = field(default_factory=lambda: {
        "low": 1,
        "medium": 10,
        "high": 50,
        "critical": 200
    })

    # Maximum related calls to store per incident (prevents JSON bloat)
    max_related_calls_per_incident: int = 1000

    # Minimum time between incidents of same type (seconds)
    incident_cooldown_seconds: int = 60

    # Auto-resolve incidents after this duration if no new events (seconds)
    auto_resolve_after_seconds: int = 900  # 15 minutes


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
            self.tenant_id == other.tenant_id and
            self.trigger_type == other.trigger_type and
            self.window_start == other.window_start
        )

    @classmethod
    def from_event(
        cls,
        tenant_id: str,
        trigger_type: str,
        event_time: datetime,
        window_seconds: int = 300
    ) -> "IncidentKey":
        """Create an incident key from an event, bucketed to window."""
        # Bucket to nearest window
        epoch = event_time.timestamp()
        window_epoch = int(epoch // window_seconds) * window_seconds
        window_start = datetime.fromtimestamp(window_epoch, tz=timezone.utc)

        return cls(
            tenant_id=tenant_id,
            trigger_type=trigger_type,
            window_start=window_start
        )


# ============== AGGREGATOR SERVICE ==============

class IncidentAggregator:
    """
    Service for intelligent incident aggregation.

    Prevents incident explosion by:
    1. Grouping related failures into single incidents
    2. Rate limiting incident creation per tenant
    3. Auto-escalating severity based on impact
    4. Merging calls into existing open incidents
    """

    def __init__(self, config: Optional[IncidentAggregatorConfig] = None):
        self.config = config or IncidentAggregatorConfig()
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
        now = utc_now()
        key = IncidentKey.from_event(
            tenant_id=tenant_id,
            trigger_type=trigger_type,
            event_time=now,
            window_seconds=self.config.aggregation_window_seconds
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
                metadata=metadata
            )
            return existing, False

        # Check rate limiting
        if not self._can_create_incident(session, tenant_id, now):
            logger.warning(
                f"Incident rate limit reached for tenant {tenant_id}. "
                f"Dropping incident creation for {trigger_type}"
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
            metadata=metadata
        )

        return incident, True

    def _find_open_incident(
        self,
        session: Session,
        key: IncidentKey,
        now: datetime
    ) -> Optional[Incident]:
        """Find an open incident matching the key within the current window."""
        window_end = key.window_start + timedelta(seconds=self.config.aggregation_window_seconds)

        stmt = select(Incident).where(
            and_(
                Incident.tenant_id == key.tenant_id,
                Incident.trigger_type == key.trigger_type,
                Incident.status != IncidentStatus.RESOLVED.value,
                Incident.started_at >= key.window_start,
                Incident.started_at < window_end
            )
        ).order_by(Incident.started_at.desc()).limit(1)

        row = session.exec(stmt).first()
        return row[0] if row else None

    def _can_create_incident(
        self,
        session: Session,
        tenant_id: str,
        now: datetime
    ) -> bool:
        """Check if we can create a new incident (rate limiting)."""
        one_hour_ago = now - timedelta(hours=1)

        from sqlalchemy import func
        stmt = select(func.count(Incident.id)).where(
            and_(
                Incident.tenant_id == tenant_id,
                Incident.created_at >= one_hour_ago
            )
        )

        result = session.exec(stmt).one()
        count = result[0] if result else 0

        return count < self.config.max_incidents_per_tenant_per_hour

    def _get_rate_limit_incident(
        self,
        session: Session,
        tenant_id: str,
        now: datetime
    ) -> Incident:
        """Get or create a rate-limit overflow incident."""
        one_hour_ago = now - timedelta(hours=1)

        # Find existing rate-limit incident
        stmt = select(Incident).where(
            and_(
                Incident.tenant_id == tenant_id,
                Incident.trigger_type == "rate_limit_overflow",
                Incident.status != IncidentStatus.RESOLVED.value,
                Incident.created_at >= one_hour_ago
            )
        ).order_by(Incident.created_at.desc()).limit(1)

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
            id=generate_uuid(),
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
        now = utc_now()

        # Determine initial severity based on trigger type
        initial_severity = self._get_initial_severity(key.trigger_type)

        # Create title
        title = self._generate_title(key.trigger_type, trigger_value)

        incident = Incident(
            id=generate_uuid(),
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

        # Create initial event
        self._add_incident_event(
            session=session,
            incident=incident,
            event_type="incident_created",
            description=f"Incident created: {title}",
            data={"trigger_value": trigger_value, **(metadata or {})}
        )

        logger.info(
            f"Created incident {incident.id} for tenant {key.tenant_id}: "
            f"{key.trigger_type} - {title}"
        )

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
        now = utc_now()

        # Add call ID if not at limit
        if call_id:
            related_calls = incident.get_related_call_ids()
            if len(related_calls) < self.config.max_related_calls_per_incident:
                incident.add_related_call(call_id)

        # Update cost
        incident.cost_delta_cents += cost_delta_cents
        incident.updated_at = now

        # Check for severity escalation
        old_severity = incident.severity
        new_severity = self._calculate_severity(incident.calls_affected)

        if new_severity != old_severity:
            incident.severity = new_severity
            self._add_incident_event(
                session=session,
                incident=incident,
                event_type="severity_escalated",
                description=f"Severity escalated from {old_severity} to {new_severity}",
                data={
                    "old_severity": old_severity,
                    "new_severity": new_severity,
                    "calls_affected": incident.calls_affected
                }
            )
            logger.warning(
                f"Incident {incident.id} escalated: {old_severity} -> {new_severity} "
                f"(affected calls: {incident.calls_affected})"
            )

        session.add(incident)
        session.commit()

    def _calculate_severity(self, calls_affected: int) -> str:
        """Calculate severity based on number of affected calls."""
        thresholds = self.config.severity_thresholds

        if calls_affected >= thresholds["critical"]:
            return IncidentSeverity.CRITICAL.value
        elif calls_affected >= thresholds["high"]:
            return IncidentSeverity.HIGH.value
        elif calls_affected >= thresholds["medium"]:
            return IncidentSeverity.MEDIUM.value
        else:
            return IncidentSeverity.LOW.value

    def _get_initial_severity(self, trigger_type: str) -> str:
        """Get initial severity based on trigger type."""
        severity_map = {
            "budget_breach": IncidentSeverity.CRITICAL.value,
            "failure_spike": IncidentSeverity.HIGH.value,
            "rate_limit": IncidentSeverity.MEDIUM.value,
            "content_policy": IncidentSeverity.HIGH.value,
            "freeze": IncidentSeverity.CRITICAL.value,
        }
        return severity_map.get(trigger_type, IncidentSeverity.MEDIUM.value)

    def _generate_title(self, trigger_type: str, trigger_value: str) -> str:
        """Generate human-readable incident title."""
        titles = {
            "budget_breach": f"Budget limit exceeded: {trigger_value}",
            "failure_spike": f"Failure rate spike detected: {trigger_value}",
            "rate_limit": f"Rate limit triggered: {trigger_value}",
            "content_policy": f"Content policy violation: {trigger_value}",
            "freeze": f"Traffic stopped: {trigger_value}",
            "rate_limit_overflow": "Incident rate limit reached - Events aggregated",
        }
        return titles.get(trigger_type, f"{trigger_type}: {trigger_value}")

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
            id=generate_uuid(),
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
        now = utc_now()
        cutoff = now - timedelta(seconds=self.config.auto_resolve_after_seconds)

        conditions = [
            Incident.status == IncidentStatus.OPEN.value,
            Incident.updated_at < cutoff
        ]

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
                data={"resolved_by": "system", "reason": "inactivity_timeout"}
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
            since = utc_now() - timedelta(hours=24)

        from sqlalchemy import func

        # Total incidents
        total_stmt = select(func.count(Incident.id)).where(
            and_(
                Incident.tenant_id == tenant_id,
                Incident.created_at >= since
            )
        )
        total_result = session.exec(total_stmt).one()
        total_count = total_result[0] if total_result else 0

        # Open incidents
        open_stmt = select(func.count(Incident.id)).where(
            and_(
                Incident.tenant_id == tenant_id,
                Incident.status == IncidentStatus.OPEN.value,
                Incident.created_at >= since
            )
        )
        open_result = session.exec(open_stmt).one()
        open_count = open_result[0] if open_result else 0

        # Critical incidents
        critical_stmt = select(func.count(Incident.id)).where(
            and_(
                Incident.tenant_id == tenant_id,
                Incident.severity == IncidentSeverity.CRITICAL.value,
                Incident.created_at >= since
            )
        )
        critical_result = session.exec(critical_stmt).one()
        critical_count = critical_result[0] if critical_result else 0

        # Total calls affected
        calls_stmt = select(func.sum(Incident.calls_affected)).where(
            and_(
                Incident.tenant_id == tenant_id,
                Incident.created_at >= since
            )
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
            }
        }


# ============== SINGLETON INSTANCE ==============

_aggregator: Optional[IncidentAggregator] = None


def get_incident_aggregator() -> IncidentAggregator:
    """Get the singleton incident aggregator instance."""
    global _aggregator
    if _aggregator is None:
        _aggregator = IncidentAggregator()
    return _aggregator


def reset_incident_aggregator(config: Optional[IncidentAggregatorConfig] = None):
    """Reset the aggregator (for testing)."""
    global _aggregator
    _aggregator = IncidentAggregator(config)
