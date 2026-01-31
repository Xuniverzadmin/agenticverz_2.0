# phase_status_invariants.py

**Path:** `backend/app/hoc/hoc_spine/orchestrator/phase_status_invariants.py`  
**Layer:** L4 — HOC Spine (Orchestrator)  
**Component:** Orchestrator

---

## Placement Card

```
File:            phase_status_invariants.py
Lives in:        orchestrator/
Role:            Orchestrator
Inbound:         ROK, worker runtime
Outbound:        none
Transaction:     Forbidden
Cross-domain:    none
Purpose:         Module: phase_status_invariants
Violations:      none
```

## Purpose

Module: phase_status_invariants
Purpose: Enforce phase-status invariants using GovernanceConfig.

The phase_status_invariant_enforce flag in GovernanceConfig controls
whether invalid phase-status combinations are blocked.

Phase-Status Invariants:
    - CREATED, AUTHORIZED: status must be "queued"
    - EXECUTING, GOVERNANCE_CHECK, FINALIZING: status must be "running"
    - COMPLETED: status must be "succeeded"
    - FAILED: status must be "failed", "failed_policy", "cancelled", or "retry"

When enforcement is enabled, attempting an invalid combination raises
PhaseStatusInvariantEnforcementError.

Exports:
    - PhaseStatusInvariantEnforcementError: Raised on violation
    - PhaseStatusInvariantChecker: Main checker class
    - check_phase_status_invariant: Quick helper function

## Import Analysis

Pure stdlib — no application imports.

## Transaction Boundary

- **Commits:** no
- **Flushes:** no
- **Rollbacks:** no

## Functions

### `check_phase_status_invariant(phase: str, status: str, enforcement_enabled: bool) -> InvariantCheckResponse`

Quick helper to check a phase-status invariant.

Args:
    phase: Phase name
    status: Status value
    enforcement_enabled: Whether enforcement is enabled

Returns:
    InvariantCheckResponse with validation result

### `ensure_phase_status_invariant(phase: str, status: str, enforcement_enabled: bool) -> None`

Quick helper to ensure phase-status invariant or raise error.

Args:
    phase: Phase name
    status: Status value
    enforcement_enabled: Whether enforcement is enabled

Raises:
    PhaseStatusInvariantEnforcementError: If invalid and enforcement enabled

## Classes

### `InvariantCheckResult(str, Enum)`

Result of an invariant check.

### `PhaseStatusInvariantEnforcementError(Exception)`

Raised when phase-status invariant enforcement fails.

This error indicates that an invalid phase-status combination
was attempted when enforcement is enabled.

#### Methods

- `__init__(message: str, phase: str, status: str, allowed_statuses: FrozenSet[str], enforcement_enabled: bool)` — _No docstring._
- `to_dict() -> dict[str, Any]` — Convert to dictionary for logging/API responses.

### `InvariantCheckResponse`

Response from an invariant check.

#### Methods

- `to_dict() -> dict[str, Any]` — Convert to dictionary for API responses.

### `PhaseStatusInvariantChecker`

Checks and enforces phase-status invariants.

GAP-051: Add invariant checks to ROK.

The checker validates that phase-status combinations are valid
and can raise errors when enforcement is enabled.

Usage:
    checker = PhaseStatusInvariantChecker(enforcement_enabled=True)

    # Before a phase transition
    checker.ensure_valid("EXECUTING", "running")

    # Or check without raising
    response = checker.check("EXECUTING", "running")
    if not response.is_valid and response.enforcement_enabled:
        handle_invariant_violation()

#### Methods

- `__init__(enforcement_enabled: bool)` — Initialize the invariant checker.
- `from_governance_config(config: Any) -> 'PhaseStatusInvariantChecker'` — Create checker from GovernanceConfig.
- `enforcement_enabled() -> bool` — Check if enforcement is enabled.
- `get_allowed_statuses(phase: str) -> FrozenSet[str]` — Get allowed statuses for a phase.
- `is_valid_combination(phase: str, status: str) -> bool` — Check if a phase-status combination is valid.
- `check(phase: str, status: str) -> InvariantCheckResponse` — Check if a phase-status combination is valid.
- `ensure_valid(phase: str, status: str) -> None` — Ensure a phase-status combination is valid or raise error.
- `should_allow_transition(phase: str, status: str) -> tuple[bool, str]` — Check if a transition should be allowed.

## Domain Usage

**Callers:** ROK, worker runtime

## Export Contract

```yaml
exports:
  functions:
    - name: check_phase_status_invariant
      signature: "check_phase_status_invariant(phase: str, status: str, enforcement_enabled: bool) -> InvariantCheckResponse"
      consumers: ["orchestrator"]
    - name: ensure_phase_status_invariant
      signature: "ensure_phase_status_invariant(phase: str, status: str, enforcement_enabled: bool) -> None"
      consumers: ["orchestrator"]
  classes:
    - name: InvariantCheckResult
      methods: []
      consumers: ["orchestrator"]
    - name: PhaseStatusInvariantEnforcementError
      methods:
        - to_dict
      consumers: ["orchestrator"]
    - name: InvariantCheckResponse
      methods:
        - to_dict
      consumers: ["orchestrator"]
    - name: PhaseStatusInvariantChecker
      methods:
        - from_governance_config
        - enforcement_enabled
        - get_allowed_statuses
        - is_valid_combination
        - check
        - ensure_valid
        - should_allow_transition
      consumers: ["orchestrator"]
  protocols: []
```

## Import Boundary

```yaml
boundary:
  allowed_inbound:
    - "hoc.api.*"
    - "hoc_spine.adapters.*"
  forbidden_inbound:
  actual_imports:
    spine_internal: []
    l7_model: []
    external: []
  violations: []
```

## L5 Pairing Declaration

```yaml
pairing:
  serves_domains: []
  expected_l5_consumers: []
  orchestrator_operations: []
```

