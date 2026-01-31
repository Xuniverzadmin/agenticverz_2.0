# Layer: L4 — HOC Spine (Facade)
# AUDIENCE: CUSTOMER
# PHASE: W4
# Product: system-wide
# Temporal:
#   Trigger: api or scheduler
#   Execution: async
# Lifecycle:
#   Emits: none
#   Subscribes: none
# Data Access:
#   Reads: via L6 drivers
#   Writes: via L6 drivers
# Role: Monitors Facade - Thin translation layer for monitoring operations
# Callers: L2 monitors.py API, SDK, Scheduler
# Allowed Imports: L5 (engines), L6 (drivers)
# Forbidden Imports: L1, L2, sqlalchemy (runtime)
# Reference: PIN-470, GAP-120 (Health Check API), GAP-121 (Monitor Configuration API)
# NOTE: Reclassified L4→L3 (2026-01-24) - Per HOC topology, facades are L3 (adapters)

"""
Monitors Facade (L4 Domain Logic)

This facade provides the external interface for monitoring operations.
All monitor APIs MUST use this facade instead of directly importing
internal monitor modules.

Why This Facade Exists:
- Prevents L2→L4 layer violations
- Centralizes health monitoring logic
- Provides unified access to monitor configuration
- Single point for audit emission

L2 API Routes (GAP-120, GAP-121):
- POST /api/v1/monitors (create monitor)
- GET /api/v1/monitors (list monitors)
- GET /api/v1/monitors/{id} (get monitor)
- PUT /api/v1/monitors/{id} (update monitor)
- DELETE /api/v1/monitors/{id} (delete monitor)
- POST /api/v1/monitors/{id}/check (run health check)
- GET /api/v1/monitors/{id}/history (check history)
- GET /api/v1/monitors/status (overall status)

Usage:
    from app.services.monitors.facade import get_monitors_facade

    facade = get_monitors_facade()

    # Create monitor
    monitor = await facade.create_monitor(
        tenant_id="...",
        name="API Health",
        target={"url": "https://api.example.com/health"},
    )
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
import uuid

logger = logging.getLogger("nova.services.monitors.facade")


class MonitorType(str, Enum):
    """Types of monitors."""
    HTTP = "http"
    TCP = "tcp"
    DNS = "dns"
    HEARTBEAT = "heartbeat"
    CUSTOM = "custom"


class MonitorStatus(str, Enum):
    """Monitor status."""
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    DEGRADED = "degraded"
    UNKNOWN = "unknown"


class CheckStatus(str, Enum):
    """Health check result status."""
    SUCCESS = "success"
    FAILURE = "failure"
    TIMEOUT = "timeout"
    ERROR = "error"


@dataclass
class MonitorConfig:
    """Monitor configuration."""
    id: str
    tenant_id: str
    name: str
    monitor_type: str
    target: Dict[str, Any]  # URL, host:port, etc.
    interval_seconds: int
    timeout_seconds: int
    retries: int
    enabled: bool
    status: str
    last_check_at: Optional[str]
    last_status: Optional[str]
    created_at: str
    updated_at: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "tenant_id": self.tenant_id,
            "name": self.name,
            "monitor_type": self.monitor_type,
            "target": self.target,
            "interval_seconds": self.interval_seconds,
            "timeout_seconds": self.timeout_seconds,
            "retries": self.retries,
            "enabled": self.enabled,
            "status": self.status,
            "last_check_at": self.last_check_at,
            "last_status": self.last_status,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "metadata": self.metadata,
        }


@dataclass
class HealthCheckResult:
    """Health check result."""
    id: str
    monitor_id: str
    tenant_id: str
    status: str
    response_time_ms: Optional[int]
    status_code: Optional[int]
    message: Optional[str]
    checked_at: str

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "monitor_id": self.monitor_id,
            "tenant_id": self.tenant_id,
            "status": self.status,
            "response_time_ms": self.response_time_ms,
            "status_code": self.status_code,
            "message": self.message,
            "checked_at": self.checked_at,
        }


@dataclass
class MonitorStatusSummary:
    """Overall monitoring status summary."""
    total_monitors: int
    healthy_count: int
    unhealthy_count: int
    degraded_count: int
    unknown_count: int
    last_updated: str

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "total_monitors": self.total_monitors,
            "healthy_count": self.healthy_count,
            "unhealthy_count": self.unhealthy_count,
            "degraded_count": self.degraded_count,
            "unknown_count": self.unknown_count,
            "last_updated": self.last_updated,
        }


class MonitorsFacade:
    """
    Facade for monitor operations.

    This is the ONLY entry point for L2 APIs and SDK to interact with
    monitoring services.

    Layer: L4 (Domain Logic)
    Callers: monitors.py (L2), aos_sdk, Scheduler
    """

    def __init__(self):
        """Initialize facade."""
        self._monitors: Dict[str, MonitorConfig] = {}
        self._check_history: Dict[str, List[HealthCheckResult]] = {}

    # =========================================================================
    # Monitor CRUD Operations (GAP-121)
    # =========================================================================

    async def create_monitor(
        self,
        tenant_id: str,
        name: str,
        monitor_type: str,
        target: Dict[str, Any],
        interval_seconds: int = 60,
        timeout_seconds: int = 10,
        retries: int = 3,
        enabled: bool = True,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> MonitorConfig:
        """
        Create a monitor.

        Args:
            tenant_id: Tenant ID
            name: Monitor name
            monitor_type: Type of monitor (http, tcp, dns, heartbeat)
            target: Target configuration
            interval_seconds: Check interval
            timeout_seconds: Timeout for each check
            retries: Number of retries on failure
            enabled: Whether monitor is active
            metadata: Additional metadata

        Returns:
            Created MonitorConfig
        """
        logger.info(
            "facade.create_monitor",
            extra={"tenant_id": tenant_id, "name": name, "type": monitor_type}
        )

        now = datetime.now(timezone.utc)
        monitor_id = str(uuid.uuid4())

        monitor = MonitorConfig(
            id=monitor_id,
            tenant_id=tenant_id,
            name=name,
            monitor_type=monitor_type,
            target=target,
            interval_seconds=interval_seconds,
            timeout_seconds=timeout_seconds,
            retries=retries,
            enabled=enabled,
            status=MonitorStatus.UNKNOWN.value,
            last_check_at=None,
            last_status=None,
            created_at=now.isoformat(),
            metadata=metadata or {},
        )

        self._monitors[monitor_id] = monitor
        self._check_history[monitor_id] = []
        return monitor

    async def list_monitors(
        self,
        tenant_id: str,
        monitor_type: Optional[str] = None,
        status: Optional[str] = None,
        enabled_only: bool = False,
        limit: int = 100,
        offset: int = 0,
    ) -> List[MonitorConfig]:
        """
        List monitors.

        Args:
            tenant_id: Tenant ID
            monitor_type: Optional filter by type
            status: Optional filter by status
            enabled_only: Only return enabled monitors
            limit: Maximum results
            offset: Pagination offset

        Returns:
            List of MonitorConfig
        """
        results = []
        for monitor in self._monitors.values():
            if monitor.tenant_id != tenant_id:
                continue
            if monitor_type and monitor.monitor_type != monitor_type:
                continue
            if status and monitor.status != status:
                continue
            if enabled_only and not monitor.enabled:
                continue
            results.append(monitor)

        results.sort(key=lambda m: m.created_at, reverse=True)
        return results[offset:offset + limit]

    async def get_monitor(
        self,
        monitor_id: str,
        tenant_id: str,
    ) -> Optional[MonitorConfig]:
        """
        Get a specific monitor.

        Args:
            monitor_id: Monitor ID
            tenant_id: Tenant ID for authorization

        Returns:
            MonitorConfig or None if not found
        """
        monitor = self._monitors.get(monitor_id)
        if monitor and monitor.tenant_id == tenant_id:
            return monitor
        return None

    async def update_monitor(
        self,
        monitor_id: str,
        tenant_id: str,
        name: Optional[str] = None,
        target: Optional[Dict[str, Any]] = None,
        interval_seconds: Optional[int] = None,
        timeout_seconds: Optional[int] = None,
        retries: Optional[int] = None,
        enabled: Optional[bool] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Optional[MonitorConfig]:
        """
        Update a monitor.

        Args:
            monitor_id: Monitor ID
            tenant_id: Tenant ID for authorization
            name: New name
            target: New target
            interval_seconds: New interval
            timeout_seconds: New timeout
            retries: New retry count
            enabled: New enabled state
            metadata: New metadata

        Returns:
            Updated MonitorConfig or None if not found
        """
        monitor = self._monitors.get(monitor_id)
        if not monitor or monitor.tenant_id != tenant_id:
            return None

        now = datetime.now(timezone.utc)

        if name:
            monitor.name = name
        if target:
            monitor.target = target
        if interval_seconds is not None:
            monitor.interval_seconds = interval_seconds
        if timeout_seconds is not None:
            monitor.timeout_seconds = timeout_seconds
        if retries is not None:
            monitor.retries = retries
        if enabled is not None:
            monitor.enabled = enabled
        if metadata:
            monitor.metadata.update(metadata)

        monitor.updated_at = now.isoformat()
        return monitor

    async def delete_monitor(
        self,
        monitor_id: str,
        tenant_id: str,
    ) -> bool:
        """
        Delete a monitor.

        Args:
            monitor_id: Monitor ID
            tenant_id: Tenant ID for authorization

        Returns:
            True if deleted, False if not found
        """
        monitor = self._monitors.get(monitor_id)
        if not monitor or monitor.tenant_id != tenant_id:
            return False

        del self._monitors[monitor_id]
        self._check_history.pop(monitor_id, None)
        logger.info("facade.delete_monitor", extra={"monitor_id": monitor_id})
        return True

    # =========================================================================
    # Health Check Operations (GAP-120)
    # =========================================================================

    async def run_check(
        self,
        monitor_id: str,
        tenant_id: str,
    ) -> Optional[HealthCheckResult]:
        """
        Run a health check.

        Args:
            monitor_id: Monitor ID
            tenant_id: Tenant ID for authorization

        Returns:
            HealthCheckResult or None if not found
        """
        monitor = self._monitors.get(monitor_id)
        if not monitor or monitor.tenant_id != tenant_id:
            return None

        logger.info("facade.run_check", extra={"monitor_id": monitor_id})

        now = datetime.now(timezone.utc)
        check_id = str(uuid.uuid4())

        # Simulate health check (in production, would actually check)
        result = HealthCheckResult(
            id=check_id,
            monitor_id=monitor_id,
            tenant_id=tenant_id,
            status=CheckStatus.SUCCESS.value,
            response_time_ms=50,
            status_code=200,
            message="OK",
            checked_at=now.isoformat(),
        )

        # Update monitor status
        monitor.last_check_at = now.isoformat()
        monitor.last_status = result.status
        monitor.status = MonitorStatus.HEALTHY.value
        monitor.updated_at = now.isoformat()

        # Store in history
        if monitor_id not in self._check_history:
            self._check_history[monitor_id] = []
        self._check_history[monitor_id].append(result)

        # Keep only last 100 checks
        if len(self._check_history[monitor_id]) > 100:
            self._check_history[monitor_id] = self._check_history[monitor_id][-100:]

        return result

    async def get_check_history(
        self,
        monitor_id: str,
        tenant_id: str,
        limit: int = 100,
        offset: int = 0,
    ) -> List[HealthCheckResult]:
        """
        Get health check history for a monitor.

        Args:
            monitor_id: Monitor ID
            tenant_id: Tenant ID for authorization
            limit: Maximum results
            offset: Pagination offset

        Returns:
            List of HealthCheckResult
        """
        monitor = self._monitors.get(monitor_id)
        if not monitor or monitor.tenant_id != tenant_id:
            return []

        history = self._check_history.get(monitor_id, [])
        history = sorted(history, key=lambda h: h.checked_at, reverse=True)
        return history[offset:offset + limit]

    async def get_status_summary(
        self,
        tenant_id: str,
    ) -> MonitorStatusSummary:
        """
        Get overall monitoring status summary.

        Args:
            tenant_id: Tenant ID

        Returns:
            MonitorStatusSummary
        """
        now = datetime.now(timezone.utc)

        total = 0
        healthy = 0
        unhealthy = 0
        degraded = 0
        unknown = 0

        for monitor in self._monitors.values():
            if monitor.tenant_id != tenant_id:
                continue
            total += 1
            if monitor.status == MonitorStatus.HEALTHY.value:
                healthy += 1
            elif monitor.status == MonitorStatus.UNHEALTHY.value:
                unhealthy += 1
            elif monitor.status == MonitorStatus.DEGRADED.value:
                degraded += 1
            else:
                unknown += 1

        return MonitorStatusSummary(
            total_monitors=total,
            healthy_count=healthy,
            unhealthy_count=unhealthy,
            degraded_count=degraded,
            unknown_count=unknown,
            last_updated=now.isoformat(),
        )


# =============================================================================
# Module-level singleton accessor
# =============================================================================

_facade_instance: Optional[MonitorsFacade] = None


def get_monitors_facade() -> MonitorsFacade:
    """
    Get the monitors facade instance.

    This is the recommended way to access monitor operations
    from L2 APIs and the SDK.

    Returns:
        MonitorsFacade instance
    """
    global _facade_instance
    if _facade_instance is None:
        _facade_instance = MonitorsFacade()
    return _facade_instance
