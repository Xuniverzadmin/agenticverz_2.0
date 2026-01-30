# hoc_cus_policies_L5_engines_limits_facade

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/policies/L5_engines/limits_facade.py` |
| Layer | L5 — Domain Engine |
| Domain | policies |
| Audience | CUSTOMER |
| Artifact Class | CODE |

## Description

Limits Facade - Centralized access to rate limits and quotas

## Intent

**Role:** Limits Facade - Centralized access to rate limits and quotas
**Reference:** PIN-470, GAP-122 (Limits API)
**Callers:** L2 limits.py API, SDK

## Purpose

Limits Facade (L4 Domain Logic)

---

## Functions

### `get_limits_facade() -> LimitsFacade`
- **Async:** No
- **Docstring:** Get the limits facade instance.  This is the recommended way to access limit operations
- **Calls:** LimitsFacade

## Classes

### `LimitType(str, Enum)`
- **Docstring:** Types of limits.

### `LimitPeriod(str, Enum)`
- **Docstring:** Limit period.

### `LimitConfig`
- **Docstring:** Limit configuration.
- **Methods:** to_dict
- **Class Variables:** id: str, tenant_id: str, limit_type: str, period: str, max_value: int, current_value: int, reset_at: str, enabled: bool, created_at: str, updated_at: Optional[str], metadata: Dict[str, Any]

### `LimitCheckResult`
- **Docstring:** Result of checking a limit.
- **Methods:** to_dict
- **Class Variables:** allowed: bool, limit_type: str, current_value: int, max_value: int, remaining: int, reset_at: str, message: str

### `UsageSummary`
- **Docstring:** Usage summary across all limits.
- **Methods:** to_dict
- **Class Variables:** tenant_id: str, limits: List[Dict[str, Any]], total_api_calls: int, total_token_usage: int, as_of: str

### `LimitsFacade`
- **Docstring:** Facade for limit operations.
- **Methods:** __init__, _get_or_create_limit, list_limits, get_limit, update_limit, check_limit, get_usage, reset_limit

## Attributes

- `logger` (line 60)
- `_facade_instance: Optional[LimitsFacade]` (line 443)

---

## Import Analysis

| Category | Imports |
|----------|---------|
| _None_ | Pure stdlib |

## Callers

L2 limits.py API, SDK

## Export Contract

```yaml
exports:
  functions:
    - name: get_limits_facade
      signature: "get_limits_facade() -> LimitsFacade"
  classes:
    - name: LimitType
      methods: []
    - name: LimitPeriod
      methods: []
    - name: LimitConfig
      methods: [to_dict]
    - name: LimitCheckResult
      methods: [to_dict]
    - name: UsageSummary
      methods: [to_dict]
    - name: LimitsFacade
      methods: [list_limits, get_limit, update_limit, check_limit, get_usage, reset_limit]
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
