# Incidents — Prescriptive Wiring Map

**Reference:** HOC_LAYER_TOPOLOGY_V1.md (RATIFIED, V1.4.0)

## Target State

L2.1 Facade: `hoc/api/facades/cus/incidents.py` — **TO BUILD**
  │
  └──→ L2 API: `hoc/api/cus/incidents/` (2 files)
         ├── cost_guard.py
         ├── incidents.py
         │
         └──→ L3 Adapters (1 files)
                ├── anomaly_bridge.py ✅
                │
                ├──→ L4 Runtime (via general/L4_runtime/)
                │
                └──→ L5 Engines (16 files)
                       ├── hallucination_detector.py → L6 ❌ (no matching driver)
                       ├── incident_driver.py → L6 ❌ (no matching driver)
                       ├── incident_engine.py → L6 ✅
                       ├── incident_pattern_engine.py → L6 ✅
                       ├── incident_read_engine.py → L6 ✅
                       ├── incident_severity_engine.py → L6 ❌ (no matching driver)
                       ├── incident_write_engine.py → L6 ✅
                       ├── incidents_facade.py → L6 ✅
                       ├── incidents_types.py → L6 ❌ (no matching driver)
                       ├── llm_failure_engine.py → L6 ✅
                       └── ... (+6 more)
                       │
                       └──→ L6 Drivers (11 files)
                              ├── export_bundle_driver.py
                              ├── incident_aggregator.py
                              ├── incident_pattern_driver.py
                              ├── incident_read_driver.py
                              ├── incident_write_driver.py
                              ├── incidents_facade_driver.py
                              ├── lessons_driver.py
                              ├── llm_failure_driver.py
                              └── ... (+3 more)
                              │
                              └──→ L7 Models — **GAP** (no domain models)
                                     FLAG: domain-localized data candidate (human decision)

---

## Gaps

| Type | Description | Action |
|------|-------------|--------|
| L2.1_facade | No L2.1 facade to group 2 L2 routers | Build hoc/api/facades/cus/incidents.py grouping: cost_guard.py, incidents.py |
| L7_models | 11 L6 drivers but no domain-specific L7 models | FLAG: domain-localized data candidate (human decision) |

## Violations

| File | Import | Rule Broken | Fix |
|------|--------|-------------|-----|
| `incidents.py` | `from app.models.killswitch import Incident` | L2 MUST NOT import L7 models | Use L5 schemas or response models |
| `incidents.py` | `from app.hoc.cus.incidents.L5_engines.incidents_facade impor` | L2 MUST NOT import L5 directly | Route through L3 adapter |
| `incident_severity_engine.py` | `from app.models.killswitch import IncidentSeverity` | L5 MUST NOT import L7 models directly | Route through L6 driver |
| `incident_write_engine.py` | `from app.models.audit_ledger import ActorType` | L5 MUST NOT import L7 models directly | Route through L6 driver |
