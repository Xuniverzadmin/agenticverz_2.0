# Layer: L3 — Boundary Adapters
# Product: system-wide
# Temporal:
#   Trigger: api
#   Execution: async
# Role: Notification adapters
# Callers: NotificationService, AlertManager
# Allowed Imports: L4, L6
# Forbidden Imports: L1, L2
# Reference: GAP-151, GAP-152, GAP-153 (Notification Adapters)

"""
Notification Adapters (GAP-151, GAP-152, GAP-153)

Provides adapters for sending notifications:
- SMTP Email (GAP-151)
- Slack (GAP-152)
- Webhooks with Retry Logic (GAP-153)

Features:
- Unified interface for notification delivery
- Retry logic with exponential backoff
- Circuit breaker pattern
- Rich message formatting
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .base import NotificationAdapter
    from .smtp_adapter import SMTPAdapter
    from .slack_adapter import SlackAdapter
    from .webhook_adapter import WebhookAdapter

__all__ = [
    "NotificationAdapter",
    "SMTPAdapter",
    "SlackAdapter",
    "WebhookAdapter",
    "get_notification_adapter",
    "NotificationType",
]


from enum import Enum


class NotificationType(str, Enum):
    """Supported notification types."""
    SMTP = "smtp"
    SLACK = "slack"
    WEBHOOK = "webhook"


def get_notification_adapter(
    notification_type: NotificationType,
    **config,
):
    """
    Factory function to get a notification adapter.

    Args:
        notification_type: Type of notification channel
        **config: Channel-specific configuration

    Returns:
        NotificationAdapter instance
    """
    if notification_type == NotificationType.SMTP:
        from .smtp_adapter import SMTPAdapter
        return SMTPAdapter(**config)
    elif notification_type == NotificationType.SLACK:
        from .slack_adapter import SlackAdapter
        return SlackAdapter(**config)
    elif notification_type == NotificationType.WEBHOOK:
        from .webhook_adapter import WebhookAdapter
        return WebhookAdapter(**config)
    else:
        raise ValueError(f"Unsupported notification type: {notification_type}")
