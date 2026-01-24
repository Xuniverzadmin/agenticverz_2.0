# Layer: L6 — Driver
# Product: system-wide
# Temporal:
#   Trigger: scheduler
#   Execution: async
# Role: Monitor panel invariants and detect silent governance failures
# Callers: main.py (scheduler), ops endpoints
# Allowed Imports: L5, L6
# Forbidden Imports: L1, L2, L3
# Reference: PIN-411 (Gap Closure - Part B)

"""
Panel Invariant Monitor

This module prevents silent governance failures by monitoring panel-backing queries.

A panel returning zero rows may mean:
- Correct state (no violations) - acceptable
- Broken ingestion - FAILURE
- Filter regression - FAILURE
- Upstream failure - FAILURE

The UI cannot distinguish these. This monitor provides out-of-band alerting.

Key Principle: Zero results NEVER block UI rendering.
               Zero results only trigger out-of-band alerting.

Alert Types:
- EMPTY_PANEL: Panel returning zero unexpectedly
- STALE_PANEL: Data older than freshness SLA
- FILTER_BREAK: Query returns error / no match

Reference: PIN-411 Gap Closure Spec (Part B)
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Optional

import yaml

logger = logging.getLogger(__name__)


# =============================================================================
# Enums
# =============================================================================


class AlertType(str, Enum):
    """Panel invariant alert types."""

    EMPTY_PANEL = "EMPTY_PANEL"  # Panel returning zero unexpectedly
    STALE_PANEL = "STALE_PANEL"  # Data older than freshness SLA
    FILTER_BREAK = "FILTER_BREAK"  # Query returns error / no match


class AlertSeverity(str, Enum):
    """Alert severity levels."""

    INFO = "INFO"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"


# =============================================================================
# Data Classes
# =============================================================================


@dataclass
class PanelInvariant:
    """A panel's invariant definition."""

    panel_id: str
    panel_question: str
    endpoint: str
    filters: dict[str, Any]
    min_rows: int
    warmup_grace_minutes: int
    alert_after_minutes: Optional[int]
    zero_allowed: bool
    alert_enabled: bool
    notes: str = ""


@dataclass
class PanelStatus:
    """Current status of a panel."""

    panel_id: str
    last_check: datetime
    result_count: int
    is_healthy: bool
    zero_duration_minutes: int = 0
    last_alert: Optional[datetime] = None
    alert_type: Optional[AlertType] = None


@dataclass
class PanelAlert:
    """An alert for a panel invariant violation."""

    panel_id: str
    alert_type: AlertType
    severity: AlertSeverity
    message: str
    details: dict[str, Any]
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict[str, Any]:
        return {
            "panel_id": self.panel_id,
            "alert_type": self.alert_type.value,
            "severity": self.severity.value,
            "message": self.message,
            "details": self.details,
            "timestamp": self.timestamp.isoformat(),
        }


# =============================================================================
# Panel Invariant Registry
# =============================================================================


class PanelInvariantRegistry:
    """
    Registry of panel invariants.

    Loads invariant definitions from YAML and provides lookup.
    """

    def __init__(self, registry_path: Optional[str] = None):
        self._invariants: dict[str, PanelInvariant] = {}
        self._registry_path = registry_path or self._default_registry_path()
        self._load_registry()

    def _default_registry_path(self) -> str:
        """Get the default registry path."""
        return str(Path(__file__).parent / "panel_invariant_registry.yaml")

    def _load_registry(self) -> None:
        """Load invariants from YAML registry."""
        try:
            with open(self._registry_path) as f:
                data = yaml.safe_load(f)

            panels = data.get("panels", {})
            for panel_id, config in panels.items():
                behavior = config.get("expected_behavior", {})
                self._invariants[panel_id] = PanelInvariant(
                    panel_id=panel_id,
                    panel_question=config.get("panel_question", ""),
                    endpoint=config.get("endpoint", ""),
                    filters=config.get("filters", {}),
                    min_rows=behavior.get("min_rows", 0),
                    warmup_grace_minutes=behavior.get("warmup_grace_minutes", 30),
                    alert_after_minutes=behavior.get("alert_after_minutes"),
                    zero_allowed=config.get("zero_allowed", True),
                    alert_enabled=config.get("alert_enabled", False),
                    notes=config.get("notes", ""),
                )

            logger.info(f"Loaded {len(self._invariants)} panel invariants from registry")

        except FileNotFoundError:
            logger.warning(f"Panel invariant registry not found at {self._registry_path}")
        except Exception as e:
            logger.error(f"Failed to load panel invariant registry: {e}")

    def get_invariant(self, panel_id: str) -> Optional[PanelInvariant]:
        """Get invariant for a panel."""
        return self._invariants.get(panel_id)

    def get_all_invariants(self) -> list[PanelInvariant]:
        """Get all invariants."""
        return list(self._invariants.values())

    def get_alertable_invariants(self) -> list[PanelInvariant]:
        """Get invariants that have alerting enabled."""
        return [inv for inv in self._invariants.values() if inv.alert_enabled]


# =============================================================================
# Panel Invariant Monitor
# =============================================================================


class PanelInvariantMonitor:
    """
    Monitors panel invariants and detects silent governance failures.

    Runs periodically (e.g., every 5 minutes) to check panel health.

    Evaluation Logic:
    - If now > warmup_grace
    - AND result_count < min_rows
    - FOR > alert_after_minutes
    - THEN raise alert
    """

    def __init__(
        self,
        registry: Optional[PanelInvariantRegistry] = None,
        system_start_time: Optional[datetime] = None,
    ):
        self._registry = registry or PanelInvariantRegistry()
        self._system_start_time = system_start_time or datetime.now(timezone.utc)
        self._panel_status: dict[str, PanelStatus] = {}
        self._alerts: list[PanelAlert] = []

        # Metrics counters
        self._empty_panel_count = 0
        self._stale_panel_count = 0
        self._filter_break_count = 0

    async def check_panel(
        self,
        panel_id: str,
        result_count: int,
        query_time_ms: float = 0,  # Reserved for STALE_PANEL detection
    ) -> Optional[PanelAlert]:
        """
        Check a panel's result against its invariant.

        Args:
            panel_id: The panel ID
            result_count: Number of rows returned
            query_time_ms: Query execution time in milliseconds

        Returns:
            PanelAlert if invariant violated, None otherwise
        """
        invariant = self._registry.get_invariant(panel_id)
        if not invariant:
            return None

        now = datetime.now(timezone.utc)

        # Check if still in warmup grace period
        warmup_end = self._system_start_time + timedelta(minutes=invariant.warmup_grace_minutes)
        if now < warmup_end:
            logger.debug(f"Panel {panel_id} in warmup grace period, skipping check")
            return None

        # Update panel status
        status = self._panel_status.get(panel_id)
        if status is None:
            status = PanelStatus(
                panel_id=panel_id,
                last_check=now,
                result_count=result_count,
                is_healthy=True,
            )
            self._panel_status[panel_id] = status
        else:
            status.last_check = now
            status.result_count = result_count

        # Check for zero results
        if result_count == 0:
            if not invariant.zero_allowed and invariant.alert_enabled:
                # Calculate how long it's been zero
                if status.zero_duration_minutes == 0:
                    status.zero_duration_minutes = 1  # Start counting
                else:
                    # Approximate based on check interval (assume 5 min intervals)
                    status.zero_duration_minutes += 5

                # Check if we should alert
                if (
                    invariant.alert_after_minutes
                    and status.zero_duration_minutes >= invariant.alert_after_minutes
                ):
                    # Avoid duplicate alerts
                    if status.last_alert is None or (now - status.last_alert).total_seconds() > 3600:
                        alert = self._create_empty_panel_alert(invariant, status)
                        status.last_alert = now
                        status.alert_type = AlertType.EMPTY_PANEL
                        status.is_healthy = False
                        self._alerts.append(alert)
                        self._empty_panel_count += 1
                        return alert
        else:
            # Reset zero duration if we got results
            status.zero_duration_minutes = 0
            status.is_healthy = True

        return None

    def report_filter_break(
        self,
        panel_id: str,
        error_message: str,
    ) -> PanelAlert:
        """
        Report a filter break (query error).

        Args:
            panel_id: The panel ID
            error_message: Error message from the query

        Returns:
            PanelAlert for the filter break
        """
        invariant = self._registry.get_invariant(panel_id)

        alert = PanelAlert(
            panel_id=panel_id,
            alert_type=AlertType.FILTER_BREAK,
            severity=AlertSeverity.CRITICAL,
            message=f"Panel query failed: {error_message}",
            details={
                "panel_question": invariant.panel_question if invariant else "",
                "endpoint": invariant.endpoint if invariant else "",
                "error": error_message,
            },
        )

        self._alerts.append(alert)
        self._filter_break_count += 1

        # Log the alert
        logger.warning(
            f"PANEL_INVARIANT_ALERT panel={panel_id} type=FILTER_BREAK "
            f"severity=CRITICAL message={error_message}"
        )

        return alert

    def _create_empty_panel_alert(
        self,
        invariant: PanelInvariant,
        status: PanelStatus,
    ) -> PanelAlert:
        """Create an alert for an empty panel."""
        alert = PanelAlert(
            panel_id=invariant.panel_id,
            alert_type=AlertType.EMPTY_PANEL,
            severity=AlertSeverity.WARNING,
            message=f"Panel returning zero rows for {status.zero_duration_minutes} minutes",
            details={
                "panel_question": invariant.panel_question,
                "endpoint": invariant.endpoint,
                "filters": invariant.filters,
                "min_rows_expected": invariant.min_rows,
                "zero_duration_minutes": status.zero_duration_minutes,
                "alert_threshold_minutes": invariant.alert_after_minutes,
            },
        )

        # Log the alert (structured)
        logger.warning(
            f"PANEL_INVARIANT_ALERT panel={invariant.panel_id} type=EMPTY_PANEL "
            f"severity=WARNING duration_minutes={status.zero_duration_minutes} "
            f"endpoint={invariant.endpoint}"
        )

        return alert

    def get_panel_status(self, panel_id: str) -> Optional[PanelStatus]:
        """Get current status of a panel."""
        return self._panel_status.get(panel_id)

    def get_all_statuses(self) -> list[PanelStatus]:
        """Get all panel statuses."""
        return list(self._panel_status.values())

    def get_unhealthy_panels(self) -> list[PanelStatus]:
        """Get panels that are currently unhealthy."""
        return [s for s in self._panel_status.values() if not s.is_healthy]

    def get_recent_alerts(self, since_minutes: int = 60) -> list[PanelAlert]:
        """Get alerts from the last N minutes."""
        cutoff = datetime.now(timezone.utc) - timedelta(minutes=since_minutes)
        return [a for a in self._alerts if a.timestamp >= cutoff]

    def get_metrics(self) -> dict[str, Any]:
        """Get monitoring metrics."""
        return {
            "panels_monitored": len(self._panel_status),
            "panels_healthy": sum(1 for s in self._panel_status.values() if s.is_healthy),
            "panels_unhealthy": sum(1 for s in self._panel_status.values() if not s.is_healthy),
            "empty_panel_alerts_total": self._empty_panel_count,
            "stale_panel_alerts_total": self._stale_panel_count,
            "filter_break_alerts_total": self._filter_break_count,
            "alerts_last_hour": len(self.get_recent_alerts(60)),
        }


# =============================================================================
# Prometheus Metrics (if available)
# =============================================================================

try:
    from prometheus_client import Counter, Gauge

    # Metrics
    panel_empty_total = Counter(
        "panel_empty_total",
        "Total number of empty panel alerts",
        ["panel_id"],
    )

    panel_filter_break_total = Counter(
        "panel_filter_break_total",
        "Total number of filter break alerts",
        ["panel_id"],
    )

    panel_health_status = Gauge(
        "panel_health_status",
        "Panel health status (1=healthy, 0=unhealthy)",
        ["panel_id"],
    )

    METRICS_ENABLED = True
except ImportError:
    METRICS_ENABLED = False
    logger.debug("Prometheus client not available, metrics disabled")


# =============================================================================
# Factory Function
# =============================================================================


_monitor_instance: Optional[PanelInvariantMonitor] = None


def get_panel_monitor() -> PanelInvariantMonitor:
    """Get the singleton panel invariant monitor."""
    global _monitor_instance
    if _monitor_instance is None:
        _monitor_instance = PanelInvariantMonitor()
    return _monitor_instance


def reset_panel_monitor() -> None:
    """Reset the monitor (for testing)."""
    global _monitor_instance
    _monitor_instance = None
