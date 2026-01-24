# Layer: L5 — Domain Engine
# AUDIENCE: CUSTOMER
# Product: system-wide
# Temporal:
#   Trigger: worker/api
#   Execution: sync
# Role: Alert deduplication and fatigue control (Redis-backed)
# Callers: AlertEmitter (L3), EventReactor (L5)
# Allowed Imports: L6, L7 (Redis, stdlib)
# Forbidden Imports: L1, L2, L3, L4, sqlalchemy, sqlmodel
# Reference: PIN-454 (Cross-Domain Orchestration Audit), Section 3.3
# NOTE: Reclassified L6→L5 (2026-01-24) - Redis infrastructure, not SQL driver
#       Remains in drivers/ per Layer ≠ Directory principle

"""
Alert Fatigue Controller

Provides deduplication and fatigue controls for alerts:

1. Same-domain alert deduplication (within configurable window)
2. Per-domain cooldown periods
3. Per-tenant fatigue settings
4. Sliding window rate limiting

Design Principles:
1. Alerts are important - but too many alerts = no alerts
2. Configurable per-tenant and per-domain
3. Feature flag controlled for safe rollout
4. Redis-backed for distributed deployment (optional)

Usage:
    from app.services.alert_fatigue import get_alert_fatigue_controller

    controller = get_alert_fatigue_controller()

    # Check if alert should be sent
    if controller.should_send_alert(
        alert_key="incidents:high_failure_rate",
        tenant_id="tenant-123",
        domain="incidents",
    ):
        # Send the alert
        ...

    # Record that alert was sent
    controller.record_alert_sent(
        alert_key="incidents:high_failure_rate",
        tenant_id="tenant-123",
        domain="incidents",
    )
"""

import hashlib
import logging
import os
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from threading import Lock
from typing import Any, Dict, FrozenSet, List, Optional

logger = logging.getLogger("nova.services.alert_fatigue")

# =============================================================================
# Configuration (PIN-454 Section 3.3)
# =============================================================================

# Feature flag
ALERT_FATIGUE_ENABLED = os.getenv("ALERT_FATIGUE_ENABLED", "true").lower() == "true"

# Default cooldown periods per domain (seconds)
DEFAULT_DOMAIN_COOLDOWNS = {
    "incidents": int(os.getenv("ALERT_COOLDOWN_INCIDENTS", "300")),  # 5 min
    "policies": int(os.getenv("ALERT_COOLDOWN_POLICIES", "600")),  # 10 min
    "logs": int(os.getenv("ALERT_COOLDOWN_LOGS", "60")),  # 1 min
    "orchestrator": int(os.getenv("ALERT_COOLDOWN_ORCHESTRATOR", "300")),  # 5 min
    "audit": int(os.getenv("ALERT_COOLDOWN_AUDIT", "300")),  # 5 min
    "default": int(os.getenv("ALERT_COOLDOWN_DEFAULT", "300")),  # 5 min
}

# Deduplication window (seconds) - alerts with same key within window are deduped
DEDUP_WINDOW_SECONDS = int(os.getenv("ALERT_DEDUP_WINDOW_SECONDS", "60"))

# Max alerts per tenant per hour (sliding window)
MAX_ALERTS_PER_TENANT_PER_HOUR = int(os.getenv("MAX_ALERTS_PER_TENANT_PER_HOUR", "100"))

# Redis key prefix (if using Redis)
REDIS_KEY_PREFIX = "alert_fatigue:"
REDIS_TTL_SECONDS = 3600 * 24  # 24 hours


class AlertSuppressReason(str, Enum):
    """Reason why an alert was suppressed."""

    NOT_SUPPRESSED = "NOT_SUPPRESSED"  # Alert should be sent
    DUPLICATE = "DUPLICATE"  # Same alert within dedup window
    DOMAIN_COOLDOWN = "DOMAIN_COOLDOWN"  # Domain is in cooldown
    TENANT_RATE_LIMIT = "TENANT_RATE_LIMIT"  # Tenant exceeded rate limit
    DISABLED = "DISABLED"  # Alert fatigue disabled for tenant
    FEATURE_FLAG_OFF = "FEATURE_FLAG_OFF"  # Feature flag disabled


@dataclass
class AlertRecord:
    """Record of a sent alert for deduplication tracking."""

    alert_key: str
    tenant_id: str
    domain: str
    sent_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    alert_hash: str = ""

    def __post_init__(self):
        """Compute alert hash for deduplication."""
        if not self.alert_hash:
            hash_input = f"{self.alert_key}:{self.tenant_id}:{self.domain}"
            self.alert_hash = hashlib.sha256(hash_input.encode()).hexdigest()[:16]

    @property
    def age(self) -> timedelta:
        """Time since alert was sent."""
        return datetime.now(timezone.utc) - self.sent_at


@dataclass
class TenantFatigueSettings:
    """Per-tenant fatigue settings."""

    tenant_id: str
    enabled: bool = True
    max_alerts_per_hour: int = MAX_ALERTS_PER_TENANT_PER_HOUR
    domain_cooldowns: Dict[str, int] = field(default_factory=dict)  # domain -> seconds
    dedup_window_seconds: int = DEDUP_WINDOW_SECONDS

    def get_domain_cooldown(self, domain: str) -> int:
        """Get cooldown for a domain."""
        if domain in self.domain_cooldowns:
            return self.domain_cooldowns[domain]
        return DEFAULT_DOMAIN_COOLDOWNS.get(domain, DEFAULT_DOMAIN_COOLDOWNS["default"])


@dataclass
class AlertCheckResult:
    """Result of checking whether an alert should be sent."""

    should_send: bool
    suppress_reason: AlertSuppressReason
    details: str = ""
    next_allowed_at: Optional[datetime] = None
    alerts_remaining_in_window: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        """Serialize for logging."""
        return {
            "should_send": self.should_send,
            "suppress_reason": self.suppress_reason.value,
            "details": self.details,
            "next_allowed_at": self.next_allowed_at.isoformat() if self.next_allowed_at else None,
            "alerts_remaining_in_window": self.alerts_remaining_in_window,
        }


class AlertFatigueController:
    """
    Controls alert deduplication and fatigue.

    Per PIN-454 Section 3.3, this provides:
    - Same-domain alert deduplication
    - Configurable cooldowns per domain
    - Per-tenant fatigue settings
    - Sliding window rate limiting

    Layer: L4 (Domain Engine)
    """

    def __init__(self, redis_client=None):
        """
        Initialize fatigue controller.

        Args:
            redis_client: Optional Redis client for distributed state
        """
        self._redis = redis_client
        self._lock = Lock()

        # In-memory storage (used when Redis unavailable)
        self._alert_history: Dict[str, List[AlertRecord]] = {}  # tenant_id -> alerts
        self._domain_last_alert: Dict[str, Dict[str, datetime]] = {}  # tenant_id -> {domain -> time}
        self._tenant_settings: Dict[str, TenantFatigueSettings] = {}

        logger.info(
            "alert_fatigue.initialized",
            extra={
                "redis_available": redis_client is not None,
                "fatigue_enabled": ALERT_FATIGUE_ENABLED,
            },
        )

    def check_alert(
        self,
        alert_key: str,
        tenant_id: str,
        domain: str,
    ) -> AlertCheckResult:
        """
        Check if an alert should be sent.

        Args:
            alert_key: Unique key for the alert type (e.g., "incidents:high_failure_rate")
            tenant_id: Tenant ID
            domain: Domain (incidents, policies, logs, etc.)

        Returns:
            AlertCheckResult with decision and details
        """
        # Check feature flag
        if not ALERT_FATIGUE_ENABLED:
            return AlertCheckResult(
                should_send=True,
                suppress_reason=AlertSuppressReason.NOT_SUPPRESSED,
                details="Alert fatigue disabled (feature flag)",
            )

        # Get tenant settings
        settings = self._get_tenant_settings(tenant_id)

        # Check if fatigue is disabled for tenant
        if not settings.enabled:
            return AlertCheckResult(
                should_send=True,
                suppress_reason=AlertSuppressReason.NOT_SUPPRESSED,
                details="Alert fatigue disabled for tenant",
            )

        with self._lock:
            # Check 1: Deduplication
            dedup_result = self._check_deduplication(alert_key, tenant_id, domain, settings)
            if not dedup_result.should_send:
                return dedup_result

            # Check 2: Domain cooldown
            cooldown_result = self._check_domain_cooldown(tenant_id, domain, settings)
            if not cooldown_result.should_send:
                return cooldown_result

            # Check 3: Tenant rate limit
            rate_result = self._check_tenant_rate_limit(tenant_id, settings)
            if not rate_result.should_send:
                return rate_result

        # All checks passed
        return AlertCheckResult(
            should_send=True,
            suppress_reason=AlertSuppressReason.NOT_SUPPRESSED,
            details="Alert passed all fatigue checks",
            alerts_remaining_in_window=rate_result.alerts_remaining_in_window,
        )

    def should_send_alert(
        self,
        alert_key: str,
        tenant_id: str,
        domain: str,
    ) -> bool:
        """
        Simple check if alert should be sent (convenience method).

        Args:
            alert_key: Unique key for the alert type
            tenant_id: Tenant ID
            domain: Domain

        Returns:
            True if alert should be sent
        """
        return self.check_alert(alert_key, tenant_id, domain).should_send

    def record_alert_sent(
        self,
        alert_key: str,
        tenant_id: str,
        domain: str,
    ) -> None:
        """
        Record that an alert was sent.

        Must be called after sending an alert to update fatigue tracking.

        Args:
            alert_key: Unique key for the alert type
            tenant_id: Tenant ID
            domain: Domain
        """
        record = AlertRecord(
            alert_key=alert_key,
            tenant_id=tenant_id,
            domain=domain,
        )

        with self._lock:
            # Record in alert history
            if tenant_id not in self._alert_history:
                self._alert_history[tenant_id] = []
            self._alert_history[tenant_id].append(record)

            # Update domain last alert time
            if tenant_id not in self._domain_last_alert:
                self._domain_last_alert[tenant_id] = {}
            self._domain_last_alert[tenant_id][domain] = record.sent_at

            # Cleanup old records
            self._cleanup_old_records(tenant_id)

        logger.debug(
            "alert_fatigue.alert_recorded",
            extra={
                "alert_key": alert_key,
                "tenant_id": tenant_id,
                "domain": domain,
                "alert_hash": record.alert_hash,
            },
        )

    def set_tenant_settings(
        self,
        tenant_id: str,
        settings: TenantFatigueSettings,
    ) -> None:
        """
        Set custom fatigue settings for a tenant.

        Args:
            tenant_id: Tenant ID
            settings: Custom settings
        """
        with self._lock:
            self._tenant_settings[tenant_id] = settings

        logger.info(
            "alert_fatigue.tenant_settings_updated",
            extra={
                "tenant_id": tenant_id,
                "enabled": settings.enabled,
                "max_alerts_per_hour": settings.max_alerts_per_hour,
            },
        )

    def get_tenant_stats(self, tenant_id: str) -> Dict[str, Any]:
        """
        Get fatigue statistics for a tenant.

        Args:
            tenant_id: Tenant ID

        Returns:
            Dictionary with stats
        """
        with self._lock:
            alerts = self._alert_history.get(tenant_id, [])
            now = datetime.now(timezone.utc)
            one_hour_ago = now - timedelta(hours=1)

            recent_alerts = [a for a in alerts if a.sent_at > one_hour_ago]
            settings = self._get_tenant_settings(tenant_id)

            # Get alerts by domain
            domain_counts: Dict[str, int] = {}
            for alert in recent_alerts:
                domain_counts[alert.domain] = domain_counts.get(alert.domain, 0) + 1

            return {
                "tenant_id": tenant_id,
                "alerts_in_last_hour": len(recent_alerts),
                "max_alerts_per_hour": settings.max_alerts_per_hour,
                "alerts_by_domain": domain_counts,
                "fatigue_enabled": settings.enabled,
            }

    def _get_tenant_settings(self, tenant_id: str) -> TenantFatigueSettings:
        """Get settings for a tenant (with defaults)."""
        if tenant_id in self._tenant_settings:
            return self._tenant_settings[tenant_id]
        return TenantFatigueSettings(tenant_id=tenant_id)

    def _check_deduplication(
        self,
        alert_key: str,
        tenant_id: str,
        domain: str,
        settings: TenantFatigueSettings,
    ) -> AlertCheckResult:
        """Check for duplicate alerts within dedup window."""
        alerts = self._alert_history.get(tenant_id, [])
        dedup_window = timedelta(seconds=settings.dedup_window_seconds)
        now = datetime.now(timezone.utc)

        # Create hash for this alert
        alert_hash = hashlib.sha256(f"{alert_key}:{tenant_id}:{domain}".encode()).hexdigest()[:16]

        # Look for matching alert in window
        for alert in alerts:
            if alert.alert_hash == alert_hash:
                if (now - alert.sent_at) < dedup_window:
                    next_allowed = alert.sent_at + dedup_window
                    return AlertCheckResult(
                        should_send=False,
                        suppress_reason=AlertSuppressReason.DUPLICATE,
                        details=f"Duplicate alert within {settings.dedup_window_seconds}s window",
                        next_allowed_at=next_allowed,
                    )

        return AlertCheckResult(
            should_send=True,
            suppress_reason=AlertSuppressReason.NOT_SUPPRESSED,
        )

    def _check_domain_cooldown(
        self,
        tenant_id: str,
        domain: str,
        settings: TenantFatigueSettings,
    ) -> AlertCheckResult:
        """Check domain-specific cooldown."""
        domain_times = self._domain_last_alert.get(tenant_id, {})
        last_alert_time = domain_times.get(domain)

        if last_alert_time is None:
            return AlertCheckResult(
                should_send=True,
                suppress_reason=AlertSuppressReason.NOT_SUPPRESSED,
            )

        cooldown_seconds = settings.get_domain_cooldown(domain)
        cooldown = timedelta(seconds=cooldown_seconds)
        now = datetime.now(timezone.utc)

        if (now - last_alert_time) < cooldown:
            next_allowed = last_alert_time + cooldown
            return AlertCheckResult(
                should_send=False,
                suppress_reason=AlertSuppressReason.DOMAIN_COOLDOWN,
                details=f"Domain '{domain}' in cooldown ({cooldown_seconds}s)",
                next_allowed_at=next_allowed,
            )

        return AlertCheckResult(
            should_send=True,
            suppress_reason=AlertSuppressReason.NOT_SUPPRESSED,
        )

    def _check_tenant_rate_limit(
        self,
        tenant_id: str,
        settings: TenantFatigueSettings,
    ) -> AlertCheckResult:
        """Check tenant rate limit (sliding window)."""
        alerts = self._alert_history.get(tenant_id, [])
        now = datetime.now(timezone.utc)
        one_hour_ago = now - timedelta(hours=1)

        # Count alerts in last hour
        recent_count = sum(1 for a in alerts if a.sent_at > one_hour_ago)
        remaining = settings.max_alerts_per_hour - recent_count

        if recent_count >= settings.max_alerts_per_hour:
            # Find oldest alert in window to determine when we can send again
            recent_alerts = sorted(
                (a for a in alerts if a.sent_at > one_hour_ago),
                key=lambda a: a.sent_at,
            )
            if recent_alerts:
                oldest = recent_alerts[0]
                next_allowed = oldest.sent_at + timedelta(hours=1)
            else:
                next_allowed = now + timedelta(minutes=1)

            return AlertCheckResult(
                should_send=False,
                suppress_reason=AlertSuppressReason.TENANT_RATE_LIMIT,
                details=f"Tenant rate limit exceeded ({settings.max_alerts_per_hour}/hour)",
                next_allowed_at=next_allowed,
                alerts_remaining_in_window=0,
            )

        return AlertCheckResult(
            should_send=True,
            suppress_reason=AlertSuppressReason.NOT_SUPPRESSED,
            alerts_remaining_in_window=remaining,
        )

    def _cleanup_old_records(self, tenant_id: str) -> None:
        """Remove old records outside the tracking window."""
        if tenant_id not in self._alert_history:
            return

        now = datetime.now(timezone.utc)
        cutoff = now - timedelta(hours=2)  # Keep 2 hours of history

        self._alert_history[tenant_id] = [
            a for a in self._alert_history[tenant_id] if a.sent_at > cutoff
        ]


# =============================================================================
# Singleton
# =============================================================================

_fatigue_controller_instance: Optional[AlertFatigueController] = None


def get_alert_fatigue_controller(redis_client=None) -> AlertFatigueController:
    """
    Get or create AlertFatigueController singleton.

    Args:
        redis_client: Optional Redis client (only used on first call)

    Returns:
        AlertFatigueController instance
    """
    global _fatigue_controller_instance
    if _fatigue_controller_instance is None:
        _fatigue_controller_instance = AlertFatigueController(redis_client=redis_client)
    return _fatigue_controller_instance


def reset_alert_fatigue_controller() -> None:
    """Reset the singleton (for testing)."""
    global _fatigue_controller_instance
    _fatigue_controller_instance = None
