# hoc_cus_policies_L5_engines_degraded_mode

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/policies/L5_engines/degraded_mode.py` |
| Layer | L5 — Domain Engine |
| Domain | policies |
| Audience | CUSTOMER |
| Artifact Class | CODE |

## Description

Degraded mode for governance system (pure state logic)

## Intent

**Role:** Degraded mode for governance system (pure state logic)
**Reference:** PIN-470, GAP-070
**Callers:** main.py, prevention_engine.py

## Purpose

Degraded Mode - Graceful Governance Degradation

---

## Functions

### `enter_degraded_mode(reason: str, entered_by: str, existing_runs_action: str) -> DegradedModeTransition`
- **Async:** No
- **Docstring:** Enter degraded mode.  New runs will be blocked, existing runs continue with warnings.
- **Calls:** DegradedModeStatus, DegradedModeTransition, isoformat, now, warning

### `exit_degraded_mode(exited_by: str) -> DegradedModeTransition`
- **Async:** No
- **Docstring:** Exit degraded mode.  Restores normal governance operation.
- **Calls:** DegradedModeTransition, get_inactive, info, isoformat, now

### `is_degraded_mode_active() -> bool`
- **Async:** No
- **Docstring:** Check if degraded mode is currently active.  Returns:

### `get_degraded_mode_status() -> DegradedModeStatus`
- **Async:** No
- **Docstring:** Get current degraded mode status.  Returns:
- **Calls:** get_inactive

### `should_allow_new_run(run_id: str) -> bool`
- **Async:** No
- **Docstring:** Check if a new run should be allowed.  In degraded mode, new runs are blocked.
- **Calls:** is_degraded_mode_active, warning

### `get_existing_run_action() -> str`
- **Async:** No
- **Docstring:** Get action for existing/in-flight runs in degraded mode.  Returns:

## Classes

### `DegradedModeStatus`
- **Docstring:** Current status of degraded mode.
- **Methods:** get_inactive
- **Class Variables:** is_active: bool, reason: Optional[str], entered_by: Optional[str], entered_at: Optional[str], existing_runs_action: str

### `DegradedModeTransition`
- **Docstring:** Result of degraded mode transition.
- **Class Variables:** success: bool, message: str, transitioned_at: Optional[str]

## Attributes

- `logger` (line 38)
- `_state_lock` (line 41)
- `_degraded_mode_active` (line 42)
- `_degraded_mode_status: Optional['DegradedModeStatus']` (line 43)

---

## Import Analysis

| Category | Imports |
|----------|---------|
| _None_ | Pure stdlib |

## Callers

main.py, prevention_engine.py

## Export Contract

```yaml
exports:
  functions:
    - name: enter_degraded_mode
      signature: "enter_degraded_mode(reason: str, entered_by: str, existing_runs_action: str) -> DegradedModeTransition"
    - name: exit_degraded_mode
      signature: "exit_degraded_mode(exited_by: str) -> DegradedModeTransition"
    - name: is_degraded_mode_active
      signature: "is_degraded_mode_active() -> bool"
    - name: get_degraded_mode_status
      signature: "get_degraded_mode_status() -> DegradedModeStatus"
    - name: should_allow_new_run
      signature: "should_allow_new_run(run_id: str) -> bool"
    - name: get_existing_run_action
      signature: "get_existing_run_action() -> str"
  classes:
    - name: DegradedModeStatus
      methods: [get_inactive]
    - name: DegradedModeTransition
      methods: []
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
