# guard_write_driver.py

**Path:** `backend/app/hoc/hoc_spine/drivers/guard_write_driver.py`  
**Layer:** L4 — HOC Spine (Driver)  
**Component:** Drivers

---

## Placement Card

```
File:            guard_write_driver.py
Lives in:        drivers/
Role:            Drivers
Inbound:         guard engines (L5)
Outbound:        app.hoc.hoc_spine.services.time
Transaction:     Forbidden
Cross-domain:    none
Purpose:         Guard Write Driver (L6)
Violations:      none
```

## Purpose

Guard Write Driver (L6)

Pure database write operations for Guard Console (KillSwitch, Incidents).

L4 (GuardWriteService) → L6 (this driver)

Responsibilities:
- Get/create KillSwitchState records
- Freeze/unfreeze killswitch
- Acknowledge/resolve incidents
- Create demo incidents with events
- NO business logic (L4 responsibility)

Reference: PIN-250, PHASE2_EXTRACTION_PROTOCOL.md

## Import Analysis

**Spine-internal:**
- `app.hoc.hoc_spine.services.time`

**L7 Models:**
- `app.models.killswitch`

**External:**
- `sqlalchemy`
- `sqlmodel`

## Transaction Boundary

- **Commits:** no
- **Flushes:** no
- **Rollbacks:** no

## Functions

### `get_guard_write_driver(session: Session) -> GuardWriteDriver`

Factory function to get GuardWriteDriver instance.

## Classes

### `GuardWriteDriver`

L6 driver for guard write operations.

Pure database access - no business logic.

#### Methods

- `__init__(session: Session)` — _No docstring._
- `get_or_create_killswitch_state(entity_type: str, entity_id: str, tenant_id: str) -> Tuple[KillSwitchState, bool]` — Get existing KillSwitchState or create a new unfrozen one.
- `freeze_killswitch(state: KillSwitchState, by: str, reason: str, auto: bool, trigger: Optional[str]) -> KillSwitchState` — Freeze a KillSwitchState and persist.
- `unfreeze_killswitch(state: KillSwitchState, by: str) -> KillSwitchState` — Unfreeze a KillSwitchState and persist.
- `acknowledge_incident(incident: Incident) -> Incident` — Mark an incident as acknowledged and persist.
- `resolve_incident(incident: Incident) -> Incident` — Mark an incident as resolved and persist.
- `create_demo_incident(incident_id: str, tenant_id: str, title: str, trigger_type: str, policy_id: str, auto_action: str, events: List[Tuple[str, str]], severity: str, calls_affected: int, cost_delta_cents: Decimal, call_id: Optional[str]) -> Tuple[Incident, List[IncidentEvent]]` — Create a demo incident with timeline events for onboarding verification.

## Domain Usage

**Callers:** guard engines (L5)

## Export Contract

```yaml
exports:
  functions:
    - name: get_guard_write_driver
      signature: "get_guard_write_driver(session: Session) -> GuardWriteDriver"
      consumers: ["orchestrator"]
  classes:
    - name: GuardWriteDriver
      methods:
        - get_or_create_killswitch_state
        - freeze_killswitch
        - unfreeze_killswitch
        - acknowledge_incident
        - resolve_incident
        - create_demo_incident
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
    spine_internal: ['app.hoc.hoc_spine.services.time']
    l7_model: ['app.models.killswitch']
    external: ['sqlalchemy', 'sqlmodel']
  violations: []
```

## L5 Pairing Declaration

```yaml
pairing:
  serves_domains: []
  expected_l5_consumers: []
  orchestrator_operations: []
```

