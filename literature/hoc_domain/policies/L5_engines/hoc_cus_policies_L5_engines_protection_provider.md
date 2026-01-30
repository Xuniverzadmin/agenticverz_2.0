# hoc_cus_policies_L5_engines_protection_provider

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/policies/L5_engines/protection_provider.py` |
| Layer | L5 — Domain Engine |
| Domain | policies |
| Audience | CUSTOMER |
| Artifact Class | CODE |

## Description

Phase-7 AbuseProtectionProvider protocol and MockAbuseProtectionProvider

## Intent

**Role:** Phase-7 AbuseProtectionProvider protocol and MockAbuseProtectionProvider
**Reference:** PIN-470, PIN-399 Phase-7 (Abuse & Protection Layer)
**Callers:** protection middleware, SDK endpoints, runtime paths

## Purpose

Phase-7 Abuse Protection Provider — Interface and Mock Implementation

---

## Functions

### `get_protection_provider() -> AbuseProtectionProvider`
- **Async:** No
- **Docstring:** Get the abuse protection provider instance.  Returns MockAbuseProtectionProvider by default.
- **Calls:** MockAbuseProtectionProvider

### `set_protection_provider(provider: AbuseProtectionProvider) -> None`
- **Async:** No
- **Docstring:** Set the abuse protection provider instance.  Used for testing or to swap in a real provider.

## Classes

### `AbuseProtectionProvider(Protocol)`
- **Docstring:** Phase-7 Abuse Protection Provider Protocol.
- **Methods:** check_rate_limit, check_burst, check_cost, detect_anomaly, check_all

### `MockAbuseProtectionProvider`
- **Docstring:** Phase-7 Mock Abuse Protection Provider.
- **Methods:** __init__, check_rate_limit, check_burst, check_cost, detect_anomaly, check_all, add_cost, reset, reset_rate_limits

## Attributes

- `logger` (line 60)
- `_protection_provider: Optional[AbuseProtectionProvider]` (line 357)
- `__all__` (line 383)

---

## Import Analysis

| Category | Imports |
|----------|---------|
| External | `app.billing`, `app.protection.decisions` |

## Callers

protection middleware, SDK endpoints, runtime paths

## Export Contract

```yaml
exports:
  functions:
    - name: get_protection_provider
      signature: "get_protection_provider() -> AbuseProtectionProvider"
    - name: set_protection_provider
      signature: "set_protection_provider(provider: AbuseProtectionProvider) -> None"
  classes:
    - name: AbuseProtectionProvider
      methods: [check_rate_limit, check_burst, check_cost, detect_anomaly, check_all]
    - name: MockAbuseProtectionProvider
      methods: [check_rate_limit, check_burst, check_cost, detect_anomaly, check_all, add_cost, reset, reset_rate_limits]
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
