# hoc_cus_controls_L5_controls_customer_killswitch_read_engine

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/controls/L5_controls/engines/customer_killswitch_read_engine.py` |
| Layer | L5 — Domain Engine |
| Domain | controls |
| Audience | CUSTOMER |
| Artifact Class | CODE |

## Description

Customer killswitch read operations (L5 engine over L6 driver)

## Intent

**Role:** Customer killswitch read operations (L5 engine over L6 driver)
**Reference:** PIN-280, PIN-281, PHASE2_EXTRACTION_PROTOCOL.md
**Callers:** customer_killswitch_adapter.py (L3)

## Purpose

Customer Killswitch Read Service (L4)

---

## Functions

### `get_customer_killswitch_read_service() -> CustomerKillswitchReadService`
- **Async:** No
- **Docstring:** Get the singleton CustomerKillswitchReadService instance.  This is the ONLY way L3 should obtain a killswitch read service.
- **Calls:** CustomerKillswitchReadService

## Classes

### `KillswitchState(BaseModel)`
- **Docstring:** Killswitch state information.
- **Class Variables:** is_frozen: bool, frozen_at: Optional[datetime], frozen_by: Optional[str]

### `GuardrailInfo(BaseModel)`
- **Docstring:** Active guardrail information.
- **Class Variables:** name: str

### `IncidentStats(BaseModel)`
- **Docstring:** Incident statistics for a tenant.
- **Class Variables:** incidents_blocked_24h: int, last_incident_time: Optional[datetime]

### `KillswitchStatusInfo(BaseModel)`
- **Docstring:** Complete killswitch status information.
- **Class Variables:** state: KillswitchState, active_guardrails: List[str], incident_stats: IncidentStats

### `CustomerKillswitchReadService`
- **Docstring:** Read operations for customer killswitch status.
- **Methods:** __init__, get_killswitch_status

## Attributes

- `_customer_killswitch_read_service_instance: Optional[CustomerKillswitchReadService]` (line 148)
- `__all__` (line 171)

---

## Import Analysis

| Category | Imports |
|----------|---------|
| External | `app.hoc.cus.policies.controls.drivers.killswitch_read_driver`, `pydantic`, `sqlmodel` |

## Callers

customer_killswitch_adapter.py (L3)

## Export Contract

```yaml
exports:
  functions:
    - name: get_customer_killswitch_read_service
      signature: "get_customer_killswitch_read_service() -> CustomerKillswitchReadService"
  classes:
    - name: KillswitchState
      methods: []
    - name: GuardrailInfo
      methods: []
    - name: IncidentStats
      methods: []
    - name: KillswitchStatusInfo
      methods: []
    - name: CustomerKillswitchReadService
      methods: [get_killswitch_status]
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
