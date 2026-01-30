# hoc_models_run_lifecycle

| Field | Value |
|-------|-------|
| Path | `backend/app/models/run_lifecycle.py` |
| Layer | L6 — Platform Substrate |
| Domain | shared |
| Audience | SHARED |
| Artifact Class | CODE |

## Description

Run lifecycle enums and models for governance

## Intent

**Role:** Run lifecycle enums and models for governance
**Reference:** BACKEND_REMEDIATION_PLAN.md GAP-002, GAP-007
**Callers:** worker/runner.py, services/*, api/*

## Purpose

Run Lifecycle Models

---

## Functions

### `get_lifecycle_state(status: RunStatus) -> RunLifecycleState`
- **Async:** No
- **Docstring:** Map run status to lifecycle state.

## Classes

### `RunTerminationReason(str, Enum)`
- **Docstring:** Formal enum for why a run terminated.

### `RunStatus(str, Enum)`
- **Docstring:** Run execution status.

### `RunLifecycleState(str, Enum)`
- **Docstring:** High-level lifecycle state for UI purposes.

### `PolicyViolationType(str, Enum)`
- **Docstring:** Types of policy violations that can stop a run.

### `ViolationSeverity(str, Enum)`
- **Docstring:** Severity levels for violations.

### `RunViolationInfo(BaseModel)`
- **Docstring:** Information about a policy violation that stopped a run.
- **Class Variables:** policy_id: str, policy_name: str, violation_type: PolicyViolationType, severity: ViolationSeverity, step_index: int, timestamp: datetime, threshold_value: Optional[str], actual_value: Optional[str], reason: str

### `RunTerminationInfo(BaseModel)`
- **Docstring:** Complete termination information for a run.
- **Class Variables:** termination_reason: RunTerminationReason, terminated_at: datetime, stopped_at_step: Optional[int], violation_info: Optional[RunViolationInfo], error_message: Optional[str]

## Attributes

- `TERMINATION_TO_STATUS: dict[RunTerminationReason, RunStatus]` (line 131)
- `SEVERITY_PRIORITY: dict[ViolationSeverity, int]` (line 142)

---

## Import Analysis

| Category | Imports |
|----------|---------|
| External | `pydantic` |

## Callers

worker/runner.py, services/*, api/*

## Export Contract

```yaml
exports:
  functions:
    - name: get_lifecycle_state
      signature: "get_lifecycle_state(status: RunStatus) -> RunLifecycleState"
  classes:
    - name: RunTerminationReason
      methods: []
    - name: RunStatus
      methods: []
    - name: RunLifecycleState
      methods: []
    - name: PolicyViolationType
      methods: []
    - name: ViolationSeverity
      methods: []
    - name: RunViolationInfo
      methods: []
    - name: RunTerminationInfo
      methods: []
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
