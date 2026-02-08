# Activity — Prescriptive Wiring Map

**Reference:** HOC_LAYER_TOPOLOGY_V2.0.0.md (RATIFIED)

## Target State

L2.1 Facade: `/root/agenticverz2.0/backend/app/hoc/api/facades/cus/activity.py` ✅
  │
  └──→ L2 API: `hoc/api/cus/activity/` (1 files)
         ├── activity.py
         │
         ├──→ L4 Spine (via hoc_spine/)
                │
                └──→ L5 Engines (8 files)
                       ├── activity_enums.py → L6 ❌ (no matching driver)
                       ├── activity_facade.py → L6 ✅
                       ├── attention_ranking.py → L6 ❌ (no matching driver)
                       ├── cost_analysis.py → L6 ❌ (no matching driver)
                       ├── cus_telemetry_engine.py → L6 ✅
                       ├── pattern_detection.py → L6 ❌ (no matching driver)
                       ├── signal_feedback_engine.py → L6 ❌ (no matching driver)
                       ├── signal_identity.py → L6 ❌ (no matching driver)
                       │
                       └──→ L6 Drivers (4 files)
                              ├── activity_read_driver.py
                              ├── cus_telemetry_driver.py
                              ├── orphan_recovery_driver.py
                              ├── run_signal_driver.py
                              │
                              └──→ L7 Models — **GAP** (no domain models)
                                     FLAG: domain-localized data candidate (human decision)

---

## Gaps

| Type | Description | Action |
|------|-------------|--------|
| L7_models | 4 L6 drivers but no domain-specific L7 models | FLAG: domain-localized data candidate (human decision) |
