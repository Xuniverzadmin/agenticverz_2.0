# hoc_cus_integrations_L5_engines_customer_policies_adapter

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/integrations/L5_engines/external_adapters/customer_policies_adapter.py` |
| Layer | L3 — Boundary Adapter |
| Domain | integrations |
| Audience | CUSTOMER |
| Artifact Class | CODE |

## Description

Customer policies boundary adapter (L2 → L3 → L4)

## Intent

**Role:** Customer policies boundary adapter (L2 → L3 → L4)
**Reference:** PIN-280, PIN-281 (L2 Promotion Governance)
**Callers:** guard_policies.py (L2)

## Purpose

Customer Policies Boundary Adapter (L3)

---

## Functions

### `get_customer_policies_adapter() -> CustomerPoliciesAdapter`
- **Async:** No
- **Docstring:** Get the singleton CustomerPoliciesAdapter instance.  This is the ONLY way L2 should obtain a policies adapter.
- **Calls:** CustomerPoliciesAdapter

## Classes

### `CustomerBudgetConstraint(BaseModel)`
- **Docstring:** Customer-visible budget constraint.
- **Class Variables:** limit_cents: int, period: str, current_usage_cents: int, remaining_cents: int, percentage_used: float, reset_at: Optional[str]

### `CustomerRateLimit(BaseModel)`
- **Docstring:** Customer-visible rate limit.
- **Class Variables:** requests_per_period: int, period: str, current_usage: int, remaining: int

### `CustomerGuardrail(BaseModel)`
- **Docstring:** Customer-visible guardrail configuration.
- **Class Variables:** id: str, name: str, description: str, enabled: bool, category: str, action_on_trigger: str

### `CustomerPolicyConstraints(BaseModel)`
- **Docstring:** Customer-visible policy constraints summary.
- **Class Variables:** tenant_id: str, budget: Optional[CustomerBudgetConstraint], rate_limits: List[CustomerRateLimit], guardrails: List[CustomerGuardrail], last_updated: str

### `CustomerPoliciesAdapter`
- **Docstring:** Boundary adapter for customer policy constraints.
- **Methods:** __init__, _get_service, get_policy_constraints, get_guardrail_detail, _to_customer_policy_constraints, _to_customer_guardrail

## Attributes

- `_customer_policies_adapter_instance: Optional[CustomerPoliciesAdapter]` (line 242)
- `__all__` (line 271)

---

## Import Analysis

| Category | Imports |
|----------|---------|
| L5 Engine | `app.hoc.cus.policies.L5_engines.customer_policy_read_engine` |
| Cross-Domain | `app.hoc.cus.policies.L5_engines.customer_policy_read_engine` |
| External | `pydantic` |

## Callers

guard_policies.py (L2)

## Export Contract

```yaml
exports:
  functions:
    - name: get_customer_policies_adapter
      signature: "get_customer_policies_adapter() -> CustomerPoliciesAdapter"
  classes:
    - name: CustomerBudgetConstraint
      methods: []
    - name: CustomerRateLimit
      methods: []
    - name: CustomerGuardrail
      methods: []
    - name: CustomerPolicyConstraints
      methods: []
    - name: CustomerPoliciesAdapter
      methods: [get_policy_constraints, get_guardrail_detail]
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
