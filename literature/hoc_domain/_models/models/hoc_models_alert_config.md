# hoc_models_alert_config

| Field | Value |
|-------|-------|
| Path | `backend/app/models/alert_config.py` |
| Layer | L4 — Domain Engine |
| Domain | shared |
| Audience | SHARED |
| Artifact Class | CODE |

## Description

Configure alerting behavior for near-threshold events

## Intent

**Role:** Configure alerting behavior for near-threshold events
**Reference:** POLICY_CONTROL_LEVER_IMPLEMENTATION_PLAN.md PCL-007
**Callers:** services/alert_emitter.py, api/policy_alerts.py

## Purpose

Alert Configuration Model

---

## Classes

### `AlertChannel(str, Enum)`
- **Docstring:** Available alert notification channels.

### `AlertConfig(SQLModel)`
- **Docstring:** Alert configuration for a policy.
- **Methods:** enabled_channels, enabled_channels, email_recipients, email_recipients, should_alert, is_throttled, can_send_alert, record_alert_sent
- **Class Variables:** id: Optional[int], policy_id: str, tenant_id: str, near_threshold_enabled: bool, near_threshold_percentage: int, breach_alert_enabled: bool, enabled_channels_json: str, webhook_url: Optional[str], webhook_secret: Optional[str], email_recipients_json: Optional[str], slack_webhook_url: Optional[str], slack_channel: Optional[str], min_alert_interval_seconds: int, max_alerts_per_run: int, created_at: datetime, updated_at: datetime, last_alert_at: Optional[datetime], alerts_sent_count: int

### `AlertConfigCreate(BaseModel)`
- **Docstring:** Request model for creating alert config.
- **Class Variables:** policy_id: str, near_threshold_enabled: bool, near_threshold_percentage: int, breach_alert_enabled: bool, enabled_channels: list[AlertChannel], webhook_url: Optional[str], webhook_secret: Optional[str], email_recipients: Optional[list[str]], slack_webhook_url: Optional[str], slack_channel: Optional[str], min_alert_interval_seconds: int, max_alerts_per_run: int

### `AlertConfigUpdate(BaseModel)`
- **Docstring:** Request model for updating alert config.
- **Class Variables:** near_threshold_enabled: Optional[bool], near_threshold_percentage: Optional[int], breach_alert_enabled: Optional[bool], enabled_channels: Optional[list[AlertChannel]], webhook_url: Optional[str], webhook_secret: Optional[str], email_recipients: Optional[list[str]], slack_webhook_url: Optional[str], slack_channel: Optional[str], min_alert_interval_seconds: Optional[int], max_alerts_per_run: Optional[int]

### `AlertConfigResponse(BaseModel)`
- **Docstring:** Response model for alert config.
- **Class Variables:** policy_id: str, tenant_id: str, near_threshold_enabled: bool, near_threshold_percentage: int, breach_alert_enabled: bool, enabled_channels: list[AlertChannel], webhook_url: Optional[str], email_recipients: list[str], slack_channel: Optional[str], min_alert_interval_seconds: int, max_alerts_per_run: int, created_at: datetime, updated_at: datetime

---

## Import Analysis

| Category | Imports |
|----------|---------|
| External | `pydantic`, `sqlmodel` |

## Callers

services/alert_emitter.py, api/policy_alerts.py

## Export Contract

```yaml
exports:
  functions: []
  classes:
    - name: AlertChannel
      methods: []
    - name: AlertConfig
      methods: [enabled_channels, enabled_channels, email_recipients, email_recipients, should_alert, is_throttled, can_send_alert, record_alert_sent]
    - name: AlertConfigCreate
      methods: []
    - name: AlertConfigUpdate
      methods: []
    - name: AlertConfigResponse
      methods: []
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
