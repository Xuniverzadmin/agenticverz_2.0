# hoc_cus_controls_L5_engines_killswitch

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/controls/L5_engines/killswitch.py` |
| Layer | L5 — Domain Engine |
| Domain | controls |
| Audience | CUSTOMER |
| Artifact Class | CODE |

## Description

Optimization killswitch for emergency stops (pure state logic)

## Intent

**Role:** Optimization killswitch for emergency stops (pure state logic)
**Reference:** C3_KILLSWITCH_ROLLBACK_MODEL.md (FROZEN)
**Callers:** API routes, workers

## Purpose

_No module docstring._

---

## Functions

### `get_killswitch() -> KillSwitch`
- **Async:** No
- **Docstring:** Get the global kill-switch instance.
- **Calls:** KillSwitch

### `reset_killswitch_for_testing() -> None`
- **Async:** No
- **Docstring:** Reset kill-switch state. FOR TESTING ONLY.
- **Calls:** KillSwitch

## Classes

### `KillSwitchState(str, Enum)`
- **Docstring:** Global kill-switch state. Exactly two values. No partial states.

### `KillSwitchTrigger(str, Enum)`
- **Docstring:** What triggered the kill-switch.

### `RollbackStatus(str, Enum)`
- **Docstring:** Status of rollback operation.

### `KillSwitchEvent`
- **Docstring:** Immutable audit record for kill-switch events.
- **Class Variables:** event_id: str, triggered_by: KillSwitchTrigger, trigger_reason: str, activated_at: datetime, active_envelopes_count: int, rollback_completed_at: Optional[datetime], rollback_status: RollbackStatus

### `KillSwitch`
- **Docstring:** Global, authoritative kill-switch for C3 optimization.
- **Methods:** __init__, state, is_enabled, is_disabled, activate, mark_rollback_complete, rearm, on_activate, get_events, get_last_event

## Attributes

- `logger` (line 40)
- `_killswitch: Optional[KillSwitch]` (line 245)
- `_killswitch_lock` (line 246)

---

## Import Analysis

| Category | Imports |
|----------|---------|
| _None_ | Pure stdlib |

## Callers

API routes, workers

## Export Contract

```yaml
exports:
  functions:
    - name: get_killswitch
      signature: "get_killswitch() -> KillSwitch"
    - name: reset_killswitch_for_testing
      signature: "reset_killswitch_for_testing() -> None"
  classes:
    - name: KillSwitchState
      methods: []
    - name: KillSwitchTrigger
      methods: []
    - name: RollbackStatus
      methods: []
    - name: KillSwitchEvent
      methods: []
    - name: KillSwitch
      methods: [state, is_enabled, is_disabled, activate, mark_rollback_complete, rearm, on_activate, get_events, get_last_event]
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
