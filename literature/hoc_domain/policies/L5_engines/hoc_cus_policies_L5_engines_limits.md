# hoc_cus_policies_L5_engines_limits

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/policies/L5_engines/limits.py` |
| Layer | L5 — Domain Engine |
| Domain | policies |
| Audience | CUSTOMER |
| Artifact Class | CODE |

## Description

Phase-6 Limits derivation (code only, not stored)

## Intent

**Role:** Phase-6 Limits derivation (code only, not stored)
**Reference:** PIN-470, PIN-399 Phase-6 (Billing, Plans & Limits)
**Callers:** BillingProvider, enforcement middleware

## Purpose

Phase-6 Limits — Derived from Plan (Not Stored)

---

## Functions

### `derive_limits(limits_profile: str) -> Limits`
- **Async:** No
- **Docstring:** Derive limits from a limits profile key.  INVARIANT: This is the single source of limit derivation.
- **Calls:** get

## Classes

### `Limits`
- **Docstring:** Phase-6 Limits Model (Immutable, Derived).
- **Methods:** is_unlimited
- **Class Variables:** max_requests_per_day: Optional[int], max_active_agents: Optional[int], max_storage_mb: Optional[int], max_monthly_cost_usd: Optional[float], max_runs_per_day: Optional[int], max_policies: Optional[int]

## Attributes

- `LIMITS_PROFILES: dict[str, Limits]` (line 99)
- `DEFAULT_LIMITS` (line 127)
- `__all__` (line 152)

---

## Import Analysis

| Category | Imports |
|----------|---------|
| _None_ | Pure stdlib |

## Callers

BillingProvider, enforcement middleware

## Export Contract

```yaml
exports:
  functions:
    - name: derive_limits
      signature: "derive_limits(limits_profile: str) -> Limits"
  classes:
    - name: Limits
      methods: [is_unlimited]
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
