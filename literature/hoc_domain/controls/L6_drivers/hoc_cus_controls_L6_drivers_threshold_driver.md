# hoc_cus_controls_L6_drivers_threshold_driver

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/controls/L6_drivers/threshold_driver.py` |
| Layer | L6 — Domain Driver |
| Domain | controls |
| Audience | CUSTOMER |
| Artifact Class | CODE |

## Description

Database operations for threshold limits

## Intent

**Role:** Database operations for threshold limits
**Reference:** PIN-470, docs/architecture/hoc/INDEX.md → Activity Phase 2.5A
**Callers:** threshold_engine.py (L5)

## Purpose

Threshold Driver (L6)

---

## Functions

### `emit_threshold_signal_sync(session: Any, tenant_id: str, run_id: str, state: str, signal: Any, params_used: dict) -> None`
- **Async:** No
- **Docstring:** Emit a threshold signal to ops_events table (sync).  For use in sync contexts (e.g., worker callbacks).
- **Calls:** EventEmitter, OpsEvent, UUID, emit, get, info, isinstance

### `emit_and_persist_threshold_signal(session: Any, tenant_id: str, run_id: str, state: str, signals: list, params_used: dict) -> None`
- **Async:** No
- **Docstring:** Emit threshold signals to both Founder and Customer consoles.  This function performs DUAL emission:
- **Calls:** RunSignalService, emit_threshold_signal_sync, info, len, update_risk_level

## Classes

### `LimitSnapshot`
- **Docstring:** Immutable snapshot of a Limit record returned to engines.
- **Class Variables:** id: str, tenant_id: str, scope: str, scope_id: Optional[str], params: dict, status: str, created_at: datetime

### `ThresholdDriver`
- **Docstring:** Async database driver for threshold limit operations.
- **Methods:** __init__, get_active_threshold_limits, get_threshold_limit_by_scope

### `ThresholdDriverSync`
- **Docstring:** Sync database driver for threshold limit operations.
- **Methods:** __init__, get_active_threshold_limits

## Attributes

- `logger` (line 60)

---

## Import Analysis

| Category | Imports |
|----------|---------|
| L5 Engine | `app.hoc.cus.controls.L5_engines.threshold_engine` |
| L6 Driver | `app.hoc.cus.activity.L6_drivers.run_signal_service` |
| L7 Model | `app.models.policy_control_plane` |
| Cross-Domain | `app.hoc.cus.activity.L6_drivers.run_signal_service` |
| External | `app.hoc.int.agent.drivers.event_emitter`, `sqlalchemy`, `sqlalchemy.ext.asyncio`, `sqlmodel` |

## Callers

threshold_engine.py (L5)

## Export Contract

```yaml
exports:
  functions:
    - name: emit_threshold_signal_sync
      signature: "emit_threshold_signal_sync(session: Any, tenant_id: str, run_id: str, state: str, signal: Any, params_used: dict) -> None"
    - name: emit_and_persist_threshold_signal
      signature: "emit_and_persist_threshold_signal(session: Any, tenant_id: str, run_id: str, state: str, signals: list, params_used: dict) -> None"
  classes:
    - name: LimitSnapshot
      methods: []
    - name: ThresholdDriver
      methods: [get_active_threshold_limits, get_threshold_limit_by_scope]
    - name: ThresholdDriverSync
      methods: [get_active_threshold_limits]
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
