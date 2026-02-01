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

### ~~`emit_and_persist_threshold_signal`~~ — DELETED (PIN-507 Law 4, 2026-02-01)
- **Moved to:** `app.hoc.hoc_spine.orchestrator.coordinators.signal_coordinator`
- **Reason:** Cross-domain orchestration (controls→activity) belongs at L4, not L6

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
| L5 Schema | `app.hoc.cus.controls.L5_schemas.threshold_signals` (PIN-507 Law 1) |
| L7 Model | `app.models.policy_control_plane` |
| Cross-Domain | ~~`app.hoc.cus.activity.L6_drivers.run_signal_service`~~ REMOVED (PIN-507 Law 4) |
| L5 Engine | ~~`app.hoc.cus.controls.L5_engines.threshold_engine`~~ REMOVED (PIN-507 Law 1 — ThresholdSignal moved to L5_schemas) |
| External | `app.hoc.int.agent.drivers.event_emitter`, `sqlalchemy`, `sqlalchemy.ext.asyncio`, `sqlmodel` |

## Callers

threshold_engine.py (L5)

## Export Contract

```yaml
exports:
  functions:
    - name: emit_threshold_signal_sync
      signature: "emit_threshold_signal_sync(session: Any, tenant_id: str, run_id: str, state: str, signal: Any, params_used: dict) -> None"
    # emit_and_persist_threshold_signal — DELETED (PIN-507 Law 4, moved to L4 signal_coordinator)
  classes:
    - name: LimitSnapshot
      methods: []
    - name: ThresholdDriver
      methods: [get_active_threshold_limits, get_threshold_limit_by_scope]
    - name: ThresholdDriverSync
      methods: [get_active_threshold_limits]
```

## PIN-507 Law 4 Amendment (2026-02-01)

`emit_and_persist_threshold_signal` deleted from this L6 driver. It orchestrated two domains (controls→activity) which belongs at L4. Moved to `app.hoc.hoc_spine.orchestrator.coordinators.signal_coordinator`. Cross-domain activity import (`run_signal_driver`) removed from this file. `emit_threshold_signal_sync` remains (pure L6 DB write, single domain).

## PIN-507 Law 1 Amendment (2026-02-01)

`ThresholdSignal` import changed from `L5_engines.threshold_engine` (lazy, function-scoped) to `L5_schemas.threshold_signals` (module-level). Law 1: L6 must not reach up to L5 engines. `ThresholdSignal` is a type (enum), canonically belonging in L5_schemas. CI guard `check_l6_no_l5_engine_imports` prevents regression.

## Evaluation Notes

- **Disposition:** KEEP
- **Rationale:** Core L6 driver for threshold limits. Cross-domain orchestration removed per PIN-507.
