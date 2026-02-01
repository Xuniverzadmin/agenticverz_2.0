# hoc_cus_policies_L5_engines_governance_facade

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/policies/L5_engines/governance_facade.py` |
| Layer | L6 — Driver |
| Domain | policies |
| Audience | CUSTOMER |
| Artifact Class | CODE |

## Description

Governance Facade - Centralized access to governance control operations

## Intent

**Role:** Governance Facade - Centralized access to governance control operations
**Reference:** GAP-090, GAP-091, GAP-092, GAP-095
**Callers:** L2 governance.py API, SDK

## Purpose

Governance Facade (L4 Domain Logic)

---

## Functions

### `get_governance_facade() -> GovernanceFacade`
- **Async:** No
- **Docstring:** Get the governance facade instance.  This is the recommended way to access governance control operations
- **Calls:** GovernanceFacade

## Classes

### `GovernanceMode(str, Enum)`
- **Docstring:** Governance operation modes.

### `GovernanceStateResult`
- **Docstring:** Result of governance state query.
- **Methods:** to_dict
- **Class Variables:** mode: GovernanceMode, active: bool, degraded_mode: bool, last_changed: Optional[datetime], last_change_reason: Optional[str], last_change_actor: Optional[str]

### `KillSwitchResult`
- **Docstring:** Result of kill switch operation.
- **Methods:** to_dict
- **Class Variables:** success: bool, previous_mode: GovernanceMode, current_mode: GovernanceMode, timestamp: datetime, actor: str, reason: Optional[str], error: Optional[str]

### `ConflictResolutionResult`
- **Docstring:** Result of conflict resolution.
- **Methods:** to_dict
- **Class Variables:** success: bool, conflict_id: str, resolution: str, resolved_by: str, resolved_at: datetime, affected_policies: List[str], error: Optional[str]

### `BootStatusResult`
- **Docstring:** Result of boot status check.
- **Methods:** to_dict
- **Class Variables:** healthy: bool, components: Dict[str, Dict[str, Any]], boot_time: Optional[datetime], uptime_seconds: Optional[int]

### `GovernanceFacade`
- **Docstring:** Facade for governance control operations.
- **Methods:** __init__, enable_kill_switch, disable_kill_switch, set_mode, get_governance_state, resolve_conflict, list_conflicts, get_boot_status

## Attributes

- `logger` (line 59)
- `_facade_instance: Optional[GovernanceFacade]` (line 602)

---

## Import Analysis

| Category | Imports |
|----------|---------|
| L5 Engine | `app.hoc.cus.policies.L5_engines.policy_driver` |
| External | `app.hoc.cus.hoc_spine.authority.runtime_switch` |

## Callers

L2 governance.py API, SDK

## Export Contract

```yaml
exports:
  functions:
    - name: get_governance_facade
      signature: "get_governance_facade() -> GovernanceFacade"
  classes:
    - name: GovernanceMode
      methods: []
    - name: GovernanceStateResult
      methods: [to_dict]
    - name: KillSwitchResult
      methods: [to_dict]
    - name: ConflictResolutionResult
      methods: [to_dict]
    - name: BootStatusResult
      methods: [to_dict]
    - name: GovernanceFacade
      methods: [enable_kill_switch, disable_kill_switch, set_mode, get_governance_state, resolve_conflict, list_conflicts, get_boot_status]
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
