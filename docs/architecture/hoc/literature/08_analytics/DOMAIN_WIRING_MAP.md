# Analytics — Prescriptive Wiring Map

**Reference:** HOC_LAYER_TOPOLOGY_V1.md (RATIFIED, V1.4.0)

## Target State

L2.1 Facade: `/root/agenticverz2.0/backend/app/hoc/api/facades/cus/analytics.py` ✅
  │
  └──→ L2 API: `hoc/api/cus/analytics/` (4 files)
         ├── costsim.py
         ├── feedback.py
         ├── predictions.py
         ├── scenarios.py
         │
         └──→ L3 Adapters — **GAP** (0 files, need domain adapter)
                │
                ├──→ L4 Runtime (via general/L4_runtime/)
                │
                └──→ L5 Engines (4 files)
                       ├── analytics_facade.py → L6 ✅
                       ├── costsim_models.py → L6 ❌ (no matching driver)
                       ├── detection_facade.py → L6 ✅
                       ├── provenance.py → L6 ❌ (no matching driver)
                     L5 Schemas (1 files)
                       │
                       └──→ L6 Drivers (5 files)
                              ├── analytics_read_driver.py
                              ├── cost_anomaly_driver.py
                              ├── cost_write_driver.py
                              ├── pattern_detection_driver.py
                              ├── prediction_driver.py
                              │
                              └──→ L7 Models — **GAP** (no domain models)
                                     FLAG: domain-localized data candidate (human decision)

---

## Gaps

| Type | Description | Action |
|------|-------------|--------|
| L3_adapter | No L3 adapters but 4 L5 engines exist — L2 cannot reach L5 | Build hoc/cus/analytics/L3_adapters/ with domain adapter(s) |
| L7_models | 5 L6 drivers but no domain-specific L7 models | FLAG: domain-localized data candidate (human decision) |
