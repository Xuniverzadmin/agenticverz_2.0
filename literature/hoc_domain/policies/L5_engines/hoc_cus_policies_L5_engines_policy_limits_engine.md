# hoc_cus_policies_L5_engines_policy_limits_engine

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/policies/L5_engines/policy_limits_engine.py` |
| Layer | L5 — Domain Engine |
| Domain | policies |
| Audience | CUSTOMER |
| Artifact Class | CODE |

## Description

Policy limits CRUD engine (PIN-LIM-01) - pure business logic

## Intent

**Role:** Policy limits CRUD engine (PIN-LIM-01) - pure business logic
**Reference:** PIN-470, PIN-LIM-01, PIN-468
**Callers:** api/policies.py

## Purpose

Policy Limits Service (PIN-LIM-01)

---

## Classes

### `PolicyLimitsServiceError(Exception)`
- **Docstring:** Base exception for policy limits service.

### `LimitNotFoundError(PolicyLimitsServiceError)`
- **Docstring:** Raised when limit is not found.

### `LimitValidationError(PolicyLimitsServiceError)`
- **Docstring:** Raised when limit validation fails.

### `ImmutableFieldError(PolicyLimitsServiceError)`
- **Docstring:** Raised when attempting to modify immutable fields.

### `PolicyLimitsService`
- **Docstring:** Service for policy limit CRUD operations.
- **Methods:** __init__, create, update, delete, get, _get_limit, _validate_category_fields, _to_response

---

## Import Analysis

| Category | Imports |
|----------|---------|
| L5 Schema | `app.hoc.cus.controls.L5_schemas.policy_limits` |
| L6 Driver | `app.hoc.cus.controls.L6_drivers.policy_limits_driver`, `app.hoc.cus.logs.L6_drivers.audit_ledger_service_async` |
| L7 Model | `app.models.audit_ledger`, `app.models.policy_control_plane` |
| Cross-Domain | `app.hoc.cus.controls.L6_drivers.policy_limits_driver`, `app.hoc.cus.logs.L6_drivers.audit_ledger_service_async` |
| External | `app.hoc.hoc_spine.drivers.cross_domain`, `app.hoc.hoc_spine.services.time`, `sqlalchemy.ext.asyncio` |

## Callers

api/policies.py

## Export Contract

```yaml
exports:
  functions: []
  classes:
    - name: PolicyLimitsServiceError
      methods: []
    - name: LimitNotFoundError
      methods: []
    - name: LimitValidationError
      methods: []
    - name: ImmutableFieldError
      methods: []
    - name: PolicyLimitsService
      methods: [create, update, delete, get]
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
