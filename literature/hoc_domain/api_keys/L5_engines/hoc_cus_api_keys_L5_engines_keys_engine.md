# hoc_cus_api_keys_L5_engines_keys_engine

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/api_keys/L5_engines/keys_engine.py` |
| Layer | L5 — Domain Engine |
| Domain | api_keys |
| Audience | CUSTOMER |
| Artifact Class | CODE |

## Description

API Keys domain engine - business logic for key operations

## Intent

**Role:** API Keys domain engine - business logic for key operations
**Reference:** PIN-470, PIN-281, PHASE3_DIRECTORY_RESTRUCTURE_PLAN.md
**Callers:** customer_keys_adapter.py (L3), runtime, gateway — NOT L2

## Purpose

Keys Engine (L4 Domain Logic)

---

## Functions

### `get_keys_read_engine(session: Session) -> KeysReadEngine`
- **Async:** No
- **Docstring:** Factory function to get KeysReadEngine instance.
- **Calls:** KeysReadEngine

### `get_keys_write_engine(session: Session) -> KeysWriteEngine`
- **Async:** No
- **Docstring:** Factory function to get KeysWriteEngine instance.
- **Calls:** KeysWriteEngine

## Classes

### `KeysReadEngine`
- **Docstring:** L4 engine for API key read operations.
- **Methods:** __init__, list_keys, get_key, get_key_usage_today

### `KeysWriteEngine`
- **Docstring:** L4 engine for API key write operations.
- **Methods:** __init__, freeze_key, unfreeze_key

## Attributes

- `__all__` (line 225)

---

## Import Analysis

| Category | Imports |
|----------|---------|
| L6 Driver | `app.hoc.cus.api_keys.L6_drivers.keys_driver` |
| External | `__future__`, `sqlmodel` |

## Callers

customer_keys_adapter.py (L3), runtime, gateway — NOT L2

## Export Contract

```yaml
exports:
  functions:
    - name: get_keys_read_engine
      signature: "get_keys_read_engine(session: Session) -> KeysReadEngine"
    - name: get_keys_write_engine
      signature: "get_keys_write_engine(session: Session) -> KeysWriteEngine"
  classes:
    - name: KeysReadEngine
      methods: [list_keys, get_key, get_key_usage_today]
    - name: KeysWriteEngine
      methods: [freeze_key, unfreeze_key]
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
