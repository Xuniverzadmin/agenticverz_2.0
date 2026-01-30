# hoc_cus_policies_L6_drivers_policy_engine_driver

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/policies/L6_drivers/policy_engine_driver.py` |
| Layer | L6 — Domain Driver |
| Domain | policies |
| Audience | CUSTOMER |
| Artifact Class | CODE |

## Description

Policy Engine data access operations

## Intent

**Role:** Policy Engine data access operations
**Reference:** PIN-470, PIN-468 (Phase-2.5A)
**Callers:** engine.py (L5)

## Purpose

Policy Engine Driver (L6)

---

## Functions

### `get_policy_engine_driver(db_url: str) -> PolicyEngineDriver`
- **Async:** No
- **Docstring:** Factory function for PolicyEngineDriver.
- **Calls:** PolicyEngineDriver

## Classes

### `PolicyEngineDriver`
- **Docstring:** L6 driver for PolicyEngine data access.
- **Methods:** __init__, _get_engine, fetch_ethical_constraints, fetch_risk_ceilings, fetch_safety_rules, fetch_business_rules, insert_evaluation, insert_violation, fetch_violations, fetch_violation_by_id, update_violation_acknowledged, update_risk_ceiling, reset_risk_ceiling, update_safety_rule, fetch_policy_versions, fetch_current_active_version, fetch_policy_version_by_id, fetch_policy_version_by_id_or_version, deactivate_all_versions, insert_policy_version, fetch_version_for_rollback, mark_version_rolled_back, activate_version, insert_provenance, fetch_provenance, fetch_dependencies, fetch_dependency_edges, fetch_dependency_edges_with_type, insert_dependency, fetch_conflicts, fetch_unresolved_conflicts, resolve_conflict, fetch_temporal_policies, insert_temporal_policy, fetch_temporal_policy_for_utilization, fetch_temporal_metric_sum, delete_old_temporal_events, compact_temporal_events, cap_temporal_events, fetch_temporal_stats, fetch_temporal_storage_stats, fetch_active_policies_for_integrity, fetch_temporal_policies_for_integrity, fetch_ethical_constraints_for_integrity

## Attributes

- `__all__` (line 1408)

---

## Import Analysis

| Category | Imports |
|----------|---------|
| External | `sqlalchemy`, `sqlalchemy.engine` |

## Callers

engine.py (L5)

## Export Contract

```yaml
exports:
  functions:
    - name: get_policy_engine_driver
      signature: "get_policy_engine_driver(db_url: str) -> PolicyEngineDriver"
  classes:
    - name: PolicyEngineDriver
      methods: [fetch_ethical_constraints, fetch_risk_ceilings, fetch_safety_rules, fetch_business_rules, insert_evaluation, insert_violation, fetch_violations, fetch_violation_by_id, update_violation_acknowledged, update_risk_ceiling, reset_risk_ceiling, update_safety_rule, fetch_policy_versions, fetch_current_active_version, fetch_policy_version_by_id, fetch_policy_version_by_id_or_version, deactivate_all_versions, insert_policy_version, fetch_version_for_rollback, mark_version_rolled_back, activate_version, insert_provenance, fetch_provenance, fetch_dependencies, fetch_dependency_edges, fetch_dependency_edges_with_type, insert_dependency, fetch_conflicts, fetch_unresolved_conflicts, resolve_conflict, fetch_temporal_policies, insert_temporal_policy, fetch_temporal_policy_for_utilization, fetch_temporal_metric_sum, delete_old_temporal_events, compact_temporal_events, cap_temporal_events, fetch_temporal_stats, fetch_temporal_storage_stats, fetch_active_policies_for_integrity, fetch_temporal_policies_for_integrity, fetch_ethical_constraints_for_integrity]
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
