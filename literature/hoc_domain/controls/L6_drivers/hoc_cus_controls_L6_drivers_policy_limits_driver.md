# hoc_cus_controls_L6_drivers_policy_limits_driver

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/controls/L6_drivers/policy_limits_driver.py` |
| Layer | L6 — Domain Driver |
| Domain | controls |
| Audience | CUSTOMER |
| Artifact Class | CODE |

## Description

Data access for policy limits CRUD operations

## Intent

**Role:** Data access for policy limits CRUD operations
**Reference:** PIN-470, PIN-468, POLICIES_DOMAIN_LOCK.md
**Callers:** policy_limits_service.py (L5 engine)

## Purpose

Policy Limits Driver

---

## Functions

### `get_policy_limits_driver(session: AsyncSession) -> PolicyLimitsDriver`
- **Async:** No
- **Docstring:** Factory function for PolicyLimitsDriver.
- **Calls:** PolicyLimitsDriver

## Classes

### `PolicyLimitsDriver`
- **Docstring:** Data access driver for policy limits.
- **Methods:** __init__, fetch_limit_by_id, add_limit, add_integrity, flush

---

## Import Analysis

| Category | Imports |
|----------|---------|
| L7 Model | `app.models.policy_control_plane` |
| External | `sqlalchemy`, `sqlalchemy.ext.asyncio` |

## Callers

policy_limits_service.py (L5 engine)

## Export Contract

```yaml
exports:
  functions:
    - name: get_policy_limits_driver
      signature: "get_policy_limits_driver(session: AsyncSession) -> PolicyLimitsDriver"
  classes:
    - name: PolicyLimitsDriver
      methods: [fetch_limit_by_id, add_limit, add_integrity, flush]
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
