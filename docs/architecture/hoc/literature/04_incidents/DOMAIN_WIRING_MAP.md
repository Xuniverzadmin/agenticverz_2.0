# Incidents — Prescriptive Wiring Map

**Reference:** HOC_LAYER_TOPOLOGY_V2.0.0.md (RATIFIED)

## Target State

L2.1 Facade: `/root/agenticverz2.0/backend/app/hoc/api/facades/cus/incidents.py` ✅
  │
  └──→ L2 API: `hoc/api/cus/incidents/` (2 files)
         ├── cost_guard.py
         ├── incidents.py
         │
         ├──→ L4 Spine (via hoc_spine/)
                │
                └──→ L5 Engines (14 files)
                       ├── anomaly_bridge.py → L6 ❌ (no matching driver)
                       ├── export_engine.py → L6 ✅
                       ├── hallucination_detector.py → L6 ❌ (no matching driver)
                       ├── incident_engine.py → L6 ✅
                       ├── incident_pattern.py → L6 ❌ (no matching driver)
                       ├── incident_read_engine.py → L6 ✅
                       ├── incident_write_engine.py → L6 ✅
                       ├── incidents_facade.py → L6 ✅
                       ├── incidents_types.py → L6 ❌ (no matching driver)
                       ├── policy_violation_engine.py → L6 ✅
                       └── ... (+4 more)
                     L5 Schemas (3 files)
                       │
                       └──→ L6 Drivers (13 files)
                              ├── cost_guard_driver.py
                              ├── export_bundle_driver.py
                              ├── incident_aggregator.py
                              ├── incident_driver.py
                              ├── incident_pattern_driver.py
                              ├── incident_read_driver.py
                              ├── incident_write_driver.py
                              ├── incidents_facade_driver.py
                              └── ... (+5 more)
                              │
                              └──→ L7 Models — **GAP** (no domain models)
                                     FLAG: domain-localized data candidate (human decision)

---

## Gaps

| Type | Description | Action |
|------|-------------|--------|
| L7_models | 13 L6 drivers but no domain-specific L7 models | FLAG: domain-localized data candidate (human decision) |
