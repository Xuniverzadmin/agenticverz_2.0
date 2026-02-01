# hoc_cus_policies_L5_engines_policy_rules_engine

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/policies/L5_engines/policy_rules_engine.py` |
| Layer | L5 — Domain Engine |
| Domain | policies |
| Audience | CUSTOMER |
| Artifact Class | CODE |

## Description

Policy rules CRUD engine (PIN-LIM-02) - pure business logic

## Intent

**Role:** Policy rules CRUD engine (PIN-LIM-02) - pure business logic
**Reference:** PIN-470, PIN-LIM-02, PIN-468
**Callers:** api/policies.py

## Purpose

Policy Rules Service (PIN-LIM-02)

---

## Classes

### `PolicyRulesServiceError(Exception)`
- **Docstring:** Base exception for policy rules service.

### `RuleNotFoundError(PolicyRulesServiceError)`
- **Docstring:** Raised when rule is not found.

### `RuleValidationError(PolicyRulesServiceError)`
- **Docstring:** Raised when rule validation fails.

### `PolicyRulesService`
- **Docstring:** Service for policy rule CRUD operations.
- **Methods:** __init__, create, update, get, _get_rule, _validate_conditions, _compute_hash, _to_response

---

## Import Analysis

| Category | Imports |
|----------|---------|
| L5 Schema | `app.hoc.cus.policies.L5_schemas.policy_rules` |
| L6 Driver | `app.hoc.cus.logs.L6_drivers.audit_ledger_service_async`, `app.hoc.cus.policies.L6_drivers.policy_rules_driver` |
| L7 Model | `app.models.audit_ledger`, `app.models.policy_control_plane` |
| Cross-Domain | `app.hoc.cus.logs.L6_drivers.audit_ledger_service_async` |
| External | `app.hoc.cus.hoc_spine.drivers.cross_domain`, `app.hoc.cus.hoc_spine.services.time`, `sqlalchemy.ext.asyncio` |

## Callers

api/policies.py

## Export Contract

```yaml
exports:
  functions: []
  classes:
    - name: PolicyRulesServiceError
      methods: []
    - name: RuleNotFoundError
      methods: []
    - name: RuleValidationError
      methods: []
    - name: PolicyRulesService
      methods: [create, update, get]
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
