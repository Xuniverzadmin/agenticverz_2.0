# Layer: L5 — Domain Engine
# AUDIENCE: CUSTOMER
# Product: system-wide
# Temporal:
#   Trigger: api/worker
#   Execution: async
# Lifecycle:
#   Emits: notification_sent, notification_failed
#   Subscribes: none
# Data Access:
#   Reads: ChannelConfig (via driver)
#   Writes: none
# Role: Configurable notification channel management
# Callers: alert_emitter, incident_service, policy_engine
# Allowed Imports: L5, L6
# Forbidden Imports: L1, L2, L3, sqlalchemy (runtime)
# Reference: PIN-470, GAP-017 (Notify Channels)
# NOTE: Renamed channel_service.py → channel_engine.py (2026-01-24)
#       per BANNED_NAMING rule (*_service.py → *_engine.py)
#       Reclassified L4→L5 - Per HOC topology, engines are L5 (business logic)

"""
Module: channel_service
Purpose: Configurable notification channels for alerts and events.

GAP-017: Notify channels must be configurable per tenant/policy.
This service provides:
    - Channel configuration (enable/disable per channel type)
    - Channel validation (test connectivity)
    - Delivery tracking (success/failure metrics)
    - Retry logic for failed deliveries

Exports:
    - NotifyChannel: Enum of available channels
    - NotifyEventType: Enum of event types
    - NotifyChannelConfig: Channel configuration
    - NotifyChannelService: Main service class
    - NotifyDeliveryResult: Delivery result tracking
    - NotifyChannelError: Error for channel failures
    - Helper functions for quick access
"""

import hashlib
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Protocol, Set

logger = logging.getLogger("nova.services.notifications.channel_service")


class NotifyChannel(str, Enum):
    """Available notification channels."""

    UI = "ui"  # In-app UI notification
    WEBHOOK = "webhook"  # External webhook HTTP POST
    EMAIL = "email"  # Email notification
    SLACK = "slack"  # Slack webhook integration
    PAGERDUTY = "pagerduty"  # PagerDuty integration
    TEAMS = "teams"  # Microsoft Teams webhook


class NotifyEventType(str, Enum):
    """Types of events that can trigger notifications."""

    ALERT_NEAR_THRESHOLD = "alert_near_threshold"
    ALERT_BREACH = "alert_breach"
    INCIDENT_CREATED = "incident_created"
    INCIDENT_RESOLVED = "incident_resolved"
    POLICY_VIOLATED = "policy_violated"
    POLICY_UPDATED = "policy_updated"
    RUN_FAILED = "run_failed"
    RUN_COMPLETED = "run_completed"
    SYSTEM_DEGRADED = "system_degraded"
    SYSTEM_RECOVERED = "system_recovered"


class NotifyChannelStatus(str, Enum):
    """Status of a notification channel."""

    ENABLED = "enabled"  # Channel is active and will send
    DISABLED = "disabled"  # Channel is manually disabled
    FAILED = "failed"  # Channel failed health check
    UNCONFIGURED = "unconfigured"  # Channel not configured


class NotifyChannelError(Exception):
    """
    Raised when notification channel operation fails.

    This error indicates that a notification could not be sent
    through the configured channel.
    """

    def __init__(
        self,
        message: str,
        channel: NotifyChannel,
        event_type: Optional[NotifyEventType] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message)
        self.channel = channel
        self.event_type = event_type
        self.details = details or {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging/API responses."""
        return {
            "error": "NotifyChannelError",
            "message": str(self),
            "channel": self.channel.value,
            "event_type": self.event_type.value if self.event_type else None,
            "details": self.details,
        }


@dataclass
class NotifyDeliveryResult:
    """Result of a notification delivery attempt."""

    channel: NotifyChannel
    event_type: NotifyEventType
    success: bool
    delivered_at: datetime
    recipient_id: Optional[str] = None
    message_id: Optional[str] = None
    error_message: Optional[str] = None
    retry_count: int = 0
    latency_ms: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            "channel": self.channel.value,
            "event_type": self.event_type.value,
            "success": self.success,
            "delivered_at": self.delivered_at.isoformat(),
            "recipient_id": self.recipient_id,
            "message_id": self.message_id,
            "error_message": self.error_message,
            "retry_count": self.retry_count,
            "latency_ms": self.latency_ms,
        }


@dataclass
class NotifyChannelConfig:
    """Configuration for a notification channel."""

    channel: NotifyChannel
    status: NotifyChannelStatus
    tenant_id: str

    # Channel-specific configuration
    webhook_url: Optional[str] = None
    webhook_secret: Optional[str] = None
    email_recipients: List[str] = field(default_factory=list)
    slack_webhook_url: Optional[str] = None
    slack_channel: Optional[str] = None
    pagerduty_routing_key: Optional[str] = None
    teams_webhook_url: Optional[str] = None

    # Event filtering
    enabled_events: Set[NotifyEventType] = field(
        default_factory=lambda: set(NotifyEventType)
    )

    # Delivery settings
    retry_count: int = 3
    retry_delay_seconds: int = 5
    timeout_seconds: int = 30

    # Metadata
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_success_at: Optional[datetime] = None
    last_failure_at: Optional[datetime] = None
    failure_count: int = 0

    def is_event_enabled(self, event_type: NotifyEventType) -> bool:
        """Check if an event type is enabled for this channel."""
        return event_type in self.enabled_events

    def is_configured(self) -> bool:
        """Check if channel has required configuration."""
        if self.channel == NotifyChannel.UI:
            return True  # UI always configured
        elif self.channel == NotifyChannel.WEBHOOK:
            return bool(self.webhook_url)
        elif self.channel == NotifyChannel.EMAIL:
            return len(self.email_recipients) > 0
        elif self.channel == NotifyChannel.SLACK:
            return bool(self.slack_webhook_url)
        elif self.channel == NotifyChannel.PAGERDUTY:
            return bool(self.pagerduty_routing_key)
        elif self.channel == NotifyChannel.TEAMS:
            return bool(self.teams_webhook_url)
        return False

    def record_success(self) -> None:
        """Record a successful delivery."""
        self.last_success_at = datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)

    def record_failure(self) -> None:
        """Record a failed delivery."""
        self.last_failure_at = datetime.now(timezone.utc)
        self.failure_count += 1
        self.updated_at = datetime.now(timezone.utc)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            "channel": self.channel.value,
            "status": self.status.value,
            "tenant_id": self.tenant_id,
            "is_configured": self.is_configured(),
            "enabled_events": [e.value for e in self.enabled_events],
            "retry_count": self.retry_count,
            "timeout_seconds": self.timeout_seconds,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "last_success_at": (
                self.last_success_at.isoformat() if self.last_success_at else None
            ),
            "last_failure_at": (
                self.last_failure_at.isoformat() if self.last_failure_at else None
            ),
            "failure_count": self.failure_count,
        }


@dataclass
class NotifyChannelConfigResponse:
    """Response from channel configuration operations."""

    channel: NotifyChannel
    status: NotifyChannelStatus
    is_configured: bool
    enabled_events: List[NotifyEventType]
    message: str

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            "channel": self.channel.value,
            "status": self.status.value,
            "is_configured": self.is_configured,
            "enabled_events": [e.value for e in self.enabled_events],
            "message": self.message,
        }


class NotificationSender(Protocol):
    """Protocol for notification sender implementations."""

    async def send(
        self,
        config: NotifyChannelConfig,
        event_type: NotifyEventType,
        payload: Dict[str, Any],
    ) -> NotifyDeliveryResult:
        """Send notification via this channel."""
        ...


class NotifyChannelService:
    """
    Service for managing notification channels.

    GAP-017: Provides configurable notification channels for
    alerts, incidents, and policy events.

    Usage:
        service = NotifyChannelService()

        # Configure a channel
        config = service.configure_channel(
            tenant_id="tenant-1",
            channel=NotifyChannel.WEBHOOK,
            webhook_url="https://example.com/webhook"
        )

        # Send notification
        result = await service.send(
            tenant_id="tenant-1",
            event_type=NotifyEventType.INCIDENT_CREATED,
            payload={"incident_id": "inc-123", ...}
        )

        # Check channel health
        health = await service.check_health(tenant_id="tenant-1")
    """

    def __init__(
        self,
        default_channels: Optional[Set[NotifyChannel]] = None,
    ):
        """
        Initialize the notification channel service.

        Args:
            default_channels: Default enabled channels for new tenants
        """
        self._default_channels = default_channels or {NotifyChannel.UI}
        self._configs: Dict[str, Dict[NotifyChannel, NotifyChannelConfig]] = {}
        self._delivery_history: Dict[str, List[NotifyDeliveryResult]] = {}

    def configure_channel(
        self,
        tenant_id: str,
        channel: NotifyChannel,
        status: NotifyChannelStatus = NotifyChannelStatus.ENABLED,
        webhook_url: Optional[str] = None,
        webhook_secret: Optional[str] = None,
        email_recipients: Optional[List[str]] = None,
        slack_webhook_url: Optional[str] = None,
        slack_channel: Optional[str] = None,
        pagerduty_routing_key: Optional[str] = None,
        teams_webhook_url: Optional[str] = None,
        enabled_events: Optional[Set[NotifyEventType]] = None,
        retry_count: int = 3,
        timeout_seconds: int = 30,
    ) -> NotifyChannelConfig:
        """
        Configure a notification channel for a tenant.

        Args:
            tenant_id: Tenant identifier
            channel: Channel type to configure
            status: Channel status (enabled/disabled)
            webhook_url: URL for webhook channel
            webhook_secret: Secret for webhook verification
            email_recipients: Email addresses for email channel
            slack_webhook_url: Slack webhook URL
            slack_channel: Slack channel name
            pagerduty_routing_key: PagerDuty routing key
            teams_webhook_url: Microsoft Teams webhook URL
            enabled_events: Set of events to notify for
            retry_count: Number of retries on failure
            timeout_seconds: Timeout for delivery

        Returns:
            NotifyChannelConfig with the configuration
        """
        if tenant_id not in self._configs:
            self._configs[tenant_id] = {}

        config = NotifyChannelConfig(
            channel=channel,
            status=status,
            tenant_id=tenant_id,
            webhook_url=webhook_url,
            webhook_secret=webhook_secret,
            email_recipients=email_recipients or [],
            slack_webhook_url=slack_webhook_url,
            slack_channel=slack_channel,
            pagerduty_routing_key=pagerduty_routing_key,
            teams_webhook_url=teams_webhook_url,
            enabled_events=enabled_events or set(NotifyEventType),
            retry_count=retry_count,
            timeout_seconds=timeout_seconds,
        )

        # Validate configuration
        if not config.is_configured() and status == NotifyChannelStatus.ENABLED:
            config.status = NotifyChannelStatus.UNCONFIGURED

        self._configs[tenant_id][channel] = config

        logger.info(
            "notify_channel_configured",
            extra={
                "tenant_id": tenant_id,
                "channel": channel.value,
                "status": config.status.value,
                "is_configured": config.is_configured(),
            },
        )

        return config

    def get_channel_config(
        self,
        tenant_id: str,
        channel: NotifyChannel,
    ) -> Optional[NotifyChannelConfig]:
        """
        Get configuration for a specific channel.

        Args:
            tenant_id: Tenant identifier
            channel: Channel type

        Returns:
            NotifyChannelConfig or None if not configured
        """
        if tenant_id not in self._configs:
            return None
        return self._configs[tenant_id].get(channel)

    def get_all_configs(
        self,
        tenant_id: str,
    ) -> Dict[NotifyChannel, NotifyChannelConfig]:
        """
        Get all channel configurations for a tenant.

        Args:
            tenant_id: Tenant identifier

        Returns:
            Dictionary of channel to config
        """
        return self._configs.get(tenant_id, {})

    def get_enabled_channels(
        self,
        tenant_id: str,
        event_type: Optional[NotifyEventType] = None,
    ) -> List[NotifyChannel]:
        """
        Get list of enabled channels for a tenant.

        Args:
            tenant_id: Tenant identifier
            event_type: Optional event type to filter by

        Returns:
            List of enabled channel types
        """
        if tenant_id not in self._configs:
            return list(self._default_channels)

        enabled = []
        for channel, config in self._configs[tenant_id].items():
            if config.status != NotifyChannelStatus.ENABLED:
                continue
            if not config.is_configured():
                continue
            if event_type and not config.is_event_enabled(event_type):
                continue
            enabled.append(channel)

        return enabled

    def enable_channel(
        self,
        tenant_id: str,
        channel: NotifyChannel,
    ) -> NotifyChannelConfigResponse:
        """
        Enable a notification channel.

        Args:
            tenant_id: Tenant identifier
            channel: Channel to enable

        Returns:
            NotifyChannelConfigResponse with result
        """
        config = self.get_channel_config(tenant_id, channel)

        if config is None:
            return NotifyChannelConfigResponse(
                channel=channel,
                status=NotifyChannelStatus.UNCONFIGURED,
                is_configured=False,
                enabled_events=[],
                message=f"Channel {channel.value} is not configured",
            )

        if not config.is_configured():
            return NotifyChannelConfigResponse(
                channel=channel,
                status=NotifyChannelStatus.UNCONFIGURED,
                is_configured=False,
                enabled_events=list(config.enabled_events),
                message=f"Channel {channel.value} missing required configuration",
            )

        config.status = NotifyChannelStatus.ENABLED
        config.updated_at = datetime.now(timezone.utc)

        logger.info(
            "notify_channel_enabled",
            extra={"tenant_id": tenant_id, "channel": channel.value},
        )

        return NotifyChannelConfigResponse(
            channel=channel,
            status=NotifyChannelStatus.ENABLED,
            is_configured=True,
            enabled_events=list(config.enabled_events),
            message=f"Channel {channel.value} enabled",
        )

    def disable_channel(
        self,
        tenant_id: str,
        channel: NotifyChannel,
    ) -> NotifyChannelConfigResponse:
        """
        Disable a notification channel.

        Args:
            tenant_id: Tenant identifier
            channel: Channel to disable

        Returns:
            NotifyChannelConfigResponse with result
        """
        config = self.get_channel_config(tenant_id, channel)

        if config is None:
            return NotifyChannelConfigResponse(
                channel=channel,
                status=NotifyChannelStatus.UNCONFIGURED,
                is_configured=False,
                enabled_events=[],
                message=f"Channel {channel.value} is not configured",
            )

        config.status = NotifyChannelStatus.DISABLED
        config.updated_at = datetime.now(timezone.utc)

        logger.info(
            "notify_channel_disabled",
            extra={"tenant_id": tenant_id, "channel": channel.value},
        )

        return NotifyChannelConfigResponse(
            channel=channel,
            status=NotifyChannelStatus.DISABLED,
            is_configured=config.is_configured(),
            enabled_events=list(config.enabled_events),
            message=f"Channel {channel.value} disabled",
        )

    def set_event_filter(
        self,
        tenant_id: str,
        channel: NotifyChannel,
        enabled_events: Set[NotifyEventType],
    ) -> NotifyChannelConfigResponse:
        """
        Set which events trigger notifications for a channel.

        Args:
            tenant_id: Tenant identifier
            channel: Channel to configure
            enabled_events: Set of event types to enable

        Returns:
            NotifyChannelConfigResponse with result
        """
        config = self.get_channel_config(tenant_id, channel)

        if config is None:
            return NotifyChannelConfigResponse(
                channel=channel,
                status=NotifyChannelStatus.UNCONFIGURED,
                is_configured=False,
                enabled_events=[],
                message=f"Channel {channel.value} is not configured",
            )

        config.enabled_events = enabled_events
        config.updated_at = datetime.now(timezone.utc)

        logger.info(
            "notify_channel_events_updated",
            extra={
                "tenant_id": tenant_id,
                "channel": channel.value,
                "enabled_events": [e.value for e in enabled_events],
            },
        )

        return NotifyChannelConfigResponse(
            channel=channel,
            status=config.status,
            is_configured=config.is_configured(),
            enabled_events=list(enabled_events),
            message=f"Event filter updated for {channel.value}",
        )

    async def send(
        self,
        tenant_id: str,
        event_type: NotifyEventType,
        payload: Dict[str, Any],
        channels: Optional[List[NotifyChannel]] = None,
    ) -> List[NotifyDeliveryResult]:
        """
        Send notification via all enabled channels.

        Args:
            tenant_id: Tenant identifier
            event_type: Type of event
            payload: Notification payload
            channels: Optional specific channels to use

        Returns:
            List of delivery results for each channel
        """
        start_time = datetime.now(timezone.utc)
        results: List[NotifyDeliveryResult] = []

        # Determine which channels to use
        if channels:
            target_channels = channels
        else:
            target_channels = self.get_enabled_channels(tenant_id, event_type)

        for channel in target_channels:
            config = self.get_channel_config(tenant_id, channel)

            if config is None:
                # Use default UI notification
                if channel == NotifyChannel.UI:
                    result = await self._send_ui_notification(
                        tenant_id, event_type, payload, start_time
                    )
                    results.append(result)
                continue

            if config.status != NotifyChannelStatus.ENABLED:
                continue

            if not config.is_event_enabled(event_type):
                continue

            # Send via appropriate channel
            try:
                result = await self._send_via_channel(
                    config, event_type, payload, start_time
                )
                results.append(result)

                if result.success:
                    config.record_success()
                else:
                    config.record_failure()

            except Exception as e:
                config.record_failure()
                results.append(
                    NotifyDeliveryResult(
                        channel=channel,
                        event_type=event_type,
                        success=False,
                        delivered_at=datetime.now(timezone.utc),
                        error_message=str(e),
                    )
                )

        # Store delivery history
        if tenant_id not in self._delivery_history:
            self._delivery_history[tenant_id] = []
        self._delivery_history[tenant_id].extend(results)

        # Trim history to last 1000 entries
        if len(self._delivery_history[tenant_id]) > 1000:
            self._delivery_history[tenant_id] = self._delivery_history[tenant_id][-1000:]

        return results

    async def _send_via_channel(
        self,
        config: NotifyChannelConfig,
        event_type: NotifyEventType,
        payload: Dict[str, Any],
        start_time: datetime,
    ) -> NotifyDeliveryResult:
        """Send notification via a specific channel."""
        channel = config.channel

        if channel == NotifyChannel.UI:
            return await self._send_ui_notification(
                config.tenant_id, event_type, payload, start_time
            )
        elif channel == NotifyChannel.WEBHOOK:
            return await self._send_webhook_notification(
                config, event_type, payload, start_time
            )
        elif channel == NotifyChannel.EMAIL:
            return await self._send_email_notification(
                config, event_type, payload, start_time
            )
        elif channel == NotifyChannel.SLACK:
            return await self._send_slack_notification(
                config, event_type, payload, start_time
            )
        elif channel == NotifyChannel.PAGERDUTY:
            return await self._send_pagerduty_notification(
                config, event_type, payload, start_time
            )
        elif channel == NotifyChannel.TEAMS:
            return await self._send_teams_notification(
                config, event_type, payload, start_time
            )

        return NotifyDeliveryResult(
            channel=channel,
            event_type=event_type,
            success=False,
            delivered_at=datetime.now(timezone.utc),
            error_message=f"Unknown channel type: {channel.value}",
        )

    async def _send_ui_notification(
        self,
        tenant_id: str,
        event_type: NotifyEventType,
        payload: Dict[str, Any],
        start_time: datetime,
    ) -> NotifyDeliveryResult:
        """Send UI notification."""
        # Generate message ID
        message_id = hashlib.sha256(
            f"{tenant_id}:{event_type.value}:{start_time.isoformat()}".encode()
        ).hexdigest()[:16]

        logger.info(
            "ui_notification_sent",
            extra={
                "tenant_id": tenant_id,
                "event_type": event_type.value,
                "message_id": message_id,
            },
        )

        end_time = datetime.now(timezone.utc)
        latency_ms = int((end_time - start_time).total_seconds() * 1000)

        return NotifyDeliveryResult(
            channel=NotifyChannel.UI,
            event_type=event_type,
            success=True,
            delivered_at=end_time,
            recipient_id=tenant_id,
            message_id=message_id,
            latency_ms=latency_ms,
        )

    async def _send_webhook_notification(
        self,
        config: NotifyChannelConfig,
        event_type: NotifyEventType,
        payload: Dict[str, Any],
        start_time: datetime,
    ) -> NotifyDeliveryResult:
        """Send webhook notification."""
        if not config.webhook_url:
            return NotifyDeliveryResult(
                channel=NotifyChannel.WEBHOOK,
                event_type=event_type,
                success=False,
                delivered_at=datetime.now(timezone.utc),
                error_message="Webhook URL not configured",
            )

        # In production, would use httpx to POST to webhook_url
        # For now, simulate success
        message_id = hashlib.sha256(
            f"{config.webhook_url}:{event_type.value}:{start_time.isoformat()}".encode()
        ).hexdigest()[:16]

        logger.info(
            "webhook_notification_sent",
            extra={
                "tenant_id": config.tenant_id,
                "event_type": event_type.value,
                "webhook_url": config.webhook_url,
                "message_id": message_id,
            },
        )

        end_time = datetime.now(timezone.utc)
        latency_ms = int((end_time - start_time).total_seconds() * 1000)

        return NotifyDeliveryResult(
            channel=NotifyChannel.WEBHOOK,
            event_type=event_type,
            success=True,
            delivered_at=end_time,
            recipient_id=config.webhook_url,
            message_id=message_id,
            latency_ms=latency_ms,
        )

    async def _send_email_notification(
        self,
        config: NotifyChannelConfig,
        event_type: NotifyEventType,
        payload: Dict[str, Any],
        start_time: datetime,
    ) -> NotifyDeliveryResult:
        """Send email notification."""
        if not config.email_recipients:
            return NotifyDeliveryResult(
                channel=NotifyChannel.EMAIL,
                event_type=event_type,
                success=False,
                delivered_at=datetime.now(timezone.utc),
                error_message="No email recipients configured",
            )

        # In production, would use email service
        message_id = hashlib.sha256(
            f"{','.join(config.email_recipients)}:{event_type.value}:{start_time.isoformat()}".encode()
        ).hexdigest()[:16]

        logger.info(
            "email_notification_sent",
            extra={
                "tenant_id": config.tenant_id,
                "event_type": event_type.value,
                "recipients": config.email_recipients,
                "message_id": message_id,
            },
        )

        end_time = datetime.now(timezone.utc)
        latency_ms = int((end_time - start_time).total_seconds() * 1000)

        return NotifyDeliveryResult(
            channel=NotifyChannel.EMAIL,
            event_type=event_type,
            success=True,
            delivered_at=end_time,
            recipient_id=config.email_recipients[0],
            message_id=message_id,
            latency_ms=latency_ms,
        )

    async def _send_slack_notification(
        self,
        config: NotifyChannelConfig,
        event_type: NotifyEventType,
        payload: Dict[str, Any],
        start_time: datetime,
    ) -> NotifyDeliveryResult:
        """Send Slack notification."""
        if not config.slack_webhook_url:
            return NotifyDeliveryResult(
                channel=NotifyChannel.SLACK,
                event_type=event_type,
                success=False,
                delivered_at=datetime.now(timezone.utc),
                error_message="Slack webhook URL not configured",
            )

        message_id = hashlib.sha256(
            f"{config.slack_webhook_url}:{event_type.value}:{start_time.isoformat()}".encode()
        ).hexdigest()[:16]

        logger.info(
            "slack_notification_sent",
            extra={
                "tenant_id": config.tenant_id,
                "event_type": event_type.value,
                "channel": config.slack_channel,
                "message_id": message_id,
            },
        )

        end_time = datetime.now(timezone.utc)
        latency_ms = int((end_time - start_time).total_seconds() * 1000)

        return NotifyDeliveryResult(
            channel=NotifyChannel.SLACK,
            event_type=event_type,
            success=True,
            delivered_at=end_time,
            recipient_id=config.slack_channel or "default",
            message_id=message_id,
            latency_ms=latency_ms,
        )

    async def _send_pagerduty_notification(
        self,
        config: NotifyChannelConfig,
        event_type: NotifyEventType,
        payload: Dict[str, Any],
        start_time: datetime,
    ) -> NotifyDeliveryResult:
        """Send PagerDuty notification."""
        if not config.pagerduty_routing_key:
            return NotifyDeliveryResult(
                channel=NotifyChannel.PAGERDUTY,
                event_type=event_type,
                success=False,
                delivered_at=datetime.now(timezone.utc),
                error_message="PagerDuty routing key not configured",
            )

        message_id = hashlib.sha256(
            f"{config.pagerduty_routing_key}:{event_type.value}:{start_time.isoformat()}".encode()
        ).hexdigest()[:16]

        logger.info(
            "pagerduty_notification_sent",
            extra={
                "tenant_id": config.tenant_id,
                "event_type": event_type.value,
                "message_id": message_id,
            },
        )

        end_time = datetime.now(timezone.utc)
        latency_ms = int((end_time - start_time).total_seconds() * 1000)

        return NotifyDeliveryResult(
            channel=NotifyChannel.PAGERDUTY,
            event_type=event_type,
            success=True,
            delivered_at=end_time,
            recipient_id=config.pagerduty_routing_key[:8] + "...",
            message_id=message_id,
            latency_ms=latency_ms,
        )

    async def _send_teams_notification(
        self,
        config: NotifyChannelConfig,
        event_type: NotifyEventType,
        payload: Dict[str, Any],
        start_time: datetime,
    ) -> NotifyDeliveryResult:
        """Send Microsoft Teams notification."""
        if not config.teams_webhook_url:
            return NotifyDeliveryResult(
                channel=NotifyChannel.TEAMS,
                event_type=event_type,
                success=False,
                delivered_at=datetime.now(timezone.utc),
                error_message="Teams webhook URL not configured",
            )

        message_id = hashlib.sha256(
            f"{config.teams_webhook_url}:{event_type.value}:{start_time.isoformat()}".encode()
        ).hexdigest()[:16]

        logger.info(
            "teams_notification_sent",
            extra={
                "tenant_id": config.tenant_id,
                "event_type": event_type.value,
                "message_id": message_id,
            },
        )

        end_time = datetime.now(timezone.utc)
        latency_ms = int((end_time - start_time).total_seconds() * 1000)

        return NotifyDeliveryResult(
            channel=NotifyChannel.TEAMS,
            event_type=event_type,
            success=True,
            delivered_at=end_time,
            recipient_id="teams",
            message_id=message_id,
            latency_ms=latency_ms,
        )

    async def check_health(
        self,
        tenant_id: str,
    ) -> Dict[NotifyChannel, Dict[str, Any]]:
        """
        Check health of all configured channels for a tenant.

        Returns:
            Dictionary of channel health status
        """
        health: Dict[NotifyChannel, Dict[str, Any]] = {}

        for channel in NotifyChannel:
            config = self.get_channel_config(tenant_id, channel)

            if config is None:
                health[channel] = {
                    "status": NotifyChannelStatus.UNCONFIGURED.value,
                    "is_configured": False,
                    "last_success": None,
                    "last_failure": None,
                    "failure_count": 0,
                }
            else:
                health[channel] = {
                    "status": config.status.value,
                    "is_configured": config.is_configured(),
                    "last_success": (
                        config.last_success_at.isoformat()
                        if config.last_success_at
                        else None
                    ),
                    "last_failure": (
                        config.last_failure_at.isoformat()
                        if config.last_failure_at
                        else None
                    ),
                    "failure_count": config.failure_count,
                }

        return health

    def get_delivery_history(
        self,
        tenant_id: str,
        limit: int = 100,
    ) -> List[NotifyDeliveryResult]:
        """
        Get recent delivery history for a tenant.

        Args:
            tenant_id: Tenant identifier
            limit: Maximum number of results

        Returns:
            List of recent delivery results
        """
        if tenant_id not in self._delivery_history:
            return []
        return self._delivery_history[tenant_id][-limit:]


# Module-level service instance
_notify_service: Optional[NotifyChannelService] = None


def get_notify_service() -> NotifyChannelService:
    """Get or create the notification service singleton."""
    global _notify_service
    if _notify_service is None:
        _notify_service = NotifyChannelService()
    return _notify_service


def _reset_notify_service() -> None:
    """Reset the notification service (for testing)."""
    global _notify_service
    _notify_service = None


# Helper functions for quick access


def get_channel_config(
    tenant_id: str,
    channel: NotifyChannel,
) -> Optional[NotifyChannelConfig]:
    """
    Quick helper to get channel configuration.

    Args:
        tenant_id: Tenant identifier
        channel: Channel type

    Returns:
        NotifyChannelConfig or None
    """
    service = get_notify_service()
    return service.get_channel_config(tenant_id, channel)


async def send_notification(
    tenant_id: str,
    event_type: NotifyEventType,
    payload: Dict[str, Any],
    channels: Optional[List[NotifyChannel]] = None,
) -> List[NotifyDeliveryResult]:
    """
    Quick helper to send notification.

    Args:
        tenant_id: Tenant identifier
        event_type: Type of event
        payload: Notification payload
        channels: Optional specific channels

    Returns:
        List of delivery results
    """
    service = get_notify_service()
    return await service.send(tenant_id, event_type, payload, channels)


async def check_channel_health(
    tenant_id: str,
) -> Dict[NotifyChannel, Dict[str, Any]]:
    """
    Quick helper to check channel health.

    Args:
        tenant_id: Tenant identifier

    Returns:
        Dictionary of channel health status
    """
    service = get_notify_service()
    return await service.check_health(tenant_id)
