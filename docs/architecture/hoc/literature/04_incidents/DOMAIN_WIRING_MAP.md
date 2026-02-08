# Incidents — Prescriptive Wiring Map

**Reference:** HOC_LAYER_TOPOLOGY_V1.md (RATIFIED, V1.4.0)

## Target State

L2.1 Facade: `/root/agenticverz2.0/backend/app/hoc/api/facades/cus/incidents.py` ✅
  │
  └──→ L2 API: `hoc/api/cus/incidents/` (2 files)
         ├── cost_guard.py
         ├── incidents.py
         │
         └──→ L3 Adapters — **GAP** (0 files, need domain adapter)
                │
                ├──→ L4 Runtime (via general/L4_runtime/)
                │
                └──→ L5 Engines (9 files)
                       ├── hallucination_detector.py → L6 ❌ (no matching driver)
                       ├── incident_engine.py → L6 ✅
                       ├── incident_read_engine.py → L6 ✅
                       ├── incident_write_engine.py → L6 ✅
                       ├── incidents_facade.py → L6 ✅
                       ├── incidents_types.py → L6 ❌ (no matching driver)
                       ├── policy_violation_engine.py → L6 ✅
                       ├── recovery_rule_engine.py → L6 ❌ (no matching driver)
                       ├── semantic_failures.py → L6 ❌ (no matching driver)
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
| L3_adapter | No L3 adapters but 9 L5 engines exist — L2 cannot reach L5 | Build hoc/cus/incidents/L3_adapters/ with domain adapter(s) |
| L7_models | 11 L6 drivers but no domain-specific L7 models | FLAG: domain-localized data candidate (human decision) |
