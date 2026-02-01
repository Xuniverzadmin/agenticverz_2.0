# guard_write_engine.py

**Path:** `backend/app/hoc/cus/hoc_spine/authority/guard_write_engine.py`  
**Layer:** L4 — HOC Spine (Authority)  
**Component:** Authority

---

## Placement Card

```
File:            guard_write_engine.py
Lives in:        authority/
Role:            Authority
Inbound:         api/guard.py
Outbound:        app.hoc.cus.hoc_spine.drivers.guard_write_driver
Transaction:     Forbidden
Cross-domain:    none
Purpose:         Guard Write Engine (L5)
Violations:      none
```

## Purpose

Guard Write Engine (L5)

DB write operations for Guard API.
Delegates to GuardWriteDriver (L6) for all database access.

L2 (API) → L4 (this service) → L6 (GuardWriteDriver)

Responsibilities:
- Delegate to L6 driver for data access
- Maintain backward compatibility for callers

Reference: PIN-250, PHASE2_EXTRACTION_PROTOCOL.md

## Import Analysis

**Spine-internal:**
- `app.hoc.cus.hoc_spine.drivers.guard_write_driver`

**L7 Models:**
- `app.models.killswitch`

**External:**
- `sqlmodel`

## Transaction Boundary

- **Commits:** no
- **Flushes:** no
- **Rollbacks:** no

## Classes

### `GuardWriteService`

DB write operations for Guard Console.

Delegates all operations to GuardWriteDriver (L6).
NO DIRECT DB ACCESS - driver calls only.

#### Methods

- `__init__(session: 'Session')` — _No docstring._
- `get_or_create_killswitch_state(entity_type: str, entity_id: str, tenant_id: str) -> Tuple['KillSwitchState', bool]` — Delegate to driver.
- `freeze_killswitch(state: 'KillSwitchState', by: str, reason: str, auto: bool, trigger: Optional[str]) -> 'KillSwitchState'` — Delegate to driver.
- `unfreeze_killswitch(state: 'KillSwitchState', by: str) -> 'KillSwitchState'` — Delegate to driver.
- `acknowledge_incident(incident: 'Incident') -> 'Incident'` — Delegate to driver.
- `resolve_incident(incident: 'Incident') -> 'Incident'` — Delegate to driver.
- `create_demo_incident(incident_id: str, tenant_id: str, title: str, trigger_type: str, policy_id: str, auto_action: str, events: List[Tuple[str, str]], severity: str, calls_affected: int, cost_delta_cents: Decimal, call_id: Optional[str]) -> Tuple['Incident', List['IncidentEvent']]` — Delegate to driver.

## Domain Usage

**Callers:** api/guard.py

## Export Contract

```yaml
exports:
  functions: []
  classes:
    - name: GuardWriteService
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
  forbidden_inbound:
    - "hoc.cus.*"
    - "hoc.api.*"
  actual_imports:
    spine_internal: ['app.hoc.cus.hoc_spine.drivers.guard_write_driver']
    l7_model: ['app.models.killswitch']
    external: ['sqlmodel']
  violations: []
```

## L5 Pairing Declaration

```yaml
pairing:
  serves_domains: []
  expected_l5_consumers: []
  orchestrator_operations: []
```

