# Layer: L5 — Domain Engine
# AUDIENCE: CUSTOMER
# Product: system-wide
# Location: hoc/cus/account/L5_engines/notifications_facade.py
# Temporal:
#   Trigger: api or worker (async delivery)
#   Execution: async
# Role: Notifications Facade - Centralized access to notification operations
# Callers: L2 notifications.py API, SDK, Worker
# Allowed Imports: L5, L6
# Forbidden Imports: L1, L2, L3, L7
# Reference: GAP-109, PHASE3_DIRECTORY_RESTRUCTURE_PLAN.md
#
# L4 is reserved for general/L4_runtime/ only per HOC Layer Topology.

"""
Notifications Facade (L5 Domain Engine)

This facade provides the external interface for notification operations.
All notification APIs MUST use this facade instead of directly importing
internal notification modules.

Why This Facade Exists:
- Prevents L2→L4 layer violations
- Centralizes notification delivery logic
- Provides unified access to multiple notification channels
- Single point for audit emission

L2 API Routes (GAP-109):
- POST /api/v1/notifications (send notification)
- GET /api/v1/notifications (list notifications)
- GET /api/v1/notifications/{id} (get notification)
- POST /api/v1/notifications/{id}/read (mark as read)
- GET /api/v1/notifications/channels (list channels)
- PUT /api/v1/notifications/preferences (update preferences)

Usage:
    from app.hoc.cus.account.L5_engines import get_notifications_facade

    facade = get_notifications_facade()

    # Send notification
    result = await facade.send_notification(
        tenant_id="...",
        channel="email",
        recipient="...",
        message="...",
    )
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
import uuid

logger = logging.getLogger("nova.services.notifications.facade")


class NotificationChannel(str, Enum):
    """Notification channels."""
    EMAIL = "email"
    SLACK = "slack"
    WEBHOOK = "webhook"
    IN_APP = "in_app"
    SMS = "sms"


class NotificationPriority(str, Enum):
    """Notification priorities."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class NotificationStatus(str, Enum):
    """Notification delivery status."""
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"
    READ = "read"


@dataclass
class NotificationInfo:
    """Notification information."""
    id: str
    tenant_id: str
    channel: str
    recipient: str
    subject: Optional[str]
    message: str
    priority: str
    status: str
    created_at: str
    sent_at: Optional[str] = None
    read_at: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "tenant_id": self.tenant_id,
            "channel": self.channel,
            "recipient": self.recipient,
            "subject": self.subject,
            "message": self.message,
            "priority": self.priority,
            "status": self.status,
            "created_at": self.created_at,
            "sent_at": self.sent_at,
            "read_at": self.read_at,
            "metadata": self.metadata,
        }


@dataclass
class ChannelInfo:
    """Notification channel information."""
    id: str
    name: str
    enabled: bool
    configured: bool
    config_required: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "enabled": self.enabled,
            "configured": self.configured,
            "config_required": self.config_required,
        }


@dataclass
class NotificationPreferences:
    """User notification preferences."""
    tenant_id: str
    user_id: str
    channels: Dict[str, bool]
    priorities: Dict[str, List[str]]  # channel -> list of priorities to receive

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "tenant_id": self.tenant_id,
            "user_id": self.user_id,
            "channels": self.channels,
            "priorities": self.priorities,
        }


class NotificationsFacade:
    """
    Facade for notification operations.

    This is the ONLY entry point for L2 APIs and SDK to interact with
    notification services.

    Layer: L4 (Domain Logic)
    Callers: notifications.py (L2), aos_sdk, Worker
    """

    def __init__(self):
        """Initialize facade."""
        # In-memory stores for demo (would be database in production)
        self._notifications: Dict[str, NotificationInfo] = {}
        self._preferences: Dict[str, NotificationPreferences] = {}

        # Available channels
        self._channels = {
            "email": ChannelInfo(
                id="email",
                name="Email",
                enabled=True,
                configured=True,
                config_required=["smtp_host", "smtp_user"],
            ),
            "slack": ChannelInfo(
                id="slack",
                name="Slack",
                enabled=True,
                configured=False,
                config_required=["webhook_url"],
            ),
            "webhook": ChannelInfo(
                id="webhook",
                name="Webhook",
                enabled=True,
                configured=False,
                config_required=["url", "secret"],
            ),
            "in_app": ChannelInfo(
                id="in_app",
                name="In-App",
                enabled=True,
                configured=True,
                config_required=[],
            ),
            "sms": ChannelInfo(
                id="sms",
                name="SMS",
                enabled=False,
                configured=False,
                config_required=["twilio_sid", "twilio_token"],
            ),
        }

    # =========================================================================
    # Notification Operations (GAP-109)
    # =========================================================================

    async def send_notification(
        self,
        tenant_id: str,
        channel: str,
        recipient: str,
        message: str,
        subject: Optional[str] = None,
        priority: str = "normal",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> NotificationInfo:
        """
        Send a notification.

        Args:
            tenant_id: Tenant ID
            channel: Notification channel (email, slack, webhook, in_app, sms)
            recipient: Recipient (email, user_id, webhook_url, etc.)
            message: Notification message
            subject: Optional subject (for email)
            priority: Priority (low, normal, high, urgent)
            metadata: Additional metadata

        Returns:
            NotificationInfo with delivery status
        """
        logger.info(
            "facade.send_notification",
            extra={
                "tenant_id": tenant_id,
                "channel": channel,
                "priority": priority,
            }
        )

        now = datetime.now(timezone.utc)
        notification_id = str(uuid.uuid4())

        # Create notification record
        notification = NotificationInfo(
            id=notification_id,
            tenant_id=tenant_id,
            channel=channel,
            recipient=recipient,
            subject=subject,
            message=message,
            priority=priority,
            status=NotificationStatus.PENDING.value,
            created_at=now.isoformat(),
            metadata=metadata or {},
        )

        # Simulate delivery (in production, would queue async delivery)
        channel_info = self._channels.get(channel)
        if not channel_info or not channel_info.enabled:
            notification.status = NotificationStatus.FAILED.value
            notification.metadata["error"] = f"Channel {channel} not available"
        elif not channel_info.configured:
            notification.status = NotificationStatus.FAILED.value
            notification.metadata["error"] = f"Channel {channel} not configured"
        else:
            notification.status = NotificationStatus.SENT.value
            notification.sent_at = now.isoformat()

        self._notifications[notification_id] = notification
        return notification

    async def list_notifications(
        self,
        tenant_id: str,
        channel: Optional[str] = None,
        status: Optional[str] = None,
        recipient: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[NotificationInfo]:
        """
        List notifications.

        Args:
            tenant_id: Tenant ID
            channel: Optional filter by channel
            status: Optional filter by status
            recipient: Optional filter by recipient
            limit: Maximum results
            offset: Pagination offset

        Returns:
            List of NotificationInfo
        """
        results = []
        for notification in self._notifications.values():
            if notification.tenant_id != tenant_id:
                continue
            if channel and notification.channel != channel:
                continue
            if status and notification.status != status:
                continue
            if recipient and notification.recipient != recipient:
                continue
            results.append(notification)

        # Sort by created_at descending
        results.sort(key=lambda n: n.created_at, reverse=True)

        return results[offset:offset + limit]

    async def get_notification(
        self,
        notification_id: str,
        tenant_id: str,
    ) -> Optional[NotificationInfo]:
        """
        Get a specific notification.

        Args:
            notification_id: Notification ID
            tenant_id: Tenant ID for authorization

        Returns:
            NotificationInfo or None if not found
        """
        notification = self._notifications.get(notification_id)
        if notification and notification.tenant_id == tenant_id:
            return notification
        return None

    async def mark_as_read(
        self,
        notification_id: str,
        tenant_id: str,
    ) -> Optional[NotificationInfo]:
        """
        Mark notification as read.

        Args:
            notification_id: Notification ID
            tenant_id: Tenant ID for authorization

        Returns:
            Updated NotificationInfo or None if not found
        """
        notification = self._notifications.get(notification_id)
        if not notification or notification.tenant_id != tenant_id:
            return None

        notification.status = NotificationStatus.READ.value
        notification.read_at = datetime.now(timezone.utc).isoformat()
        return notification

    # =========================================================================
    # Channel Operations (GAP-109)
    # =========================================================================

    async def list_channels(self) -> List[ChannelInfo]:
        """
        List available notification channels.

        Returns:
            List of ChannelInfo
        """
        return list(self._channels.values())

    async def get_channel(self, channel_id: str) -> Optional[ChannelInfo]:
        """
        Get a specific channel.

        Args:
            channel_id: Channel ID

        Returns:
            ChannelInfo or None if not found
        """
        return self._channels.get(channel_id)

    # =========================================================================
    # Preference Operations (GAP-109)
    # =========================================================================

    async def get_preferences(
        self,
        tenant_id: str,
        user_id: str,
    ) -> NotificationPreferences:
        """
        Get notification preferences.

        Args:
            tenant_id: Tenant ID
            user_id: User ID

        Returns:
            NotificationPreferences
        """
        key = f"{tenant_id}:{user_id}"
        if key not in self._preferences:
            # Return defaults
            return NotificationPreferences(
                tenant_id=tenant_id,
                user_id=user_id,
                channels={c: True for c in self._channels if self._channels[c].enabled},
                priorities={c: ["high", "urgent"] for c in self._channels},
            )
        return self._preferences[key]

    async def update_preferences(
        self,
        tenant_id: str,
        user_id: str,
        channels: Optional[Dict[str, bool]] = None,
        priorities: Optional[Dict[str, List[str]]] = None,
    ) -> NotificationPreferences:
        """
        Update notification preferences.

        Args:
            tenant_id: Tenant ID
            user_id: User ID
            channels: Channel enable/disable settings
            priorities: Priority settings per channel

        Returns:
            Updated NotificationPreferences
        """
        key = f"{tenant_id}:{user_id}"
        prefs = await self.get_preferences(tenant_id, user_id)

        if channels:
            prefs.channels.update(channels)
        if priorities:
            prefs.priorities.update(priorities)

        self._preferences[key] = prefs
        return prefs


# =============================================================================
# Module-level singleton accessor
# =============================================================================

_facade_instance: Optional[NotificationsFacade] = None


def get_notifications_facade() -> NotificationsFacade:
    """
    Get the notifications facade instance.

    This is the recommended way to access notification operations
    from L2 APIs and the SDK.

    Returns:
        NotificationsFacade instance
    """
    global _facade_instance
    if _facade_instance is None:
        _facade_instance = NotificationsFacade()
    return _facade_instance
