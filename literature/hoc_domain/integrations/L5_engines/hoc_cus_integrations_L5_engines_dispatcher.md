# hoc_cus_integrations_L5_engines_dispatcher

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/integrations/L5_engines/dispatcher.py` |
| Layer | L5/L6 — HYBRID (pending refactor) |
| Domain | integrations |
| Audience | CUSTOMER |
| Artifact Class | CODE |

## Description

Integration event dispatcher with embedded DB persistence

## Intent

**Role:** Integration event dispatcher with embedded DB persistence
**Reference:** PIN-470, HOC_LAYER_TOPOLOGY_V1.md, INTEGRATIONS_PHASE2.5_IMPLEMENTATION_PLAN.md
**Callers:** workers, bridges

## Purpose

M25 Integration Dispatcher

---

## Classes

### `DispatcherConfig`
- **Docstring:** Configuration for the integration dispatcher.
- **Methods:** from_env
- **Class Variables:** enabled: bool, bridge_1_enabled: bool, bridge_2_enabled: bool, bridge_3_enabled: bool, bridge_4_enabled: bool, bridge_5_enabled: bool, stage_timeout_seconds: float, loop_timeout_seconds: float, max_routing_delta: float, routing_decay_days: int, policy_confirmations_required: int, auto_apply_confidence_threshold: float, require_human_for_weak_match: bool, require_human_for_novel: bool

### `IntegrationDispatcher`
- **Docstring:** Central dispatcher for the M25 integration loop.
- **Methods:** __init__, register_handler, is_bridge_enabled, dispatch, _check_db_idempotency, _execute_handlers, _check_human_checkpoint_needed, resolve_checkpoint, _get_or_create_loop_status, _update_loop_status, _trigger_next_stage, _persist_event, _persist_loop_status, _persist_checkpoint, _load_loop_status, _load_checkpoint, _publish_event, _publish_checkpoint_needed, get_loop_status, get_pending_checkpoints, retry_failed_stage, revert_loop

## Attributes

- `logger` (line 58)
- `Handler` (line 113)

---

## Import Analysis

| Category | Imports |
|----------|---------|
| External | `__future__`, `schemas.loop_events`, `sqlalchemy` |

## Callers

workers, bridges

## Export Contract

```yaml
exports:
  functions: []
  classes:
    - name: DispatcherConfig
      methods: [from_env]
    - name: IntegrationDispatcher
      methods: [register_handler, is_bridge_enabled, dispatch, resolve_checkpoint, get_loop_status, get_pending_checkpoints, retry_failed_stage, revert_loop]
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
