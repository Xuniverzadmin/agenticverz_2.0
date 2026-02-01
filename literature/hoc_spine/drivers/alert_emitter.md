# alert_emitter.py

**Path:** `backend/app/hoc/cus/hoc_spine/drivers/alert_emitter.py`  
**Layer:** L4 — HOC Spine (Driver)  
**Component:** Drivers

---

## Placement Card

```
File:            alert_emitter.py
Lives in:        drivers/
Role:            Drivers
Inbound:         policy/prevention_engine.py
Outbound:        none
Transaction:     Forbidden
Cross-domain:    none
Purpose:         Alert Emitter Service
Violations:      none
```

## Purpose

Alert Emitter Service

Emits alerts for threshold events via configured channels:
- UI notifications
- Webhooks
- Email (future)
- Slack (future)

Alert flow:
1. ThresholdSignal created
2. AlertEmitter checks AlertConfig
3. If enabled and not throttled, send via configured channels
4. Record alert sent status

## Import Analysis

**L7 Models:**
- `app.models.alert_config`
- `app.models.threshold_signal`

**External:**
- `httpx`
- `sqlmodel`
- `app.db`

## Transaction Boundary

- **Commits:** no
- **Flushes:** no
- **Rollbacks:** no

## Functions

### `get_alert_emitter() -> AlertEmitter`

Get or create AlertEmitter singleton.

## Classes

### `AlertEmitter`

Emits alerts for threshold events.

Handles alert throttling, channel routing, and delivery tracking.

#### Methods

- `__init__(session: Optional[Session], http_client: Optional[httpx.AsyncClient])` — Initialize alert emitter.
- `async emit_near_threshold(signal: ThresholdSignal, alert_config: AlertConfig, run_alert_count: int) -> bool` — Emit near-threshold alert via configured channels.
- `async emit_breach(signal: ThresholdSignal, alert_config: AlertConfig, action_taken: str) -> bool` — Emit breach alert with enforcement action.
- `async _send_via_channel(channel: AlertChannel, signal: ThresholdSignal, config: AlertConfig, is_breach: bool, action_taken: Optional[str]) -> bool` — Send alert via a specific channel.
- `async _send_ui_notification(signal: ThresholdSignal, is_breach: bool, action_taken: Optional[str]) -> bool` — Send UI notification.
- `async _send_webhook(signal: ThresholdSignal, config: AlertConfig, is_breach: bool, action_taken: Optional[str]) -> bool` — Send webhook notification.
- `async _send_slack(signal: ThresholdSignal, config: AlertConfig, is_breach: bool, action_taken: Optional[str]) -> bool` — Send Slack notification.
- `async _send_email(signal: ThresholdSignal, config: AlertConfig, is_breach: bool, action_taken: Optional[str]) -> bool` — Send email notification.
- `async _persist_signal(signal: ThresholdSignal) -> None` — Persist signal changes to database.
- `async _persist_config(config: AlertConfig) -> None` — Persist config changes to database.

## Domain Usage

**Callers:** policy/prevention_engine.py

## Export Contract

```yaml
exports:
  functions:
    - name: get_alert_emitter
      signature: "get_alert_emitter() -> AlertEmitter"
      consumers: ["orchestrator"]
  classes:
    - name: AlertEmitter
      methods:
        - emit_near_threshold
        - emit_breach
      consumers: ["orchestrator"]
  protocols: []
```

## Import Boundary

```yaml
boundary:
  allowed_inbound:
    - "hoc_spine.orchestrator.*"
    - "hoc_spine.services.*"
  forbidden_inbound:
    - "hoc.cus.*"
    - "hoc.api.*"
  actual_imports:
    spine_internal: []
    l7_model: ['app.models.alert_config', 'app.models.threshold_signal']
    external: ['httpx', 'sqlmodel', 'app.db']
  violations: []
```

## L5 Pairing Declaration

```yaml
pairing:
  serves_domains: []
  expected_l5_consumers: []
  orchestrator_operations: []
```

