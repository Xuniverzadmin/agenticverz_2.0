# hoc_cus_policies_L5_engines_recovery_evaluation_engine

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/policies/L5_engines/recovery_evaluation_engine.py` |
| Layer | L5 — Domain Engine (System Truth) |
| Domain | policies |
| Audience | CUSTOMER |
| Artifact Class | CODE |

## Description

Recovery evaluation decision-making (domain logic)

## Intent

**Role:** Recovery evaluation decision-making (domain logic)
**Reference:** PIN-470, PIN-257 Phase R-1 (L5→L4 Violation Fix)
**Callers:** API endpoints, failure processing pipeline

## Purpose

Domain engine for recovery evaluation decisions.

---

## Functions

### `evaluate_recovery(failure_match_id: str, error_code: str, error_message: str, **kwargs) -> RecoveryDecision`
- **Async:** No
- **Docstring:** Convenience function to evaluate a failure and get a decision.  This is the L4 entry point for recovery evaluation. It returns
- **Calls:** FailureContext, RecoveryEvaluationEngine, evaluate, get

### `async evaluate_and_execute(failure_match_id: str, error_code: str, error_message: str, **kwargs) -> 'EvaluationOutcome'`
- **Async:** Yes
- **Docstring:** Full entry point: evaluate failure and execute decision.  This L4 function:
- **Calls:** FailureContext, FailureEvent, RecoveryEvaluationEngine, RecoveryExecutor, emit_decision_record, evaluate, execute_decision, get

## Classes

### `FailureContext`
- **Docstring:** Context for recovery evaluation (mirrors L5 FailureEvent for L4 use).
- **Methods:** __post_init__
- **Class Variables:** failure_match_id: str, error_code: str, error_message: str, skill_id: Optional[str], tenant_id: Optional[str], agent_id: Optional[str], run_id: Optional[str], occurred_at: Optional[datetime], metadata: Dict[str, Any]

### `RecoveryDecision`
- **Docstring:** Domain decision DTO returned by L4 engine to L5 executor.
- **Methods:** to_dict
- **Class Variables:** suggested_action: Optional[str], combined_confidence: float, should_select_action: bool, should_auto_execute: bool, candidate_id: Optional[int], rule_result: Dict[str, Any], match_confidence: float, failure_match_id: str, run_id: Optional[str], tenant_id: Optional[str]

### `RecoveryEvaluationEngine`
- **Docstring:** L4 Domain Engine for recovery evaluation decisions.
- **Methods:** __init__, evaluate, emit_decision_record

## Attributes

- `logger` (line 50)
- `__all__` (line 405)

---

## Import Analysis

| Category | Imports |
|----------|---------|
| L5 Engine | `app.hoc.cus.incidents.L5_engines.recovery_rule_engine` |
| L6 Driver | `app.hoc.cus.policies.L6_drivers.recovery_matcher` |
| Cross-Domain | `app.hoc.cus.incidents.L5_engines.recovery_rule_engine` |
| External | `app.contracts.decisions`, `app.worker.recovery_evaluator` |

## Callers

API endpoints, failure processing pipeline

## Export Contract

```yaml
exports:
  functions:
    - name: evaluate_recovery
      signature: "evaluate_recovery(failure_match_id: str, error_code: str, error_message: str, **kwargs) -> RecoveryDecision"
    - name: evaluate_and_execute
      signature: "async evaluate_and_execute(failure_match_id: str, error_code: str, error_message: str, **kwargs) -> 'EvaluationOutcome'"
  classes:
    - name: FailureContext
      methods: []
    - name: RecoveryDecision
      methods: [to_dict]
    - name: RecoveryEvaluationEngine
      methods: [evaluate, emit_decision_record]
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
