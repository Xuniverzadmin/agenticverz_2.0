# Layer: L8 — Catalyst / Meta
# Product: system-wide
# Role: Test T3 multi-tier alert governance requirements (GAP-018)
# Reference: DOMAINS_E2E_SCAFFOLD_V3.md, GAP_IMPLEMENTATION_PLAN_V1.md

"""
T3-005: Multi-Tier Alert Tests (GAP-018)

Tests the multi-tier alerting configuration:
- GAP-018: Support 50%, 70%, 80%, 90% alert tiers instead of just NEAR/BREACH

The current implementation supports configurable near_threshold_percentage
which can be set to different values. Multi-tier alerts can be achieved
by creating multiple AlertConfig instances or using the percentage-based
threshold detection.

Key Principle:
> Alert tiers provide graduated awareness before breach.
"""

from datetime import datetime, timezone

import pytest

from app.models.alert_config import (
    AlertChannel,
    AlertConfig,
    AlertConfigCreate,
    AlertConfigResponse,
    AlertConfigUpdate,
)


# ===========================================================================
# Test: Import Verification
# ===========================================================================


class TestAlertImports:
    """Verify all alert-related imports are accessible."""

    def test_alert_config_import(self) -> None:
        """Test AlertConfig model is importable."""
        assert AlertConfig is not None

    def test_alert_channel_import(self) -> None:
        """Test AlertChannel enum is importable."""
        assert AlertChannel is not None

    def test_alert_config_create_import(self) -> None:
        """Test AlertConfigCreate model is importable."""
        assert AlertConfigCreate is not None

    def test_alert_config_update_import(self) -> None:
        """Test AlertConfigUpdate model is importable."""
        assert AlertConfigUpdate is not None

    def test_alert_config_response_import(self) -> None:
        """Test AlertConfigResponse model is importable."""
        assert AlertConfigResponse is not None


# ===========================================================================
# GAP-018: Multi-Tier Alerts
# ===========================================================================


class TestGAP018MultiTierAlerts:
    """
    GAP-018: Multi-Tier Alerts

    CURRENT: Only NEAR/BREACH (single near threshold)
    REQUIRED: Support 50%, 70%, 80%, 90% tiers
    """

    def test_near_threshold_percentage_field_exists(self) -> None:
        """AlertConfig has near_threshold_percentage field."""
        config = AlertConfig(
            policy_id="POL-001",
            tenant_id="tenant-001",
        )
        assert hasattr(config, "near_threshold_percentage")

    def test_near_threshold_default_80_percent(self) -> None:
        """Near threshold defaults to 80%."""
        config = AlertConfig(
            policy_id="POL-001",
            tenant_id="tenant-001",
        )
        assert config.near_threshold_percentage == 80

    def test_can_configure_50_percent_threshold(self) -> None:
        """Can set near threshold to 50%."""
        config = AlertConfig(
            policy_id="POL-001",
            tenant_id="tenant-001",
            near_threshold_percentage=50,
        )
        assert config.near_threshold_percentage == 50

    def test_can_configure_70_percent_threshold(self) -> None:
        """Can set near threshold to 70%."""
        config = AlertConfig(
            policy_id="POL-001",
            tenant_id="tenant-001",
            near_threshold_percentage=70,
        )
        assert config.near_threshold_percentage == 70

    def test_can_configure_90_percent_threshold(self) -> None:
        """Can set near threshold to 90%."""
        config = AlertConfig(
            policy_id="POL-001",
            tenant_id="tenant-001",
            near_threshold_percentage=90,
        )
        assert config.near_threshold_percentage == 90

    def test_should_alert_method_exists(self) -> None:
        """AlertConfig has should_alert method."""
        config = AlertConfig(
            policy_id="POL-001",
            tenant_id="tenant-001",
        )
        assert hasattr(config, "should_alert")
        assert callable(config.should_alert)

    def test_should_alert_at_threshold(self) -> None:
        """Alert should trigger when percentage reaches threshold."""
        config = AlertConfig(
            policy_id="POL-001",
            tenant_id="tenant-001",
            near_threshold_percentage=80,
            near_threshold_enabled=True,
        )
        assert config.should_alert(80.0) is True
        assert config.should_alert(90.0) is True

    def test_should_not_alert_below_threshold(self) -> None:
        """Alert should not trigger below threshold."""
        config = AlertConfig(
            policy_id="POL-001",
            tenant_id="tenant-001",
            near_threshold_percentage=80,
            near_threshold_enabled=True,
        )
        assert config.should_alert(79.9) is False
        assert config.should_alert(50.0) is False

    def test_tier_50_alert_detection(self) -> None:
        """50% tier alert detection works correctly."""
        config = AlertConfig(
            policy_id="POL-001",
            tenant_id="tenant-001",
            near_threshold_percentage=50,
            near_threshold_enabled=True,
        )
        assert config.should_alert(49.9) is False
        assert config.should_alert(50.0) is True
        assert config.should_alert(60.0) is True

    def test_tier_70_alert_detection(self) -> None:
        """70% tier alert detection works correctly."""
        config = AlertConfig(
            policy_id="POL-001",
            tenant_id="tenant-001",
            near_threshold_percentage=70,
            near_threshold_enabled=True,
        )
        assert config.should_alert(69.9) is False
        assert config.should_alert(70.0) is True
        assert config.should_alert(80.0) is True

    def test_tier_90_alert_detection(self) -> None:
        """90% tier alert detection works correctly."""
        config = AlertConfig(
            policy_id="POL-001",
            tenant_id="tenant-001",
            near_threshold_percentage=90,
            near_threshold_enabled=True,
        )
        assert config.should_alert(89.9) is False
        assert config.should_alert(90.0) is True
        assert config.should_alert(95.0) is True

    def test_breach_alert_enabled_field(self) -> None:
        """AlertConfig has breach_alert_enabled field."""
        config = AlertConfig(
            policy_id="POL-001",
            tenant_id="tenant-001",
        )
        assert hasattr(config, "breach_alert_enabled")
        assert config.breach_alert_enabled is True  # Default


# ===========================================================================
# Test: Alert Channels
# ===========================================================================


class TestAlertChannels:
    """Test AlertChannel enum and channel configuration."""

    def test_ui_channel_exists(self) -> None:
        """UI alert channel exists."""
        assert AlertChannel.UI.value == "ui"

    def test_webhook_channel_exists(self) -> None:
        """WEBHOOK alert channel exists."""
        assert AlertChannel.WEBHOOK.value == "webhook"

    def test_email_channel_exists(self) -> None:
        """EMAIL alert channel exists."""
        assert AlertChannel.EMAIL.value == "email"

    def test_slack_channel_exists(self) -> None:
        """SLACK alert channel exists."""
        assert AlertChannel.SLACK.value == "slack"

    def test_enabled_channels_property(self) -> None:
        """Can get enabled channels as list."""
        config = AlertConfig(
            policy_id="POL-001",
            tenant_id="tenant-001",
        )
        channels = config.enabled_channels
        assert isinstance(channels, list)
        assert AlertChannel.UI in channels  # Default

    def test_can_enable_multiple_channels(self) -> None:
        """Can enable multiple alert channels."""
        config = AlertConfig(
            policy_id="POL-001",
            tenant_id="tenant-001",
        )
        config.enabled_channels = [
            AlertChannel.UI,
            AlertChannel.SLACK,
            AlertChannel.EMAIL,
        ]
        channels = config.enabled_channels
        assert len(channels) == 3
        assert AlertChannel.UI in channels
        assert AlertChannel.SLACK in channels
        assert AlertChannel.EMAIL in channels


# ===========================================================================
# Test: Alert Throttling
# ===========================================================================


class TestAlertThrottling:
    """Test alert throttling to prevent alert fatigue."""

    def test_min_alert_interval_field_exists(self) -> None:
        """AlertConfig has min_alert_interval_seconds field."""
        config = AlertConfig(
            policy_id="POL-001",
            tenant_id="tenant-001",
        )
        assert hasattr(config, "min_alert_interval_seconds")
        assert config.min_alert_interval_seconds == 60  # Default

    def test_max_alerts_per_run_field_exists(self) -> None:
        """AlertConfig has max_alerts_per_run field."""
        config = AlertConfig(
            policy_id="POL-001",
            tenant_id="tenant-001",
        )
        assert hasattr(config, "max_alerts_per_run")
        assert config.max_alerts_per_run == 10  # Default

    def test_is_throttled_method(self) -> None:
        """AlertConfig has is_throttled method."""
        config = AlertConfig(
            policy_id="POL-001",
            tenant_id="tenant-001",
        )
        assert hasattr(config, "is_throttled")
        assert callable(config.is_throttled)

    def test_can_send_alert_method(self) -> None:
        """AlertConfig has can_send_alert method."""
        config = AlertConfig(
            policy_id="POL-001",
            tenant_id="tenant-001",
        )
        assert hasattr(config, "can_send_alert")
        assert callable(config.can_send_alert)

    def test_not_throttled_initially(self) -> None:
        """Alerts are not throttled initially."""
        config = AlertConfig(
            policy_id="POL-001",
            tenant_id="tenant-001",
        )
        assert config.is_throttled() is False
        assert config.can_send_alert(run_alert_count=0) is True

    def test_record_alert_sent_method(self) -> None:
        """Can record when alert is sent."""
        config = AlertConfig(
            policy_id="POL-001",
            tenant_id="tenant-001",
        )
        assert config.last_alert_at is None
        assert config.alerts_sent_count == 0

        config.record_alert_sent()

        assert config.last_alert_at is not None
        assert config.alerts_sent_count == 1

    def test_throttle_after_recent_alert(self) -> None:
        """Alerts are throttled after recent alert."""
        config = AlertConfig(
            policy_id="POL-001",
            tenant_id="tenant-001",
            min_alert_interval_seconds=60,
        )
        config.record_alert_sent()
        # Should be throttled immediately after sending
        assert config.is_throttled() is True


# ===========================================================================
# Test: Alert Config Webhook
# ===========================================================================


class TestAlertWebhookConfig:
    """Test webhook configuration for alerts."""

    def test_webhook_url_field_exists(self) -> None:
        """AlertConfig has webhook_url field."""
        config = AlertConfig(
            policy_id="POL-001",
            tenant_id="tenant-001",
        )
        assert hasattr(config, "webhook_url")

    def test_webhook_secret_field_exists(self) -> None:
        """AlertConfig has webhook_secret field."""
        config = AlertConfig(
            policy_id="POL-001",
            tenant_id="tenant-001",
        )
        assert hasattr(config, "webhook_secret")

    def test_can_configure_webhook(self) -> None:
        """Can configure webhook URL and secret."""
        config = AlertConfig(
            policy_id="POL-001",
            tenant_id="tenant-001",
            webhook_url="https://example.com/webhook",
            webhook_secret="secret123",
        )
        assert config.webhook_url == "https://example.com/webhook"
        assert config.webhook_secret == "secret123"


# ===========================================================================
# Test: Alert Config Slack
# ===========================================================================


class TestAlertSlackConfig:
    """Test Slack configuration for alerts."""

    def test_slack_webhook_url_field_exists(self) -> None:
        """AlertConfig has slack_webhook_url field."""
        config = AlertConfig(
            policy_id="POL-001",
            tenant_id="tenant-001",
        )
        assert hasattr(config, "slack_webhook_url")

    def test_slack_channel_field_exists(self) -> None:
        """AlertConfig has slack_channel field."""
        config = AlertConfig(
            policy_id="POL-001",
            tenant_id="tenant-001",
        )
        assert hasattr(config, "slack_channel")

    def test_can_configure_slack(self) -> None:
        """Can configure Slack webhook and channel."""
        config = AlertConfig(
            policy_id="POL-001",
            tenant_id="tenant-001",
            slack_webhook_url="https://hooks.slack.com/services/XXX",
            slack_channel="#alerts",
        )
        assert config.slack_webhook_url == "https://hooks.slack.com/services/XXX"
        assert config.slack_channel == "#alerts"


# ===========================================================================
# Test: Alert Config Email
# ===========================================================================


class TestAlertEmailConfig:
    """Test email configuration for alerts."""

    def test_email_recipients_field_exists(self) -> None:
        """AlertConfig has email_recipients_json field."""
        config = AlertConfig(
            policy_id="POL-001",
            tenant_id="tenant-001",
        )
        assert hasattr(config, "email_recipients_json")

    def test_email_recipients_property(self) -> None:
        """Can get and set email recipients via property."""
        config = AlertConfig(
            policy_id="POL-001",
            tenant_id="tenant-001",
        )
        # Initially empty
        assert config.email_recipients == []

        # Set recipients
        config.email_recipients = ["admin@example.com", "alerts@example.com"]
        assert len(config.email_recipients) == 2
        assert "admin@example.com" in config.email_recipients


# ===========================================================================
# Test: Pydantic Models
# ===========================================================================


class TestAlertPydanticModels:
    """Test Pydantic models for API operations."""

    def test_create_model_has_near_threshold(self) -> None:
        """AlertConfigCreate has near_threshold_percentage."""
        create = AlertConfigCreate(
            policy_id="POL-001",
            near_threshold_percentage=70,
        )
        assert create.near_threshold_percentage == 70

    def test_create_model_defaults(self) -> None:
        """AlertConfigCreate has sensible defaults."""
        create = AlertConfigCreate(policy_id="POL-001")
        assert create.near_threshold_enabled is True
        assert create.near_threshold_percentage == 80
        assert create.breach_alert_enabled is True
        assert AlertChannel.UI in create.enabled_channels

    def test_update_model_all_optional(self) -> None:
        """AlertConfigUpdate has all fields optional."""
        update = AlertConfigUpdate()
        assert update.near_threshold_percentage is None
        assert update.near_threshold_enabled is None

    def test_response_model_structure(self) -> None:
        """AlertConfigResponse has expected structure."""
        response = AlertConfigResponse(
            policy_id="POL-001",
            tenant_id="tenant-001",
            near_threshold_enabled=True,
            near_threshold_percentage=80,
            breach_alert_enabled=True,
            enabled_channels=[AlertChannel.UI],
            webhook_url=None,
            email_recipients=[],
            slack_channel=None,
            min_alert_interval_seconds=60,
            max_alerts_per_run=10,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        assert response.policy_id == "POL-001"
        assert response.near_threshold_percentage == 80
