# hoc_cus_policies_L5_engines_prevention_engine

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/policies/L5_engines/prevention_engine.py` |
| Layer | L5 — Domain Engine |
| Domain | policies |
| Audience | CUSTOMER |
| Artifact Class | CODE |

## Description

Policy prevention engine for runtime enforcement

## Intent

**Role:** Policy prevention engine for runtime enforcement
**Reference:** PIN-470, BACKEND_REMEDIATION_PLAN.md GAP-001, GAP-002
**Callers:** worker/runner.py

## Purpose

Prevention Engine

---

## Functions

### `create_policy_snapshot_for_run(tenant_id: str, run_id: str) -> Optional[str]`
- **Async:** No
- **Docstring:** Create a policy snapshot at run start.  Captures all active policies and thresholds for consistent
- **Calls:** Session, add, create_snapshot, error, flush, info, refresh, str

## Classes

### `PreventionAction(str, Enum)`
- **Docstring:** Action to take based on policy evaluation.

### `ViolationType(str, Enum)`
- **Docstring:** Types of policy violations.

### `PreventionContext`
- **Docstring:** Context for policy evaluation at a step checkpoint.
- **Class Variables:** run_id: str, tenant_id: str, step_index: int, policy_snapshot_id: Optional[str], tokens_used: int, cost_cents: int, steps_completed: int, step_skill: Optional[str], step_tokens: int, step_cost_cents: int, step_duration_ms: float, llm_response: Optional[dict[str, Any]], max_tokens_per_run: Optional[int], max_cost_cents_per_run: Optional[int], max_tokens_per_step: Optional[int], max_cost_cents_per_step: Optional[int]

### `PreventionResult`
- **Docstring:** Result of policy evaluation.
- **Methods:** allow, warn, block
- **Class Variables:** action: PreventionAction, policy_id: Optional[str], policy_name: Optional[str], violation_type: Optional[ViolationType], threshold_value: Optional[str], actual_value: Optional[str], reason: str, evaluated_at: datetime

### `PolicyViolationError(Exception)`
- **Docstring:** Exception raised when a policy violation stops a run.
- **Methods:** __init__

### `PreventionEngine`
- **Docstring:** Evaluates policies at runtime checkpoints.
- **Methods:** __init__, load_snapshot, evaluate_step, _evaluate_step_inner, _evaluate_custom_policy

## Attributes

- `logger` (line 41)

---

## Import Analysis

| Category | Imports |
|----------|---------|
| L7 Model | `app.models.policy_snapshot` |
| External | `app.db`, `app.policy.binding_moment_enforcer`, `app.policy.conflict_resolver`, `app.policy.failure_mode_handler`, `sqlmodel` |

## Callers

worker/runner.py

## Export Contract

```yaml
exports:
  functions:
    - name: create_policy_snapshot_for_run
      signature: "create_policy_snapshot_for_run(tenant_id: str, run_id: str) -> Optional[str]"
  classes:
    - name: PreventionAction
      methods: []
    - name: ViolationType
      methods: []
    - name: PreventionContext
      methods: []
    - name: PreventionResult
      methods: [allow, warn, block]
    - name: PolicyViolationError
      methods: []
    - name: PreventionEngine
      methods: [load_snapshot, evaluate_step]
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
