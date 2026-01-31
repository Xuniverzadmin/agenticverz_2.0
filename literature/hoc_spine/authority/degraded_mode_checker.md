# degraded_mode_checker.py

**Path:** `backend/app/hoc/hoc_spine/authority/degraded_mode_checker.py`  
**Layer:** L4 — HOC Spine (Authority)  
**Component:** Authority

---

## Placement Card

```
File:            degraded_mode_checker.py
Lives in:        authority/
Role:            Authority
Inbound:         ROK (L5), prevention_engine, incident_engine
Outbound:        none
Transaction:     Forbidden
Cross-domain:    none
Purpose:         Module: degraded_mode_checker
Violations:      none
```

## Purpose

Module: degraded_mode_checker
Purpose: Check and manage governance degraded mode with incident integration.

When governance systems are unavailable or degraded, this module:
    - Tracks the degraded state with proper metadata
    - Creates incidents for degraded mode transitions
    - Enforces degraded mode rules (block new runs, warn existing)
    - Integrates with incident response for visibility

Degraded Mode States:
    - NORMAL: Governance is fully operational
    - DEGRADED: Governance is partially unavailable
    - CRITICAL: Governance is fully unavailable (block all)

Exports:
    - GovernanceDegradedModeError: Raised when degraded mode blocks operation
    - GovernanceDegradedModeChecker: Main checker class
    - DegradedModeIncidentCreator: Creates incidents for degraded mode
    - check_degraded_mode: Quick helper function
    - enter_degraded_with_incident: Enter degraded mode with incident

## Import Analysis

Pure stdlib — no application imports.

## Transaction Boundary

- **Commits:** no
- **Flushes:** no
- **Rollbacks:** no

## Functions

### `check_degraded_mode(check_enabled: bool) -> DegradedModeCheckResponse`

Quick helper to check degraded mode.

Args:
    check_enabled: Whether checking is enabled

Returns:
    DegradedModeCheckResponse with current state

### `ensure_not_degraded(operation: str, check_enabled: bool) -> None`

Quick helper to ensure not in degraded mode or raise error.

Args:
    operation: Name of the operation being attempted
    check_enabled: Whether checking is enabled

Raises:
    GovernanceDegradedModeError: If governance is degraded and blocking

### `enter_degraded_with_incident(state: DegradedModeState, reason: str, entered_by: str, new_runs_action: str, existing_runs_action: str) -> DegradedModeStatus`

Quick helper to enter degraded mode with incident.

Args:
    state: Degraded mode state to enter
    reason: Reason for entering degraded mode
    entered_by: Who/what triggered the transition
    new_runs_action: Action for new runs
    existing_runs_action: Action for existing runs

Returns:
    DegradedModeStatus after transition

### `_reset_degraded_mode_state() -> None`

Reset global state (for testing only).

## Classes

### `DegradedModeCheckResult(str, Enum)`

Result of a degraded mode check.

### `DegradedModeState(str, Enum)`

Possible degraded mode states.

### `GovernanceDegradedModeError(Exception)`

Raised when governance degraded mode blocks an operation.

This error indicates that governance is in a degraded state
and the requested operation cannot be performed.

#### Methods

- `__init__(message: str, state: DegradedModeState, operation: str, degraded_since: Optional[str], degraded_reason: Optional[str])` — _No docstring._
- `to_dict() -> Dict[str, Any]` — Convert to dictionary for logging/API responses.

### `DegradedModeStatus`

Current degraded mode status.

#### Methods

- `to_dict() -> Dict[str, Any]` — Convert to dictionary.

### `DegradedModeCheckResponse`

Response from a degraded mode check.

#### Methods

- `to_dict() -> Dict[str, Any]` — Convert to dictionary for API responses.

### `DegradedModeIncident`

Incident data for degraded mode transition.

### `DegradedModeIncidentCreator`

Creates incidents for degraded mode transitions.

When governance enters or exits degraded mode, an incident
is created to provide visibility and audit trail.

#### Methods

- `__init__(tenant_id: str)` — Initialize the incident creator.
- `create_degraded_incident(state: DegradedModeState, reason: str, entered_by: str) -> DegradedModeIncident` — Create an incident for entering degraded mode.
- `create_recovery_incident(previous_state: DegradedModeState, recovered_by: str, duration_seconds: Optional[int]) -> DegradedModeIncident` — Create an incident for exiting degraded mode (recovery).

### `GovernanceDegradedModeChecker`

Checks and manages governance degraded mode.

GAP-070: Add DEGRADED state for incident response.

The checker validates governance availability and can enter/exit
degraded mode, creating incidents for visibility.

Usage:
    checker = GovernanceDegradedModeChecker(check_enabled=True)

    # Check before starting a new run
    response = checker.check()
    if response.is_degraded:
        handle_degraded_mode(response)

    # Or ensure not degraded (raises on degraded)
    checker.ensure_not_degraded("start_new_run")

    # Enter degraded mode with incident
    checker.enter_degraded(
        state=DegradedModeState.DEGRADED,
        reason="Database connection pool exhausted",
        entered_by="health_monitor",
    )

#### Methods

- `__init__(check_enabled: bool, incident_creator: Optional[DegradedModeIncidentCreator])` — Initialize the degraded mode checker.
- `from_governance_config(config: Any) -> 'GovernanceDegradedModeChecker'` — Create checker from GovernanceConfig.
- `check_enabled() -> bool` — Check if degraded mode checking is enabled.
- `get_current_status() -> DegradedModeStatus` — Get current degraded mode status.
- `check() -> DegradedModeCheckResponse` — Check current degraded mode state.
- `ensure_not_degraded(operation: str) -> None` — Ensure governance is not in degraded mode or raise error.
- `enter_degraded(state: DegradedModeState, reason: str, entered_by: str, new_runs_action: str, existing_runs_action: str, create_incident: bool) -> DegradedModeStatus` — Enter degraded mode.
- `exit_degraded(exited_by: str, create_incident: bool) -> DegradedModeStatus` — Exit degraded mode (recover to normal).
- `should_allow_new_run(run_id: str) -> tuple[bool, str]` — Check if a new run should be allowed.
- `get_existing_run_action() -> str` — Get action for existing/in-flight runs.

## Domain Usage

**Callers:** ROK (L5), prevention_engine, incident_engine

## Export Contract

```yaml
exports:
  functions:
    - name: check_degraded_mode
      signature: "check_degraded_mode(check_enabled: bool) -> DegradedModeCheckResponse"
      consumers: ["orchestrator"]
    - name: ensure_not_degraded
      signature: "ensure_not_degraded(operation: str, check_enabled: bool) -> None"
      consumers: ["orchestrator"]
    - name: enter_degraded_with_incident
      signature: "enter_degraded_with_incident(state: DegradedModeState, reason: str, entered_by: str, new_runs_action: str, existing_runs_action: str) -> DegradedModeStatus"
      consumers: ["orchestrator"]
    - name: _reset_degraded_mode_state
      signature: "_reset_degraded_mode_state() -> None"
      consumers: ["orchestrator"]
  classes:
    - name: DegradedModeCheckResult
      methods: []
      consumers: ["orchestrator"]
    - name: DegradedModeState
      methods: []
      consumers: ["orchestrator"]
    - name: GovernanceDegradedModeError
      methods:
        - to_dict
      consumers: ["orchestrator"]
    - name: DegradedModeStatus
      methods:
        - to_dict
      consumers: ["orchestrator"]
    - name: DegradedModeCheckResponse
      methods:
        - to_dict
      consumers: ["orchestrator"]
    - name: DegradedModeIncident
      methods: []
      consumers: ["orchestrator"]
    - name: DegradedModeIncidentCreator
      methods:
        - create_degraded_incident
        - create_recovery_incident
      consumers: ["orchestrator"]
    - name: GovernanceDegradedModeChecker
      methods:
        - from_governance_config
        - check_enabled
        - get_current_status
        - check
        - ensure_not_degraded
        - enter_degraded
        - exit_degraded
        - should_allow_new_run
        - get_existing_run_action
      consumers: ["orchestrator"]
  protocols: []
```

## Import Boundary

```yaml
boundary:
  allowed_inbound:
    - "hoc_spine.orchestrator.*"
  forbidden_inbound:
    - "hoc.cus.*"
    - "hoc.api.*"
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

