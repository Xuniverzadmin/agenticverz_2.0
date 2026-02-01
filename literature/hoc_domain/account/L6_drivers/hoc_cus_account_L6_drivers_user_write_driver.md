# hoc_cus_account_L6_drivers_user_write_driver

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/account/L6_drivers/user_write_driver.py` |
| Layer | L6 — Domain Driver |
| Domain | account |
| Audience | CUSTOMER |
| Artifact Class | CODE |

## Description

Data access for user write operations

## Intent

**Role:** Data access for user write operations
**Reference:** PIN-470, PIN-250, PHASE2_EXTRACTION_PROTOCOL.md
**Callers:** user_write_engine.py (L5)

## Purpose

User Write Driver (L6)

---

## Functions

### `get_user_write_driver(session: Session) -> UserWriteDriver`
- **Async:** No
- **Docstring:** Factory function to get UserWriteDriver instance.
- **Calls:** UserWriteDriver

## Classes

### `UserWriteDriver`
- **Docstring:** L6 driver for user write operations.
- **Methods:** __init__, create_user, update_user_login, user_to_dict

## Attributes

- `__all__` (line 134)

---

## Import Analysis

| Category | Imports |
|----------|---------|
| L7 Model | `app.models.tenant` |
| External | `app.hoc.cus.hoc_spine.services.time`, `sqlmodel` |

## Callers

user_write_engine.py (L5)

## Export Contract

```yaml
exports:
  functions:
    - name: get_user_write_driver
      signature: "get_user_write_driver(session: Session) -> UserWriteDriver"
  classes:
    - name: UserWriteDriver
      methods: [create_user, update_user_login, user_to_dict]
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
