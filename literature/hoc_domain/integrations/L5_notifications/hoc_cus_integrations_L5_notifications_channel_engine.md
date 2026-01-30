# hoc_cus_integrations_L5_notifications_channel_engine

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/integrations/L5_notifications/engines/channel_engine.py` |
| Layer | L4 — Domain Engine |
| Domain | integrations |
| Audience | CUSTOMER |
| Artifact Class | CODE |

## Description

Configurable notification channel management engine

## Intent

**Role:** Configurable notification channel management engine
**Reference:** GAP-017 (Notify Channels), ACCOUNT_PHASE2.5_IMPLEMENTATION_PLAN.md
**Callers:** alert_emitter, incident_service, policy_engine

## Purpose

Module: channel_engine
Purpose: Configurable notification channels for alerts and events.

---

## Functions

### `get_notify_service() -> NotifyChannelService`
- **Async:** No
- **Docstring:** Get or create the notification service singleton.
- **Calls:** NotifyChannelService

### `_reset_notify_service() -> None`
- **Async:** No
- **Docstring:** Reset the notification service (for testing).

### `get_channel_config(tenant_id: str, channel: NotifyChannel) -> Optional[NotifyChannelConfig]`
- **Async:** No
- **Docstring:** Quick helper to get channel configuration.  Args:
- **Calls:** get_channel_config, get_notify_service

### `async send_notification(tenant_id: str, event_type: NotifyEventType, payload: Dict[str, Any], channels: Optional[List[NotifyChannel]]) -> List[NotifyDeliveryResult]`
- **Async:** Yes
- **Docstring:** Quick helper to send notification.  Args:
- **Calls:** get_notify_service, send

### `async check_channel_health(tenant_id: str) -> Dict[NotifyChannel, Dict[str, Any]]`
- **Async:** Yes
- **Docstring:** Quick helper to check channel health.  Args:
- **Calls:** check_health, get_notify_service

## Classes

### `NotifyChannel(str, Enum)`
- **Docstring:** Available notification channels.

### `NotifyEventType(str, Enum)`
- **Docstring:** Types of events that can trigger notifications.

### `NotifyChannelStatus(str, Enum)`
- **Docstring:** Status of a notification channel.

### `NotifyChannelError(Exception)`
- **Docstring:** Raised when notification channel operation fails.
- **Methods:** __init__, to_dict

### `NotifyDeliveryResult`
- **Docstring:** Result of a notification delivery attempt.
- **Methods:** to_dict
- **Class Variables:** channel: NotifyChannel, event_type: NotifyEventType, success: bool, delivered_at: datetime, recipient_id: Optional[str], message_id: Optional[str], error_message: Optional[str], retry_count: int, latency_ms: Optional[int]

### `NotifyChannelConfig`
- **Docstring:** Configuration for a notification channel.
- **Methods:** is_event_enabled, is_configured, record_success, record_failure, to_dict
- **Class Variables:** channel: NotifyChannel, status: NotifyChannelStatus, tenant_id: str, webhook_url: Optional[str], webhook_secret: Optional[str], email_recipients: List[str], slack_webhook_url: Optional[str], slack_channel: Optional[str], pagerduty_routing_key: Optional[str], teams_webhook_url: Optional[str], enabled_events: Set[NotifyEventType], retry_count: int, retry_delay_seconds: int, timeout_seconds: int, created_at: datetime, updated_at: datetime, last_success_at: Optional[datetime], last_failure_at: Optional[datetime], failure_count: int

### `NotifyChannelConfigResponse`
- **Docstring:** Response from channel configuration operations.
- **Methods:** to_dict
- **Class Variables:** channel: NotifyChannel, status: NotifyChannelStatus, is_configured: bool, enabled_events: List[NotifyEventType], message: str

### `NotificationSender(Protocol)`
- **Docstring:** Protocol for notification sender implementations.
- **Methods:** send

### `NotifyChannelService`
- **Docstring:** Service for managing notification channels.
- **Methods:** __init__, configure_channel, get_channel_config, get_all_configs, get_enabled_channels, enable_channel, disable_channel, set_event_filter, send, _send_via_channel, _send_ui_notification, _send_webhook_notification, _send_email_notification, _send_slack_notification, _send_pagerduty_notification, _send_teams_notification, check_health, get_delivery_history

## Attributes

- `logger` (line 46)
- `_notify_service: Optional[NotifyChannelService]` (line 1029)

---

## Import Analysis

| Category | Imports |
|----------|---------|
| _None_ | Pure stdlib |

## Callers

alert_emitter, incident_service, policy_engine

## Export Contract

```yaml
exports:
  functions:
    - name: get_notify_service
      signature: "get_notify_service() -> NotifyChannelService"
    - name: get_channel_config
      signature: "get_channel_config(tenant_id: str, channel: NotifyChannel) -> Optional[NotifyChannelConfig]"
    - name: send_notification
      signature: "async send_notification(tenant_id: str, event_type: NotifyEventType, payload: Dict[str, Any], channels: Optional[List[NotifyChannel]]) -> List[NotifyDeliveryResult]"
    - name: check_channel_health
      signature: "async check_channel_health(tenant_id: str) -> Dict[NotifyChannel, Dict[str, Any]]"
  classes:
    - name: NotifyChannel
      methods: []
    - name: NotifyEventType
      methods: []
    - name: NotifyChannelStatus
      methods: []
    - name: NotifyChannelError
      methods: [to_dict]
    - name: NotifyDeliveryResult
      methods: [to_dict]
    - name: NotifyChannelConfig
      methods: [is_event_enabled, is_configured, record_success, record_failure, to_dict]
    - name: NotifyChannelConfigResponse
      methods: [to_dict]
    - name: NotificationSender
      methods: [send]
    - name: NotifyChannelService
      methods: [configure_channel, get_channel_config, get_all_configs, get_enabled_channels, enable_channel, disable_channel, set_event_filter, send, check_health, get_delivery_history]
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
