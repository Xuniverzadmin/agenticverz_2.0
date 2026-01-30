# hoc_cus_policies_L5_engines_deterministic_engine

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/policies/L5_engines/deterministic_engine.py` |
| Layer | L5 — Domain Engine |
| Domain | policies |
| Audience | CUSTOMER |
| Artifact Class | CODE |

## Description

Deterministic policy execution engine

## Intent

**Role:** Deterministic policy execution engine
**Reference:** PIN-470, Policy System
**Callers:** policy evaluators, workers

## Purpose

Deterministic execution engine for PLang v2.0.

---

## Classes

### `ExecutionStatus(Enum)`
- **Docstring:** Status of policy execution.

### `ExecutionContext`
- **Docstring:** Execution context for policy evaluation.
- **Methods:** __post_init__, _generate_id, get_variable, set_variable, push_call, pop_call, add_trace
- **Class Variables:** execution_id: str, request_id: Optional[str], user_id: Optional[str], agent_id: Optional[str], variables: Dict[str, Any], call_stack: List[str], trace: List[Dict[str, Any]], final_action: Optional[ActionType], emitted_intents: List[Intent], step_count: int, max_steps: int, status: ExecutionStatus

### `ExecutionResult`
- **Docstring:** Result of policy execution.
- **Methods:** to_dict
- **Class Variables:** success: bool, action: Optional[ActionType], intents: List[Intent], trace: List[Dict[str, Any]], error: Optional[str], execution_id: str, step_count: int

### `DeterministicEngine`
- **Docstring:** Deterministic policy execution engine.
- **Methods:** __init__, _register_builtins, execute, _execute_function, _execute_instruction, _eval_binary_op, _eval_unary_op, _eval_compare, _call_function, _action_to_intent_type

---

## Import Analysis

| Category | Imports |
|----------|---------|
| External | `app.policy.compiler.grammar`, `app.policy.ir.ir_nodes`, `app.policy.runtime.intent` |

## Callers

policy evaluators, workers

## Export Contract

```yaml
exports:
  functions: []
  classes:
    - name: ExecutionStatus
      methods: []
    - name: ExecutionContext
      methods: [get_variable, set_variable, push_call, pop_call, add_trace]
    - name: ExecutionResult
      methods: [to_dict]
    - name: DeterministicEngine
      methods: [execute]
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
