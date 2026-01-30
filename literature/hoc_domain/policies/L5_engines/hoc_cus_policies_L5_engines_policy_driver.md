# hoc_cus_policies_L5_engines_policy_driver

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/policies/L5_engines/policy_driver.py` |
| Layer | L5 — Domain Engine |
| Domain | policies |
| Audience | INTERNAL |
| Artifact Class | CODE |

## Description

Policy Domain Driver - Internal orchestration for policy operations

## Intent

**Role:** Policy Domain Driver - Internal orchestration for policy operations
**Reference:** PIN-470, FACADE_CONSOLIDATION_PLAN.md, API-001 Guardrail
**Callers:** policy_layer API, governance services, worker runtime

## Purpose

Policy Domain Driver (INTERNAL)

---

## Functions

### `get_policy_driver(db_url: Optional[str]) -> PolicyDriver`
- **Async:** No
- **Docstring:** Get the PolicyDriver singleton.  This is the recommended way to access policy evaluation from
- **Calls:** PolicyDriver

### `reset_policy_driver() -> None`
- **Async:** No
- **Docstring:** Reset the driver singleton (for testing).

## Classes

### `PolicyDriver`
- **Docstring:** Driver for Policy domain operations (INTERNAL).
- **Methods:** __init__, _engine, evaluate, pre_check, get_state, reload_policies, get_violations, get_violation, acknowledge_violation, get_risk_ceilings, get_risk_ceiling, update_risk_ceiling, reset_risk_ceiling, get_safety_rules, update_safety_rule, get_ethical_constraints, get_active_cooldowns, clear_cooldowns, get_metrics, get_policy_versions, get_current_version, create_policy_version, rollback_to_version, get_version_provenance, activate_policy_version, get_dependency_graph, get_policy_conflicts, resolve_conflict, validate_dependency_dag, add_dependency_with_dag_check, get_topological_evaluation_order, get_temporal_policies, create_temporal_policy, get_temporal_utilization, prune_temporal_metrics, get_temporal_storage_stats, evaluate_with_context

## Attributes

- `logger` (line 52)
- `_policy_driver: Optional['PolicyDriver']` (line 55)
- `PolicyFacade` (line 413)
- `get_policy_facade` (line 414)
- `reset_policy_facade` (line 415)

---

## Import Analysis

| Category | Imports |
|----------|---------|
| External | `app.policy.engine` |

## Callers

policy_layer API, governance services, worker runtime

## Export Contract

```yaml
exports:
  functions:
    - name: get_policy_driver
      signature: "get_policy_driver(db_url: Optional[str]) -> PolicyDriver"
    - name: reset_policy_driver
      signature: "reset_policy_driver() -> None"
  classes:
    - name: PolicyDriver
      methods: [evaluate, pre_check, get_state, reload_policies, get_violations, get_violation, acknowledge_violation, get_risk_ceilings, get_risk_ceiling, update_risk_ceiling, reset_risk_ceiling, get_safety_rules, update_safety_rule, get_ethical_constraints, get_active_cooldowns, clear_cooldowns, get_metrics, get_policy_versions, get_current_version, create_policy_version, rollback_to_version, get_version_provenance, activate_policy_version, get_dependency_graph, get_policy_conflicts, resolve_conflict, validate_dependency_dag, add_dependency_with_dag_check, get_topological_evaluation_order, get_temporal_policies, create_temporal_policy, get_temporal_utilization, prune_temporal_metrics, get_temporal_storage_stats, evaluate_with_context]
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
