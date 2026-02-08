# Analytics — Prescriptive Wiring Map

**Reference:** HOC_LAYER_TOPOLOGY_V2.0.0.md (RATIFIED)

## Target State

L2.1 Facade: `/root/agenticverz2.0/backend/app/hoc/api/facades/cus/analytics.py` ✅
  │
  └──→ L2 API: `hoc/api/cus/analytics/` (4 files)
         ├── costsim.py
         ├── feedback.py
         ├── predictions.py
         ├── scenarios.py
         │
         ├──→ L4 Spine (via hoc_spine/)
                │
                └──→ L5 Engines (18 files)
                       ├── analytics_facade.py → L6 ✅
                       ├── canary_engine.py → L6 ✅
                       ├── config_engine.py → L6 ❌ (no matching driver)
                       ├── cost_anomaly_detector_engine.py → L6 ❌ (no matching driver)
                       ├── cost_model.py → L6 ❌ (no matching driver)
                       ├── cost_snapshots_engine.py → L6 ✅
                       ├── cost_write.py → L6 ❌ (no matching driver)
                       ├── costsim_models.py → L6 ❌ (no matching driver)
                       ├── datasets_engine.py → L6 ❌ (no matching driver)
                       ├── detection_facade.py → L6 ✅
                       └── ... (+8 more)
                     L5 Schemas (5 files)
                       │
                       └──→ L6 Drivers (13 files)
                              ├── analytics_read_driver.py
                              ├── canary_report_driver.py
                              ├── coordination_audit_driver.py
                              ├── cost_anomaly_driver.py
                              ├── cost_anomaly_read_driver.py
                              ├── cost_snapshots_driver.py
                              ├── cost_write_driver.py
                              ├── feedback_read_driver.py
                              └── ... (+5 more)
                              │
                              └──→ L7 Models — **GAP** (no domain models)
                                     FLAG: domain-localized data candidate (human decision)

---

## Gaps

| Type | Description | Action |
|------|-------------|--------|
| L7_models | 13 L6 drivers but no domain-specific L7 models | FLAG: domain-localized data candidate (human decision) |
