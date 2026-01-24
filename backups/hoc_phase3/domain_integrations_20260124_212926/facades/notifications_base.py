# Layer: L3 — Boundary Adapters
# Product: system-wide
# Temporal:
#   Trigger: api
#   Execution: async
# Role: Base class for notification adapters
# Callers: Notification adapter implementations
# Allowed Imports: L4, L6
# Forbidden Imports: L1, L2
# Reference: GAP-151, GAP-152, GAP-153

"""
Notification Base Adapter

Provides abstract interface for notification operations.
All notification adapters must implement this interface.
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class NotificationPriority(str, Enum):
    """Priority level for notifications."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class NotificationStatus(str, Enum):
    """Status of a notification."""
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"
    RETRYING = "retrying"


@dataclass
class NotificationRecipient:
    """Recipient of a notification."""

    address: str  # Email, channel ID, webhook URL, etc.
    name: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class NotificationMessage:
    """A notification message to be sent."""

    subject: str
    body: str
    recipients: List[NotificationRecipient]
    priority: NotificationPriority = NotificationPriority.NORMAL
    html_body: Optional[str] = None
    attachments: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    correlation_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "subject": self.subject,
            "body": self.body,
            "recipients": [
                {"address": r.address, "name": r.name, "metadata": r.metadata}
                for r in self.recipients
            ],
            "priority": self.priority.value,
            "html_body": self.html_body,
            "attachments": self.attachments,
            "metadata": self.metadata,
            "correlation_id": self.correlation_id,
        }


@dataclass
class NotificationResult:
    """Result of sending a notification."""

    message_id: str
    status: NotificationStatus
    recipients_succeeded: List[str] = field(default_factory=list)
    recipients_failed: List[str] = field(default_factory=list)
    error: Optional[str] = None
    sent_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def success(self) -> bool:
        return self.status in (NotificationStatus.SENT, NotificationStatus.DELIVERED)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "message_id": self.message_id,
            "status": self.status.value,
            "recipients_succeeded": self.recipients_succeeded,
            "recipients_failed": self.recipients_failed,
            "error": self.error,
            "sent_at": self.sent_at.isoformat(),
            "metadata": self.metadata,
            "success": self.success,
        }


@dataclass
class RetryConfig:
    """Configuration for retry logic."""

    max_retries: int = 3
    initial_delay_seconds: float = 1.0
    max_delay_seconds: float = 60.0
    exponential_base: float = 2.0
    jitter: bool = True
    retryable_errors: List[str] = field(default_factory=list)

    def get_delay(self, attempt: int) -> float:
        """Calculate delay for given attempt (0-indexed)."""
        import random

        delay = self.initial_delay_seconds * (self.exponential_base ** attempt)
        delay = min(delay, self.max_delay_seconds)

        if self.jitter:
            delay = delay * (0.5 + random.random())

        return delay


class NotificationAdapter(ABC):
    """
    Abstract base class for notification adapters.

    All notification implementations must implement these methods.
    """

    @abstractmethod
    async def connect(self) -> bool:
        """
        Connect to the notification service.

        Returns:
            True if connected successfully
        """
        pass

    @abstractmethod
    async def disconnect(self) -> None:
        """Disconnect from the notification service."""
        pass

    @abstractmethod
    async def send(
        self,
        message: NotificationMessage,
    ) -> NotificationResult:
        """
        Send a notification.

        Args:
            message: Notification message to send

        Returns:
            NotificationResult
        """
        pass

    @abstractmethod
    async def send_batch(
        self,
        messages: List[NotificationMessage],
        max_concurrent: int = 10,
    ) -> List[NotificationResult]:
        """
        Send multiple notifications concurrently.

        Args:
            messages: List of notification messages
            max_concurrent: Maximum concurrent sends

        Returns:
            List of NotificationResult
        """
        pass

    @abstractmethod
    async def get_status(
        self,
        message_id: str,
    ) -> Optional[NotificationResult]:
        """
        Get the status of a sent notification.

        Args:
            message_id: ID of the message to check

        Returns:
            NotificationResult or None if not found
        """
        pass

    async def health_check(self) -> bool:
        """
        Check if the notification service is healthy.

        Returns:
            True if healthy
        """
        try:
            return await self.connect()
        except Exception as e:
            logger.warning(f"Notification health check failed: {e}")
            return False
