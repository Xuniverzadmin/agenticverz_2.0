# hoc_cus_policies_L6_drivers_policy_rules_read_driver

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/policies/L6_drivers/policy_rules_read_driver.py` |
| Layer | L6 — Data Access Driver |
| Domain | policies |
| Audience | INTERNAL |
| Artifact Class | CODE |

## Description

Read operations for policy rules

## Intent

**Role:** Read operations for policy rules
**Reference:** PIN-470, Phase 3B P3 Design-First
**Callers:** L5 policies_rules_query_engine

## Purpose

Policy Rules Read Driver (L6)

---

## Functions

### `get_policy_rules_read_driver(session: AsyncSession) -> PolicyRulesReadDriver`
- **Async:** No
- **Docstring:** Factory function for PolicyRulesReadDriver.
- **Calls:** PolicyRulesReadDriver

## Classes

### `PolicyRulesReadDriver`
- **Docstring:** Read operations for policy rules.
- **Methods:** __init__, fetch_policy_rules, fetch_policy_rule_by_id, count_policy_rules

## Attributes

- `__all__` (line 253)

---

## Import Analysis

| Category | Imports |
|----------|---------|
| L7 Model | `app.models.policy_control_plane` |
| External | `app.hoc.hoc_spine.services.time`, `sqlalchemy`, `sqlalchemy.ext.asyncio` |

## Callers

L5 policies_rules_query_engine

## Export Contract

```yaml
exports:
  functions:
    - name: get_policy_rules_read_driver
      signature: "get_policy_rules_read_driver(session: AsyncSession) -> PolicyRulesReadDriver"
  classes:
    - name: PolicyRulesReadDriver
      methods: [fetch_policy_rules, fetch_policy_rule_by_id, count_policy_rules]
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
