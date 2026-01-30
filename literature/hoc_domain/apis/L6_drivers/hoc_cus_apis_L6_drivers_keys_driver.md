# hoc_cus_apis_L6_drivers_keys_driver

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/apis/L6_drivers/keys_driver.py` |
| Layer | L6 — Domain Driver |
| Domain | apis |
| Audience | CUSTOMER |
| Artifact Class | CODE |

## Description

API Keys data access operations

## Intent

**Role:** API Keys data access operations
**Reference:** PIN-470, PIN-468, PIN-281 (L3 Adapter Closure)
**Callers:** keys_service.py (L5 shim), customer_keys_adapter.py (L3)

## Purpose

Keys Driver (L6)

---

## Functions

### `get_keys_driver(session: Session) -> KeysDriver`
- **Async:** No
- **Docstring:** Factory function for KeysDriver.
- **Calls:** KeysDriver

## Classes

### `KeysDriver`
- **Docstring:** L6 driver for API key data access.
- **Methods:** __init__, fetch_keys_paginated, fetch_key_by_id, fetch_key_usage_today, update_key_frozen

## Attributes

- `__all__` (line 193)

---

## Import Analysis

| Category | Imports |
|----------|---------|
| L7 Model | `app.models.killswitch`, `app.models.tenant` |
| External | `sqlalchemy`, `sqlmodel` |

## Callers

keys_service.py (L5 shim), customer_keys_adapter.py (L3)

## Export Contract

```yaml
exports:
  functions:
    - name: get_keys_driver
      signature: "get_keys_driver(session: Session) -> KeysDriver"
  classes:
    - name: KeysDriver
      methods: [fetch_keys_paginated, fetch_key_by_id, fetch_key_usage_today, update_key_frozen]
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
