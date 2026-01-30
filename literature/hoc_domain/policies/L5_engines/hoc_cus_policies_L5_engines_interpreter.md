# hoc_cus_policies_L5_engines_interpreter

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/policies/L5_engines/interpreter.py` |
| Layer | L5 — Domain Engine |
| Domain | policies |
| Audience | CUSTOMER |
| Artifact Class | CODE |

## Description

Policy DSL Interpreter (pure IR evaluation)

## Intent

**Role:** Policy DSL Interpreter (pure IR evaluation)
**Reference:** PIN-470, PIN-341 Section 1.8, PIN-345
**Callers:** policy engine

## Purpose

Policy DSL Interpreter

---

## Functions

### `evaluate(ir: PolicyIR, facts: dict[str, Any]) -> EvaluationResult`
- **Async:** No
- **Docstring:** Evaluate policy IR against facts.  This is the CANONICAL evaluation function.
- **Calls:** Interpreter, evaluate

### `evaluate_policy(ir: PolicyIR, facts: dict[str, Any], strict: bool) -> EvaluationResult`
- **Async:** No
- **Docstring:** Evaluate policy with optional strict mode.  Args:
- **Calls:** _LenientInterpreter, evaluate

## Classes

### `EvaluationError(Exception)`
- **Docstring:** Raised when evaluation fails.
- **Methods:** __init__

### `TypeMismatchError(EvaluationError)`
- **Docstring:** Raised when types are incompatible for comparison.

### `MissingMetricError(EvaluationError)`
- **Docstring:** Raised when a required metric is not in facts.

### `ActionResult`
- **Docstring:** A single action from evaluation.
- **Methods:** to_dict
- **Class Variables:** type: str, message: str | None

### `ClauseResult`
- **Docstring:** Evaluation result for a single clause.
- **Methods:** to_dict
- **Class Variables:** matched: bool, actions: tuple[ActionResult, ...]

### `EvaluationResult`
- **Docstring:** Complete evaluation result for a policy.
- **Methods:** to_dict, has_block, has_require_approval, warnings
- **Class Variables:** any_matched: bool, clauses: tuple[ClauseResult, ...], all_actions: tuple[ActionResult, ...]

### `Interpreter`
- **Docstring:** Pure interpreter for Policy IR.
- **Methods:** __init__, evaluate, _evaluate_clause, _evaluate_condition, _execute_instruction, _compare, _types_compatible, _collect_actions

### `_LenientInterpreter(Interpreter)`
- **Docstring:** Lenient interpreter that treats missing metrics as non-matching.
- **Methods:** _execute_instruction, _compare

### `_MissingSentinel`
- **Docstring:** Sentinel value for missing metrics.

## Attributes

- `_MISSING_SENTINEL` (line 562)

---

## Import Analysis

| Category | Imports |
|----------|---------|
| External | `__future__`, `app.dsl.ir_compiler` |

## Callers

policy engine

## Export Contract

```yaml
exports:
  functions:
    - name: evaluate
      signature: "evaluate(ir: PolicyIR, facts: dict[str, Any]) -> EvaluationResult"
    - name: evaluate_policy
      signature: "evaluate_policy(ir: PolicyIR, facts: dict[str, Any], strict: bool) -> EvaluationResult"
  classes:
    - name: EvaluationError
      methods: []
    - name: TypeMismatchError
      methods: []
    - name: MissingMetricError
      methods: []
    - name: ActionResult
      methods: [to_dict]
    - name: ClauseResult
      methods: [to_dict]
    - name: EvaluationResult
      methods: [to_dict, has_block, has_require_approval, warnings]
    - name: Interpreter
      methods: [evaluate]
    - name: _LenientInterpreter
      methods: []
    - name: _MissingSentinel
      methods: []
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
