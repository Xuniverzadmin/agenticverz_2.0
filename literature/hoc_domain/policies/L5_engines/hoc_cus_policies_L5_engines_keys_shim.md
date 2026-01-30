# hoc_cus_policies_L5_engines_keys_shim

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/policies/L5_engines/keys_shim.py` |
| Layer | L4 — Domain Engine (DEPRECATED SHIM) |
| Domain | policies |
| Audience | CUSTOMER |
| Artifact Class | CODE |

## Description

API Keys domain operations — delegates to L6 driver

## Intent

**Role:** API Keys domain operations — delegates to L6 driver
**Reference:** PIN-468, PIN-281

## Purpose

Keys Service (L4) — DEPRECATED SHIM

---

## Functions

### `get_keys_read_service(session: 'Session') -> KeysReadService`
- **Async:** No
- **Docstring:** Factory function to get KeysReadService instance.
- **Calls:** KeysReadService

### `get_keys_write_service(session: 'Session') -> KeysWriteService`
- **Async:** No
- **Docstring:** Factory function to get KeysWriteService instance.
- **Calls:** KeysWriteService

## Classes

### `KeysReadService`
- **Docstring:** L4 service for API key read operations.
- **Methods:** __init__, list_keys, get_key, get_key_usage_today

### `KeysWriteService`
- **Docstring:** L4 service for API key write operations.
- **Methods:** __init__, freeze_key, unfreeze_key

## Attributes

- `__all__` (line 147)

---

## Import Analysis

| Category | Imports |
|----------|---------|
| L6 Driver | `app.hoc.cus.apis.L6_drivers.keys_driver` |
| L7 Model | `app.models.tenant` |
| Cross-Domain | `app.hoc.cus.apis.L6_drivers.keys_driver` |
| External | `sqlmodel` |

## Callers

_Not declared in file header._

## Export Contract

```yaml
exports:
  functions:
    - name: get_keys_read_service
      signature: "get_keys_read_service(session: 'Session') -> KeysReadService"
    - name: get_keys_write_service
      signature: "get_keys_write_service(session: 'Session') -> KeysWriteService"
  classes:
    - name: KeysReadService
      methods: [list_keys, get_key, get_key_usage_today]
    - name: KeysWriteService
      methods: [freeze_key, unfreeze_key]
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
