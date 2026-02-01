# hoc_cus_controls_L6_drivers_override_driver

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/controls/L6_drivers/override_driver.py` |
| Layer | L6 — Domain Driver |
| Domain | controls |
| Audience | CUSTOMER |
| Artifact Class | CODE |

## Description

Limit override driver (PIN-LIM-05) - DB boundary crossing

## Intent

**Role:** Limit override driver (PIN-LIM-05) - DB boundary crossing
**Reference:** PIN-470, PIN-LIM-05
**Callers:** L5 engines, api/limits/override.py

## Purpose

Limit Override Service (PIN-LIM-05)

---

## Classes

### `LimitOverrideServiceError(Exception)`
- **Docstring:** Base exception for override service.

### `LimitNotFoundError(LimitOverrideServiceError)`
- **Docstring:** Raised when limit is not found.

### `OverrideNotFoundError(LimitOverrideServiceError)`
- **Docstring:** Raised when override is not found.

### `OverrideValidationError(LimitOverrideServiceError)`
- **Docstring:** Raised when override validation fails.

### `StackingAbuseError(LimitOverrideServiceError)`
- **Docstring:** Raised when too many overrides are active.

### `LimitOverrideService`
- **Docstring:** Service for limit override lifecycle.
- **Methods:** __init__, request_override, get_override, list_overrides, cancel_override, _get_limit, _to_response

## Attributes

- `_OVERRIDE_STORE: dict[str, dict]` (line 83)

---

## Import Analysis

| Category | Imports |
|----------|---------|
| L5 Schema | `app.hoc.cus.controls.L5_schemas.overrides` |
| L7 Model | `app.models.policy_control_plane` |
| External | `app.hoc.cus.hoc_spine.drivers.cross_domain`, `app.hoc.cus.hoc_spine.services.time`, `sqlalchemy`, `sqlalchemy.ext.asyncio` |

## Callers

L5 engines, api/limits/override.py

## Export Contract

```yaml
exports:
  functions: []
  classes:
    - name: LimitOverrideServiceError
      methods: []
    - name: LimitNotFoundError
      methods: []
    - name: OverrideNotFoundError
      methods: []
    - name: OverrideValidationError
      methods: []
    - name: StackingAbuseError
      methods: []
    - name: LimitOverrideService
      methods: [request_override, get_override, list_overrides, cancel_override]
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
