# hoc_cus_api_keys_L5_engines_api_keys_facade

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/api_keys/L5_engines/api_keys_facade.py` |
| Layer | L5 — Domain Engine |
| Domain | api_keys |
| Audience | CUSTOMER |
| Artifact Class | CODE |

## Description

API Keys domain engine - unified entry point for API key operations

## Intent

**Role:** API Keys domain engine - unified entry point for API key operations
**Reference:** PIN-470, Connectivity Domain - Customer Console v1 Constitution
**Callers:** L2 api-keys API (aos_api_key.py)

## Purpose

API Keys Domain Engine (L5)

---

## Functions

### `get_api_keys_facade() -> APIKeysFacade`
- **Async:** No
- **Docstring:** Get the singleton APIKeysFacade instance.
- **Calls:** APIKeysFacade

## Classes

### `APIKeySummaryResult`
- **Docstring:** API key summary for list view.
- **Class Variables:** key_id: str, name: str, prefix: str, status: str, created_at: datetime, last_used_at: Optional[datetime], expires_at: Optional[datetime], total_requests: int

### `APIKeysListResult`
- **Docstring:** API keys list response.
- **Class Variables:** items: list[APIKeySummaryResult], total: int, has_more: bool, filters_applied: dict[str, Any]

### `APIKeyDetailResult`
- **Docstring:** API key detail response.
- **Class Variables:** key_id: str, name: str, prefix: str, status: str, created_at: datetime, last_used_at: Optional[datetime], expires_at: Optional[datetime], total_requests: int, permissions: Optional[list[str]], allowed_workers: Optional[list[str]], rate_limit_rpm: Optional[int], max_concurrent_runs: Optional[int], revoked_at: Optional[datetime], revoked_reason: Optional[str]

### `APIKeysFacade`
- **Docstring:** Unified facade for API key management.
- **Methods:** __init__, list_api_keys, get_api_key_detail

## Attributes

- `_facade_instance: APIKeysFacade | None` (line 218)
- `__all__` (line 229)

---

## Import Analysis

| Category | Imports |
|----------|---------|
| L6 Driver | `app.hoc.cus.api_keys.L6_drivers.api_keys_facade_driver` |
| External | `__future__`, `sqlalchemy.ext.asyncio` |

## Callers

L2 api-keys API (aos_api_key.py)

## Export Contract

```yaml
exports:
  functions:
    - name: get_api_keys_facade
      signature: "get_api_keys_facade() -> APIKeysFacade"
  classes:
    - name: APIKeySummaryResult
      methods: []
    - name: APIKeysListResult
      methods: []
    - name: APIKeyDetailResult
      methods: []
    - name: APIKeysFacade
      methods: [list_api_keys, get_api_key_detail]
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
