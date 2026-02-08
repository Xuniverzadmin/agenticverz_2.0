# Controls — Prescriptive Wiring Map

**Reference:** HOC_LAYER_TOPOLOGY_V2.0.0.md (RATIFIED)

## Target State

L2.1 Facade: `/root/agenticverz2.0/backend/app/hoc/api/facades/cus/controls.py` ✅
  │
  └──→ L2 API: `hoc/api/cus/controls/` (1 files)
         ├── controls.py
         │
         ├──→ L4 Spine (via hoc_spine/)
                │
                └──→ L5 Engines (3 files)
                       ├── cb_sync_wrapper_engine.py → L6 ❌ (no matching driver)
                       ├── controls_facade.py → L6 ❌ (no matching driver)
                       ├── threshold_engine.py → L6 ✅
                     L5 Schemas (5 files)
                       │
                       └──→ L6 Drivers (10 files)
                              ├── budget_enforcement_driver.py
                              ├── circuit_breaker_async_driver.py
                              ├── circuit_breaker_driver.py
                              ├── killswitch_ops_driver.py
                              ├── killswitch_read_driver.py
                              ├── limits_read_driver.py
                              ├── override_driver.py
                              ├── policy_limits_driver.py
                              └── ... (+2 more)
                              │
                              └──→ L7 Models — **GAP** (no domain models)
                                     FLAG: domain-localized data candidate (human decision)

---

## Gaps

| Type | Description | Action |
|------|-------------|--------|
| L7_models | 10 L6 drivers but no domain-specific L7 models | FLAG: domain-localized data candidate (human decision) |
