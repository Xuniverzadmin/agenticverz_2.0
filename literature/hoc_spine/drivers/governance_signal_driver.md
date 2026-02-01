# governance_signal_driver.py

**Path:** `backend/app/hoc/cus/hoc_spine/drivers/governance_signal_driver.py`  
**Layer:** L4 — HOC Spine (Driver)  
**Component:** Drivers

---

## Placement Card

```
File:            governance_signal_driver.py
Lives in:        drivers/
Role:            Drivers
Inbound:         L7 (BLCA, CI) for writes, L4/L5 for reads
Outbound:        none
Transaction:     Flush only (no commit)
Cross-domain:    none
Purpose:         Governance Signal Service (Phase E FIX-03)
Violations:      none
```

## Purpose

Governance Signal Service (Phase E FIX-03)

L6 service for persisting and querying governance signals.

Write Path (L7 → L6):
- BLCA, CI, OPS write signals via record_signal()
- Signals are persisted to governance_signals table
- Previous signals for same scope/type are superseded

Read Path (L4/L5 ← L6):
- Domain orchestrators check governance before decisions
- Workers check governance before execution
- Returns blocking/warning signals for scope

Contract:
- All governance influence becomes visible data
- No implicit pressure - only explicit signals
- L4/L5 can query WHY they're blocked

## Import Analysis

**L7 Models:**
- `app.models.governance`

**External:**
- `sqlalchemy`
- `sqlalchemy.orm`

## Transaction Boundary

- **Commits:** no
- **Flushes:** yes
- **Rollbacks:** no

## Functions

### `check_governance_status(session: Session, scope: str, signal_type: Optional[str]) -> GovernanceCheckResult`

Check governance status for a scope.

### `is_governance_blocked(session: Session, scope: str, signal_type: Optional[str]) -> bool`

Quick check if scope is blocked.

### `record_governance_signal(session: Session, signal_type: str, scope: str, decision: str, recorded_by: str, reason: Optional[str], constraints: Optional[dict]) -> GovernanceSignal`

Record a governance signal.

## Classes

### `GovernanceSignalService`

Service for governance signal operations.

Phase E: Makes L7 → L4/L5 influence explicit and queryable.

#### Methods

- `__init__(session: Session)` — _No docstring._
- `record_signal(signal_type: str, scope: str, decision: str, recorded_by: str, reason: Optional[str], constraints: Optional[dict], expires_at: Optional[datetime]) -> GovernanceSignal` — Record a new governance signal (L7 → L6 write).
- `_supersede_existing_signals(scope: str, signal_type: str, superseded_at: datetime) -> int` — Mark existing active signals as superseded.
- `check_governance(scope: str, signal_type: Optional[str], include_expired: bool) -> GovernanceCheckResult` — Check governance status for a scope (L4/L5 ← L6 read).
- `is_blocked(scope: str, signal_type: Optional[str]) -> bool` — Quick check if scope is blocked (convenience method).
- `get_active_signals(scope: str, signal_type: Optional[str]) -> list[GovernanceSignal]` — Get all active (non-superseded, non-expired) signals for a scope.
- `clear_signal(scope: str, signal_type: str, cleared_by: str, reason: Optional[str]) -> GovernanceSignal` — Clear a governance block by recording a CLEAN signal.

## Domain Usage

**Callers:** L7 (BLCA, CI) for writes, L4/L5 for reads

## Export Contract

```yaml
exports:
  functions:
    - name: check_governance_status
      signature: "check_governance_status(session: Session, scope: str, signal_type: Optional[str]) -> GovernanceCheckResult"
      consumers: ["orchestrator"]
    - name: is_governance_blocked
      signature: "is_governance_blocked(session: Session, scope: str, signal_type: Optional[str]) -> bool"
      consumers: ["orchestrator"]
    - name: record_governance_signal
      signature: "record_governance_signal(session: Session, signal_type: str, scope: str, decision: str, recorded_by: str, reason: Optional[str], constraints: Optional[dict]) -> GovernanceSignal"
      consumers: ["orchestrator"]
  classes:
    - name: GovernanceSignalService
      methods:
        - record_signal
        - check_governance
        - is_blocked
        - get_active_signals
        - clear_signal
      consumers: ["orchestrator"]
  protocols: []
```

## Import Boundary

```yaml
boundary:
  allowed_inbound:
    - "hoc_spine.orchestrator.*"
    - "hoc_spine.services.*"
  forbidden_inbound:
    - "hoc.cus.*"
    - "hoc.api.*"
  actual_imports:
    spine_internal: []
    l7_model: ['app.models.governance']
    external: ['sqlalchemy', 'sqlalchemy.orm']
  violations: []
```

## L5 Pairing Declaration

```yaml
pairing:
  serves_domains: []
  expected_l5_consumers: []
  orchestrator_operations: []
```

