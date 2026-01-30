# hoc_cus_integrations_L5_engines_bridges

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/integrations/L5_engines/bridges.py` |
| Layer | L5/L6 — HYBRID (pending refactor) |
| Domain | integrations |
| Audience | CUSTOMER |
| Artifact Class | CODE |

## Description

Integration bridge abstractions with embedded DB operations

## Intent

**Role:** Integration bridge abstractions with embedded DB operations
**Reference:** PIN-470, HOC_LAYER_TOPOLOGY_V1.md, INTEGRATIONS_PHASE2.5_IMPLEMENTATION_PLAN.md
**Callers:** dispatcher, workers

## Purpose

M25 Integration Bridges

---

## Functions

### `_check_frozen() -> None`
- **Async:** No
- **Docstring:** Log that frozen mechanics are in use.
- **Calls:** info

### `create_bridges(db_session_factory, redis_client, config) -> list[BaseBridge]`
- **Async:** No
- **Docstring:** Create all bridges with shared configuration.
- **Calls:** IncidentToCatalogBridge, LoopStatusBridge, PatternToRecoveryBridge, PolicyToRoutingBridge, RecoveryToPolicyBridge

### `register_all_bridges(dispatcher: 'IntegrationDispatcher', db_session_factory, redis_client, config) -> None`
- **Async:** No
- **Docstring:** Register all bridges with the dispatcher.
- **Calls:** create_bridges, register

## Classes

### `BaseBridge(ABC)`
- **Docstring:** Base class for all integration bridges.
- **Methods:** stage, process, register

### `IncidentToCatalogBridge(BaseBridge)`
- **Docstring:** Bridge 1: Route incidents to failure catalog.
- **Methods:** __init__, stage, process, _extract_signature, _hash_signature, _find_matching_pattern, _calculate_fuzzy_confidence, _increment_pattern_count, _create_pattern

### `PatternToRecoveryBridge(BaseBridge)`
- **Docstring:** Bridge 2: Generate recovery suggestions from patterns.
- **Methods:** __init__, stage, process, _load_pattern, _instantiate_template, _generate_recovery, _apply_recovery, _queue_for_review, _persist_recovery

### `RecoveryToPolicyBridge(BaseBridge)`
- **Docstring:** Bridge 3: Convert applied recovery into prevention policy.
- **Methods:** __init__, stage, process, _load_pattern, _generate_policy, _persist_policy

### `PolicyToRoutingBridge(BaseBridge)`
- **Docstring:** Bridge 4: Update CARE routing based on new policy.
- **Methods:** __init__, stage, process, _identify_affected_agents, _create_adjustment, _get_active_adjustments, _get_agent_kpi, _persist_adjustment

### `LoopStatusBridge(BaseBridge)`
- **Docstring:** Bridge 5: Aggregate loop status for console display.
- **Methods:** __init__, stage, process, _build_loop_status, _push_sse_update

## Attributes

- `logger` (line 67)

---

## Import Analysis

| Category | Imports |
|----------|---------|
| External | `__future__`, `bridges_driver`, `dispatcher`, `schemas.audit_schemas`, `schemas.loop_events`, `sqlalchemy` |

## Callers

dispatcher, workers

## Export Contract

```yaml
exports:
  functions:
    - name: create_bridges
      signature: "create_bridges(db_session_factory, redis_client, config) -> list[BaseBridge]"
    - name: register_all_bridges
      signature: "register_all_bridges(dispatcher: 'IntegrationDispatcher', db_session_factory, redis_client, config) -> None"
  classes:
    - name: BaseBridge
      methods: [stage, process, register]
    - name: IncidentToCatalogBridge
      methods: [stage, process]
    - name: PatternToRecoveryBridge
      methods: [stage, process]
    - name: RecoveryToPolicyBridge
      methods: [stage, process]
    - name: PolicyToRoutingBridge
      methods: [stage, process]
    - name: LoopStatusBridge
      methods: [stage, process]
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
