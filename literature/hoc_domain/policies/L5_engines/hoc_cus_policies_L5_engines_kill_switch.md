# hoc_cus_policies_L5_engines_kill_switch

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/policies/L5_engines/kill_switch.py` |
| Layer | L5 — Domain Engine |
| Domain | policies |
| Audience | CUSTOMER |
| Artifact Class | CODE |

## Description

Runtime kill switch for governance bypass (pure state logic)

## Intent

**Role:** Runtime kill switch for governance bypass (pure state logic)
**Reference:** PIN-470, GAP-069
**Callers:** main.py, prevention_engine.py

## Purpose

Kill Switch - Runtime Governance Bypass

---

## Functions

### `activate_kill_switch(reason: str, activated_by: str, auto_expire_minutes: int) -> KillSwitchActivation`
- **Async:** No
- **Docstring:** Activate the runtime kill switch.  When active, governance checks are bypassed (fail-open).
- **Calls:** KillSwitchActivation, KillSwitchStatus, isoformat, now, timedelta, warning

### `deactivate_kill_switch(deactivated_by: str) -> KillSwitchDeactivation`
- **Async:** No
- **Docstring:** Deactivate the runtime kill switch.  Restores normal governance enforcement.
- **Calls:** KillSwitchDeactivation, KillSwitchStatus, info, isoformat, now

### `is_kill_switch_active() -> bool`
- **Async:** No
- **Docstring:** Check if kill switch is currently active.  Also handles auto-expiration.
- **Calls:** KillSwitchStatus, fromisoformat, info, now

### `should_bypass_governance() -> bool`
- **Async:** No
- **Docstring:** Check if governance should be bypassed.  Alias for is_kill_switch_active() for clearer intent.
- **Calls:** is_kill_switch_active

## Classes

### `KillSwitchStatus`
- **Docstring:** Current status of the kill switch.
- **Methods:** get_current
- **Class Variables:** is_active: bool, reason: Optional[str], activated_by: Optional[str], activated_at: Optional[str], auto_expire_at: Optional[str]

### `KillSwitchActivation`
- **Docstring:** Result of kill switch activation.
- **Class Variables:** success: bool, message: str, activated_at: Optional[str], error: Optional[str]

### `KillSwitchDeactivation`
- **Docstring:** Result of kill switch deactivation.
- **Class Variables:** success: bool, message: str, deactivated_at: Optional[str]

## Attributes

- `logger` (line 43)
- `_state_lock` (line 46)
- `_kill_switch_active` (line 47)
- `_kill_switch_status: Optional['KillSwitchStatus']` (line 48)

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
    - name: activate_kill_switch
      signature: "activate_kill_switch(reason: str, activated_by: str, auto_expire_minutes: int) -> KillSwitchActivation"
    - name: deactivate_kill_switch
      signature: "deactivate_kill_switch(deactivated_by: str) -> KillSwitchDeactivation"
    - name: is_kill_switch_active
      signature: "is_kill_switch_active() -> bool"
    - name: should_bypass_governance
      signature: "should_bypass_governance() -> bool"
  classes:
    - name: KillSwitchStatus
      methods: [get_current]
    - name: KillSwitchActivation
      methods: []
    - name: KillSwitchDeactivation
      methods: []
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
