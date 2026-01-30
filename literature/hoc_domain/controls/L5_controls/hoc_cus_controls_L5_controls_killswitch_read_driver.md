# hoc_cus_controls_L5_controls_killswitch_read_driver

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/controls/L5_controls/drivers/killswitch_read_driver.py` |
| Layer | L6 — Driver |
| Domain | controls |
| Audience | CUSTOMER |
| Artifact Class | CODE |

## Description

Data access for killswitch read operations

## Intent

**Role:** Data access for killswitch read operations
**Reference:** PIN-280, PIN-281, PHASE2_EXTRACTION_PROTOCOL.md
**Callers:** killswitch engines (L4)

## Purpose

Killswitch Read Driver (L6)

---

## Functions

### `get_killswitch_read_driver(session: Optional[Session]) -> KillswitchReadDriver`
- **Async:** No
- **Docstring:** Get KillswitchReadDriver instance.  Args:
- **Calls:** KillswitchReadDriver

## Classes

### `KillswitchStateDTO(BaseModel)`
- **Docstring:** Killswitch state information.
- **Class Variables:** is_frozen: bool, frozen_at: Optional[datetime], frozen_by: Optional[str]

### `GuardrailInfoDTO(BaseModel)`
- **Docstring:** Active guardrail information.
- **Class Variables:** name: str

### `IncidentStatsDTO(BaseModel)`
- **Docstring:** Incident statistics for a tenant.
- **Class Variables:** incidents_blocked_24h: int, last_incident_time: Optional[datetime]

### `KillswitchStatusDTO(BaseModel)`
- **Docstring:** Complete killswitch status information.
- **Class Variables:** state: KillswitchStateDTO, active_guardrails: List[str], incident_stats: IncidentStatsDTO

### `KillswitchReadDriver`
- **Docstring:** L6 driver for killswitch read operations.
- **Methods:** __init__, _get_session, get_killswitch_status, _get_killswitch_state, _get_active_guardrails, _get_incident_stats

## Attributes

- `__all__` (line 221)

---

## Import Analysis

| Category | Imports |
|----------|---------|
| L7 Model | `app.models.killswitch` |
| External | `app.db`, `pydantic`, `sqlalchemy`, `sqlmodel` |

## Callers

killswitch engines (L4)

## Export Contract

```yaml
exports:
  functions:
    - name: get_killswitch_read_driver
      signature: "get_killswitch_read_driver(session: Optional[Session]) -> KillswitchReadDriver"
  classes:
    - name: KillswitchStateDTO
      methods: []
    - name: GuardrailInfoDTO
      methods: []
    - name: IncidentStatsDTO
      methods: []
    - name: KillswitchStatusDTO
      methods: []
    - name: KillswitchReadDriver
      methods: [get_killswitch_status]
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
