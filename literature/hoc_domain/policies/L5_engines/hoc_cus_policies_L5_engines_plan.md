# hoc_cus_policies_L5_engines_plan

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/policies/L5_engines/plan.py` |
| Layer | L5 — Domain Engine |
| Domain | policies |
| Audience | CUSTOMER |
| Artifact Class | CODE |

## Description

Phase-6 Plan model (abstract, no DB persistence)

## Intent

**Role:** Phase-6 Plan model (abstract, no DB persistence)
**Reference:** PIN-470, PIN-399 Phase-6 (Billing, Plans & Limits)
**Callers:** BillingProvider, limits derivation

## Purpose

Phase-6 Plan Model — Named Contracts (Not Pricing Logic)

---

## Classes

### `PlanTier(Enum)`
- **Docstring:** Plan tier hierarchy.
- **Methods:** from_string

### `Plan`
- **Docstring:** Phase-6 Plan Model (Immutable).
- **Methods:** __post_init__
- **Class Variables:** id: str, name: str, tier: PlanTier, limits_profile: str, description: Optional[str]

## Attributes

- `PLAN_FREE` (line 110)
- `PLAN_PRO` (line 118)
- `PLAN_ENTERPRISE` (line 126)
- `DEFAULT_PLAN` (line 135)
- `__all__` (line 138)

---

## Import Analysis

| Category | Imports |
|----------|---------|
| _None_ | Pure stdlib |

## Callers

BillingProvider, limits derivation

## Export Contract

```yaml
exports:
  functions: []
  classes:
    - name: PlanTier
      methods: [from_string]
    - name: Plan
      methods: []
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
