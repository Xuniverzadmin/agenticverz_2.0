# incidents_bridge.py

**Path:** `backend/app/hoc/cus/hoc_spine/orchestrator/coordinators/bridges/incidents_bridge.py`
**Layer:** L4 — HOC Spine (Bridge)
**Component:** Orchestrator / Coordinator / Bridge
**Created:** 2026-02-06
**Reference:** PIN-520 Iter3.1 (L4 Uniformity Initiative)

---

## Placement Card

```
File:            incidents_bridge.py
Lives in:        orchestrator/coordinators/bridges/
Role:            Incidents domain capability factory
Inbound:         hoc_spine/orchestrator/handlers/incidents_*.py
Outbound:        incidents/L5_engines/*, incidents/L6_drivers/* (lazy imports)
Transaction:     none (factory only)
Cross-domain:    no (single domain)
Purpose:         Bridge for incidents L5 engine and L6 driver access from L4
Violations:      none
```

## Purpose

Domain-specific capability factory for incidents domain.
Implements the Switchboard Pattern (Law 4 - PIN-507):

- Never accepts session parameters (except where noted for sync capabilities)
- Returns module references for lazy access
- Handler binds session (Law 4 responsibility)
- No retry logic, no decisions, no state

## Capabilities

### IncidentsBridge (L4 -> L5/L6, primary capabilities)

| Method | Returns | L5/L6 Module |
|--------|---------|--------------|
| `incident_read_capability()` | Incident read factory | L5 IncidentQueryEngine - PIN-520 Iter3.1 (2026-02-06) |
| `incident_write_capability()` | Incident write factory | L5 IncidentWriteEngine - PIN-520 Iter3.1 (2026-02-06) |
| `lessons_capability()` | Lessons learned factory | L5 LessonsEngine - PIN-520 Iter3.1 (2026-02-06) |
| `export_capability()` | Export factory | L5 IncidentExportEngine - PIN-520 Iter3.1 (2026-02-06) |
| `incidents_for_run_capability()` | Incidents for run query factory | L5 IncidentQueryEngine - PIN-520 Iter3.1 (2026-02-06) |

### IncidentsEngineBridge (L4 -> L5 engine access, extended capabilities)

| Method | Returns | L5 Module |
|--------|---------|-----------|
| `recovery_rule_engine_capability()` | Recovery rule engine factory | L5 RecoveryRuleEngine - PIN-520 Iter3.1 (2026-02-06) |
| `evidence_recorder_capability()` | Evidence recorder factory | L5 EvidenceRecorderEngine - PIN-520 Iter3.1 (2026-02-06) |

## Usage Pattern

```python
from app.hoc.cus.hoc_spine.orchestrator.coordinators.bridges.incidents_bridge import (
    get_incidents_bridge,
    get_incidents_engine_bridge,
)

bridge = get_incidents_bridge()

# Get incident read capability
reader = bridge.incident_read_capability()
incidents = await reader.get_incidents(session, filters)

# Get incident write capability
writer = bridge.incident_write_capability()
incident_id = await writer.create_incident(session, incident_data)

# Get lessons capability
lessons = bridge.lessons_capability()
lesson = await lessons.record_lesson(session, incident_id, lesson_data)

# Get export capability
exporter = bridge.export_capability()
export_data = await exporter.export_incidents(session, export_params)

# Get incidents for run capability
run_incidents = bridge.incidents_for_run_capability()
incidents = await run_incidents.get_incidents_for_run(session, run_id)

# Extended engine bridge usage
engine_bridge = get_incidents_engine_bridge()

# Get recovery rule engine capability
recovery = engine_bridge.recovery_rule_engine_capability()
rules = await recovery.evaluate_rules(session, incident_data)

# Get evidence recorder capability
recorder = engine_bridge.evidence_recorder_capability()
await recorder.record_evidence(session, incident_id, evidence_data)
```

## Bridge Contract

| Rule | Enforcement |
|------|-------------|
| Max 5 methods per bridge class | CI check 19 |
| Returns modules (not sessions) | Code review |
| Lazy imports only | No top-level L5/L6 imports |
| L4 handlers only | Forbidden import check |

**Note:** `IncidentsEngineBridge` exists to keep the base bridge within the 5-method limit.

## PIN-520 Iter3.1 (L4 Uniformity Initiative)

This bridge was created as part of PIN-520 Iter3.1 (Bridge Completion).
Provides comprehensive L4 bridge access for incidents domain including:

- Incident read/write operations
- Lessons learned management
- Incident export functionality
- Run-based incident queries
- Recovery rule evaluation
- Evidence recording

## Singleton Access

```python
_bridge_instance: IncidentsBridge | None = None
_engine_bridge_instance: IncidentsEngineBridge | None = None

def get_incidents_bridge() -> IncidentsBridge:
    global _bridge_instance
    if _bridge_instance is None:
        _bridge_instance = IncidentsBridge()
    return _bridge_instance

def get_incidents_engine_bridge() -> IncidentsEngineBridge:
    global _engine_bridge_instance
    if _engine_bridge_instance is None:
        _engine_bridge_instance = IncidentsEngineBridge()
    return _engine_bridge_instance
```

---

*Generated: 2026-02-06*
