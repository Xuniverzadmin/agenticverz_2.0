# hoc_cus_account_L5_engines_user_write_engine

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/account/L5_engines/user_write_engine.py` |
| Layer | L5 — Domain Engine |
| Domain | account |
| Audience | CUSTOMER |
| Artifact Class | CODE |

## Description

User write operations (L5 engine over L6 driver)

## Intent

**Role:** User write operations (L5 engine over L6 driver)
**Reference:** PIN-470, PIN-250, PHASE3_DIRECTORY_RESTRUCTURE_PLAN.md
**Callers:** api/onboarding.py

## Purpose

User Write Engine (L5)

---

## Classes

### `UserWriteService`
- **Docstring:** DB write operations for User management.
- **Methods:** __init__, create_user, update_user_login, user_to_dict

---

## Import Analysis

| Category | Imports |
|----------|---------|
| L6 Driver | `app.hoc.cus.account.L6_drivers.user_write_driver` |
| L7 Model | `app.models.tenant` |
| External | `sqlmodel` |

## Callers

api/onboarding.py

## Export Contract

```yaml
exports:
  functions: []
  classes:
    - name: UserWriteService
      methods: [create_user, update_user_login, user_to_dict]
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
