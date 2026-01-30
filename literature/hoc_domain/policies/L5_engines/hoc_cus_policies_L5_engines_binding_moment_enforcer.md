# hoc_cus_policies_L5_engines_binding_moment_enforcer

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/policies/L5_engines/binding_moment_enforcer.py` |
| Layer | L5 — Domain Engine |
| Domain | policies |
| Audience | CUSTOMER |
| Artifact Class | CODE |

## Description

Enforce binding moments - when policies are evaluated

## Intent

**Role:** Enforce binding moments - when policies are evaluated
**Reference:** PIN-470, GAP-031
**Callers:** prevention_engine.py

## Purpose

Module: binding_moment_enforcer
Purpose: Ensures policies are evaluated at the correct binding moment.

---

## Functions

### `should_evaluate_policy(policy: Any, context: Dict[str, Any], evaluation_point: EvaluationPoint) -> BindingDecision`
- **Async:** No
- **Docstring:** Determine if a policy should be evaluated at this point.  Respects the policy's bind_at setting:
- **Calls:** BindingDecision, _check_fields_changed, _mark_evaluated, _was_evaluated, debug, get, get_binding_moment, getattr, str

### `get_binding_moment(policy: Any) -> BindingMoment`
- **Async:** No
- **Docstring:** Get the binding moment for a policy.  Args:
- **Calls:** BindingMoment, getattr, isinstance, lower, warning

### `clear_run_cache(run_id: str) -> None`
- **Async:** No
- **Docstring:** Clear the evaluation cache for a run (call on run completion).

### `_mark_evaluated(run_id: str, policy_id: str) -> None`
- **Async:** No
- **Docstring:** Mark a policy as evaluated for a run.
- **Calls:** add, set

### `_was_evaluated(run_id: str, policy_id: str) -> bool`
- **Async:** No
- **Docstring:** Check if a policy was already evaluated for a run.

### `_check_fields_changed(policy: Any, context: Dict[str, Any]) -> bool`
- **Async:** No
- **Docstring:** Check if monitored fields changed (for ON_CHANGE binding).
- **Calls:** get, getattr

## Classes

### `BindingMoment(str, Enum)`
- **Docstring:** When a policy should be evaluated.

### `EvaluationPoint(str, Enum)`
- **Docstring:** Current point in execution where evaluation is requested.

### `BindingDecision`
- **Docstring:** Decision about whether to evaluate a policy.
- **Class Variables:** should_evaluate: bool, binding_moment: BindingMoment, evaluation_point: EvaluationPoint, reason: str, policy_id: str

## Attributes

- `logger` (line 55)
- `_run_evaluated_policies: Dict[str, Set[str]]` (line 86)

---

## Import Analysis

| Category | Imports |
|----------|---------|
| _None_ | Pure stdlib |

## Callers

prevention_engine.py

## Export Contract

```yaml
exports:
  functions:
    - name: should_evaluate_policy
      signature: "should_evaluate_policy(policy: Any, context: Dict[str, Any], evaluation_point: EvaluationPoint) -> BindingDecision"
    - name: get_binding_moment
      signature: "get_binding_moment(policy: Any) -> BindingMoment"
    - name: clear_run_cache
      signature: "clear_run_cache(run_id: str) -> None"
  classes:
    - name: BindingMoment
      methods: []
    - name: EvaluationPoint
      methods: []
    - name: BindingDecision
      methods: []
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
