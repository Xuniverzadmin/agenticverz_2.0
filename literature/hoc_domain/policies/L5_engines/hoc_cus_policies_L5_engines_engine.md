# hoc_cus_policies_L5_engines_engine

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/policies/L5_engines/engine.py` |
| Layer | L5 — Domain Engine |
| Domain | policies |
| Audience | CUSTOMER |
| Artifact Class | CODE |

## Description

Policy rule evaluation engine

## Intent

**Role:** Policy rule evaluation engine
**Reference:** PIN-470, Policy System, PIN-468 (Phase-2.5A)
**Callers:** API routes, workers, services

## Purpose

_No module docstring._

---

## Functions

### `get_policy_engine() -> PolicyEngine`
- **Async:** No
- **Docstring:** Get singleton policy engine with M18 Governor integration.
- **Calls:** PolicyEngine, get_governor, info, set_governor, warning

## Classes

### `PolicyEngine`
- **Docstring:** M19 Policy Engine - Constitutional Governance Layer.
- **Methods:** __init__, evaluate, pre_check, _check_ethical_constraints, _evaluate_ethical_constraint, _extract_text_content, _check_safety_rules, _evaluate_safety_rule, _check_cooldown, _check_risk_ceilings, _evaluate_risk_ceiling, _get_windowed_value, _add_windowed_value, _check_compliance, _evaluate_compliance_rule, _check_business_rules, _evaluate_business_rule, _route_to_governor, _load_policies, _load_default_policies, _is_cache_stale, _persist_evaluation, get_state, reload_policies, set_governor, get_violations, get_violation, acknowledge_violation, get_risk_ceilings, get_risk_ceiling, update_risk_ceiling, reset_risk_ceiling, get_safety_rules, update_safety_rule, get_ethical_constraints, get_active_cooldowns, clear_cooldowns, get_metrics, get_policy_versions, get_current_version, create_policy_version, rollback_to_version, get_version_provenance, get_dependency_graph, get_policy_conflicts, resolve_conflict, get_temporal_policies, create_temporal_policy, get_temporal_utilization, evaluate_with_context, _classify_severity, _classify_recoverability, validate_dependency_dag, add_dependency_with_dag_check, get_topological_evaluation_order, prune_temporal_metrics, get_temporal_storage_stats, activate_policy_version

## Attributes

- `logger` (line 126)
- `POLICY_SIGNING_SECRET` (line 136)
- `MAX_EVALUATION_TIME_MS` (line 139)
- `CACHE_TTL_SECONDS` (line 140)
- `DEFAULT_COST_CEILING_PER_HOUR` (line 143)
- `DEFAULT_RETRY_CEILING_PER_MINUTE` (line 144)
- `DEFAULT_CASCADE_DEPTH` (line 145)
- `DEFAULT_CONCURRENT_AGENTS` (line 146)
- `_policy_engine: Optional[PolicyEngine]` (line 2822)

---

## Import Analysis

| Category | Imports |
|----------|---------|
| L6 Driver | `app.hoc.cus.policies.L6_drivers.policy_engine_driver` |
| External | `__future__`, `app.contracts.decisions`, `app.policy.models`, `app.routing`, `sqlalchemy.exc` |

## Callers

API routes, workers, services

## Export Contract

```yaml
exports:
  functions:
    - name: get_policy_engine
      signature: "get_policy_engine() -> PolicyEngine"
  classes:
    - name: PolicyEngine
      methods: [evaluate, pre_check, get_state, reload_policies, set_governor, get_violations, get_violation, acknowledge_violation, get_risk_ceilings, get_risk_ceiling, update_risk_ceiling, reset_risk_ceiling, get_safety_rules, update_safety_rule, get_ethical_constraints, get_active_cooldowns, clear_cooldowns, get_metrics, get_policy_versions, get_current_version, create_policy_version, rollback_to_version, get_version_provenance, get_dependency_graph, get_policy_conflicts, resolve_conflict, get_temporal_policies, create_temporal_policy, get_temporal_utilization, evaluate_with_context, validate_dependency_dag, add_dependency_with_dag_check, get_topological_evaluation_order, prune_temporal_metrics, get_temporal_storage_stats, activate_policy_version]
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
