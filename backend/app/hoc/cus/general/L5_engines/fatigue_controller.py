# Layer: L5 — Domain Engine
# AUDIENCE: CUSTOMER
# Product: system-wide
# Temporal:
#   Trigger: api/worker
#   Execution: sync
# Lifecycle:
#   Emits: none
#   Subscribes: none
# Data Access:
#   Reads: none
#   Writes: none
# Role: Alert fatigue management (pure in-memory business logic, no boundary crossing)
# Callers: alert processing engines
# Allowed Imports: L5, L6
# Forbidden Imports: L1, L2, L3, sqlalchemy (runtime)
# Reference: PIN-470, GAP-049 (AlertFatigueController)
# NOTE: Reclassified L6→L5 (2026-01-24) - No DB/cache boundary, contains decision logic
"""
AlertFatigueController - Alert fatigue management service.

Manages alert fatigue through:
- Rate limiting: Limit alerts per source per time window
- Suppression: Temporarily suppress repetitive alerts
- Aggregation: Group similar alerts together
- Cool-down periods: Auto-suppress after threshold breaches
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Optional
import hashlib
import json


class AlertFatigueMode(str, Enum):
    """Operating modes for fatigue control."""

    MONITOR = "monitor"           # Track only, no suppression
    WARN = "warn"                 # Warn but allow alerts
    ENFORCE = "enforce"           # Actively suppress alerts
    AGGREGATE = "aggregate"       # Aggregate similar alerts


class AlertFatigueAction(str, Enum):
    """Actions taken by the fatigue controller."""

    ALLOW = "allow"               # Alert allowed through
    RATE_LIMITED = "rate_limited" # Alert blocked by rate limit
    SUPPRESSED = "suppressed"     # Alert actively suppressed
    AGGREGATED = "aggregated"     # Alert added to aggregation
    WARNED = "warned"             # Alert allowed with warning
    COOLING_DOWN = "cooling_down" # In cool-down period


@dataclass
class AlertFatigueConfig:
    """Configuration for alert fatigue thresholds."""

    # Rate limiting
    rate_limit_count: int = 10    # Max alerts per window
    rate_limit_window_seconds: int = 60  # Window size

    # Suppression
    suppression_threshold: int = 5  # Alerts before auto-suppress
    suppression_duration_seconds: int = 300  # 5 minute suppression

    # Aggregation
    aggregation_window_seconds: int = 60  # Group alerts in window
    aggregation_threshold: int = 3  # Min alerts to aggregate

    # Cool-down
    cooldown_threshold: int = 20  # Alerts before cooldown
    cooldown_duration_seconds: int = 600  # 10 minute cooldown

    # Mode
    mode: AlertFatigueMode = AlertFatigueMode.ENFORCE

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "rate_limit_count": self.rate_limit_count,
            "rate_limit_window_seconds": self.rate_limit_window_seconds,
            "suppression_threshold": self.suppression_threshold,
            "suppression_duration_seconds": self.suppression_duration_seconds,
            "aggregation_window_seconds": self.aggregation_window_seconds,
            "aggregation_threshold": self.aggregation_threshold,
            "cooldown_threshold": self.cooldown_threshold,
            "cooldown_duration_seconds": self.cooldown_duration_seconds,
            "mode": self.mode.value,
        }


@dataclass
class AlertFatigueState:
    """State tracking for an alert source."""

    source_id: str
    tenant_id: str
    alert_type: str

    # Counters
    total_count: int = 0
    window_count: int = 0
    window_start: Optional[datetime] = None

    # Suppression
    is_suppressed: bool = False
    suppression_started: Optional[datetime] = None
    suppression_count: int = 0

    # Aggregation
    aggregation_bucket: list[dict[str, Any]] = field(default_factory=list)
    aggregation_started: Optional[datetime] = None

    # Cooldown
    is_cooling_down: bool = False
    cooldown_started: Optional[datetime] = None

    # Timestamps
    first_alert: Optional[datetime] = None
    last_alert: Optional[datetime] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def record_alert(self, now: Optional[datetime] = None) -> None:
        """Record a new alert occurrence."""
        now = now or datetime.now(timezone.utc)

        self.total_count += 1
        self.window_count += 1
        self.last_alert = now

        if self.first_alert is None:
            self.first_alert = now

    def reset_window(self, now: Optional[datetime] = None) -> None:
        """Reset the rate limit window."""
        now = now or datetime.now(timezone.utc)
        self.window_count = 0
        self.window_start = now

    def start_suppression(self, now: Optional[datetime] = None) -> None:
        """Start suppression period."""
        now = now or datetime.now(timezone.utc)
        self.is_suppressed = True
        self.suppression_started = now
        self.suppression_count += 1

    def end_suppression(self) -> None:
        """End suppression period."""
        self.is_suppressed = False
        self.suppression_started = None

    def start_cooldown(self, now: Optional[datetime] = None) -> None:
        """Start cooldown period."""
        now = now or datetime.now(timezone.utc)
        self.is_cooling_down = True
        self.cooldown_started = now

    def end_cooldown(self) -> None:
        """End cooldown period."""
        self.is_cooling_down = False
        self.cooldown_started = None
        self.reset_window()

    def add_to_aggregation(
        self,
        alert_data: dict[str, Any],
        now: Optional[datetime] = None,
    ) -> None:
        """Add alert to aggregation bucket."""
        now = now or datetime.now(timezone.utc)

        if self.aggregation_started is None:
            self.aggregation_started = now

        self.aggregation_bucket.append({
            "data": alert_data,
            "timestamp": now.isoformat(),
        })

    def flush_aggregation(self) -> list[dict[str, Any]]:
        """Flush and return aggregated alerts."""
        bucket = self.aggregation_bucket
        self.aggregation_bucket = []
        self.aggregation_started = None
        return bucket

    def is_window_expired(
        self,
        window_seconds: int,
        now: Optional[datetime] = None,
    ) -> bool:
        """Check if rate limit window has expired."""
        if self.window_start is None:
            return True

        now = now or datetime.now(timezone.utc)
        window_end = self.window_start + timedelta(seconds=window_seconds)
        return now >= window_end

    def is_suppression_expired(
        self,
        duration_seconds: int,
        now: Optional[datetime] = None,
    ) -> bool:
        """Check if suppression period has expired."""
        if not self.is_suppressed or self.suppression_started is None:
            return True

        now = now or datetime.now(timezone.utc)
        expiry = self.suppression_started + timedelta(seconds=duration_seconds)
        return now >= expiry

    def is_cooldown_expired(
        self,
        duration_seconds: int,
        now: Optional[datetime] = None,
    ) -> bool:
        """Check if cooldown period has expired."""
        if not self.is_cooling_down or self.cooldown_started is None:
            return True

        now = now or datetime.now(timezone.utc)
        expiry = self.cooldown_started + timedelta(seconds=duration_seconds)
        return now >= expiry

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "source_id": self.source_id,
            "tenant_id": self.tenant_id,
            "alert_type": self.alert_type,
            "total_count": self.total_count,
            "window_count": self.window_count,
            "window_start": self.window_start.isoformat() if self.window_start else None,
            "is_suppressed": self.is_suppressed,
            "suppression_started": (
                self.suppression_started.isoformat()
                if self.suppression_started else None
            ),
            "suppression_count": self.suppression_count,
            "aggregation_count": len(self.aggregation_bucket),
            "is_cooling_down": self.is_cooling_down,
            "cooldown_started": (
                self.cooldown_started.isoformat()
                if self.cooldown_started else None
            ),
            "first_alert": self.first_alert.isoformat() if self.first_alert else None,
            "last_alert": self.last_alert.isoformat() if self.last_alert else None,
            "created_at": self.created_at.isoformat(),
        }


@dataclass
class AlertFatigueStats:
    """Statistics from fatigue controller."""

    total_alerts: int = 0
    allowed_alerts: int = 0
    rate_limited_alerts: int = 0
    suppressed_alerts: int = 0
    aggregated_alerts: int = 0
    warned_alerts: int = 0
    cooldown_alerts: int = 0

    # Source counts
    active_sources: int = 0
    suppressed_sources: int = 0
    cooling_down_sources: int = 0

    # Calculated
    suppression_rate: float = 0.0

    def update_rates(self) -> None:
        """Update calculated rates."""
        if self.total_alerts > 0:
            blocked = (
                self.rate_limited_alerts +
                self.suppressed_alerts +
                self.cooldown_alerts
            )
            self.suppression_rate = blocked / self.total_alerts

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        self.update_rates()
        return {
            "total_alerts": self.total_alerts,
            "allowed_alerts": self.allowed_alerts,
            "rate_limited_alerts": self.rate_limited_alerts,
            "suppressed_alerts": self.suppressed_alerts,
            "aggregated_alerts": self.aggregated_alerts,
            "warned_alerts": self.warned_alerts,
            "cooldown_alerts": self.cooldown_alerts,
            "active_sources": self.active_sources,
            "suppressed_sources": self.suppressed_sources,
            "cooling_down_sources": self.cooling_down_sources,
            "suppression_rate": round(self.suppression_rate, 4),
        }


class AlertFatigueError(Exception):
    """Exception for fatigue controller errors."""

    def __init__(
        self,
        message: str,
        source_id: Optional[str] = None,
        action: Optional[AlertFatigueAction] = None,
    ):
        super().__init__(message)
        self.message = message
        self.source_id = source_id
        self.action = action

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "error": self.message,
            "source_id": self.source_id,
            "action": self.action.value if self.action else None,
        }


@dataclass
class FatigueCheckResult:
    """Result of a fatigue check."""

    action: AlertFatigueAction
    allowed: bool
    source_id: str
    alert_type: str
    message: str
    state: Optional[AlertFatigueState] = None
    aggregated_count: int = 0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "action": self.action.value,
            "allowed": self.allowed,
            "source_id": self.source_id,
            "alert_type": self.alert_type,
            "message": self.message,
            "aggregated_count": self.aggregated_count,
        }


class AlertFatigueController:
    """
    Controller for managing alert fatigue.

    Features:
    - Rate limiting per source
    - Automatic suppression after thresholds
    - Alert aggregation
    - Cool-down periods
    - Per-tenant configuration
    """

    def __init__(self, default_config: Optional[AlertFatigueConfig] = None):
        """Initialize the controller."""
        self._default_config = default_config or AlertFatigueConfig()
        self._tenant_configs: dict[str, AlertFatigueConfig] = {}
        self._states: dict[str, AlertFatigueState] = {}
        self._stats = AlertFatigueStats()

    def _get_state_key(
        self,
        tenant_id: str,
        source_id: str,
        alert_type: str,
    ) -> str:
        """Generate unique key for state tracking."""
        return f"{tenant_id}:{source_id}:{alert_type}"

    def _generate_source_id(
        self,
        source_data: dict[str, Any],
    ) -> str:
        """Generate source ID from alert data."""
        # Create deterministic hash from source data
        normalized = json.dumps(source_data, sort_keys=True)
        return hashlib.sha256(normalized.encode()).hexdigest()[:16]

    def configure_tenant(
        self,
        tenant_id: str,
        config: AlertFatigueConfig,
    ) -> None:
        """Configure fatigue settings for a tenant."""
        self._tenant_configs[tenant_id] = config

    def get_config(self, tenant_id: str) -> AlertFatigueConfig:
        """Get configuration for a tenant."""
        return self._tenant_configs.get(tenant_id, self._default_config)

    def get_or_create_state(
        self,
        tenant_id: str,
        source_id: str,
        alert_type: str,
    ) -> AlertFatigueState:
        """Get or create state for an alert source."""
        key = self._get_state_key(tenant_id, source_id, alert_type)

        if key not in self._states:
            self._states[key] = AlertFatigueState(
                source_id=source_id,
                tenant_id=tenant_id,
                alert_type=alert_type,
            )

        return self._states[key]

    def get_state(
        self,
        tenant_id: str,
        source_id: str,
        alert_type: str,
    ) -> Optional[AlertFatigueState]:
        """Get state for an alert source if it exists."""
        key = self._get_state_key(tenant_id, source_id, alert_type)
        return self._states.get(key)

    def check_alert(
        self,
        tenant_id: str,
        alert_type: str,
        source_id: Optional[str] = None,
        source_data: Optional[dict[str, Any]] = None,
        alert_data: Optional[dict[str, Any]] = None,
        now: Optional[datetime] = None,
    ) -> FatigueCheckResult:
        """
        Check if an alert should be allowed or suppressed.

        Args:
            tenant_id: Tenant identifier
            alert_type: Type of alert
            source_id: Optional explicit source ID
            source_data: Data to generate source ID from
            alert_data: Alert payload for aggregation
            now: Current timestamp for testing

        Returns:
            FatigueCheckResult with action and details
        """
        now = now or datetime.now(timezone.utc)
        config = self.get_config(tenant_id)

        # Determine source ID
        if source_id is None:
            if source_data:
                source_id = self._generate_source_id(source_data)
            else:
                source_id = f"unknown-{alert_type}"

        # Get or create state
        state = self.get_or_create_state(tenant_id, source_id, alert_type)

        # Track for stats
        self._stats.total_alerts += 1

        # Check mode
        if config.mode == AlertFatigueMode.MONITOR:
            # Just track, always allow
            state.record_alert(now)
            self._stats.allowed_alerts += 1
            return FatigueCheckResult(
                action=AlertFatigueAction.ALLOW,
                allowed=True,
                source_id=source_id,
                alert_type=alert_type,
                message="Allowed (monitor mode)",
                state=state,
            )

        # Check if in cooldown
        if state.is_cooling_down:
            if state.is_cooldown_expired(config.cooldown_duration_seconds, now):
                state.end_cooldown()
            else:
                state.record_alert(now)
                self._stats.cooldown_alerts += 1
                return FatigueCheckResult(
                    action=AlertFatigueAction.COOLING_DOWN,
                    allowed=False,
                    source_id=source_id,
                    alert_type=alert_type,
                    message="Source is in cooldown period",
                    state=state,
                )

        # Check if suppressed
        if state.is_suppressed:
            if state.is_suppression_expired(config.suppression_duration_seconds, now):
                state.end_suppression()
            else:
                state.record_alert(now)
                self._stats.suppressed_alerts += 1
                return FatigueCheckResult(
                    action=AlertFatigueAction.SUPPRESSED,
                    allowed=False,
                    source_id=source_id,
                    alert_type=alert_type,
                    message="Alert is temporarily suppressed",
                    state=state,
                )

        # Check/reset rate limit window
        if state.is_window_expired(config.rate_limit_window_seconds, now):
            state.reset_window(now)

        # Record alert
        state.record_alert(now)

        # Check cooldown threshold
        if state.total_count >= config.cooldown_threshold:
            state.start_cooldown(now)
            self._stats.cooldown_alerts += 1
            return FatigueCheckResult(
                action=AlertFatigueAction.COOLING_DOWN,
                allowed=False,
                source_id=source_id,
                alert_type=alert_type,
                message=f"Cooldown triggered after {config.cooldown_threshold} alerts",
                state=state,
            )

        # Check suppression threshold
        if state.window_count >= config.suppression_threshold:
            if config.mode == AlertFatigueMode.ENFORCE:
                state.start_suppression(now)
                self._stats.suppressed_alerts += 1
                return FatigueCheckResult(
                    action=AlertFatigueAction.SUPPRESSED,
                    allowed=False,
                    source_id=source_id,
                    alert_type=alert_type,
                    message=f"Suppressed after {config.suppression_threshold} alerts in window",
                    state=state,
                )

        # Check rate limit
        if state.window_count > config.rate_limit_count:
            if config.mode == AlertFatigueMode.ENFORCE:
                self._stats.rate_limited_alerts += 1
                return FatigueCheckResult(
                    action=AlertFatigueAction.RATE_LIMITED,
                    allowed=False,
                    source_id=source_id,
                    alert_type=alert_type,
                    message=f"Rate limited: {state.window_count}/{config.rate_limit_count}",
                    state=state,
                )
            elif config.mode == AlertFatigueMode.WARN:
                self._stats.warned_alerts += 1
                return FatigueCheckResult(
                    action=AlertFatigueAction.WARNED,
                    allowed=True,
                    source_id=source_id,
                    alert_type=alert_type,
                    message=f"Warning: Rate limit exceeded {state.window_count}/{config.rate_limit_count}",
                    state=state,
                )

        # Check aggregation mode
        if config.mode == AlertFatigueMode.AGGREGATE and alert_data:
            state.add_to_aggregation(alert_data, now)

            if len(state.aggregation_bucket) >= config.aggregation_threshold:
                # Flush aggregation
                bucket = state.flush_aggregation()
                self._stats.aggregated_alerts += len(bucket)
                return FatigueCheckResult(
                    action=AlertFatigueAction.AGGREGATED,
                    allowed=True,
                    source_id=source_id,
                    alert_type=alert_type,
                    message=f"Aggregated {len(bucket)} alerts",
                    state=state,
                    aggregated_count=len(bucket),
                )
            else:
                self._stats.aggregated_alerts += 1
                return FatigueCheckResult(
                    action=AlertFatigueAction.AGGREGATED,
                    allowed=False,  # Held for aggregation
                    source_id=source_id,
                    alert_type=alert_type,
                    message=f"Queued for aggregation ({len(state.aggregation_bucket)}/{config.aggregation_threshold})",
                    state=state,
                )

        # Allow through
        self._stats.allowed_alerts += 1
        return FatigueCheckResult(
            action=AlertFatigueAction.ALLOW,
            allowed=True,
            source_id=source_id,
            alert_type=alert_type,
            message="Allowed",
            state=state,
        )

    def suppress_source(
        self,
        tenant_id: str,
        source_id: str,
        alert_type: str,
        duration_seconds: Optional[int] = None,
        now: Optional[datetime] = None,
    ) -> AlertFatigueState:
        """Manually suppress an alert source."""
        now = now or datetime.now(timezone.utc)
        state = self.get_or_create_state(tenant_id, source_id, alert_type)
        state.start_suppression(now)
        return state

    def unsuppress_source(
        self,
        tenant_id: str,
        source_id: str,
        alert_type: str,
    ) -> Optional[AlertFatigueState]:
        """Manually unsuppress an alert source."""
        state = self.get_state(tenant_id, source_id, alert_type)
        if state:
            state.end_suppression()
        return state

    def get_statistics(
        self,
        tenant_id: Optional[str] = None,
    ) -> AlertFatigueStats:
        """Get fatigue statistics, optionally filtered by tenant."""
        stats = AlertFatigueStats()

        for state in self._states.values():
            if tenant_id and state.tenant_id != tenant_id:
                continue

            stats.total_alerts += state.total_count
            stats.active_sources += 1

            if state.is_suppressed:
                stats.suppressed_sources += 1
            if state.is_cooling_down:
                stats.cooling_down_sources += 1

        stats.update_rates()
        return stats

    def get_active_sources(
        self,
        tenant_id: Optional[str] = None,
    ) -> list[AlertFatigueState]:
        """Get all active alert sources."""
        sources = []
        for state in self._states.values():
            if tenant_id and state.tenant_id != tenant_id:
                continue
            sources.append(state)
        return sources

    def clear_tenant(self, tenant_id: str) -> int:
        """Clear all state for a tenant."""
        keys_to_remove = [
            key for key, state in self._states.items()
            if state.tenant_id == tenant_id
        ]

        for key in keys_to_remove:
            del self._states[key]

        if tenant_id in self._tenant_configs:
            del self._tenant_configs[tenant_id]

        return len(keys_to_remove)

    def reset(self) -> None:
        """Reset all state (for testing)."""
        self._states.clear()
        self._tenant_configs.clear()
        self._stats = AlertFatigueStats()


# Module-level singleton
_controller: Optional[AlertFatigueController] = None


def get_alert_fatigue_controller() -> AlertFatigueController:
    """Get the singleton controller instance."""
    global _controller
    if _controller is None:
        _controller = AlertFatigueController()
    return _controller


def _reset_controller() -> None:
    """Reset the singleton (for testing)."""
    global _controller
    if _controller:
        _controller.reset()
    _controller = None


# Helper functions
def check_alert_fatigue(
    tenant_id: str,
    alert_type: str,
    source_id: Optional[str] = None,
    source_data: Optional[dict[str, Any]] = None,
    alert_data: Optional[dict[str, Any]] = None,
) -> FatigueCheckResult:
    """Check if an alert should be allowed or suppressed."""
    controller = get_alert_fatigue_controller()
    return controller.check_alert(
        tenant_id=tenant_id,
        alert_type=alert_type,
        source_id=source_id,
        source_data=source_data,
        alert_data=alert_data,
    )


def suppress_alert(
    tenant_id: str,
    source_id: str,
    alert_type: str,
    duration_seconds: Optional[int] = None,
) -> AlertFatigueState:
    """Manually suppress an alert source."""
    controller = get_alert_fatigue_controller()
    return controller.suppress_source(
        tenant_id=tenant_id,
        source_id=source_id,
        alert_type=alert_type,
        duration_seconds=duration_seconds,
    )


def get_fatigue_stats(tenant_id: Optional[str] = None) -> AlertFatigueStats:
    """Get fatigue statistics."""
    controller = get_alert_fatigue_controller()
    return controller.get_statistics(tenant_id=tenant_id)
