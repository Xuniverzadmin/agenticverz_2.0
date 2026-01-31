# fatigue_controller.py

**Path:** `backend/app/hoc/hoc_spine/services/fatigue_controller.py`  
**Layer:** L4 — HOC Spine (Service)  
**Component:** Services

---

## Placement Card

```
File:            fatigue_controller.py
Lives in:        services/
Role:            Services
Inbound:         alert processing engines
Outbound:        none
Transaction:     Forbidden
Cross-domain:    none
Purpose:         AlertFatigueController - Alert fatigue management service.
Violations:      none
```

## Purpose

AlertFatigueController - Alert fatigue management service.

Manages alert fatigue through:
- Rate limiting: Limit alerts per source per time window
- Suppression: Temporarily suppress repetitive alerts
- Aggregation: Group similar alerts together
- Cool-down periods: Auto-suppress after threshold breaches

## Import Analysis

Pure stdlib — no application imports.

## Transaction Boundary

- **Commits:** no
- **Flushes:** no
- **Rollbacks:** no

## Functions

### `get_alert_fatigue_controller() -> AlertFatigueController`

Get the singleton controller instance.

### `_reset_controller() -> None`

Reset the singleton (for testing).

### `check_alert_fatigue(tenant_id: str, alert_type: str, source_id: Optional[str], source_data: Optional[dict[str, Any]], alert_data: Optional[dict[str, Any]]) -> FatigueCheckResult`

Check if an alert should be allowed or suppressed.

### `suppress_alert(tenant_id: str, source_id: str, alert_type: str, duration_seconds: Optional[int]) -> AlertFatigueState`

Manually suppress an alert source.

### `get_fatigue_stats(tenant_id: Optional[str]) -> AlertFatigueStats`

Get fatigue statistics.

## Classes

### `AlertFatigueMode(str, Enum)`

Operating modes for fatigue control.

### `AlertFatigueAction(str, Enum)`

Actions taken by the fatigue controller.

### `AlertFatigueConfig`

Configuration for alert fatigue thresholds.

#### Methods

- `to_dict() -> dict[str, Any]` — Convert to dictionary.

### `AlertFatigueState`

State tracking for an alert source.

#### Methods

- `record_alert(now: Optional[datetime]) -> None` — Record a new alert occurrence.
- `reset_window(now: Optional[datetime]) -> None` — Reset the rate limit window.
- `start_suppression(now: Optional[datetime]) -> None` — Start suppression period.
- `end_suppression() -> None` — End suppression period.
- `start_cooldown(now: Optional[datetime]) -> None` — Start cooldown period.
- `end_cooldown() -> None` — End cooldown period.
- `add_to_aggregation(alert_data: dict[str, Any], now: Optional[datetime]) -> None` — Add alert to aggregation bucket.
- `flush_aggregation() -> list[dict[str, Any]]` — Flush and return aggregated alerts.
- `is_window_expired(window_seconds: int, now: Optional[datetime]) -> bool` — Check if rate limit window has expired.
- `is_suppression_expired(duration_seconds: int, now: Optional[datetime]) -> bool` — Check if suppression period has expired.
- `is_cooldown_expired(duration_seconds: int, now: Optional[datetime]) -> bool` — Check if cooldown period has expired.
- `to_dict() -> dict[str, Any]` — Convert to dictionary.

### `AlertFatigueStats`

Statistics from fatigue controller.

#### Methods

- `update_rates() -> None` — Update calculated rates.
- `to_dict() -> dict[str, Any]` — Convert to dictionary.

### `AlertFatigueError(Exception)`

Exception for fatigue controller errors.

#### Methods

- `__init__(message: str, source_id: Optional[str], action: Optional[AlertFatigueAction])` — _No docstring._
- `to_dict() -> dict[str, Any]` — Convert to dictionary.

### `FatigueCheckResult`

Result of a fatigue check.

#### Methods

- `to_dict() -> dict[str, Any]` — Convert to dictionary.

### `AlertFatigueController`

Controller for managing alert fatigue.

Features:
- Rate limiting per source
- Automatic suppression after thresholds
- Alert aggregation
- Cool-down periods
- Per-tenant configuration

#### Methods

- `__init__(default_config: Optional[AlertFatigueConfig])` — Initialize the controller.
- `_get_state_key(tenant_id: str, source_id: str, alert_type: str) -> str` — Generate unique key for state tracking.
- `_generate_source_id(source_data: dict[str, Any]) -> str` — Generate source ID from alert data.
- `configure_tenant(tenant_id: str, config: AlertFatigueConfig) -> None` — Configure fatigue settings for a tenant.
- `get_config(tenant_id: str) -> AlertFatigueConfig` — Get configuration for a tenant.
- `get_or_create_state(tenant_id: str, source_id: str, alert_type: str) -> AlertFatigueState` — Get or create state for an alert source.
- `get_state(tenant_id: str, source_id: str, alert_type: str) -> Optional[AlertFatigueState]` — Get state for an alert source if it exists.
- `check_alert(tenant_id: str, alert_type: str, source_id: Optional[str], source_data: Optional[dict[str, Any]], alert_data: Optional[dict[str, Any]], now: Optional[datetime]) -> FatigueCheckResult` — Check if an alert should be allowed or suppressed.
- `suppress_source(tenant_id: str, source_id: str, alert_type: str, duration_seconds: Optional[int], now: Optional[datetime]) -> AlertFatigueState` — Manually suppress an alert source.
- `unsuppress_source(tenant_id: str, source_id: str, alert_type: str) -> Optional[AlertFatigueState]` — Manually unsuppress an alert source.
- `get_statistics(tenant_id: Optional[str]) -> AlertFatigueStats` — Get fatigue statistics, optionally filtered by tenant.
- `get_active_sources(tenant_id: Optional[str]) -> list[AlertFatigueState]` — Get all active alert sources.
- `clear_tenant(tenant_id: str) -> int` — Clear all state for a tenant.
- `reset() -> None` — Reset all state (for testing).

## Domain Usage

**Callers:** alert processing engines

## Export Contract

```yaml
exports:
  functions:
    - name: get_alert_fatigue_controller
      signature: "get_alert_fatigue_controller() -> AlertFatigueController"
      consumers: ["orchestrator"]
    - name: _reset_controller
      signature: "_reset_controller() -> None"
      consumers: ["orchestrator"]
    - name: check_alert_fatigue
      signature: "check_alert_fatigue(tenant_id: str, alert_type: str, source_id: Optional[str], source_data: Optional[dict[str, Any]], alert_data: Optional[dict[str, Any]]) -> FatigueCheckResult"
      consumers: ["orchestrator"]
    - name: suppress_alert
      signature: "suppress_alert(tenant_id: str, source_id: str, alert_type: str, duration_seconds: Optional[int]) -> AlertFatigueState"
      consumers: ["orchestrator"]
    - name: get_fatigue_stats
      signature: "get_fatigue_stats(tenant_id: Optional[str]) -> AlertFatigueStats"
      consumers: ["orchestrator"]
  classes:
    - name: AlertFatigueMode
      methods: []
      consumers: ["orchestrator"]
    - name: AlertFatigueAction
      methods: []
      consumers: ["orchestrator"]
    - name: AlertFatigueConfig
      methods:
        - to_dict
      consumers: ["orchestrator"]
    - name: AlertFatigueState
      methods:
        - record_alert
        - reset_window
        - start_suppression
        - end_suppression
        - start_cooldown
        - end_cooldown
        - add_to_aggregation
        - flush_aggregation
        - is_window_expired
        - is_suppression_expired
        - is_cooldown_expired
        - to_dict
      consumers: ["orchestrator"]
    - name: AlertFatigueStats
      methods:
        - update_rates
        - to_dict
      consumers: ["orchestrator"]
    - name: AlertFatigueError
      methods:
        - to_dict
      consumers: ["orchestrator"]
    - name: FatigueCheckResult
      methods:
        - to_dict
      consumers: ["orchestrator"]
    - name: AlertFatigueController
      methods:
        - configure_tenant
        - get_config
        - get_or_create_state
        - get_state
        - check_alert
        - suppress_source
        - unsuppress_source
        - get_statistics
        - get_active_sources
        - clear_tenant
        - reset
      consumers: ["orchestrator"]
  protocols: []
```

## Import Boundary

```yaml
boundary:
  allowed_inbound:
    - "hoc_spine.orchestrator.*"
    - "hoc_spine.authority.*"
    - "hoc_spine.consequences.*"
    - "hoc_spine.drivers.*"
  forbidden_inbound:
    - "hoc.cus.*"
    - "hoc.api.*"
  actual_imports:
    spine_internal: []
    l7_model: []
    external: []
  violations: []
```

## L5 Pairing Declaration

```yaml
pairing:
  serves_domains: []
  expected_l5_consumers: []
  orchestrator_operations: []
```

