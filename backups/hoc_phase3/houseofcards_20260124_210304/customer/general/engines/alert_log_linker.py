# Layer: L5 — Domain Engine
# AUDIENCE: CUSTOMER
# Product: system-wide
# Temporal:
#   Trigger: api/worker
#   Execution: sync
# Role: Link alerts to log records for explicit correlation (pure business logic)
# Callers: alert_emitter, incident_service, trace_service
# Allowed Imports: L6
# Forbidden Imports: L1, L2, L3, L4
# Reference: GAP-019 (Alert → Log Linking)
# NOTE: Reclassified L4→L5 (2026-01-24) - Per HOC topology, engines are L5 (business logic)

"""
Module: alert_log_linker
Purpose: Explicit linking between alerts and log records.

GAP-019: Alert → Log linking must be explicit, not implicit.
This service provides:
    - Create links between alerts and log entries
    - Query logs by alert or alerts by run
    - Track link creation and access patterns
    - Support for different link types (threshold, breach, incident)

Exports:
    - AlertLogLinkType: Type of link (threshold, breach, incident)
    - AlertLogLinkStatus: Status of link (active, expired, archived)
    - AlertLogLink: Model for alert-log relationships
    - AlertLogLinker: Main service class
    - AlertLogLinkResponse: Response model
    - AlertLogLinkError: Error for link operations
    - Helper functions for quick access
"""

import hashlib
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Set

logger = logging.getLogger("nova.services.logging.alert_log_linker")


class AlertLogLinkType(str, Enum):
    """Type of alert-to-log link."""

    THRESHOLD_NEAR = "threshold_near"  # Near-threshold warning
    THRESHOLD_BREACH = "threshold_breach"  # Threshold breach
    INCIDENT_CREATED = "incident_created"  # Incident was created
    INCIDENT_RESOLVED = "incident_resolved"  # Incident was resolved
    POLICY_VIOLATED = "policy_violated"  # Policy violation occurred
    RUN_TERMINATED = "run_terminated"  # Run was terminated
    SYSTEM_ALERT = "system_alert"  # System-level alert


class AlertLogLinkStatus(str, Enum):
    """Status of an alert-log link."""

    ACTIVE = "active"  # Link is current and valid
    EXPIRED = "expired"  # Link has expired (past retention)
    ARCHIVED = "archived"  # Link is archived for compliance
    DELETED = "deleted"  # Link has been soft-deleted


class AlertLogLinkError(Exception):
    """
    Raised when alert-log linking operation fails.

    This error indicates that a link could not be created
    or queried due to validation or consistency issues.
    """

    def __init__(
        self,
        message: str,
        link_type: Optional[AlertLogLinkType] = None,
        alert_id: Optional[str] = None,
        run_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message)
        self.link_type = link_type
        self.alert_id = alert_id
        self.run_id = run_id
        self.details = details or {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging/API responses."""
        return {
            "error": "AlertLogLinkError",
            "message": str(self),
            "link_type": self.link_type.value if self.link_type else None,
            "alert_id": self.alert_id,
            "run_id": self.run_id,
            "details": self.details,
        }


@dataclass
class AlertLogLink:
    """
    Represents a link between an alert and log records.

    This is the core model for GAP-019 alert-log linking.
    Each link connects one alert to one or more log entries
    (trace steps, execution logs, etc.).
    """

    link_id: str
    link_type: AlertLogLinkType
    status: AlertLogLinkStatus

    # Alert reference
    alert_id: str
    alert_timestamp: datetime

    # Run/trace reference
    run_id: str
    tenant_id: str
    trace_id: Optional[str] = None

    # Log references (step indices or log entry IDs)
    log_entry_ids: List[str] = field(default_factory=list)
    step_indices: List[int] = field(default_factory=list)

    # Context
    policy_id: Optional[str] = None
    metric_name: Optional[str] = None
    metric_value: Optional[float] = None
    threshold_value: Optional[float] = None
    action_taken: Optional[str] = None

    # Metadata
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: Optional[datetime] = None
    created_by: str = "system"

    # Access tracking
    access_count: int = 0
    last_accessed_at: Optional[datetime] = None

    def is_valid(self) -> bool:
        """Check if link is valid and not expired."""
        if self.status != AlertLogLinkStatus.ACTIVE:
            return False
        if self.expires_at and datetime.now(timezone.utc) > self.expires_at:
            return False
        return True

    def record_access(self) -> None:
        """Record that this link was accessed."""
        self.access_count += 1
        self.last_accessed_at = datetime.now(timezone.utc)

    def expire(self) -> None:
        """Mark link as expired."""
        self.status = AlertLogLinkStatus.EXPIRED
        self.updated_at = datetime.now(timezone.utc)

    def archive(self) -> None:
        """Archive the link."""
        self.status = AlertLogLinkStatus.ARCHIVED
        self.updated_at = datetime.now(timezone.utc)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            "link_id": self.link_id,
            "link_type": self.link_type.value,
            "status": self.status.value,
            "alert_id": self.alert_id,
            "alert_timestamp": self.alert_timestamp.isoformat(),
            "run_id": self.run_id,
            "tenant_id": self.tenant_id,
            "trace_id": self.trace_id,
            "log_entry_ids": self.log_entry_ids,
            "step_indices": self.step_indices,
            "policy_id": self.policy_id,
            "metric_name": self.metric_name,
            "metric_value": self.metric_value,
            "threshold_value": self.threshold_value,
            "action_taken": self.action_taken,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "access_count": self.access_count,
            "is_valid": self.is_valid(),
        }


@dataclass
class AlertLogLinkResponse:
    """Response from link operations."""

    success: bool
    link: Optional[AlertLogLink]
    message: str
    links_found: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            "success": self.success,
            "link": self.link.to_dict() if self.link else None,
            "message": self.message,
            "links_found": self.links_found,
        }


class AlertLogLinker:
    """
    Service for managing alert-to-log links.

    GAP-019: Provides explicit linking between alerts and log records
    for the LLM Runs domain.

    Usage:
        linker = AlertLogLinker()

        # Create a link when alert is generated
        link = linker.create_link(
            alert_id="alert-123",
            run_id="run-456",
            tenant_id="tenant-1",
            link_type=AlertLogLinkType.THRESHOLD_BREACH,
            step_indices=[10, 11, 12],
        )

        # Query logs for an alert
        links = linker.get_links_for_alert("alert-123")

        # Query alerts for a run
        links = linker.get_links_for_run("run-456")
    """

    def __init__(
        self,
        default_retention_days: int = 90,
        max_links_per_run: int = 100,
    ):
        """
        Initialize the alert log linker.

        Args:
            default_retention_days: Default retention period for links
            max_links_per_run: Maximum links allowed per run
        """
        self._default_retention_days = default_retention_days
        self._max_links_per_run = max_links_per_run
        self._links: Dict[str, AlertLogLink] = {}  # link_id -> link
        self._by_alert: Dict[str, Set[str]] = {}  # alert_id -> set of link_ids
        self._by_run: Dict[str, Set[str]] = {}  # run_id -> set of link_ids
        self._by_tenant: Dict[str, Set[str]] = {}  # tenant_id -> set of link_ids

    def _generate_link_id(
        self,
        alert_id: str,
        run_id: str,
        link_type: AlertLogLinkType,
    ) -> str:
        """Generate a unique link ID."""
        content = f"{alert_id}:{run_id}:{link_type.value}:{datetime.now(timezone.utc).isoformat()}"
        return hashlib.sha256(content.encode()).hexdigest()[:24]

    def create_link(
        self,
        alert_id: str,
        run_id: str,
        tenant_id: str,
        link_type: AlertLogLinkType,
        alert_timestamp: Optional[datetime] = None,
        trace_id: Optional[str] = None,
        log_entry_ids: Optional[List[str]] = None,
        step_indices: Optional[List[int]] = None,
        policy_id: Optional[str] = None,
        metric_name: Optional[str] = None,
        metric_value: Optional[float] = None,
        threshold_value: Optional[float] = None,
        action_taken: Optional[str] = None,
        retention_days: Optional[int] = None,
        created_by: str = "system",
    ) -> AlertLogLink:
        """
        Create a new alert-to-log link.

        Args:
            alert_id: ID of the alert
            run_id: ID of the run
            tenant_id: Tenant identifier
            link_type: Type of link
            alert_timestamp: When the alert was generated
            trace_id: Optional trace ID
            log_entry_ids: List of log entry IDs to link
            step_indices: List of step indices to link
            policy_id: Related policy ID
            metric_name: Name of the metric that triggered alert
            metric_value: Current value of the metric
            threshold_value: Threshold that was crossed
            action_taken: Action taken in response
            retention_days: Days to retain the link
            created_by: Who created the link

        Returns:
            The created AlertLogLink

        Raises:
            AlertLogLinkError: If link cannot be created
        """
        # Check run link limit
        if run_id in self._by_run:
            if len(self._by_run[run_id]) >= self._max_links_per_run:
                raise AlertLogLinkError(
                    message=f"Maximum links ({self._max_links_per_run}) exceeded for run",
                    link_type=link_type,
                    alert_id=alert_id,
                    run_id=run_id,
                )

        # Generate link ID
        link_id = self._generate_link_id(alert_id, run_id, link_type)

        # Calculate expiration
        retention = retention_days or self._default_retention_days
        expires_at = datetime.now(timezone.utc) + timedelta(days=retention)

        # Create link
        link = AlertLogLink(
            link_id=link_id,
            link_type=link_type,
            status=AlertLogLinkStatus.ACTIVE,
            alert_id=alert_id,
            alert_timestamp=alert_timestamp or datetime.now(timezone.utc),
            run_id=run_id,
            tenant_id=tenant_id,
            trace_id=trace_id,
            log_entry_ids=log_entry_ids or [],
            step_indices=step_indices or [],
            policy_id=policy_id,
            metric_name=metric_name,
            metric_value=metric_value,
            threshold_value=threshold_value,
            action_taken=action_taken,
            expires_at=expires_at,
            created_by=created_by,
        )

        # Store link
        self._links[link_id] = link

        # Index by alert
        if alert_id not in self._by_alert:
            self._by_alert[alert_id] = set()
        self._by_alert[alert_id].add(link_id)

        # Index by run
        if run_id not in self._by_run:
            self._by_run[run_id] = set()
        self._by_run[run_id].add(link_id)

        # Index by tenant
        if tenant_id not in self._by_tenant:
            self._by_tenant[tenant_id] = set()
        self._by_tenant[tenant_id].add(link_id)

        logger.info(
            "alert_log_link_created",
            extra={
                "link_id": link_id,
                "alert_id": alert_id,
                "run_id": run_id,
                "link_type": link_type.value,
                "step_count": len(step_indices or []),
            },
        )

        return link

    def get_link(self, link_id: str) -> Optional[AlertLogLink]:
        """
        Get a link by ID.

        Args:
            link_id: Link identifier

        Returns:
            AlertLogLink or None
        """
        link = self._links.get(link_id)
        if link:
            link.record_access()
        return link

    def get_links_for_alert(
        self,
        alert_id: str,
        include_expired: bool = False,
    ) -> List[AlertLogLink]:
        """
        Get all links for an alert.

        Args:
            alert_id: Alert identifier
            include_expired: Whether to include expired links

        Returns:
            List of AlertLogLinks
        """
        if alert_id not in self._by_alert:
            return []

        links = []
        for link_id in self._by_alert[alert_id]:
            link = self._links.get(link_id)
            if link:
                if include_expired or link.is_valid():
                    link.record_access()
                    links.append(link)

        return sorted(links, key=lambda l: l.created_at, reverse=True)

    def get_links_for_run(
        self,
        run_id: str,
        link_type: Optional[AlertLogLinkType] = None,
        include_expired: bool = False,
    ) -> List[AlertLogLink]:
        """
        Get all links for a run.

        Args:
            run_id: Run identifier
            link_type: Optional filter by link type
            include_expired: Whether to include expired links

        Returns:
            List of AlertLogLinks
        """
        if run_id not in self._by_run:
            return []

        links = []
        for link_id in self._by_run[run_id]:
            link = self._links.get(link_id)
            if link:
                if link_type and link.link_type != link_type:
                    continue
                if include_expired or link.is_valid():
                    link.record_access()
                    links.append(link)

        return sorted(links, key=lambda l: l.created_at, reverse=True)

    def get_links_for_tenant(
        self,
        tenant_id: str,
        limit: int = 100,
        include_expired: bool = False,
    ) -> List[AlertLogLink]:
        """
        Get all links for a tenant.

        Args:
            tenant_id: Tenant identifier
            limit: Maximum number of links to return
            include_expired: Whether to include expired links

        Returns:
            List of AlertLogLinks
        """
        if tenant_id not in self._by_tenant:
            return []

        links = []
        for link_id in self._by_tenant[tenant_id]:
            link = self._links.get(link_id)
            if link:
                if include_expired or link.is_valid():
                    links.append(link)

        # Sort by creation time descending
        links = sorted(links, key=lambda l: l.created_at, reverse=True)
        return links[:limit]

    def get_links_by_step(
        self,
        run_id: str,
        step_index: int,
    ) -> List[AlertLogLink]:
        """
        Get all links that reference a specific step.

        Args:
            run_id: Run identifier
            step_index: Step index to find

        Returns:
            List of AlertLogLinks that reference the step
        """
        run_links = self.get_links_for_run(run_id)
        return [link for link in run_links if step_index in link.step_indices]

    def update_link(
        self,
        link_id: str,
        log_entry_ids: Optional[List[str]] = None,
        step_indices: Optional[List[int]] = None,
        action_taken: Optional[str] = None,
    ) -> Optional[AlertLogLink]:
        """
        Update an existing link.

        Args:
            link_id: Link identifier
            log_entry_ids: New log entry IDs to add
            step_indices: New step indices to add
            action_taken: Updated action taken

        Returns:
            Updated AlertLogLink or None
        """
        link = self._links.get(link_id)
        if not link:
            return None

        if log_entry_ids:
            link.log_entry_ids.extend(log_entry_ids)
        if step_indices:
            link.step_indices.extend(step_indices)
        if action_taken:
            link.action_taken = action_taken

        link.updated_at = datetime.now(timezone.utc)

        logger.info(
            "alert_log_link_updated",
            extra={
                "link_id": link_id,
                "log_entry_count": len(link.log_entry_ids),
                "step_count": len(link.step_indices),
            },
        )

        return link

    def expire_link(self, link_id: str) -> bool:
        """
        Expire a link.

        Args:
            link_id: Link identifier

        Returns:
            True if expired, False if not found
        """
        link = self._links.get(link_id)
        if not link:
            return False

        link.expire()

        logger.info("alert_log_link_expired", extra={"link_id": link_id})
        return True

    def archive_link(self, link_id: str) -> bool:
        """
        Archive a link.

        Args:
            link_id: Link identifier

        Returns:
            True if archived, False if not found
        """
        link = self._links.get(link_id)
        if not link:
            return False

        link.archive()

        logger.info("alert_log_link_archived", extra={"link_id": link_id})
        return True

    def delete_link(self, link_id: str) -> bool:
        """
        Soft-delete a link.

        Args:
            link_id: Link identifier

        Returns:
            True if deleted, False if not found
        """
        link = self._links.get(link_id)
        if not link:
            return False

        link.status = AlertLogLinkStatus.DELETED
        link.updated_at = datetime.now(timezone.utc)

        logger.info("alert_log_link_deleted", extra={"link_id": link_id})
        return True

    def cleanup_expired(self, before: Optional[datetime] = None) -> int:
        """
        Clean up expired links.

        Args:
            before: Clean up links expired before this time

        Returns:
            Number of links cleaned up
        """
        if before is None:
            before = datetime.now(timezone.utc)

        cleaned = 0
        for link_id, link in list(self._links.items()):
            if link.expires_at and link.expires_at < before:
                if link.status == AlertLogLinkStatus.ACTIVE:
                    link.expire()
                    cleaned += 1

        if cleaned > 0:
            logger.info("alert_log_links_cleaned", extra={"count": cleaned})

        return cleaned

    def get_statistics(self, tenant_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get statistics about links.

        Args:
            tenant_id: Optional tenant filter

        Returns:
            Statistics dictionary
        """
        if tenant_id:
            link_ids = self._by_tenant.get(tenant_id, set())
            links = [self._links[lid] for lid in link_ids if lid in self._links]
        else:
            links = list(self._links.values())

        active = sum(1 for l in links if l.status == AlertLogLinkStatus.ACTIVE)
        expired = sum(1 for l in links if l.status == AlertLogLinkStatus.EXPIRED)
        archived = sum(1 for l in links if l.status == AlertLogLinkStatus.ARCHIVED)

        by_type: Dict[str, int] = {}
        for link in links:
            type_name = link.link_type.value
            by_type[type_name] = by_type.get(type_name, 0) + 1

        return {
            "total_links": len(links),
            "active": active,
            "expired": expired,
            "archived": archived,
            "by_type": by_type,
            "unique_runs": len(self._by_run) if not tenant_id else len(
                {self._links[lid].run_id for lid in link_ids if lid in self._links}
            ),
            "unique_alerts": len(self._by_alert) if not tenant_id else len(
                {self._links[lid].alert_id for lid in link_ids if lid in self._links}
            ),
        }


# Module-level service instance
_linker: Optional[AlertLogLinker] = None


def get_alert_log_linker() -> AlertLogLinker:
    """Get or create the alert log linker singleton."""
    global _linker
    if _linker is None:
        _linker = AlertLogLinker()
    return _linker


def _reset_alert_log_linker() -> None:
    """Reset the alert log linker (for testing)."""
    global _linker
    _linker = None


# Helper functions for quick access


def create_alert_log_link(
    alert_id: str,
    run_id: str,
    tenant_id: str,
    link_type: AlertLogLinkType,
    step_indices: Optional[List[int]] = None,
    **kwargs,
) -> AlertLogLink:
    """
    Quick helper to create an alert-log link.

    Args:
        alert_id: Alert identifier
        run_id: Run identifier
        tenant_id: Tenant identifier
        link_type: Type of link
        step_indices: Steps to link
        **kwargs: Additional link parameters

    Returns:
        Created AlertLogLink
    """
    linker = get_alert_log_linker()
    return linker.create_link(
        alert_id=alert_id,
        run_id=run_id,
        tenant_id=tenant_id,
        link_type=link_type,
        step_indices=step_indices,
        **kwargs,
    )


def get_alerts_for_run(
    run_id: str,
    link_type: Optional[AlertLogLinkType] = None,
) -> List[AlertLogLink]:
    """
    Quick helper to get alerts for a run.

    Args:
        run_id: Run identifier
        link_type: Optional filter by type

    Returns:
        List of alert-log links for the run
    """
    linker = get_alert_log_linker()
    return linker.get_links_for_run(run_id, link_type=link_type)


def get_logs_for_alert(alert_id: str) -> List[AlertLogLink]:
    """
    Quick helper to get log links for an alert.

    Args:
        alert_id: Alert identifier

    Returns:
        List of alert-log links for the alert
    """
    linker = get_alert_log_linker()
    return linker.get_links_for_alert(alert_id)
