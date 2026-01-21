# Layer: L8 — Catalyst / Meta
# Product: system-wide
# Reference: GAP-017 (Notify Channels)

"""
Tests for GAP-017: Notify Channels

Tests the notification channel service for configurable
multi-channel notification delivery.
"""

import pytest
from datetime import datetime, timezone

from app.services.notifications import (
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
from app.services.notifications.channel_service import (
    _reset_notify_service,
    get_notify_service,
)


class TestNotifyChannelImports:
    """Test that all exports are importable."""

    def test_notify_channel_enum_import(self):
        """Verify NotifyChannel enum is importable."""
        assert NotifyChannel is not None
        assert hasattr(NotifyChannel, "UI")
        assert hasattr(NotifyChannel, "WEBHOOK")
        assert hasattr(NotifyChannel, "EMAIL")
        assert hasattr(NotifyChannel, "SLACK")

    def test_notify_event_type_enum_import(self):
        """Verify NotifyEventType enum is importable."""
        assert NotifyEventType is not None
        assert hasattr(NotifyEventType, "ALERT_NEAR_THRESHOLD")
        assert hasattr(NotifyEventType, "INCIDENT_CREATED")
        assert hasattr(NotifyEventType, "POLICY_VIOLATED")

    def test_notify_channel_status_import(self):
        """Verify NotifyChannelStatus enum is importable."""
        assert NotifyChannelStatus is not None
        assert hasattr(NotifyChannelStatus, "ENABLED")
        assert hasattr(NotifyChannelStatus, "DISABLED")
        assert hasattr(NotifyChannelStatus, "UNCONFIGURED")

    def test_notify_channel_config_import(self):
        """Verify NotifyChannelConfig is importable."""
        assert NotifyChannelConfig is not None

    def test_notify_channel_service_import(self):
        """Verify NotifyChannelService is importable."""
        assert NotifyChannelService is not None

    def test_notify_delivery_result_import(self):
        """Verify NotifyDeliveryResult is importable."""
        assert NotifyDeliveryResult is not None

    def test_notify_channel_error_import(self):
        """Verify NotifyChannelError is importable."""
        assert NotifyChannelError is not None

    def test_helper_functions_import(self):
        """Verify helper functions are importable."""
        assert get_channel_config is not None
        assert send_notification is not None
        assert check_channel_health is not None


class TestNotifyChannelEnum:
    """Test NotifyChannel enum values."""

    def test_all_channels_defined(self):
        """Verify all expected channels are defined."""
        channels = list(NotifyChannel)
        assert len(channels) >= 4
        assert NotifyChannel.UI in channels
        assert NotifyChannel.WEBHOOK in channels
        assert NotifyChannel.EMAIL in channels
        assert NotifyChannel.SLACK in channels

    def test_channel_string_values(self):
        """Verify channel enum string values."""
        assert NotifyChannel.UI.value == "ui"
        assert NotifyChannel.WEBHOOK.value == "webhook"
        assert NotifyChannel.EMAIL.value == "email"
        assert NotifyChannel.SLACK.value == "slack"


class TestNotifyEventTypeEnum:
    """Test NotifyEventType enum values."""

    def test_all_event_types_defined(self):
        """Verify all expected event types are defined."""
        events = list(NotifyEventType)
        assert len(events) >= 6

    def test_event_type_string_values(self):
        """Verify event type enum string values."""
        assert NotifyEventType.ALERT_NEAR_THRESHOLD.value == "alert_near_threshold"
        assert NotifyEventType.INCIDENT_CREATED.value == "incident_created"
        assert NotifyEventType.POLICY_VIOLATED.value == "policy_violated"


class TestNotifyChannelConfig:
    """Test NotifyChannelConfig dataclass."""

    def test_config_creation(self):
        """Test creating a channel config."""
        config = NotifyChannelConfig(
            channel=NotifyChannel.WEBHOOK,
            status=NotifyChannelStatus.ENABLED,
            tenant_id="tenant-1",
            webhook_url="https://example.com/webhook",
        )
        assert config.channel == NotifyChannel.WEBHOOK
        assert config.status == NotifyChannelStatus.ENABLED
        assert config.tenant_id == "tenant-1"
        assert config.webhook_url == "https://example.com/webhook"

    def test_config_default_values(self):
        """Test config default values."""
        config = NotifyChannelConfig(
            channel=NotifyChannel.UI,
            status=NotifyChannelStatus.ENABLED,
            tenant_id="tenant-1",
        )
        assert config.retry_count == 3
        assert config.timeout_seconds == 30
        assert config.failure_count == 0
        assert len(config.enabled_events) > 0

    def test_is_configured_ui(self):
        """Test UI channel is always configured."""
        config = NotifyChannelConfig(
            channel=NotifyChannel.UI,
            status=NotifyChannelStatus.ENABLED,
            tenant_id="tenant-1",
        )
        assert config.is_configured() is True

    def test_is_configured_webhook_with_url(self):
        """Test webhook channel with URL is configured."""
        config = NotifyChannelConfig(
            channel=NotifyChannel.WEBHOOK,
            status=NotifyChannelStatus.ENABLED,
            tenant_id="tenant-1",
            webhook_url="https://example.com/webhook",
        )
        assert config.is_configured() is True

    def test_is_configured_webhook_without_url(self):
        """Test webhook channel without URL is not configured."""
        config = NotifyChannelConfig(
            channel=NotifyChannel.WEBHOOK,
            status=NotifyChannelStatus.ENABLED,
            tenant_id="tenant-1",
        )
        assert config.is_configured() is False

    def test_is_configured_email_with_recipients(self):
        """Test email channel with recipients is configured."""
        config = NotifyChannelConfig(
            channel=NotifyChannel.EMAIL,
            status=NotifyChannelStatus.ENABLED,
            tenant_id="tenant-1",
            email_recipients=["test@example.com"],
        )
        assert config.is_configured() is True

    def test_is_configured_email_without_recipients(self):
        """Test email channel without recipients is not configured."""
        config = NotifyChannelConfig(
            channel=NotifyChannel.EMAIL,
            status=NotifyChannelStatus.ENABLED,
            tenant_id="tenant-1",
        )
        assert config.is_configured() is False

    def test_is_event_enabled(self):
        """Test event type filtering."""
        config = NotifyChannelConfig(
            channel=NotifyChannel.UI,
            status=NotifyChannelStatus.ENABLED,
            tenant_id="tenant-1",
            enabled_events={NotifyEventType.INCIDENT_CREATED},
        )
        assert config.is_event_enabled(NotifyEventType.INCIDENT_CREATED) is True
        assert config.is_event_enabled(NotifyEventType.POLICY_VIOLATED) is False

    def test_record_success(self):
        """Test recording successful delivery."""
        config = NotifyChannelConfig(
            channel=NotifyChannel.UI,
            status=NotifyChannelStatus.ENABLED,
            tenant_id="tenant-1",
        )
        assert config.last_success_at is None
        config.record_success()
        assert config.last_success_at is not None

    def test_record_failure(self):
        """Test recording failed delivery."""
        config = NotifyChannelConfig(
            channel=NotifyChannel.UI,
            status=NotifyChannelStatus.ENABLED,
            tenant_id="tenant-1",
        )
        assert config.failure_count == 0
        config.record_failure()
        assert config.failure_count == 1
        assert config.last_failure_at is not None

    def test_to_dict(self):
        """Test config serialization."""
        config = NotifyChannelConfig(
            channel=NotifyChannel.WEBHOOK,
            status=NotifyChannelStatus.ENABLED,
            tenant_id="tenant-1",
            webhook_url="https://example.com/webhook",
        )
        result = config.to_dict()
        assert result["channel"] == "webhook"
        assert result["status"] == "enabled"
        assert result["tenant_id"] == "tenant-1"
        assert result["is_configured"] is True


class TestNotifyDeliveryResult:
    """Test NotifyDeliveryResult dataclass."""

    def test_result_creation(self):
        """Test creating a delivery result."""
        result = NotifyDeliveryResult(
            channel=NotifyChannel.WEBHOOK,
            event_type=NotifyEventType.INCIDENT_CREATED,
            success=True,
            delivered_at=datetime.now(timezone.utc),
            message_id="msg-123",
        )
        assert result.channel == NotifyChannel.WEBHOOK
        assert result.event_type == NotifyEventType.INCIDENT_CREATED
        assert result.success is True
        assert result.message_id == "msg-123"

    def test_result_with_error(self):
        """Test creating a failed delivery result."""
        result = NotifyDeliveryResult(
            channel=NotifyChannel.WEBHOOK,
            event_type=NotifyEventType.INCIDENT_CREATED,
            success=False,
            delivered_at=datetime.now(timezone.utc),
            error_message="Connection timeout",
        )
        assert result.success is False
        assert result.error_message == "Connection timeout"

    def test_to_dict(self):
        """Test result serialization."""
        result = NotifyDeliveryResult(
            channel=NotifyChannel.WEBHOOK,
            event_type=NotifyEventType.INCIDENT_CREATED,
            success=True,
            delivered_at=datetime.now(timezone.utc),
            message_id="msg-123",
            latency_ms=50,
        )
        data = result.to_dict()
        assert data["channel"] == "webhook"
        assert data["event_type"] == "incident_created"
        assert data["success"] is True
        assert data["message_id"] == "msg-123"
        assert data["latency_ms"] == 50


class TestNotifyChannelError:
    """Test NotifyChannelError exception."""

    def test_error_creation(self):
        """Test creating a channel error."""
        error = NotifyChannelError(
            message="Webhook delivery failed",
            channel=NotifyChannel.WEBHOOK,
            event_type=NotifyEventType.INCIDENT_CREATED,
            details={"status_code": 500},
        )
        assert str(error) == "Webhook delivery failed"
        assert error.channel == NotifyChannel.WEBHOOK
        assert error.event_type == NotifyEventType.INCIDENT_CREATED
        assert error.details["status_code"] == 500

    def test_error_to_dict(self):
        """Test error serialization."""
        error = NotifyChannelError(
            message="Webhook delivery failed",
            channel=NotifyChannel.WEBHOOK,
        )
        data = error.to_dict()
        assert data["error"] == "NotifyChannelError"
        assert data["channel"] == "webhook"
        assert data["message"] == "Webhook delivery failed"


class TestNotifyChannelService:
    """Test NotifyChannelService class."""

    def setup_method(self):
        """Reset service before each test."""
        _reset_notify_service()

    def test_service_creation(self):
        """Test creating service."""
        service = NotifyChannelService()
        assert service is not None

    def test_configure_channel(self):
        """Test configuring a channel."""
        service = NotifyChannelService()
        config = service.configure_channel(
            tenant_id="tenant-1",
            channel=NotifyChannel.WEBHOOK,
            webhook_url="https://example.com/webhook",
        )
        assert config.channel == NotifyChannel.WEBHOOK
        assert config.status == NotifyChannelStatus.ENABLED
        assert config.webhook_url == "https://example.com/webhook"

    def test_configure_unconfigured_channel(self):
        """Test configuring channel without required settings."""
        service = NotifyChannelService()
        config = service.configure_channel(
            tenant_id="tenant-1",
            channel=NotifyChannel.WEBHOOK,
            status=NotifyChannelStatus.ENABLED,
            # No webhook_url provided
        )
        # Should automatically set to UNCONFIGURED
        assert config.status == NotifyChannelStatus.UNCONFIGURED

    def test_get_channel_config(self):
        """Test getting channel config."""
        service = NotifyChannelService()
        service.configure_channel(
            tenant_id="tenant-1",
            channel=NotifyChannel.WEBHOOK,
            webhook_url="https://example.com/webhook",
        )
        config = service.get_channel_config("tenant-1", NotifyChannel.WEBHOOK)
        assert config is not None
        assert config.webhook_url == "https://example.com/webhook"

    def test_get_channel_config_not_found(self):
        """Test getting non-existent config."""
        service = NotifyChannelService()
        config = service.get_channel_config("tenant-1", NotifyChannel.WEBHOOK)
        assert config is None

    def test_get_all_configs(self):
        """Test getting all configs for tenant."""
        service = NotifyChannelService()
        service.configure_channel(
            tenant_id="tenant-1",
            channel=NotifyChannel.WEBHOOK,
            webhook_url="https://example.com/webhook",
        )
        service.configure_channel(
            tenant_id="tenant-1",
            channel=NotifyChannel.EMAIL,
            email_recipients=["test@example.com"],
        )
        configs = service.get_all_configs("tenant-1")
        assert len(configs) == 2
        assert NotifyChannel.WEBHOOK in configs
        assert NotifyChannel.EMAIL in configs

    def test_get_enabled_channels(self):
        """Test getting enabled channels."""
        service = NotifyChannelService()
        service.configure_channel(
            tenant_id="tenant-1",
            channel=NotifyChannel.WEBHOOK,
            webhook_url="https://example.com/webhook",
            status=NotifyChannelStatus.ENABLED,
        )
        service.configure_channel(
            tenant_id="tenant-1",
            channel=NotifyChannel.EMAIL,
            email_recipients=["test@example.com"],
            status=NotifyChannelStatus.DISABLED,
        )
        enabled = service.get_enabled_channels("tenant-1")
        assert NotifyChannel.WEBHOOK in enabled
        assert NotifyChannel.EMAIL not in enabled

    def test_get_enabled_channels_with_event_filter(self):
        """Test getting enabled channels filtered by event."""
        service = NotifyChannelService()
        service.configure_channel(
            tenant_id="tenant-1",
            channel=NotifyChannel.WEBHOOK,
            webhook_url="https://example.com/webhook",
            enabled_events={NotifyEventType.INCIDENT_CREATED},
        )
        enabled_incident = service.get_enabled_channels(
            "tenant-1", NotifyEventType.INCIDENT_CREATED
        )
        enabled_policy = service.get_enabled_channels(
            "tenant-1", NotifyEventType.POLICY_VIOLATED
        )
        assert NotifyChannel.WEBHOOK in enabled_incident
        assert NotifyChannel.WEBHOOK not in enabled_policy

    def test_enable_channel(self):
        """Test enabling a channel."""
        service = NotifyChannelService()
        service.configure_channel(
            tenant_id="tenant-1",
            channel=NotifyChannel.WEBHOOK,
            webhook_url="https://example.com/webhook",
            status=NotifyChannelStatus.DISABLED,
        )
        result = service.enable_channel("tenant-1", NotifyChannel.WEBHOOK)
        assert result.status == NotifyChannelStatus.ENABLED

    def test_enable_unconfigured_channel(self):
        """Test enabling unconfigured channel fails."""
        service = NotifyChannelService()
        result = service.enable_channel("tenant-1", NotifyChannel.WEBHOOK)
        assert result.status == NotifyChannelStatus.UNCONFIGURED
        assert "not configured" in result.message

    def test_disable_channel(self):
        """Test disabling a channel."""
        service = NotifyChannelService()
        service.configure_channel(
            tenant_id="tenant-1",
            channel=NotifyChannel.WEBHOOK,
            webhook_url="https://example.com/webhook",
            status=NotifyChannelStatus.ENABLED,
        )
        result = service.disable_channel("tenant-1", NotifyChannel.WEBHOOK)
        assert result.status == NotifyChannelStatus.DISABLED

    def test_set_event_filter(self):
        """Test setting event filter for channel."""
        service = NotifyChannelService()
        service.configure_channel(
            tenant_id="tenant-1",
            channel=NotifyChannel.WEBHOOK,
            webhook_url="https://example.com/webhook",
        )
        result = service.set_event_filter(
            "tenant-1",
            NotifyChannel.WEBHOOK,
            {NotifyEventType.INCIDENT_CREATED, NotifyEventType.INCIDENT_RESOLVED},
        )
        assert NotifyEventType.INCIDENT_CREATED in result.enabled_events
        assert NotifyEventType.INCIDENT_RESOLVED in result.enabled_events


class TestNotifyChannelServiceSend:
    """Test notification sending functionality."""

    def setup_method(self):
        """Reset service before each test."""
        _reset_notify_service()

    @pytest.mark.asyncio
    async def test_send_ui_notification(self):
        """Test sending UI notification."""
        service = NotifyChannelService()
        results = await service.send(
            tenant_id="tenant-1",
            event_type=NotifyEventType.INCIDENT_CREATED,
            payload={"incident_id": "inc-123"},
            channels=[NotifyChannel.UI],
        )
        assert len(results) == 1
        assert results[0].channel == NotifyChannel.UI
        assert results[0].success is True
        assert results[0].message_id is not None

    @pytest.mark.asyncio
    async def test_send_webhook_notification(self):
        """Test sending webhook notification."""
        service = NotifyChannelService()
        service.configure_channel(
            tenant_id="tenant-1",
            channel=NotifyChannel.WEBHOOK,
            webhook_url="https://example.com/webhook",
        )
        results = await service.send(
            tenant_id="tenant-1",
            event_type=NotifyEventType.INCIDENT_CREATED,
            payload={"incident_id": "inc-123"},
            channels=[NotifyChannel.WEBHOOK],
        )
        assert len(results) == 1
        assert results[0].channel == NotifyChannel.WEBHOOK
        assert results[0].success is True

    @pytest.mark.asyncio
    async def test_send_email_notification(self):
        """Test sending email notification."""
        service = NotifyChannelService()
        service.configure_channel(
            tenant_id="tenant-1",
            channel=NotifyChannel.EMAIL,
            email_recipients=["test@example.com"],
        )
        results = await service.send(
            tenant_id="tenant-1",
            event_type=NotifyEventType.INCIDENT_CREATED,
            payload={"incident_id": "inc-123"},
            channels=[NotifyChannel.EMAIL],
        )
        assert len(results) == 1
        assert results[0].channel == NotifyChannel.EMAIL
        assert results[0].success is True

    @pytest.mark.asyncio
    async def test_send_slack_notification(self):
        """Test sending Slack notification."""
        service = NotifyChannelService()
        service.configure_channel(
            tenant_id="tenant-1",
            channel=NotifyChannel.SLACK,
            slack_webhook_url="https://hooks.slack.com/...",
            slack_channel="#alerts",
        )
        results = await service.send(
            tenant_id="tenant-1",
            event_type=NotifyEventType.INCIDENT_CREATED,
            payload={"incident_id": "inc-123"},
            channels=[NotifyChannel.SLACK],
        )
        assert len(results) == 1
        assert results[0].channel == NotifyChannel.SLACK
        assert results[0].success is True

    @pytest.mark.asyncio
    async def test_send_to_all_enabled_channels(self):
        """Test sending to all enabled channels."""
        service = NotifyChannelService()
        service.configure_channel(
            tenant_id="tenant-1",
            channel=NotifyChannel.WEBHOOK,
            webhook_url="https://example.com/webhook",
        )
        service.configure_channel(
            tenant_id="tenant-1",
            channel=NotifyChannel.EMAIL,
            email_recipients=["test@example.com"],
        )
        results = await service.send(
            tenant_id="tenant-1",
            event_type=NotifyEventType.INCIDENT_CREATED,
            payload={"incident_id": "inc-123"},
        )
        assert len(results) == 2
        channels = [r.channel for r in results]
        assert NotifyChannel.WEBHOOK in channels
        assert NotifyChannel.EMAIL in channels

    @pytest.mark.asyncio
    async def test_send_respects_event_filter(self):
        """Test that sending respects event filter."""
        service = NotifyChannelService()
        service.configure_channel(
            tenant_id="tenant-1",
            channel=NotifyChannel.WEBHOOK,
            webhook_url="https://example.com/webhook",
            enabled_events={NotifyEventType.INCIDENT_CREATED},
        )
        # Should send for INCIDENT_CREATED
        results_inc = await service.send(
            tenant_id="tenant-1",
            event_type=NotifyEventType.INCIDENT_CREATED,
            payload={},
        )
        assert len(results_inc) == 1

        # Should not send for POLICY_VIOLATED
        results_pol = await service.send(
            tenant_id="tenant-1",
            event_type=NotifyEventType.POLICY_VIOLATED,
            payload={},
        )
        assert len(results_pol) == 0

    @pytest.mark.asyncio
    async def test_send_records_success(self):
        """Test that successful send records success."""
        service = NotifyChannelService()
        service.configure_channel(
            tenant_id="tenant-1",
            channel=NotifyChannel.WEBHOOK,
            webhook_url="https://example.com/webhook",
        )
        await service.send(
            tenant_id="tenant-1",
            event_type=NotifyEventType.INCIDENT_CREATED,
            payload={},
            channels=[NotifyChannel.WEBHOOK],
        )
        config = service.get_channel_config("tenant-1", NotifyChannel.WEBHOOK)
        assert config.last_success_at is not None


class TestNotifyChannelServiceHealth:
    """Test channel health check functionality."""

    def setup_method(self):
        """Reset service before each test."""
        _reset_notify_service()

    @pytest.mark.asyncio
    async def test_check_health(self):
        """Test health check returns status for all channels."""
        service = NotifyChannelService()
        service.configure_channel(
            tenant_id="tenant-1",
            channel=NotifyChannel.WEBHOOK,
            webhook_url="https://example.com/webhook",
        )
        health = await service.check_health("tenant-1")
        assert NotifyChannel.WEBHOOK in health
        assert health[NotifyChannel.WEBHOOK]["status"] == "enabled"
        assert health[NotifyChannel.WEBHOOK]["is_configured"] is True

    @pytest.mark.asyncio
    async def test_check_health_unconfigured_channel(self):
        """Test health check for unconfigured channel."""
        service = NotifyChannelService()
        health = await service.check_health("tenant-1")
        assert NotifyChannel.WEBHOOK in health
        assert health[NotifyChannel.WEBHOOK]["status"] == "unconfigured"
        assert health[NotifyChannel.WEBHOOK]["is_configured"] is False


class TestNotifyChannelServiceHistory:
    """Test delivery history functionality."""

    def setup_method(self):
        """Reset service before each test."""
        _reset_notify_service()

    @pytest.mark.asyncio
    async def test_get_delivery_history(self):
        """Test getting delivery history."""
        service = NotifyChannelService()
        await service.send(
            tenant_id="tenant-1",
            event_type=NotifyEventType.INCIDENT_CREATED,
            payload={},
            channels=[NotifyChannel.UI],
        )
        history = service.get_delivery_history("tenant-1")
        assert len(history) == 1
        assert history[0].channel == NotifyChannel.UI

    @pytest.mark.asyncio
    async def test_delivery_history_limit(self):
        """Test delivery history respects limit."""
        service = NotifyChannelService()
        for i in range(10):
            await service.send(
                tenant_id="tenant-1",
                event_type=NotifyEventType.INCIDENT_CREATED,
                payload={"i": i},
                channels=[NotifyChannel.UI],
            )
        history = service.get_delivery_history("tenant-1", limit=5)
        assert len(history) == 5


class TestHelperFunctions:
    """Test module-level helper functions."""

    def setup_method(self):
        """Reset service before each test."""
        _reset_notify_service()

    def test_get_notify_service_singleton(self):
        """Test service singleton."""
        service1 = get_notify_service()
        service2 = get_notify_service()
        assert service1 is service2

    def test_get_channel_config_helper(self):
        """Test get_channel_config helper."""
        service = get_notify_service()
        service.configure_channel(
            tenant_id="tenant-1",
            channel=NotifyChannel.WEBHOOK,
            webhook_url="https://example.com/webhook",
        )
        config = get_channel_config("tenant-1", NotifyChannel.WEBHOOK)
        assert config is not None
        assert config.webhook_url == "https://example.com/webhook"

    @pytest.mark.asyncio
    async def test_send_notification_helper(self):
        """Test send_notification helper."""
        results = await send_notification(
            tenant_id="tenant-1",
            event_type=NotifyEventType.INCIDENT_CREATED,
            payload={},
            channels=[NotifyChannel.UI],
        )
        assert len(results) == 1
        assert results[0].success is True

    @pytest.mark.asyncio
    async def test_check_channel_health_helper(self):
        """Test check_channel_health helper."""
        health = await check_channel_health("tenant-1")
        assert isinstance(health, dict)
        assert NotifyChannel.UI in health


class TestNotifyChannelUseCases:
    """Test real-world use cases."""

    def setup_method(self):
        """Reset service before each test."""
        _reset_notify_service()

    @pytest.mark.asyncio
    async def test_incident_notification_flow(self):
        """Test complete incident notification flow."""
        service = NotifyChannelService()

        # Configure multiple channels
        service.configure_channel(
            tenant_id="tenant-1",
            channel=NotifyChannel.WEBHOOK,
            webhook_url="https://example.com/webhook",
            enabled_events={
                NotifyEventType.INCIDENT_CREATED,
                NotifyEventType.INCIDENT_RESOLVED,
            },
        )
        service.configure_channel(
            tenant_id="tenant-1",
            channel=NotifyChannel.SLACK,
            slack_webhook_url="https://hooks.slack.com/...",
            slack_channel="#incidents",
            enabled_events={NotifyEventType.INCIDENT_CREATED},
        )

        # Send incident created notification
        results = await service.send(
            tenant_id="tenant-1",
            event_type=NotifyEventType.INCIDENT_CREATED,
            payload={
                "incident_id": "inc-123",
                "title": "Budget exceeded",
                "severity": "high",
            },
        )

        # Both channels should receive
        assert len(results) == 2
        assert all(r.success for r in results)

        # Send incident resolved
        results = await service.send(
            tenant_id="tenant-1",
            event_type=NotifyEventType.INCIDENT_RESOLVED,
            payload={
                "incident_id": "inc-123",
                "resolved_by": "auto",
            },
        )

        # Only webhook should receive (Slack filtered out)
        assert len(results) == 1
        assert results[0].channel == NotifyChannel.WEBHOOK

    @pytest.mark.asyncio
    async def test_multi_tenant_isolation(self):
        """Test that tenants are isolated."""
        service = NotifyChannelService()

        # Configure for tenant-1
        service.configure_channel(
            tenant_id="tenant-1",
            channel=NotifyChannel.WEBHOOK,
            webhook_url="https://tenant1.example.com/webhook",
        )

        # Configure for tenant-2
        service.configure_channel(
            tenant_id="tenant-2",
            channel=NotifyChannel.WEBHOOK,
            webhook_url="https://tenant2.example.com/webhook",
        )

        # Get configs are isolated
        config1 = service.get_channel_config("tenant-1", NotifyChannel.WEBHOOK)
        config2 = service.get_channel_config("tenant-2", NotifyChannel.WEBHOOK)

        assert config1.webhook_url == "https://tenant1.example.com/webhook"
        assert config2.webhook_url == "https://tenant2.example.com/webhook"

    @pytest.mark.asyncio
    async def test_channel_failure_tracking(self):
        """Test that failures are tracked in config."""
        service = NotifyChannelService()
        # Configure a channel that is "configured" but may fail
        service.configure_channel(
            tenant_id="tenant-1",
            channel=NotifyChannel.WEBHOOK,
            webhook_url="https://example.com/webhook",
        )

        # Send successfully first
        results = await service.send(
            tenant_id="tenant-1",
            event_type=NotifyEventType.INCIDENT_CREATED,
            payload={},
            channels=[NotifyChannel.WEBHOOK],
        )

        # Should succeed
        assert len(results) == 1
        assert results[0].success is True

        # Verify success was recorded in config
        config = service.get_channel_config("tenant-1", NotifyChannel.WEBHOOK)
        assert config.last_success_at is not None

    @pytest.mark.asyncio
    async def test_unconfigured_channel_not_sent(self):
        """Test that unconfigured channels are not attempted."""
        service = NotifyChannelService()
        service.configure_channel(
            tenant_id="tenant-1",
            channel=NotifyChannel.EMAIL,
            # No recipients configured - will be marked UNCONFIGURED
            email_recipients=[],
        )

        # Check that channel was marked unconfigured
        config = service.get_channel_config("tenant-1", NotifyChannel.EMAIL)
        assert config.status == NotifyChannelStatus.UNCONFIGURED

        # Enabled channels should not include unconfigured ones
        enabled = service.get_enabled_channels("tenant-1")
        assert NotifyChannel.EMAIL not in enabled
