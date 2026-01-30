# hoc_cus_api_keys_L6_drivers_keys_driver

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/api_keys/L6_drivers/keys_driver.py` |
| Layer | L6 — Domain Driver |
| Domain | api_keys |
| Audience | CUSTOMER |
| Artifact Class | CODE |

## Description

Keys Driver - Pure data access for API key engine operations

## Intent

**Role:** Keys Driver - Pure data access for API key engine operations
**Reference:** PIN-470
**Callers:** keys_engine.py (L5)

## Purpose

Keys Driver (L6 Data Access)

---

## Functions

### `get_keys_driver(session: Session) -> KeysDriver`
- **Async:** No
- **Docstring:** Factory function to get KeysDriver instance.
- **Calls:** KeysDriver

## Classes

### `KeySnapshot`
- **Docstring:** API key snapshot for engine operations.
- **Class Variables:** id: str, tenant_id: str, name: str, key_prefix: str, status: str, is_frozen: bool, frozen_at: Optional[datetime], created_at: datetime, last_used_at: Optional[datetime], expires_at: Optional[datetime], total_requests: int

### `KeyUsageSnapshot`
- **Docstring:** Key usage statistics from DB.
- **Class Variables:** request_count: int, spend_cents: int

### `KeysDriver`
- **Docstring:** Keys Driver - Pure data access layer.
- **Methods:** __init__, fetch_keys, count_keys, fetch_key_by_id, fetch_key_usage, fetch_key_for_update, update_key_frozen, update_key_unfrozen

## Attributes

- `__all__` (line 284)

---

## Import Analysis

| Category | Imports |
|----------|---------|
| L7 Model | `app.models.killswitch`, `app.models.tenant` |
| External | `sqlalchemy`, `sqlmodel` |

## Callers

keys_engine.py (L5)

## Export Contract

```yaml
exports:
  functions:
    - name: get_keys_driver
      signature: "get_keys_driver(session: Session) -> KeysDriver"
  classes:
    - name: KeySnapshot
      methods: []
    - name: KeyUsageSnapshot
      methods: []
    - name: KeysDriver
      methods: [fetch_keys, count_keys, fetch_key_by_id, fetch_key_usage, fetch_key_for_update, update_key_frozen, update_key_unfrozen]
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
