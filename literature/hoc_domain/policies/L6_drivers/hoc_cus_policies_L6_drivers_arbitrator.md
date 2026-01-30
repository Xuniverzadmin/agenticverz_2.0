# hoc_cus_policies_L6_drivers_arbitrator

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/policies/L6_drivers/arbitrator.py` |
| Layer | L6 — Domain Driver |
| Domain | policies |
| Audience | CUSTOMER |
| Artifact Class | CODE |

## Description

Resolve conflicts between multiple applicable policies

## Intent

**Role:** Resolve conflicts between multiple applicable policies
**Reference:** PIN-470, POLICY_CONTROL_LEVER_IMPLEMENTATION_PLAN.md PCL-004
**Callers:** policy/prevention_engine.py, worker/runner.py

## Purpose

Policy Arbitrator Engine

---

## Functions

### `get_policy_arbitrator() -> PolicyArbitrator`
- **Async:** No
- **Docstring:** Get or create PolicyArbitrator singleton.
- **Calls:** PolicyArbitrator

## Classes

### `PolicyLimit`
- **Docstring:** Represents a policy limit.
- **Class Variables:** policy_id: str, limit_type: str, value: float, precedence: int

### `PolicyAction`
- **Docstring:** Represents a policy breach action.
- **Class Variables:** policy_id: str, action: str, precedence: int

### `ArbitrationInput`
- **Docstring:** Input for policy arbitration.
- **Class Variables:** policy_ids: list[str], token_limits: list[PolicyLimit], cost_limits: list[PolicyLimit], burn_rate_limits: list[PolicyLimit], breach_actions: list[PolicyAction]

### `PolicyArbitrator`
- **Docstring:** Resolves conflicts between multiple applicable policies.
- **Methods:** __init__, arbitrate, _load_precedence_map, _get_precedence_map, _resolve_limit_conflict, _resolve_action_conflict

## Attributes

- `logger` (line 52)
- `ACTION_SEVERITY` (line 75)
- `_arbitrator: Optional[PolicyArbitrator]` (line 331)

---

## Import Analysis

| Category | Imports |
|----------|---------|
| L7 Model | `app.models.policy_precedence` |
| External | `app.db`, `sqlmodel` |

## Callers

policy/prevention_engine.py, worker/runner.py

## Export Contract

```yaml
exports:
  functions:
    - name: get_policy_arbitrator
      signature: "get_policy_arbitrator() -> PolicyArbitrator"
  classes:
    - name: PolicyLimit
      methods: []
    - name: PolicyAction
      methods: []
    - name: ArbitrationInput
      methods: []
    - name: PolicyArbitrator
      methods: [arbitrate]
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
