# hoc_cus_controls_L5_engines_cost_safety_rails

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/controls/L5_engines/cost_safety_rails.py` |
| Layer | L5 — Domain Engine |
| Domain | controls |
| Audience | CUSTOMER |
| Artifact Class | CODE |

## Description

Cost safety rail enforcement (business rules)

## Intent

**Role:** Cost safety rail enforcement (business rules)
**Reference:** PIN-470, Cost Safety
**Callers:** cost services, workers

## Purpose

M27 Cost Safety Rails
=====================

---

## Functions

### `get_safety_rails(config: SafetyConfig | None) -> CostSafetyRails`
- **Async:** No
- **Docstring:** Get or create default safety rails instance.
- **Calls:** CostSafetyRails

## Classes

### `SafetyConfig`
- **Docstring:** M27 Safety Configuration.
- **Methods:** production, testing
- **Class Variables:** max_auto_policies_per_tenant_per_day: int, max_auto_recoveries_per_tenant_per_day: int, max_routing_adjustments_per_tenant_per_day: int, max_users_affected_per_action: int, max_features_affected_per_action: int, critical_actions_require_confirmation: bool, high_actions_require_confirmation: bool, action_cooldown_minutes: int, max_budget_reduction_pct: float

### `CostSafetyRails`
- **Docstring:** Enforces M27 safety limits.
- **Methods:** __init__, can_auto_apply_policy, can_auto_apply_recovery, can_auto_apply_routing, record_action, _get_action_count, get_status

### `SafeCostLoopOrchestrator`
- **Docstring:** Wraps CostLoopOrchestrator with safety rails.
- **Methods:** __init__, process_anomaly_safe

## Attributes

- `logger` (line 48)
- `_default_safety_rails: CostSafetyRails | None` (line 394)

---

## Import Analysis

| Category | Imports |
|----------|---------|
| External | `__future__`, `app.integrations.cost_bridges` |

## Callers

cost services, workers

## Export Contract

```yaml
exports:
  functions:
    - name: get_safety_rails
      signature: "get_safety_rails(config: SafetyConfig | None) -> CostSafetyRails"
  classes:
    - name: SafetyConfig
      methods: [production, testing]
    - name: CostSafetyRails
      methods: [can_auto_apply_policy, can_auto_apply_recovery, can_auto_apply_routing, record_action, get_status]
    - name: SafeCostLoopOrchestrator
      methods: [process_anomaly_safe]
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
