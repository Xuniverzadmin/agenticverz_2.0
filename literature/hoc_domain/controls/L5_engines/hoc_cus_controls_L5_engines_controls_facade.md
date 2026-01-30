# hoc_cus_controls_L5_engines_controls_facade

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/controls/L5_engines/controls_facade.py` |
| Layer | L5 — Domain Engine |
| Domain | controls |
| Audience | CUSTOMER |
| Artifact Class | CODE |

## Description

Controls Facade - Centralized access to control operations

## Intent

**Role:** Controls Facade - Centralized access to control operations
**Reference:** PIN-470, GAP-123 (Controls API)
**Callers:** L2 controls.py API, SDK

## Purpose

Controls Facade (L4 Domain Logic)

---

## Functions

### `get_controls_facade() -> ControlsFacade`
- **Async:** No
- **Docstring:** Get the controls facade instance.  This is the recommended way to access control operations
- **Calls:** ControlsFacade

## Classes

### `ControlType(str, Enum)`
- **Docstring:** Types of controls.

### `ControlState(str, Enum)`
- **Docstring:** Control state.

### `ControlConfig`
- **Docstring:** Control configuration.
- **Methods:** to_dict
- **Class Variables:** id: str, tenant_id: str, name: str, control_type: str, state: str, scope: str, conditions: Optional[Dict[str, Any]], enabled_at: Optional[str], disabled_at: Optional[str], enabled_by: Optional[str], disabled_by: Optional[str], created_at: str, updated_at: Optional[str], metadata: Dict[str, Any]

### `ControlStatusSummary`
- **Docstring:** Overall control status summary.
- **Methods:** to_dict
- **Class Variables:** tenant_id: str, total_controls: int, enabled_count: int, disabled_count: int, auto_count: int, killswitch_active: bool, maintenance_mode: bool, as_of: str

### `ControlsFacade`
- **Docstring:** Facade for control operations.
- **Methods:** __init__, _ensure_default_controls, list_controls, get_control, update_control, enable_control, disable_control, get_status

## Attributes

- `logger` (line 57)
- `_facade_instance: Optional[ControlsFacade]` (line 422)

---

## Import Analysis

| Category | Imports |
|----------|---------|
| _None_ | Pure stdlib |

## Callers

L2 controls.py API, SDK

## Export Contract

```yaml
exports:
  functions:
    - name: get_controls_facade
      signature: "get_controls_facade() -> ControlsFacade"
  classes:
    - name: ControlType
      methods: []
    - name: ControlState
      methods: []
    - name: ControlConfig
      methods: [to_dict]
    - name: ControlStatusSummary
      methods: [to_dict]
    - name: ControlsFacade
      methods: [list_controls, get_control, update_control, enable_control, disable_control, get_status]
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
