# hoc_cus_policies_L6_drivers_policy_rules_driver

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/policies/L6_drivers/policy_rules_driver.py` |
| Layer | L6 — Domain Driver |
| Domain | policies |
| Audience | CUSTOMER |
| Artifact Class | CODE |

## Description

Data access for policy rules CRUD operations

## Intent

**Role:** Data access for policy rules CRUD operations
**Reference:** PIN-470, PIN-468, POLICIES_DOMAIN_LOCK.md
**Callers:** policy_rules_service.py (L5 engine)

## Purpose

Policy Rules Driver

---

## Functions

### `get_policy_rules_driver(session: AsyncSession) -> PolicyRulesDriver`
- **Async:** No
- **Docstring:** Factory function for PolicyRulesDriver.
- **Calls:** PolicyRulesDriver

## Classes

### `PolicyRulesDriver`
- **Docstring:** Data access driver for policy rules.
- **Methods:** __init__, fetch_rule_by_id, add_rule, add_integrity, flush

---

## Import Analysis

| Category | Imports |
|----------|---------|
| L7 Model | `app.models.policy_control_plane` |
| External | `sqlalchemy`, `sqlalchemy.ext.asyncio` |

## Callers

policy_rules_service.py (L5 engine)

## Export Contract

```yaml
exports:
  functions:
    - name: get_policy_rules_driver
      signature: "get_policy_rules_driver(session: AsyncSession) -> PolicyRulesDriver"
  classes:
    - name: PolicyRulesDriver
      methods: [fetch_rule_by_id, add_rule, add_integrity, flush]
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
