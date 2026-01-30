# hoc_cus_policies_L5_engines_customer_policy_read_engine

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/policies/L5_engines/customer_policy_read_engine.py` |
| Layer | L5 — Domain Engine |
| Domain | policies |
| Audience | CUSTOMER |
| Artifact Class | CODE |

## Description

Customer policy domain read operations with business logic (pure logic)

## Intent

**Role:** Customer policy domain read operations with business logic (pure logic)
**Reference:** PIN-470, PIN-281, PHASE2_EXTRACTION_PROTOCOL.md
**Callers:** customer_policies_adapter.py (L3)

## Purpose

Customer Policy Read Service (L4)

---

## Functions

### `get_customer_policy_read_service(session: 'Session') -> CustomerPolicyReadService`
- **Async:** No
- **Docstring:** Factory function for CustomerPolicyReadService.  Args:
- **Calls:** CustomerPolicyReadService

## Classes

### `BudgetConstraint`
- **Docstring:** Customer-visible budget constraint.
- **Class Variables:** limit_cents: int, period: str, current_usage_cents: int, remaining_cents: int, percentage_used: float, reset_at: Optional[str]

### `RateLimit`
- **Docstring:** Customer-visible rate limit.
- **Class Variables:** requests_per_period: int, period: str, current_usage: int, remaining: int

### `GuardrailSummary`
- **Docstring:** Customer-visible guardrail summary.
- **Class Variables:** id: str, name: str, description: str, enabled: bool, category: str, action_on_trigger: str

### `PolicyConstraints`
- **Docstring:** Customer-visible policy constraints summary.
- **Class Variables:** tenant_id: str, budget: Optional[BudgetConstraint], rate_limits: List[RateLimit], guardrails: List[GuardrailSummary], last_updated: str

### `CustomerPolicyReadService`
- **Docstring:** L4 service for policy constraint read operations.
- **Methods:** __init__, get_policy_constraints, get_guardrail_detail, _get_budget_constraint, _calculate_period_bounds, _get_rate_limits, _get_guardrails

---

## Import Analysis

| Category | Imports |
|----------|---------|
| L6 Driver | `app.hoc.cus.policies.L6_drivers.policy_read_driver` |
| External | `sqlmodel` |

## Callers

customer_policies_adapter.py (L3)

## Export Contract

```yaml
exports:
  functions:
    - name: get_customer_policy_read_service
      signature: "get_customer_policy_read_service(session: 'Session') -> CustomerPolicyReadService"
  classes:
    - name: BudgetConstraint
      methods: []
    - name: RateLimit
      methods: []
    - name: GuardrailSummary
      methods: []
    - name: PolicyConstraints
      methods: []
    - name: CustomerPolicyReadService
      methods: [get_policy_constraints, get_guardrail_detail]
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
