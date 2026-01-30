# hoc_cus_account_L5_engines_billing_provider

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/account/L5_engines/billing_provider.py` |
| Layer | L5 — Domain Engine |
| Domain | account |
| Audience | CUSTOMER |
| Artifact Class | CODE |

## Description

Phase-6 BillingProvider protocol and MockBillingProvider

## Intent

**Role:** Phase-6 BillingProvider protocol and MockBillingProvider
**Reference:** PIN-470, PIN-399 Phase-6 (Billing, Plans & Limits)
**Callers:** billing middleware, billing APIs, runtime enforcement

## Purpose

Phase-6 Billing Provider — Interface and Mock Implementation

---

## Functions

### `get_billing_provider() -> BillingProvider`
- **Async:** No
- **Docstring:** Get the billing provider instance.  Returns MockBillingProvider by default.
- **Calls:** MockBillingProvider

### `set_billing_provider(provider: BillingProvider) -> None`
- **Async:** No
- **Docstring:** Set the billing provider instance.  Used for testing or to swap in a real provider.

## Classes

### `BillingProvider(Protocol)`
- **Docstring:** Phase-6 Billing Provider Protocol.
- **Methods:** get_billing_state, get_plan, get_limits, is_limit_exceeded

### `MockBillingProvider`
- **Docstring:** Phase-6 Mock Billing Provider.
- **Methods:** __init__, get_billing_state, get_plan, get_limits, is_limit_exceeded, set_billing_state, set_plan, reset

## Attributes

- `logger` (line 44)
- `_billing_provider: Optional[BillingProvider]` (line 220)
- `__all__` (line 246)

---

## Import Analysis

| Category | Imports |
|----------|---------|
| External | `app.billing.limits`, `app.billing.plan`, `app.billing.state` |

## Callers

billing middleware, billing APIs, runtime enforcement

## Export Contract

```yaml
exports:
  functions:
    - name: get_billing_provider
      signature: "get_billing_provider() -> BillingProvider"
    - name: set_billing_provider
      signature: "set_billing_provider(provider: BillingProvider) -> None"
  classes:
    - name: BillingProvider
      methods: [get_billing_state, get_plan, get_limits, is_limit_exceeded]
    - name: MockBillingProvider
      methods: [get_billing_state, get_plan, get_limits, is_limit_exceeded, set_billing_state, set_plan, reset]
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
