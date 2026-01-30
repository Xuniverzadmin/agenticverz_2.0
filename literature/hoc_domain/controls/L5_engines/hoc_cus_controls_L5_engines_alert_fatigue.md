# hoc_cus_controls_L5_engines_alert_fatigue

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/controls/L5_engines/alert_fatigue.py` |
| Layer | L5 — Domain Engine |
| Domain | controls |
| Audience | CUSTOMER |
| Artifact Class | CODE |

## Description

Alert deduplication and fatigue control (Redis-backed)

## Intent

**Role:** Alert deduplication and fatigue control (Redis-backed)
**Reference:** PIN-470, PIN-454 (Cross-Domain Orchestration Audit), Section 3.3
**Callers:** AlertEmitter (L3), EventReactor (L5)

## Purpose

Alert Fatigue Controller

---

## Functions

### `get_alert_fatigue_controller(redis_client) -> AlertFatigueController`
- **Async:** No
- **Docstring:** Get or create AlertFatigueController singleton.  Args:
- **Calls:** AlertFatigueController

### `reset_alert_fatigue_controller() -> None`
- **Async:** No
- **Docstring:** Reset the singleton (for testing).

## Classes

### `AlertSuppressReason(str, Enum)`
- **Docstring:** Reason why an alert was suppressed.

### `AlertRecord`
- **Docstring:** Record of a sent alert for deduplication tracking.
- **Methods:** __post_init__, age
- **Class Variables:** alert_key: str, tenant_id: str, domain: str, sent_at: datetime, alert_hash: str

### `TenantFatigueSettings`
- **Docstring:** Per-tenant fatigue settings.
- **Methods:** get_domain_cooldown
- **Class Variables:** tenant_id: str, enabled: bool, max_alerts_per_hour: int, domain_cooldowns: Dict[str, int], dedup_window_seconds: int

### `AlertCheckResult`
- **Docstring:** Result of checking whether an alert should be sent.
- **Methods:** to_dict
- **Class Variables:** should_send: bool, suppress_reason: AlertSuppressReason, details: str, next_allowed_at: Optional[datetime], alerts_remaining_in_window: Optional[int]

### `AlertFatigueController`
- **Docstring:** Controls alert deduplication and fatigue.
- **Methods:** __init__, check_alert, should_send_alert, record_alert_sent, set_tenant_settings, get_tenant_stats, _get_tenant_settings, _check_deduplication, _check_domain_cooldown, _check_tenant_rate_limit, _cleanup_old_records

## Attributes

- `logger` (line 67)
- `ALERT_FATIGUE_ENABLED` (line 74)
- `DEFAULT_DOMAIN_COOLDOWNS` (line 77)
- `DEDUP_WINDOW_SECONDS` (line 87)
- `MAX_ALERTS_PER_TENANT_PER_HOUR` (line 90)
- `REDIS_KEY_PREFIX` (line 93)
- `REDIS_TTL_SECONDS` (line 94)
- `_fatigue_controller_instance: Optional[AlertFatigueController]` (line 513)

---

## Import Analysis

| Category | Imports |
|----------|---------|
| _None_ | Pure stdlib |

## Callers

AlertEmitter (L3), EventReactor (L5)

## Export Contract

```yaml
exports:
  functions:
    - name: get_alert_fatigue_controller
      signature: "get_alert_fatigue_controller(redis_client) -> AlertFatigueController"
    - name: reset_alert_fatigue_controller
      signature: "reset_alert_fatigue_controller() -> None"
  classes:
    - name: AlertSuppressReason
      methods: []
    - name: AlertRecord
      methods: [age]
    - name: TenantFatigueSettings
      methods: [get_domain_cooldown]
    - name: AlertCheckResult
      methods: [to_dict]
    - name: AlertFatigueController
      methods: [check_alert, should_send_alert, record_alert_sent, set_tenant_settings, get_tenant_stats]
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
