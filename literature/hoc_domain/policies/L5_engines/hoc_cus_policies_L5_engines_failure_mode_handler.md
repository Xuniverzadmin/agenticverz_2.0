# hoc_cus_policies_L5_engines_failure_mode_handler

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/policies/L5_engines/failure_mode_handler.py` |
| Layer | L5 — Domain Engine |
| Domain | policies |
| Audience | CUSTOMER |
| Artifact Class | CODE |

## Description

Handle failure modes - default to fail-closed

## Intent

**Role:** Handle failure modes - default to fail-closed
**Reference:** PIN-470, GAP-035
**Callers:** prevention_engine.py

## Purpose

Module: failure_mode_handler
Purpose: Handles failure modes when policy evaluation fails or is uncertain.

---

## Functions

### `get_failure_mode() -> FailureMode`
- **Async:** No
- **Docstring:** Get configured failure mode.  Returns:
- **Calls:** FailureMode, get_governance_config, hasattr, lower, str, warning

### `handle_policy_failure(error: Optional[Exception], context: Dict[str, Any], failure_type: FailureType) -> FailureDecision`
- **Async:** No
- **Docstring:** Handle a policy evaluation failure.  This function determines what action to take when policy evaluation
- **Calls:** FailureDecision, error, get, get_failure_mode, info, isoformat, now, str, warning

### `handle_missing_policy(context: Dict[str, Any]) -> FailureDecision`
- **Async:** No
- **Docstring:** Handle case where no policy exists for the action.  By default, missing policy = BLOCK (fail-closed).
- **Calls:** handle_policy_failure

### `handle_evaluation_error(error: Exception, context: Dict[str, Any]) -> FailureDecision`
- **Async:** No
- **Docstring:** Handle policy evaluation error.  Args:
- **Calls:** handle_policy_failure

### `handle_timeout(context: Dict[str, Any], timeout_seconds: float) -> FailureDecision`
- **Async:** No
- **Docstring:** Handle policy evaluation timeout.  Args:
- **Calls:** Exception, handle_policy_failure

## Classes

### `FailureMode(str, Enum)`
- **Docstring:** Failure mode for policy evaluation.

### `FailureType(str, Enum)`
- **Docstring:** Type of failure encountered.

### `FailureDecision`
- **Docstring:** Decision made when failure occurs.
- **Class Variables:** action: str, failure_type: FailureType, failure_mode: FailureMode, reason: str, should_block: bool, audit_required: bool, timestamp: str

## Attributes

- `logger` (line 52)
- `DEFAULT_FAILURE_MODE` (line 85)

---

## Import Analysis

| Category | Imports |
|----------|---------|
| External | `app.hoc.cus.hoc_spine.authority.profile_policy_mode` |

## Callers

prevention_engine.py

## Export Contract

```yaml
exports:
  functions:
    - name: get_failure_mode
      signature: "get_failure_mode() -> FailureMode"
    - name: handle_policy_failure
      signature: "handle_policy_failure(error: Optional[Exception], context: Dict[str, Any], failure_type: FailureType) -> FailureDecision"
    - name: handle_missing_policy
      signature: "handle_missing_policy(context: Dict[str, Any]) -> FailureDecision"
    - name: handle_evaluation_error
      signature: "handle_evaluation_error(error: Exception, context: Dict[str, Any]) -> FailureDecision"
    - name: handle_timeout
      signature: "handle_timeout(context: Dict[str, Any], timeout_seconds: float) -> FailureDecision"
  classes:
    - name: FailureMode
      methods: []
    - name: FailureType
      methods: []
    - name: FailureDecision
      methods: []
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
