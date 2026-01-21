# Layer: L4 — Domain Engines
# Product: system-wide
# Reference: GAP-017 (Notify Channels)
"""
Notification Services (GAP-017)

Provides configurable notification channels for alerts, incidents,
and policy events. Supports UI, Webhook, Email, and Slack channels.

This module provides:
    - NotifyChannel: Enum of available notification channels
    - NotifyChannelConfig: Channel configuration model
    - NotifyChannelService: Service for channel management
    - NotifyDeliveryResult: Delivery result tracking
    - Helper functions for notification operations
"""

from app.services.notifications.channel_service import (
    NotifyChannel,
    NotifyChannelConfig,
    NotifyChannelConfigResponse,
    NotifyChannelError,
    NotifyChannelService,
    NotifyChannelStatus,
    NotifyDeliveryResult,
    NotifyEventType,
    check_channel_health,
    get_channel_config,
    send_notification,
)

__all__ = [
    "NotifyChannel",
    "NotifyChannelConfig",
    "NotifyChannelConfigResponse",
    "NotifyChannelError",
    "NotifyChannelService",
    "NotifyChannelStatus",
    "NotifyDeliveryResult",
    "NotifyEventType",
    "check_channel_health",
    "get_channel_config",
    "send_notification",
]
