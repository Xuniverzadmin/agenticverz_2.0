# hoc_cus_controls_L6_drivers_limits_read_driver

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/controls/L6_drivers/limits_read_driver.py` |
| Layer | L6 — Data Access Driver |
| Domain | controls |
| Audience | INTERNAL |
| Artifact Class | CODE |

## Description

Read operations for limits

## Intent

**Role:** Read operations for limits
**Reference:** PIN-470, Phase 3B P3 Design-First
**Callers:** L5 policies_limits_query_engine

## Purpose

Limits Read Driver (L6)

---

## Functions

### `get_limits_read_driver(session: AsyncSession) -> LimitsReadDriver`
- **Async:** No
- **Docstring:** Factory function for LimitsReadDriver.
- **Calls:** LimitsReadDriver

## Classes

### `LimitsReadDriver`
- **Docstring:** Read operations for limits.
- **Methods:** __init__, fetch_limits, fetch_limit_by_id, fetch_budget_limits

## Attributes

- `__all__` (line 278)

---

## Import Analysis

| Category | Imports |
|----------|---------|
| L7 Model | `app.models.policy_control_plane` |
| External | `app.hoc.cus.hoc_spine.services.time`, `sqlalchemy`, `sqlalchemy.ext.asyncio` |

## Callers

L5 policies_limits_query_engine

## Export Contract

```yaml
exports:
  functions:
    - name: get_limits_read_driver
      signature: "get_limits_read_driver(session: AsyncSession) -> LimitsReadDriver"
  classes:
    - name: LimitsReadDriver
      methods: [fetch_limits, fetch_limit_by_id, fetch_budget_limits]
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
