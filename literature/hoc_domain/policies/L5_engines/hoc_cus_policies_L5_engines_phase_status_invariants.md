# hoc_cus_policies_L5_engines_phase_status_invariants

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/policies/L5_engines/phase_status_invariants.py` |
| Layer | L5 — Domain Engine |
| Domain | policies |
| Audience | CUSTOMER |
| Artifact Class | CODE |

## Description

Phase-status invariant enforcement from GovernanceConfig

## Intent

**Role:** Phase-status invariant enforcement from GovernanceConfig
**Reference:** PIN-470, GAP-051 (Phase-Status Invariants)
**Callers:** ROK (L5), worker runtime

## Purpose

Module: phase_status_invariants
Purpose: Enforce phase-status invariants using GovernanceConfig.

---

## Functions

### `check_phase_status_invariant(phase: str, status: str, enforcement_enabled: bool) -> InvariantCheckResponse`
- **Async:** No
- **Docstring:** Quick helper to check a phase-status invariant.  Args:
- **Calls:** PhaseStatusInvariantChecker, check

### `ensure_phase_status_invariant(phase: str, status: str, enforcement_enabled: bool) -> None`
- **Async:** No
- **Docstring:** Quick helper to ensure phase-status invariant or raise error.  Args:
- **Calls:** PhaseStatusInvariantChecker, ensure_valid

## Classes

### `InvariantCheckResult(str, Enum)`
- **Docstring:** Result of an invariant check.

### `PhaseStatusInvariantEnforcementError(Exception)`
- **Docstring:** Raised when phase-status invariant enforcement fails.
- **Methods:** __init__, to_dict

### `InvariantCheckResponse`
- **Docstring:** Response from an invariant check.
- **Methods:** to_dict
- **Class Variables:** result: InvariantCheckResult, is_valid: bool, enforcement_enabled: bool, phase: str, status: str, allowed_statuses: FrozenSet[str], message: str

### `PhaseStatusInvariantChecker`
- **Docstring:** Checks and enforces phase-status invariants.
- **Methods:** __init__, from_governance_config, enforcement_enabled, get_allowed_statuses, is_valid_combination, check, ensure_valid, should_allow_transition

## Attributes

- `PHASE_STATUS_INVARIANTS: dict[str, FrozenSet[str]]` (line 56)

---

## Import Analysis

| Category | Imports |
|----------|---------|
| _None_ | Pure stdlib |

## Callers

ROK (L5), worker runtime

## Export Contract

```yaml
exports:
  functions:
    - name: check_phase_status_invariant
      signature: "check_phase_status_invariant(phase: str, status: str, enforcement_enabled: bool) -> InvariantCheckResponse"
    - name: ensure_phase_status_invariant
      signature: "ensure_phase_status_invariant(phase: str, status: str, enforcement_enabled: bool) -> None"
  classes:
    - name: InvariantCheckResult
      methods: []
    - name: PhaseStatusInvariantEnforcementError
      methods: [to_dict]
    - name: InvariantCheckResponse
      methods: [to_dict]
    - name: PhaseStatusInvariantChecker
      methods: [from_governance_config, enforcement_enabled, get_allowed_statuses, is_valid_combination, check, ensure_valid, should_allow_transition]
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
