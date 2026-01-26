# Layer: L5 — Adapter (Facade)
# AUDIENCE: CUSTOMER
# Product: system-wide
# Temporal:
#   Trigger: api or worker (alert processing)
#   Execution: async
# Lifecycle:
#   Emits: none
#   Subscribes: none
# Data Access:
#   Reads: via L6 drivers
#   Writes: via L6 drivers
# Role: Alerts Facade - Thin translation layer for alert operations
# Callers: L2 alerts.py API, SDK, Worker
# Allowed Imports: L5 (engines), L6 (drivers)
# Forbidden Imports: L1, L2, sqlalchemy (runtime)
# Reference: PIN-470, GAP-110 (Alert Configuration API), GAP-111 (Alert History API), GAP-124 (Alert Routing API)
# NOTE: Reclassified L6→L3 (2026-01-24) - Per HOC topology, facades are L3 (adapters)


"""
Alerts Facade (L4 Domain Logic)

This facade provides the external interface for alert operations.
All alert APIs MUST use this facade instead of directly importing
internal alert modules.

Why This Facade Exists:
- Prevents L2→L4 layer violations
- Centralizes alert configuration and routing
- Provides unified access to alert history
- Single point for audit emission

L2 API Routes (GAP-110, GAP-111, GAP-124):
- POST /api/v1/alerts/rules (create alert rule)
- GET /api/v1/alerts/rules (list alert rules)
- GET /api/v1/alerts/rules/{id} (get alert rule)
- PUT /api/v1/alerts/rules/{id} (update alert rule)
- DELETE /api/v1/alerts/rules/{id} (delete alert rule)
- GET /api/v1/alerts/history (alert history)
- GET /api/v1/alerts/routes (alert routes)
- POST /api/v1/alerts/routes (create route)

Usage:
    from app.services.alerts.facade import get_alerts_facade

    facade = get_alerts_facade()

    # Create alert rule
    rule = await facade.create_rule(
        tenant_id="...",
        name="High Cost Alert",
        condition={"metric": "cost", "threshold": 1000},
    )
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
import uuid

logger = logging.getLogger("nova.services.alerts.facade")


class AlertSeverity(str, Enum):
    """Alert severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AlertStatus(str, Enum):
    """Alert status."""
    ACTIVE = "active"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"


@dataclass
class AlertRule:
    """Alert rule definition."""
    id: str
    tenant_id: str
    name: str
    description: Optional[str]
    condition: Dict[str, Any]
    severity: str
    enabled: bool
    channels: List[str]  # Notification channels
    created_at: str
    updated_at: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "tenant_id": self.tenant_id,
            "name": self.name,
            "description": self.description,
            "condition": self.condition,
            "severity": self.severity,
            "enabled": self.enabled,
            "channels": self.channels,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "metadata": self.metadata,
        }


@dataclass
class AlertEvent:
    """Alert event (history entry)."""
    id: str
    tenant_id: str
    rule_id: str
    rule_name: str
    severity: str
    status: str
    message: str
    triggered_at: str
    acknowledged_at: Optional[str] = None
    resolved_at: Optional[str] = None
    acknowledged_by: Optional[str] = None
    resolved_by: Optional[str] = None
    context: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "tenant_id": self.tenant_id,
            "rule_id": self.rule_id,
            "rule_name": self.rule_name,
            "severity": self.severity,
            "status": self.status,
            "message": self.message,
            "triggered_at": self.triggered_at,
            "acknowledged_at": self.acknowledged_at,
            "resolved_at": self.resolved_at,
            "acknowledged_by": self.acknowledged_by,
            "resolved_by": self.resolved_by,
            "context": self.context,
        }


@dataclass
class AlertRoute:
    """Alert routing rule."""
    id: str
    tenant_id: str
    name: str
    match_labels: Dict[str, str]  # Labels to match
    channel: str  # Target notification channel
    priority_override: Optional[str]
    enabled: bool
    created_at: str

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "tenant_id": self.tenant_id,
            "name": self.name,
            "match_labels": self.match_labels,
            "channel": self.channel,
            "priority_override": self.priority_override,
            "enabled": self.enabled,
            "created_at": self.created_at,
        }


class AlertsFacade:
    """
    Facade for alert operations.

    This is the ONLY entry point for L2 APIs and SDK to interact with
    alert services.

    Layer: L4 (Domain Logic)
    Callers: alerts.py (L2), aos_sdk, Worker
    """

    def __init__(self):
        """Initialize facade."""
        # In-memory stores for demo (would be database in production)
        self._rules: Dict[str, AlertRule] = {}
        self._events: Dict[str, AlertEvent] = {}
        self._routes: Dict[str, AlertRoute] = {}

    # =========================================================================
    # Alert Rule Operations (GAP-110)
    # =========================================================================

    async def create_rule(
        self,
        tenant_id: str,
        name: str,
        condition: Dict[str, Any],
        severity: str = "warning",
        description: Optional[str] = None,
        channels: Optional[List[str]] = None,
        enabled: bool = True,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> AlertRule:
        """
        Create an alert rule.

        Args:
            tenant_id: Tenant ID
            name: Rule name
            condition: Alert condition (metric, threshold, etc.)
            severity: Alert severity
            description: Optional description
            channels: Notification channels
            enabled: Whether rule is active
            metadata: Additional metadata

        Returns:
            Created AlertRule
        """
        logger.info(
            "facade.create_rule",
            extra={"tenant_id": tenant_id, "name": name}
        )

        now = datetime.now(timezone.utc)
        rule_id = str(uuid.uuid4())

        rule = AlertRule(
            id=rule_id,
            tenant_id=tenant_id,
            name=name,
            description=description,
            condition=condition,
            severity=severity,
            enabled=enabled,
            channels=channels or ["in_app"],
            created_at=now.isoformat(),
            metadata=metadata or {},
        )

        self._rules[rule_id] = rule
        return rule

    async def list_rules(
        self,
        tenant_id: str,
        severity: Optional[str] = None,
        enabled_only: bool = False,
        limit: int = 100,
        offset: int = 0,
    ) -> List[AlertRule]:
        """
        List alert rules.

        Args:
            tenant_id: Tenant ID
            severity: Optional filter by severity
            enabled_only: Only return enabled rules
            limit: Maximum results
            offset: Pagination offset

        Returns:
            List of AlertRule
        """
        results = []
        for rule in self._rules.values():
            if rule.tenant_id != tenant_id:
                continue
            if severity and rule.severity != severity:
                continue
            if enabled_only and not rule.enabled:
                continue
            results.append(rule)

        # Sort by created_at descending
        results.sort(key=lambda r: r.created_at, reverse=True)

        return results[offset:offset + limit]

    async def get_rule(
        self,
        rule_id: str,
        tenant_id: str,
    ) -> Optional[AlertRule]:
        """
        Get a specific alert rule.

        Args:
            rule_id: Rule ID
            tenant_id: Tenant ID for authorization

        Returns:
            AlertRule or None if not found
        """
        rule = self._rules.get(rule_id)
        if rule and rule.tenant_id == tenant_id:
            return rule
        return None

    async def update_rule(
        self,
        rule_id: str,
        tenant_id: str,
        name: Optional[str] = None,
        condition: Optional[Dict[str, Any]] = None,
        severity: Optional[str] = None,
        description: Optional[str] = None,
        channels: Optional[List[str]] = None,
        enabled: Optional[bool] = None,
    ) -> Optional[AlertRule]:
        """
        Update an alert rule.

        Args:
            rule_id: Rule ID
            tenant_id: Tenant ID for authorization
            name: New name
            condition: New condition
            severity: New severity
            description: New description
            channels: New channels
            enabled: New enabled state

        Returns:
            Updated AlertRule or None if not found
        """
        rule = self._rules.get(rule_id)
        if not rule or rule.tenant_id != tenant_id:
            return None

        if name:
            rule.name = name
        if condition:
            rule.condition = condition
        if severity:
            rule.severity = severity
        if description is not None:
            rule.description = description
        if channels:
            rule.channels = channels
        if enabled is not None:
            rule.enabled = enabled

        rule.updated_at = datetime.now(timezone.utc).isoformat()
        return rule

    async def delete_rule(
        self,
        rule_id: str,
        tenant_id: str,
    ) -> bool:
        """
        Delete an alert rule.

        Args:
            rule_id: Rule ID
            tenant_id: Tenant ID for authorization

        Returns:
            True if deleted, False if not found
        """
        rule = self._rules.get(rule_id)
        if not rule or rule.tenant_id != tenant_id:
            return False

        del self._rules[rule_id]
        return True

    # =========================================================================
    # Alert History Operations (GAP-111)
    # =========================================================================

    async def list_history(
        self,
        tenant_id: str,
        rule_id: Optional[str] = None,
        severity: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[AlertEvent]:
        """
        List alert history.

        Args:
            tenant_id: Tenant ID
            rule_id: Optional filter by rule
            severity: Optional filter by severity
            status: Optional filter by status
            limit: Maximum results
            offset: Pagination offset

        Returns:
            List of AlertEvent
        """
        results = []
        for event in self._events.values():
            if event.tenant_id != tenant_id:
                continue
            if rule_id and event.rule_id != rule_id:
                continue
            if severity and event.severity != severity:
                continue
            if status and event.status != status:
                continue
            results.append(event)

        # Sort by triggered_at descending
        results.sort(key=lambda e: e.triggered_at, reverse=True)

        return results[offset:offset + limit]

    async def get_event(
        self,
        event_id: str,
        tenant_id: str,
    ) -> Optional[AlertEvent]:
        """
        Get a specific alert event.

        Args:
            event_id: Event ID
            tenant_id: Tenant ID for authorization

        Returns:
            AlertEvent or None if not found
        """
        event = self._events.get(event_id)
        if event and event.tenant_id == tenant_id:
            return event
        return None

    async def acknowledge_event(
        self,
        event_id: str,
        tenant_id: str,
        actor: str,
    ) -> Optional[AlertEvent]:
        """
        Acknowledge an alert event.

        Args:
            event_id: Event ID
            tenant_id: Tenant ID for authorization
            actor: Who acknowledged

        Returns:
            Updated AlertEvent or None if not found
        """
        event = self._events.get(event_id)
        if not event or event.tenant_id != tenant_id:
            return None

        event.status = AlertStatus.ACKNOWLEDGED.value
        event.acknowledged_at = datetime.now(timezone.utc).isoformat()
        event.acknowledged_by = actor
        return event

    async def resolve_event(
        self,
        event_id: str,
        tenant_id: str,
        actor: str,
    ) -> Optional[AlertEvent]:
        """
        Resolve an alert event.

        Args:
            event_id: Event ID
            tenant_id: Tenant ID for authorization
            actor: Who resolved

        Returns:
            Updated AlertEvent or None if not found
        """
        event = self._events.get(event_id)
        if not event or event.tenant_id != tenant_id:
            return None

        event.status = AlertStatus.RESOLVED.value
        event.resolved_at = datetime.now(timezone.utc).isoformat()
        event.resolved_by = actor
        return event

    async def trigger_alert(
        self,
        tenant_id: str,
        rule_id: str,
        message: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> AlertEvent:
        """
        Trigger an alert (internal use by detection).

        Args:
            tenant_id: Tenant ID
            rule_id: Rule ID that triggered
            message: Alert message
            context: Additional context

        Returns:
            Created AlertEvent
        """
        rule = self._rules.get(rule_id)
        if not rule or rule.tenant_id != tenant_id:
            raise ValueError(f"Rule {rule_id} not found")

        now = datetime.now(timezone.utc)
        event_id = str(uuid.uuid4())

        event = AlertEvent(
            id=event_id,
            tenant_id=tenant_id,
            rule_id=rule_id,
            rule_name=rule.name,
            severity=rule.severity,
            status=AlertStatus.ACTIVE.value,
            message=message,
            triggered_at=now.isoformat(),
            context=context or {},
        )

        self._events[event_id] = event
        logger.info(
            "facade.alert_triggered",
            extra={"event_id": event_id, "rule_id": rule_id}
        )
        return event

    # =========================================================================
    # Alert Routing Operations (GAP-124)
    # =========================================================================

    async def create_route(
        self,
        tenant_id: str,
        name: str,
        match_labels: Dict[str, str],
        channel: str,
        priority_override: Optional[str] = None,
        enabled: bool = True,
    ) -> AlertRoute:
        """
        Create an alert route.

        Args:
            tenant_id: Tenant ID
            name: Route name
            match_labels: Labels to match
            channel: Target notification channel
            priority_override: Optional priority override
            enabled: Whether route is active

        Returns:
            Created AlertRoute
        """
        logger.info(
            "facade.create_route",
            extra={"tenant_id": tenant_id, "name": name}
        )

        now = datetime.now(timezone.utc)
        route_id = str(uuid.uuid4())

        route = AlertRoute(
            id=route_id,
            tenant_id=tenant_id,
            name=name,
            match_labels=match_labels,
            channel=channel,
            priority_override=priority_override,
            enabled=enabled,
            created_at=now.isoformat(),
        )

        self._routes[route_id] = route
        return route

    async def list_routes(
        self,
        tenant_id: str,
        enabled_only: bool = False,
        limit: int = 100,
        offset: int = 0,
    ) -> List[AlertRoute]:
        """
        List alert routes.

        Args:
            tenant_id: Tenant ID
            enabled_only: Only return enabled routes
            limit: Maximum results
            offset: Pagination offset

        Returns:
            List of AlertRoute
        """
        results = []
        for route in self._routes.values():
            if route.tenant_id != tenant_id:
                continue
            if enabled_only and not route.enabled:
                continue
            results.append(route)

        # Sort by created_at descending
        results.sort(key=lambda r: r.created_at, reverse=True)

        return results[offset:offset + limit]

    async def get_route(
        self,
        route_id: str,
        tenant_id: str,
    ) -> Optional[AlertRoute]:
        """
        Get a specific alert route.

        Args:
            route_id: Route ID
            tenant_id: Tenant ID for authorization

        Returns:
            AlertRoute or None if not found
        """
        route = self._routes.get(route_id)
        if route and route.tenant_id == tenant_id:
            return route
        return None

    async def delete_route(
        self,
        route_id: str,
        tenant_id: str,
    ) -> bool:
        """
        Delete an alert route.

        Args:
            route_id: Route ID
            tenant_id: Tenant ID for authorization

        Returns:
            True if deleted, False if not found
        """
        route = self._routes.get(route_id)
        if not route or route.tenant_id != tenant_id:
            return False

        del self._routes[route_id]
        return True


# =============================================================================
# Module-level singleton accessor
# =============================================================================

_facade_instance: Optional[AlertsFacade] = None


def get_alerts_facade() -> AlertsFacade:
    """
    Get the alerts facade instance.

    This is the recommended way to access alert operations
    from L2 APIs and the SDK.

    Returns:
        AlertsFacade instance
    """
    global _facade_instance
    if _facade_instance is None:
        _facade_instance = AlertsFacade()
    return _facade_instance
