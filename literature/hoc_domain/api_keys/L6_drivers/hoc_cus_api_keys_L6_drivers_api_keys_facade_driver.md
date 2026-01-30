# hoc_cus_api_keys_L6_drivers_api_keys_facade_driver

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/api_keys/L6_drivers/api_keys_facade_driver.py` |
| Layer | L6 — Domain Driver |
| Domain | api_keys |
| Audience | CUSTOMER |
| Artifact Class | CODE |

## Description

API Keys Facade Driver - Pure data access for API key queries

## Intent

**Role:** API Keys Facade Driver - Pure data access for API key queries
**Reference:** PIN-470
**Callers:** api_keys_facade.py (L5)

## Purpose

API Keys Facade Driver (L6 Data Access)

---

## Classes

### `APIKeySnapshot`
- **Docstring:** Raw API key data from DB for list view.
- **Class Variables:** id: str, name: str, key_prefix: str, status: str, created_at: datetime, last_used_at: Optional[datetime], expires_at: Optional[datetime], total_requests: int, is_synthetic: bool

### `APIKeyDetailSnapshot`
- **Docstring:** Detailed API key data from DB.
- **Class Variables:** id: str, name: str, key_prefix: str, status: str, created_at: datetime, last_used_at: Optional[datetime], expires_at: Optional[datetime], total_requests: int, permissions_json: Optional[str], allowed_workers_json: Optional[str], rate_limit_rpm: Optional[int], max_concurrent_runs: Optional[int], revoked_at: Optional[datetime], revoked_reason: Optional[str]

### `APIKeysFacadeDriver`
- **Docstring:** API Keys Facade Driver - Pure data access layer.
- **Methods:** fetch_api_keys, count_api_keys, fetch_api_key_by_id

## Attributes

- `__all__` (line 203)

---

## Import Analysis

| Category | Imports |
|----------|---------|
| L7 Model | `app.models.tenant` |
| External | `sqlalchemy`, `sqlalchemy.ext.asyncio` |

## Callers

api_keys_facade.py (L5)

## Export Contract

```yaml
exports:
  functions: []
  classes:
    - name: APIKeySnapshot
      methods: []
    - name: APIKeyDetailSnapshot
      methods: []
    - name: APIKeysFacadeDriver
      methods: [fetch_api_keys, count_api_keys, fetch_api_key_by_id]
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
