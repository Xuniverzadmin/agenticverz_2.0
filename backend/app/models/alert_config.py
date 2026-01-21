# Layer: L4 — Domain Engine
# Product: AI Console
# Temporal:
#   Trigger: api
#   Execution: sync
# Role: Configure alerting behavior for near-threshold events
# Callers: services/alert_emitter.py, api/policy_alerts.py
# Allowed Imports: L5, L6
# Forbidden Imports: L1, L2, L3
# Reference: POLICY_CONTROL_LEVER_IMPLEMENTATION_PLAN.md PCL-007

"""
Alert Configuration Model

Configures how and when alerts are sent for threshold events:
- Near-threshold percentage trigger
- Notification channels (UI, webhook)
- Alert throttling

Alert flow:
1. ThresholdSignal created (NEAR or BREACH)
2. AlertEmitter checks AlertConfig
3. If enabled and not throttled, send via configured channels
"""

import json
from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from pydantic import BaseModel
from sqlmodel import Field, SQLModel


class AlertChannel(str, Enum):
    """Available alert notification channels."""

    UI = "ui"  # In-app notification
    WEBHOOK = "webhook"  # External webhook
    EMAIL = "email"  # Email notification
    SLACK = "slack"  # Slack integration


class AlertConfig(SQLModel, table=True):
    """
    Alert configuration for a policy.

    Defines when and how alerts are sent for threshold events.
    Supports multiple notification channels and throttling to
    prevent alert fatigue.
    """

    __tablename__ = "policy_alert_configs"

    id: Optional[int] = Field(default=None, primary_key=True)
    policy_id: str = Field(index=True, unique=True)  # FK to policy_rules.policy_id
    tenant_id: str = Field(index=True)  # FK to tenants.id

    # Near-threshold alerting
    near_threshold_enabled: bool = Field(default=True)
    near_threshold_percentage: int = Field(default=80)  # Alert at 80% of threshold

    # Breach alerting
    breach_alert_enabled: bool = Field(default=True)

    # Notification channels (JSON array)
    enabled_channels_json: str = Field(default='["ui"]')

    # Webhook configuration
    webhook_url: Optional[str] = Field(default=None)
    webhook_secret: Optional[str] = Field(default=None)

    # Email configuration
    email_recipients_json: Optional[str] = Field(default=None)  # JSON array

    # Slack configuration
    slack_webhook_url: Optional[str] = Field(default=None)
    slack_channel: Optional[str] = Field(default=None)

    # Alert throttling
    min_alert_interval_seconds: int = Field(default=60)  # Min time between alerts
    max_alerts_per_run: int = Field(default=10)  # Max alerts for a single run

    # Metadata
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # Last alert tracking (for throttling)
    last_alert_at: Optional[datetime] = Field(default=None)
    alerts_sent_count: int = Field(default=0)

    @property
    def enabled_channels(self) -> list[AlertChannel]:
        """Get enabled channels as list."""
        if self.enabled_channels_json:
            return [AlertChannel(c) for c in json.loads(self.enabled_channels_json)]
        return [AlertChannel.UI]

    @enabled_channels.setter
    def enabled_channels(self, value: list[AlertChannel]) -> None:
        """Set enabled channels from list."""
        self.enabled_channels_json = json.dumps([c.value for c in value])

    @property
    def email_recipients(self) -> list[str]:
        """Get email recipients as list."""
        if self.email_recipients_json:
            return json.loads(self.email_recipients_json)
        return []

    @email_recipients.setter
    def email_recipients(self, value: list[str]) -> None:
        """Set email recipients from list."""
        self.email_recipients_json = json.dumps(value) if value else None

    def should_alert(self, current_percentage: float) -> bool:
        """Check if alert should be sent based on percentage."""
        return (
            self.near_threshold_enabled
            and current_percentage >= self.near_threshold_percentage
        )

    def is_throttled(self) -> bool:
        """Check if alerts are currently throttled."""
        if self.last_alert_at is None:
            return False
        elapsed = (datetime.now(timezone.utc) - self.last_alert_at).total_seconds()
        return elapsed < self.min_alert_interval_seconds

    def can_send_alert(self, run_alert_count: int) -> bool:
        """Check if alert can be sent (not throttled, not exceeded max)."""
        return not self.is_throttled() and run_alert_count < self.max_alerts_per_run

    def record_alert_sent(self) -> None:
        """Record that an alert was sent."""
        self.last_alert_at = datetime.now(timezone.utc)
        self.alerts_sent_count += 1


class AlertConfigCreate(BaseModel):
    """Request model for creating alert config."""

    policy_id: str
    near_threshold_enabled: bool = True
    near_threshold_percentage: int = 80
    breach_alert_enabled: bool = True
    enabled_channels: list[AlertChannel] = [AlertChannel.UI]
    webhook_url: Optional[str] = None
    webhook_secret: Optional[str] = None
    email_recipients: Optional[list[str]] = None
    slack_webhook_url: Optional[str] = None
    slack_channel: Optional[str] = None
    min_alert_interval_seconds: int = 60
    max_alerts_per_run: int = 10


class AlertConfigUpdate(BaseModel):
    """Request model for updating alert config."""

    near_threshold_enabled: Optional[bool] = None
    near_threshold_percentage: Optional[int] = None
    breach_alert_enabled: Optional[bool] = None
    enabled_channels: Optional[list[AlertChannel]] = None
    webhook_url: Optional[str] = None
    webhook_secret: Optional[str] = None
    email_recipients: Optional[list[str]] = None
    slack_webhook_url: Optional[str] = None
    slack_channel: Optional[str] = None
    min_alert_interval_seconds: Optional[int] = None
    max_alerts_per_run: Optional[int] = None


class AlertConfigResponse(BaseModel):
    """Response model for alert config."""

    policy_id: str
    tenant_id: str
    near_threshold_enabled: bool
    near_threshold_percentage: int
    breach_alert_enabled: bool
    enabled_channels: list[AlertChannel]
    webhook_url: Optional[str]
    email_recipients: list[str]
    slack_channel: Optional[str]
    min_alert_interval_seconds: int
    max_alerts_per_run: int
    created_at: datetime
    updated_at: datetime
